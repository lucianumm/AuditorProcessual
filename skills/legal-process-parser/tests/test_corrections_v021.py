"""Regressions for the 0.21 corrections; synthetic parameters, not legal rules."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.labor_calculations import compute_calculations
from scripts.labor_ledger import apportion_workdays
from scripts.labor_parameters import review_parameters
from scripts.labor_time import count_date_window, count_deadline, working_day
from scripts.numeric_criteria import quantities
from scripts.petition_workspace import archive_markdown
from scripts.time_bank import reconcile_bank
from tests.test_labor_workflow import ledger_fixture
from tests.test_labor_specialization import calculation_fixture
from tests.test_response_research import numeric_fixture


def night_rule(**extra):
    rule = ledger_fixture()["rules"][0]
    rule.update({"night_window": {"start": "22:00", "end": "05:00", "unit_minutes": "52.5"}, "night_reduction": True,
                 "limit_basis": "legal", "daily_limit_minutes": "480", "weekly_limit_minutes": "2640", **extra})
    return rule


class Windows(unittest.TestCase):
    def test_civil_code_next_day_policy(self):
        base = {"unit": "years", "quantity": 1, "direction": "forward", "adjustments": []}
        self.assertEqual(count_date_window(dict(base, anchor_date="2024-02-29", leap_policy="next_day"))["date"], "2025-03-01")
        self.assertEqual(count_date_window(dict(base, anchor_date="2024-02-29", leap_policy="last_valid_day"))["date"], "2025-02-28")
        month = dict(base, unit="months", anchor_date="2024-01-31", leap_policy="next_day")
        self.assertEqual(count_date_window(month)["date"], "2024-03-01")
        with self.assertRaises(ValueError):
            count_date_window(dict(base, anchor_date="2024-02-29", leap_policy="strict"))

    def test_calendar_deadline_moves_only_with_supplied_calendar(self):
        record = {"event_date": "2026-10-01", "days": 3, "include_event_day": False, "mode": "calendar",
                  "trigger_fact_id": "F1", "norm_id": "N1", "jurisdiction": "Sintético", "holidays": [], "suspensions": []}
        self.assertEqual(count_deadline(record)["due_date"], "2026-10-04")
        moved = count_deadline(dict(record, shift_to_business_day=True, calendar_norm_ids=["N2"]))
        self.assertEqual((moved["due_date"], moved["shifted_from"]), ("2026-10-05", "2026-10-04"))
        with self.assertRaises(ValueError):
            count_deadline(dict(record, shift_to_business_day=True))

    def test_utc_z_suffix_and_rounded_workday(self):
        result = working_day({"clock_in": "2026-06-01T12:00:00Z", "clock_out": "2026-06-01T20:00:07Z",
                              "break_minutes": 0, "fact_ids": ["F1"]})
        self.assertEqual(result["worked_minutes"], "480.1167")


class Ledger(unittest.TestCase):
    def test_workplace_clock_decides_night_minutes(self):
        payload = ledger_fixture()
        payload["rules"] = [night_rule(workplace_utc_offset="-03:00", night_reduction=False, limit_basis="physical")]
        payload["days"][0]["intervals"] = [{"start": "2026-06-02T01:00:00+00:00", "end": "2026-06-02T10:00:00+00:00"}]
        self.assertEqual(apportion_workdays(payload)["days"][0]["night_minutes"], "420")
        del payload["rules"][0]["workplace_utc_offset"]
        self.assertEqual(apportion_workdays(payload)["days"][0]["night_minutes"], "240")

    def test_reduced_hour_has_no_decimal_residue(self):
        payload = ledger_fixture()
        payload["rules"] = [night_rule(weekly_limit_minutes="800", daily_limit_minutes="480")]
        payload["days"] = [dict(payload["days"][0], id="D" + str(i), date="2026-06-0" + str(i + 1),
                                intervals=[{"start": f"2026-06-0{i + 1}T22:00:00-03:00", "end": f"2026-06-0{i + 1}T23:40:00-03:00"}])
                           for i in range(7)]
        result = apportion_workdays(payload)
        self.assertEqual(result["days"][0]["legal_minutes"], "114.2857")
        self.assertEqual(result["weeks"][0]["additional_weekly_minutes"], "0")

    def test_supplied_night_extension_rule(self):
        payload = ledger_fixture()
        rule = night_rule(night_reduction=False, limit_basis="physical")
        rule["night_window"]["extension"] = "after_full_window"
        payload["rules"] = [rule]
        payload["days"][0]["intervals"] = [{"start": "2026-06-01T22:00:00-03:00", "end": "2026-06-02T07:00:00-03:00"}]
        self.assertEqual(apportion_workdays(payload)["days"][0]["night_minutes"], "540")

    def test_breaks_rest_gap_and_rest_day_work(self):
        payload = ledger_fixture()
        payload["rules"][0].update(intrajornada={"threshold_minutes": "360", "min_break_minutes": "60"},
                                   interjornada_min_minutes="660")
        payload["days"] = [
            dict(payload["days"][0], intervals=[{"start": "2026-06-01T08:00:00-03:00", "end": "2026-06-01T12:00:00-03:00"},
                                                {"start": "2026-06-01T12:30:00-03:00", "end": "2026-06-01T22:00:00-03:00"}]),
            dict(payload["days"][0], id="DAY2", date="2026-06-02",
                 intervals=[{"start": "2026-06-02T06:00:00-03:00", "end": "2026-06-02T10:00:00-03:00"}]),
            dict(payload["days"][0], id="DAY7", date="2026-06-07", day_status="rest_day_worked",
                 intervals=[{"start": "2026-06-07T08:00:00-03:00", "end": "2026-06-07T12:00:00-03:00"}])]
        result = apportion_workdays(payload)
        first, second, rest = result["days"]
        self.assertEqual((first["break_minutes"], first["intrajornada_shortfall_minutes"]), ("30", "30"))
        self.assertEqual((second["interjornada_gap_minutes"], second["interjornada_shortfall_minutes"]), ("480", "180"))
        self.assertEqual((rest["rest_day_work_minutes"], rest["daily_excess_minutes"]), ("240", "0"))
        self.assertEqual(result["weeks"][0]["total_excess_without_double_count"], "330")


class Calculations(unittest.TestCase):
    def test_percent_requires_explicit_division(self):
        data = calculation_fixture()
        data["inputs"][3].update(value="50", unit="percent")
        data["items"][0]["expression"] = "sal / div * horas * fator"
        with self.assertRaisesRegex(ValueError, "percentual"):
            compute_calculations(data)
        data["items"][0].update(expression="sal / div * horas * fator / 100", expected_result="50.00")
        data["items"][1]["expected_result"] = "10.00"
        self.assertEqual(compute_calculations(data)["items"][0]["result"], "50.00")

    def test_min_max_floor_and_reserved_names(self):
        data = calculation_fixture()
        data["items"][0].update(expression="max(0, pago - sal)", bindings={"pago": "PAGO", "sal": "SAL"}, expected_result="0.00")
        data["items"][1]["expected_result"] = "0.00"
        self.assertEqual(compute_calculations(data)["items"][0]["result"], "0.00")
        data["items"][0].update(expression="max(sal, horas)", bindings={"sal": "SAL", "horas": "H"})
        with self.assertRaisesRegex(ValueError, "unidades"):
            compute_calculations(data)
        data["items"][0].update(expression="min(sal)", bindings={"sal": "SAL"})
        with self.assertRaisesRegex(ValueError, "min"):
            compute_calculations(data)

    def test_total_follows_item_rounding_mode(self):
        data = calculation_fixture()
        data["rounding"] = "final_only"
        data["inputs"].append({"id": "HALF", "value": "0.005", "unit": "money", "fact_ids": ["F"], "norm_ids": [], "reason": "Fixture."})
        data["items"] = [{"id": "X", "relationship_id": "REL1", "competence": "2026-01", "claim_type": "x", "segment": "s",
                          "kind": "principal", "expression": "h", "bindings": {"h": "HALF"}, "norm_ids": ["N"],
                          "request_ids": ["R"], "expected_result": "0.00", "include_in_total": True, "reason": "Fixture.",
                          "rounding_mode": "HALF_EVEN"}]
        result = compute_calculations(data)
        self.assertEqual((result["total"], result["total_rounding_mode"]), ("0.00", "HALF_EVEN"))

    def test_payment_input_cannot_be_abated_twice(self):
        data = calculation_fixture()
        data["inputs"][5]["role"] = "payment"
        second = dict(data["items"][2], id="AB2", claim_type="outro", payment_fact_ids=["F-PAGO-2"])
        data["items"].append(second)
        with self.assertRaisesRegex(ValueError, "pagamento"):
            compute_calculations(data)


class NumericCriteria(unittest.TestCase):
    def test_statutory_spellings(self):
        rows = quantities("A hora noturna será computada como de 52 minutos e 30 segundos.")
        self.assertIn(("52.5", "minutes"), {(r["value"], r["unit"]) for r in rows})
        third = quantities("com, pelo menos, um terço a mais do que o salário normal")
        self.assertEqual([(r["unit"], r["relation"]) for r in third], [("fraction", "minimum")])
        self.assertEqual({r["relation"] for r in quantities("20% (vinte por cento), pelo menos")}, {"minimum"})
        self.assertEqual(quantities("superior, no mínimo, em cinquenta por cento")[0]["relation"], "minimum")
        self.assertEqual(quantities("o resgate 30 dias depois")[0]["relation"], "exact")

    def test_non_terminating_transformation_at_declared_precision(self):
        payload, checks, review, cites, texts = numeric_fixture()
        texts[cites[0]["source_record_id"]] = "Critério sintético de 50 minutos, aplica-se ao exercício."
        payload["inputs"][1].update(value="0.833333", unit="hours")
        payload["items"][0].update(expression="sal * rate / 100", expected_result="18.33")
        checks["inputs"][1].update(source_value="50", transform="minutes_to_hours",
                                   quote="Critério sintético de 50 minutos, aplica-se ao exercício.")
        payload["inputs"][1]["unit"] = "hours"
        result = review_parameters(payload, checks, review, cites, texts)
        self.assertFalse([e for e in result["errors"] if "RATE" in e and ("valor" in e or "condição" in e)], result["errors"])
        payload["inputs"][1]["value"] = "0.83"
        self.assertTrue(any("RATE: valor" in e for e in review_parameters(payload, checks, review, cites, texts)["errors"]))


class Records(unittest.TestCase):
    def test_bank_expired_credit_and_negative_balance_need_review(self):
        credit = {"id": "C", "relationship_id": "REL1", "kind": "credit", "date": "2026-06-01", "minutes": "120",
                  "expires_on": "2026-06-30", "fact_ids": ["F1"], "norm_ids": ["N1"], "allocations": []}
        debit = dict(credit, id="D", kind="debit", date="2026-06-02", minutes="180", expires_on=None,
                     allocations=[{"credit_id": "C", "minutes": "120"}])
        result = reconcile_bank({"schema_version": "1.0", "as_of": "2026-07-02", "movements": [credit, debit]})
        self.assertEqual(result["status"], "requires_review")
        self.assertIn("debit_without_identified_credit", {f["cause"] for f in result["findings"]})
        debit.update(minutes="60", allocations=[{"credit_id": "C", "minutes": "60"}])
        causes = {f["cause"] for f in reconcile_bank({"schema_version": "1.0", "as_of": "2026-07-02", "movements": [credit, debit]})["findings"]}
        self.assertEqual(causes, {"expired_credit_with_remaining_minutes"})

    def test_archived_link_keeps_text_and_tolerates_outside_targets(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "memoria_processual.md").write_text("# memória\n", encoding="utf-8")
            text = "[memoria_processual.md](memoria_processual.md) e [fora](../fora.md)\n"
            archive_markdown(output, "historico/relatorio/relatorio.md", text)
            archived = (output / "historico/relatorio/relatorio.md").read_text(encoding="utf-8")
            self.assertIn("[memoria_processual.md](../../memoria_processual.md)", archived)
            self.assertIn("[fora](../fora.md)", archived)


if __name__ == "__main__":
    unittest.main()
