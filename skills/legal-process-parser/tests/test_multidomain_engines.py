"""Suíte abrangente (offline) dos motores determinísticos multidomínio, DataJud, índices BCB e lookup legislativo."""
from __future__ import annotations

import io
import json
import ssl
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

CORE = Path(__file__).resolve().parents[1]
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from scripts.civil_monetary_engine import (  # noqa: E402
    calculate_monetary_update,
    compare_bank_rate,
    main as monetary_main,
)
from scripts.datajud_lookup import (  # noqa: E402
    build_query_payload,
    lookup_process,
    main as datajud_main,
    parse_datajud_hit,
    resolve_endpoint,
)
from scripts.deadline_calculator import (  # noqa: E402
    calculate_deadline,
    easter_sunday,
    main as deadline_main,
    national_holidays,
)
from scripts.helpers import cnj_check_digits  # noqa: E402
from scripts.legislation_lookup import _get_json, parse_act  # noqa: E402
from scripts.limitation_checker import (  # noqa: E402
    PROFILES,
    check_limitation,
    main as limitation_main,
)
from scripts.official_indices import (  # noqa: E402
    KNOWN_SERIES,
    accumulate,
    br_date,
    compute_lei_14905_interest,
    main as indices_main,
    parse_series,
)
from scripts.penal_dosimetry import (  # noqa: E402
    calculate_dosimetry,
    calculate_lep_progression,
    calculate_penal_prescription,
)
from scripts.social_security_calc import (  # noqa: E402
    check_rgps_decadencia_prescricao,
    convert_special_time,
    evaluate_rgps_eligibility,
    merge_intervals,
)
from scripts.source_records import inspect_source_record  # noqa: E402


def make_cnj(seq: str, year: str, seg: str, court: str, origin: str) -> str:
    seq7 = seq.zfill(7)
    dv = cnj_check_digits(seq7, year, seg, court, origin)
    return f"{seq7}-{dv}.{year}.{seg}.{court}.{origin}"


class OfficialIndicesTests(unittest.TestCase):
    def test_known_series_covers_monetary_and_bcb_credit_series(self):
        expected = {
            "4390", "11", "10764", "433", "188", "189", "226", "12", "4391", "196", "7478",
            "25464", "25463", "25470", "25462", "25461", "20714", "22022", "25471", "20749", "20724",
        }
        self.assertTrue(expected.issubset(set(KNOWN_SERIES.keys())))

    def test_lei_14905_interest_applies_floor_zero_and_simple_accumulation(self):
        selic = [
            {"date": "2024-09-01", "value": "0.84"},
            {"date": "2024-10-01", "value": "0.93"},
            {"date": "2024-11-01", "value": "0.79"},
        ]
        ipca = [
            {"date": "2024-09-01", "value": "0.44"},  # diff = 0.40
            {"date": "2024-10-01", "value": "1.10"},  # diff = -0.17 -> piso 0
            {"date": "2024-11-01", "value": "-0.05"},  # deflação -> diff = 0.84
        ]
        res = compute_lei_14905_interest(selic, ipca)
        self.assertEqual(res["legal_status"], "calculated_from_supplied_series")
        self.assertEqual(res["accumulation_mode"], "simple")
        self.assertEqual(res["accumulated_pct"], "1.240000")
        self.assertEqual(res["factor"], "1.012400000000")
        self.assertFalse(res["monthly_breakdown"][0]["floor_zero_applied"])
        self.assertTrue(res["monthly_breakdown"][1]["floor_zero_applied"])
        self.assertEqual(res["monthly_breakdown"][1]["taxa_legal_pct"], "0")
        self.assertEqual(res["monthly_breakdown"][2]["taxa_legal_pct"], "0.84")

    def test_lei_14905_interest_rejects_mismatched_or_duplicate_competences(self):
        with self.assertRaises(ValueError):
            compute_lei_14905_interest(
                [{"date": "2024-09-01", "value": "0.84"}],
                [{"date": "2024-10-01", "value": "0.44"}],
            )
        with self.assertRaises(ValueError):
            compute_lei_14905_interest(
                [{"date": "2024-09-01", "value": "0.84"}, {"date": "2024-09-15", "value": "0.84"}],
                [{"date": "2024-09-01", "value": "0.44"}],
            )

    def test_cli_list_series_outputs_json(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = indices_main(["--list-series"])
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertGreaterEqual(payload["count"], 21)
        self.assertIn("25470", payload["series"])

    def test_backward_compatible_accumulate_and_br_date(self):
        self.assertEqual(br_date("2024-08-30"), "30/08/2024")
        pts = parse_series('[{"data":"01/01/2025","valor":"0,50"},{"data":"01/02/2025","valor":"1.00"}]')
        self.assertEqual(accumulate(pts, mode="simple")["factor"], "1.015000000000")


class LegislationLookupTests(unittest.TestCase):
    def test_parse_act_supports_mp_mpv_dlg_pdl(self):
        self.assertEqual(parse_act("MP:1150:2022"), ("MPV", "1150", "2022"))
        self.assertEqual(parse_act("MPV:1150:2022"), ("MPV", "1150", "2022"))
        self.assertEqual(parse_act("DLG:6:2020"), ("DLG", "6", "2020"))
        self.assertEqual(parse_act("PDL:6:2020"), ("DLG", "6", "2020"))
        self.assertEqual(parse_act("CF/1988"), ("CON", "", "1988"))

    def test_get_json_ssl_eof_fallback_uses_ignore_unexpected_eof_context(self):
        eof_err = ssl.SSLEOFError(8, "EOF occurred in violation of protocol (_ssl.c:2406)")
        good = MagicMock()
        good.__enter__.return_value.read.return_value = b'{"resolved": true}'
        with patch("scripts.legislation_lookup.urlopen", side_effect=[eof_err, good]) as mocked:
            data = _get_json("https://normas.leg.br/api/public/normas?urn=x")
        self.assertEqual(data, {"resolved": True})
        self.assertEqual(mocked.call_count, 2)
        self.assertNotIn("context", mocked.call_args_list[0].kwargs)
        ctx = mocked.call_args_list[1].kwargs.get("context")
        self.assertIsInstance(ctx, ssl.SSLContext)
        if hasattr(ssl, "OP_IGNORE_UNEXPECTED_EOF"):
            self.assertTrue(ctx.options & ssl.OP_IGNORE_UNEXPECTED_EOF)

    def test_get_json_urlerror_wrapping_ssl_eof_also_falls_back(self):
        wrapped = URLError(ssl.SSLEOFError(8, "UNEXPECTED_EOF_WHILE_READING"))
        good = MagicMock()
        good.__enter__.return_value.read.return_value = b'{"ok": 1}'
        with patch("scripts.legislation_lookup.urlopen", side_effect=[wrapped, good]) as mocked:
            self.assertEqual(_get_json("https://legis.senado.leg.br/dadosabertos/x"), {"ok": 1})
        self.assertEqual(mocked.call_count, 2)

    def test_get_json_default_call_signature_has_no_context_kwarg(self):
        good = MagicMock()
        good.__enter__.return_value.read.return_value = b'{"clean": true}'
        with patch("scripts.legislation_lookup.urlopen", return_value=good) as mocked:
            self.assertEqual(_get_json("https://normas.leg.br/api/x"), {"clean": True})
        self.assertEqual(mocked.call_args.kwargs, {"timeout": 60})


class CivilMonetaryEngineTests(unittest.TestCase):
    def test_civil_lei_14905_splits_automatically_at_2024_08_30(self):
        spec = {
            "regime": "civil_lei_14905",
            "principal": "1000.00",
            "start_date": "2024-08-01",
            "end_date": "2024-10-31",
            "fixed_monthly_interest_pct": "1.0",
            "index_points": [
                {"date": "2024-08-01", "value": "0.00"},
                {"date": "2024-09-01", "value": "0.50"},
                {"date": "2024-10-01", "value": "1.00"},
            ],
            "selic_points": [
                {"date": "2024-09-01", "value": "0.90"},  # taxa legal = 0.40%
                {"date": "2024-10-01", "value": "0.80"},  # IPCA 1.00 > SELIC 0.80 -> piso 0%
            ],
        }
        res = calculate_monetary_update(spec)
        self.assertEqual(len(res["phases_applied"]), 2)
        self.assertEqual(res["phases_applied"][0]["name"], "pre_lei_14905")
        self.assertEqual(res["phases_applied"][1]["name"], "post_lei_14905")
        # Principal corrigido: 1000 * 1.00 * 1.005 * 1.01 = 1015.05
        self.assertEqual(res["corrected_principal"], "1015.05")
        # Juros simples totais = 1.0% (ago) + 0.40% (set) + 0.00% (out) = 1.40% de 1015.05 = 14.2107 -> 14.21
        self.assertEqual(res["moratory_interest"], "14.21")
        self.assertEqual(res["grand_total"], "1029.26")

    def test_fazenda_ec113_splits_automatically_at_2021_12_09(self):
        spec = {
            "regime": "fazenda_ec113",
            "principal": "2000.00",
            "start_date": "2021-11-01",
            "end_date": "2022-01-31",
            "fixed_monthly_interest_pct": "0.5",
            "index_points": [{"date": "2021-11-01", "value": "1.00"}],
            "selic_points": [
                {"date": "2021-12-01", "value": "0.77"},
                {"date": "2022-01-01", "value": "0.73"},
            ],
        }
        res = calculate_monetary_update(spec)
        self.assertEqual([p["name"] for p in res["phases_applied"]], ["pre_ec113_tema810", "post_ec113_selic"])
        # Nov/2021: capital = 2020.00, juros = 10.10. Dez/Jan SELIC soma 1.50% sobre 2020.00 = 30.30 -> juros totais 40.40.
        self.assertEqual(res["corrected_principal"], "2020.00")
        self.assertEqual(res["moratory_interest"], "40.40")
        self.assertEqual(res["grand_total"], "2060.40")

    def test_tributario_selic_and_fgts_adi5090_floor(self):
        trib = calculate_monetary_update({
            "regime": "tributario_selic",
            "principal": "500.00",
            "start_date": "2024-01-10",
            "end_date": "2024-02-20",
            "selic_points": [{"date": "2024-01-01", "value": "0.97"}, {"date": "2024-02-01", "value": "0.80"}],
        })
        self.assertEqual(trib["moratory_interest"], "8.85")
        self.assertEqual(trib["grand_total"], "508.85")

        fgts = calculate_monetary_update({
            "regime": "fgts_adi5090",
            "principal": "1000.00",
            "start_date": "2024-07-01",
            "end_date": "2024-07-31",
            "fixed_monthly_interest_pct": "0.25",
            "index_points": [{"date": "2024-07-01", "value": "0.05"}],  # TR+JAM ~ 0.3001%
            "ipca_points": [{"date": "2024-07-01", "value": "0.38"}],   # IPCA 0.38% vence o piso!
        })
        self.assertEqual(fgts["corrected_principal"], "1003.80")

    def test_missing_series_competence_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "2024-10"):
            calculate_monetary_update({
                "regime": "tributario_selic",
                "principal": "100.00",
                "start_date": "2024-09-01",
                "end_date": "2024-10-31",
                "selic_points": [{"date": "2024-09-01", "value": "0.84"}],
            })

    def test_float_input_is_strictly_rejected(self):
        with self.assertRaisesRegex(ValueError, "flutuante"):
            calculate_monetary_update({
                "regime": "tributario_selic",
                "principal": 100.50,
                "start_date": "2024-09-01",
                "end_date": "2024-09-30",
                "selic_points": [{"date": "2024-09-01", "value": "0.84"}],
            })

    def test_cc_art354_partial_payment_imputation_interest_first_vs_principal_first(self):
        base_spec = {
            "regime": "tributario_selic",
            "principal": "1000.00",
            "start_date": "2024-01-01",
            "end_date": "2024-02-28",
            "selic_points": [
                {"date": "2024-01-01", "value": "10.00"},  # juros = 100.00
                {"date": "2024-02-01", "value": "10.00"},
            ],
            "partial_payments": [{"date": "2024-01-20", "amount": "150.00"}],
        }
        cc354 = calculate_monetary_update(base_spec)
        # Em jan: juros=100, pagamento=150 -> abate 100 de juros e 50 do capital (resta capital 950). Em fev: 10% de 950 = 95 -> total 1045.
        self.assertEqual(cc354["partial_payments_imputed"][0]["imputed_to_interest"], "100.00")
        self.assertEqual(cc354["partial_payments_imputed"][0]["imputed_to_principal"], "50.00")
        self.assertEqual(cc354["grand_total"], "1045.00")

        prin_first = calculate_monetary_update(dict(base_spec, imputation="principal_first"))
        # Em jan: abate 150 direto do capital (resta 850) e mantém juros=100. Em fev: 10% de 850 = 85 -> total = 850 + 185 = 1035.
        self.assertEqual(prin_first["partial_payments_imputed"][0]["imputed_to_principal"], "150.00")
        self.assertEqual(prin_first["grand_total"], "1035.00")

    def test_art523_cpc_multa_and_honorarios_plus_sucumbencia(self):
        res = calculate_monetary_update({
            "regime": "tributario_selic",
            "principal": "1000.00",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "selic_points": [{"date": "2024-01-01", "value": "0.00"}],
            "honorarios_sucumbencia_pct": "10",
            "art523_cpc": {"multa_10": True, "honorarios_10": True},
        })
        # Subtotal 1000 + sucumbência 100 = base 1100; multa 110 + hon523 110 = 1320.00
        self.assertEqual(res["honorarios_sucumbencia"], "100.00")
        self.assertEqual(res["art523_multa_10"], "110.00")
        self.assertEqual(res["art523_honorarios_10"], "110.00")
        self.assertEqual(res["grand_total"], "1320.00")

    def test_compare_bank_rate_annualization_and_stj_tema_27_status(self):
        res = compare_bank_rate("4.00", "2.00", "1.5")
        self.assertTrue(res["exceeds_objective_threshold"])
        self.assertEqual(res["ratio_contract_over_market"], "2.0000")
        self.assertEqual(res["contract_annual_effective_pct"], "60.1032")
        self.assertEqual(res["bcb_market_annual_effective_pct"], "26.8242")
        self.assertEqual(res["legal_status"], "mathematical_comparison_requires_case_subsumption_stj_tema_27")

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = monetary_main(["--compare-bank-rate", "2.10", "2.00"])
        self.assertEqual(rc, 0)
        self.assertFalse(json.loads(buf.getvalue())["exceeds_objective_threshold"])


class DeadlineCalculatorTests(unittest.TestCase):
    def test_easter_and_consciencia_negra_20_11_temporal_rule(self):
        self.assertEqual(easter_sunday(2024).isoformat(), "2024-03-31")
        self.assertEqual(easter_sunday(2025).isoformat(), "2025-04-20")
        self.assertEqual(easter_sunday(2026).isoformat(), "2026-04-05")
        hols_2023 = {d.isoformat() for d in national_holidays(2023)}
        hols_2024 = {d.isoformat() for d in national_holidays(2024)}
        self.assertNotIn("2023-11-20", hols_2023)
        self.assertIn("2024-11-20", hols_2024)
        forense_2025 = {
            d.isoformat()
            for d in national_holidays(
                2025, include_dia_da_justica=True, include_quinta_feira_santa=True, include_carnaval=True
            )
        }
        self.assertTrue({"2025-12-08", "2025-04-17", "2025-03-03", "2025-03-04"}.issubset(forense_2025))

    def test_dje_publication_and_15_business_days_with_holiday(self):
        # Disponibilizado quinta 2024-11-07 -> Publicado sexta 2024-11-08 -> Início segunda 2024-11-11.
        # Pula 15/11 (sexta, Proclamação da República) e 20/11 (quarta, Consciência Negra — Lei 14.759/2023).
        res = calculate_deadline({
            "days": 15,
            "base_date": "2024-11-07",
            "rito": "civel",
            "intimation_mode": "dje",
        })
        self.assertEqual(res["publication_or_effective_intimation_date"], "2024-11-08")
        self.assertEqual(res["dies_a_quo"], "2024-11-11")
        self.assertEqual(res["dies_ad_quem"], "2024-12-03")
        counted_dates = [d["date"] for d in res["audit_trail"] if d["counted"]]
        self.assertEqual(len(counted_dates), 15)
        self.assertNotIn("2024-11-15", counted_dates)
        self.assertNotIn("2024-11-20", counted_dates)

    def test_portal_eletronico_explicit_vs_tacit_10_calendar_days(self):
        # Remessa em 2025-03-03 (segunda). Consulta explícita no sábado 2025-03-08 -> prorroga consulta p/ segunda 2025-03-10 -> início 2025-03-11.
        explicit = calculate_deadline({
            "days": 5,
            "base_date": "2025-03-03",
            "rito": "civel",
            "intimation_mode": "portal_eletronico",
            "consultation_date": "2025-03-08",
        })
        self.assertEqual(explicit["publication_or_effective_intimation_date"], "2025-03-10")
        self.assertEqual(explicit["dies_a_quo"], "2025-03-11")
        self.assertEqual(explicit["dies_ad_quem"], "2025-03-17")

        # Tácita: 2025-03-03 + 10 dias corridos = 2025-03-13 (quinta) -> início sexta 2025-03-14.
        tacit = calculate_deadline({
            "days": 5,
            "base_date": "2025-03-03",
            "rito": "civel",
            "intimation_mode": "portal_eletronico",
        })
        self.assertEqual(tacit["publication_or_effective_intimation_date"], "2025-03-13")
        self.assertEqual(tacit["dies_a_quo"], "2025-03-14")

    def test_djen_citacao_pj_privada_confirmed_vs_unconfirmed_and_fazenda_10_days(self):
        unconfirmed = calculate_deadline({
            "days": 15,
            "base_date": "2025-05-05",
            "rito": "civel",
            "intimation_mode": "djen_citacao",
            "recipient_kind": "pj_privada",
        })
        self.assertFalse(unconfirmed["citation_confirmed"])
        self.assertIsNone(unconfirmed["dies_ad_quem"])
        self.assertEqual(unconfirmed["legal_status"], "awaiting_valid_citation_no_tacit_citation_pj_privada")

        confirmed = calculate_deadline({
            "days": 15,
            "base_date": "2025-05-05",
            "rito": "civel",
            "intimation_mode": "djen_citacao",
            "recipient_kind": "pj_privada",
            "confirmation_date": "2025-05-07",
        })
        # 5º dia útil seguinte a quarta 07/05: 08(1), 09(2), 12(3), 13(4), 14/05(5) = dies_a_quo 2025-05-14!
        self.assertEqual(confirmed["dies_a_quo"], "2025-05-14")

        fazenda = calculate_deadline({
            "days": 15,
            "base_date": "2025-05-05",
            "rito": "civel",
            "intimation_mode": "djen_citacao",
            "recipient_kind": "fazenda_publica",
            "prerogative": "fazenda_publica",
        })
        self.assertEqual(fazenda["effective_days"], 30)
        self.assertEqual(fazenda["publication_or_effective_intimation_date"], "2025-05-15")
        self.assertEqual(fazenda["dies_a_quo"], "2025-05-16")

    def test_recesso_forense_suspends_civel_and_not_penal_by_default(self):
        civel = calculate_deadline({
            "days": 5,
            "base_date": "2024-12-17",
            "rito": "civel",
            "intimation_mode": "in_person_or_hearing",
        })
        # 18/12 (1), 19/12 (2), suspenso 20/12..20/01, retoma 21/01 (3), 22/01 (4), 23/01 (5).
        self.assertEqual(civel["dies_a_quo"], "2024-12-18")
        self.assertEqual(civel["dies_ad_quem"], "2025-01-23")

        penal = calculate_deadline({
            "days": 5,
            "base_date": "2024-12-17",
            "rito": "penal",
            "intimation_mode": "in_person_or_hearing",
        })
        # 18, 19, 20, 21, 22/12 (domingo, e recesso sem expediente 20/12..06/01) -> prorroga termo final p/ 07/01/2025!
        self.assertEqual(penal["dies_a_quo"], "2024-12-18")
        self.assertEqual(penal["dies_ad_quem"], "2025-01-07")

    def test_art229_p2_cpc_blocks_litisconsortes_dobra_in_electronic_autos(self):
        with self.assertRaisesRegex(ValueError, "229"):
            calculate_deadline({
                "days": 15,
                "base_date": "2025-03-10",
                "rito": "civel",
                "process_medium": "eletronico",
                "litisconsortes_dobra": True,
            })
        fisico = calculate_deadline({
            "days": 15,
            "base_date": "2025-03-10",
            "rito": "civel",
            "process_medium": "fisico",
            "litisconsortes_dobra": True,
        })
        self.assertEqual(fisico["effective_days"], 30)

    def test_system_outage_extends_start_and_end_with_lei_14939_warning(self):
        res = calculate_deadline({
            "days": 3,
            "base_date": "2025-03-10",  # segunda -> intimação juntada 10/03 -> início normal 11/03
            "rito": "civel",
            "intimation_mode": "juntada",
            "system_outage_on_start_or_end": ["2025-03-11", "2025-03-14"],
        })
        # Outage em 11/03 joga dies_a_quo p/ 12/03; dias úteis: 12(1), 13(2), 14(3, mas outage!) -> prorroga p/ segunda 17/03!
        self.assertEqual(res["dies_a_quo"], "2025-03-12")
        self.assertEqual(res["dies_ad_quem"], "2025-03-17")
        self.assertTrue(any("14.939/2024" in w for w in res["warnings"]))

    def test_deadline_cli_holidays_output(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = deadline_main(["--holidays-year", "2025"])
        self.assertEqual(rc, 0)
        self.assertIn("2025-11-20", json.loads(buf.getvalue())["holidays"])


class SocialSecurityCalcTests(unittest.TestCase):
    def test_merge_intervals_eliminates_concomitant_overlap(self):
        merged = merge_intervals([
            {"start": "2015-01-01", "end": "2017-12-31"},
            {"start": "2016-06-01", "end": "2019-12-31"},
            {"start": "2021-01-01", "end": "2021-12-31"},
        ])
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["start"], "2015-01-01")
        self.assertEqual(merged[0]["end"], "2019-12-31")
        self.assertGreater(merged[0]["concomitant_days_eliminated"], 500)
        self.assertEqual(merged[1]["days"], 365)

    def test_special_time_conversion_strictly_cuts_off_on_2019_11_13(self):
        res = convert_special_time(
            [{"start": "2018-11-14", "end": "2020-11-13", "is_special": True, "special_years": 25}],
            sex="M",
        )
        # 2018-11-14..2019-11-13 = 365 dias * 1.4 = 511.00; 2019-11-14..2020-11-13 = 366 dias * 1.0 = 366.00 -> total 877.00
        self.assertEqual(res["total_raw_days"], 731)
        self.assertEqual(res["total_bonus_days"], "146.00")
        self.assertEqual(res["total_converted_days"], "877.00")
        self.assertTrue(any("25, § 2º" in w for w in res["warnings"]))

        mine = convert_special_time(
            [{"start": "2010-01-01", "end": "2010-12-31", "is_special": True, "special_years": 15}],
            sex="F",
        )
        self.assertEqual(mine["total_converted_days"], "730.00")

    def test_concomitant_special_and_common_prioritizes_special_without_double_counting(self):
        res = convert_special_time(
            [
                {"start": "2015-01-01", "end": "2015-12-31", "is_special": False},
                {"start": "2015-01-01", "end": "2015-12-31", "is_special": True, "special_years": 25},
            ],
            sex="M",
        )
        # 365 dias especiais * 1.4 = 511.00 (sem somar +365 do vínculo comum concomitante!).
        self.assertEqual(res["total_raw_days"], 365)
        self.assertEqual(res["total_converted_days"], "511.00")

    def test_ec103_transition_rules_points_age_toll50_and_toll100(self):
        # Homem nascido em 1964-01-01 (60 anos em 2024-01-01), com 34 anos de contribuição até 13/11/2019
        # (faltava 1 ano em 13/11/2019 -> elegível ao pedágio de 50% com 35.5a e ao pedágio de 100% com 36a + 60a idade).
        res = evaluate_rgps_eligibility({
            "sex": "M",
            "birth_date": "1964-01-01",
            "der": "2024-06-01",
            "carencia_months": 240,
            "periods": [
                {"start": "1985-11-14", "end": "2019-11-13"},  # ~34 anos + bissextos
                {"start": "2019-11-14", "end": "2022-06-01"},  # +2.5 anos -> >36.5 anos totais
            ],
        })
        self.assertTrue(res["rules"]["ec103_art17_toll_50"]["passed_2019_entry_gate"])
        self.assertTrue(res["rules"]["ec103_art17_toll_50"]["eligible"])
        self.assertTrue(res["rules"]["ec103_art20_toll_100"]["eligible"])

        # Mulher com apenas 27 anos em 13/11/2019 NÃO passa na barreira de entrada (>28a) do pedágio de 50%.
        blocked_50 = evaluate_rgps_eligibility({
            "sex": "F",
            "birth_date": "1966-01-01",
            "der": "2024-06-01",
            "carencia_months": 240,
            "periods": [
                {"start": "1992-11-14", "end": "2019-11-13"},  # ~27 anos
                {"start": "2019-11-14", "end": "2024-06-01"},
            ],
        })
        self.assertFalse(blocked_50["rules"]["ec103_art17_toll_50"]["passed_2019_entry_gate"])
        self.assertFalse(blocked_50["rules"]["ec103_art17_toll_50"]["eligible"])

    def test_post_ec103_male_affiliation_requires_20_years_art19(self):
        post_male = evaluate_rgps_eligibility({
            "sex": "M",
            "birth_date": "1959-01-01",
            "affiliation_date": "2020-01-01",
            "der": "2036-01-01",
            "carencia_months": 192,
            "periods": [{"start": "2020-01-01", "end": "2035-12-31"}],  # 16 anos (< 20 anos exigidos pelo art. 19)
        })
        self.assertFalse(post_male["rules"]["ec103_art18_19_age"]["eligible"])

    def test_decadencia_art103_first_day_next_month_and_quinquenal_prescription(self):
        dec = check_rgps_decadencia_prescricao("2014-03-18", "2024-04-02")
        self.assertEqual(dec["decadencia_dies_a_quo"], "2014-04-01")
        self.assertEqual(dec["decadencia_deadline_10y"], "2024-04-01")
        self.assertTrue(dec["decadencia_occurred"])
        self.assertEqual(dec["prescricao_quinquenal_unpaid_before"], "2019-04-02")


class PenalDosimetryTests(unittest.TestCase):
    def test_sumula_231_clips_mitigating_at_statutory_minimum_and_phase3_drops_below(self):
        # Furto tentado (CP art. 155 c/c art. 14, II): pena mínima 1 ano, confissão na 2ª fase (Súmula 231 trava em 1a),
        # tentativa (-2/3) na 3ª fase reduz para 4 meses, regime aberto e PRD cabível.
        res = calculate_dosimetry({
            "min_penalty": {"years": 1, "months": 0, "days": 0},
            "max_penalty": {"years": 4, "months": 0, "days": 0},
            "unfavorable_circumstances_count": 0,
            "mitigating": [{"label": "confissão espontânea (CP, art. 65, III, 'd')", "fraction": "1/6"}],
            "minorantes": [{"label": "tentativa (CP, art. 14, parágrafo único)", "fraction": "2/3"}],
        })
        self.assertTrue(res["phase2_pena_intermediaria"]["sumula_231_clipped"])
        self.assertEqual(res["phase2_pena_intermediaria"]["penalty"]["total_days_360"], 360)
        self.assertEqual(res["pena_definitiva"]["years"], 0)
        self.assertEqual(res["pena_definitiva"]["months"], 4)
        self.assertEqual(res["initial_regime"], "aberto")
        self.assertTrue(res["art44_prd_substitution"]["eligible"])
        self.assertTrue(any("718" in w and "440" in w for w in res["warnings"]))

    def test_three_phase_cascading_concurso_formal_beneficial_cap_and_detracao(self):
        # Pena fase 3 de 6 anos (2160d) + crime adicional de 6 meses (180d) em concurso formal com fração 1/6:
        # Exacerbação = 6a + 1a = 7a (2520d) > soma material 6a6m (2340d) -> aplica cúmulo material benéfico (2340d)!
        # Com detração de 2 anos e 7 meses (930d), restam 1410d (3a11m <= 4a) -> primário com art. 59 favorável -> aberto!
        res = calculate_dosimetry({
            "min_penalty": {"years": 4, "months": 0, "days": 0},
            "max_penalty": {"years": 10, "months": 0, "days": 0},
            "pena_base": {"years": 4, "months": 0, "days": 0},
            "majorantes": ["1/2"],  # 6 anos
            "concurso": "formal_proprio",
            "additional_penalties": [{"years": 0, "months": 6, "days": 0}],
            "detracao": {"years": 2, "months": 7, "days": 0},
        })
        self.assertTrue(res["concurso"]["cumulo_material_benefico_applied"])
        self.assertEqual(res["pena_definitiva"]["total_days_360"], 2340)
        self.assertEqual(res["pena_restante_apos_detracao"]["total_days_360"], 1410)
        self.assertEqual(res["initial_regime"], "aberto")

    def test_reincidente_under_4y_favorable_art59_gets_semiaberto_sumula_269(self):
        res = calculate_dosimetry({
            "min_penalty": {"years": 1, "months": 0, "days": 0},
            "max_penalty": {"years": 4, "months": 0, "days": 0},
            "unfavorable_circumstances_count": 0,
            "aggravating": ["1/6"],
            "reincidente": True,
        })
        self.assertEqual(res["initial_regime"], "semiaberto")
        self.assertFalse(res["art44_prd_substitution"]["eligible"])
        self.assertTrue(any("269" in w for w in res["warnings"]))

    def test_penal_prescription_pre_2010_2y_vs_post_2010_3y_and_retroativa_bar(self):
        pre2010 = calculate_penal_prescription({
            "penalty": {"years": 0, "months": 8, "days": 0},
            "fato": "2008-01-10",
            "recebimento_denuncia": "2010-02-01",
        })
        self.assertEqual(pre2010["art109_bracket_years"], 2)
        self.assertTrue(pre2010["prescription_recognized"])

        post2010 = calculate_penal_prescription({
            "penalty": {"years": 0, "months": 8, "days": 0},
            "penalty_kind": "concreta",
            "fato": "2018-01-10",
            "recebimento_denuncia": "2021-06-01",  # > 3 anos, mas retroativa bloqueada pelo art. 110 § 1º (Lei 12.234/2010)
            "publicacao_sentenca": "2023-01-10",
        })
        self.assertEqual(post2010["art109_bracket_years"], 3)
        self.assertTrue(post2010["intervals"][0]["blocked_by_art110_p1_lei_12234"])
        self.assertFalse(post2010["prescription_recognized"])

    def test_penal_prescription_art115_half_reduction_and_acordao_confirmatorio(self):
        res = calculate_penal_prescription({
            "penalty": {"years": 1, "months": 6, "days": 0},  # 4 anos -> art. 115 reduz p/ 2 anos!
            "birth_date": "2002-06-01",
            "fato": "2022-01-10",  # menor de 21 na data do fato
            "recebimento_denuncia": "2022-06-10",
            "publicacao_sentenca": "2024-01-10",
            "acordao_confirmatorio": "2026-02-01",  # > 2 anos após sentença -> prescrito intercorrente!
        })
        self.assertTrue(res["art115_reduced_by_half"])
        self.assertEqual(res["effective_prescription_years"], "2")
        self.assertTrue(res["prescription_recognized"])
        self.assertTrue(any("1192" in w for w in res["warnings"]))

    def test_lep_progression_pre_2020_vs_pacote_anticrime_and_tema_1169(self):
        pre_common = calculate_lep_progression({"offense_date": "2018-05-01", "hediondo": False})
        self.assertEqual(pre_common["progression_fraction"], "1/6")

        pre_hed_spec = calculate_lep_progression({
            "offense_date": "2018-05-01",
            "hediondo": True,
            "recidivism": "reincidente_especifico",
        })
        self.assertEqual(pre_hed_spec["progression_fraction"], "3/5")

        post_hed_gen = calculate_lep_progression({
            "offense_date": "2021-03-10",
            "hediondo": True,
            "result_death": False,
            "recidivism": "reincidente_generico",
        })
        # STF Tema 1169: reincidente genérico em hediondo sem morte progride com 40% (inciso V), não 60%!
        self.assertEqual(post_hed_gen["progression_percentage"], "40")

    def test_lep_progression_feminicidio_55_pct_lei_14994_and_lei_14843_alert(self):
        fem = calculate_lep_progression({
            "offense_date": "2024-11-01",
            "feminicidio": True,
            "recidivism": "primario",
            "total_penalty": {"years": 20, "months": 0, "days": 0},
            "base_execution_date": "2025-01-01",
        })
        self.assertEqual(fem["progression_percentage"], "55")
        self.assertTrue(fem["livramento_condicional_barred"])
        self.assertTrue(fem["criminological_exam_lei_14843_applies_by_date"])
        self.assertEqual(fem["required_days_360"], 3960)
        self.assertTrue(any("14.843/2024" in w for w in fem["warnings"]))


class LimitationCheckerTests(unittest.TestCase):
    def test_cc_art202_single_interruption_rule_ignores_second_interruption(self):
        res = check_limitation({
            "profile": "art206_p3_3anos_reparacao_civil_enriquecimento",
            "start_date": "2020-01-10",
            "interrupcoes": [
                {"date": "2022-01-10", "reason": "protesto judicial"},
                {"date": "2024-06-01", "reason": "notificação extrajudicial (2ª tentativa)"},
            ],
            "reference_date": "2025-02-01",
        })
        # 1ª interrupção em 2022-01-10 joga prazo p/ 2025-01-10; 2ª interrupção é ignorada -> em 2025-02-01 está prescrito!
        self.assertEqual(res["deadline_date"], "2025-01-10")
        self.assertTrue(res["extinguished"])
        self.assertTrue(any("202" in w for w in res["warnings"]))

    def test_cc_art2028_transition_rule_both_branches(self):
        # Fato em 1990-06-01 (>10 anos em 11/01/2003): mantém 20 anos do CC/1916 -> vence 2010-06-01.
        old_rule = check_limitation({
            "profile": "art2028",
            "start_date": "1990-06-01",
            "old_cc1916_years": 20,
            "new_cc2002_years": 3,
            "reference_date": "2008-01-01",
        })
        self.assertEqual(old_rule["deadline_date"], "2010-06-01")
        self.assertFalse(old_rule["extinguished"])

        # Fato em 2000-06-01 (<10 anos em 11/01/2003): prazo novo de 3 anos contado de 11/01/2003 -> vence 2006-01-11.
        new_rule = check_limitation({
            "profile": "art2028",
            "start_date": "2000-06-01",
            "old_cc1916_years": 20,
            "new_cc2002_years": 3,
            "reference_date": "2006-01-12",
        })
        self.assertEqual(new_rule["deadline_date"], "2006-01-11")
        self.assertTrue(new_rule["extinguished"])

    def test_cdc_decadencia_ignores_ordinary_suspension_but_honors_reclamacao_and_incapaz(self):
        res = check_limitation({
            "profile": "art26_30dias_vicio_nao_duravel",
            "start_date": "2025-01-01",
            "impedimentos_suspensoes": [
                {"start": "2025-01-05", "end": "2025-01-14", "kind": "acordo_informal", "reason": "tratativa comum"},
                {"start": "2025-01-15", "end": "2025-01-24", "kind": "cdc_art26_p2_reclamacao", "reason": "reclamação SAC até resposta negativa"},
            ],
            "reference_date": "2025-02-08",
        })
        # 30 dias de 01/01 = 31/01 + 10 dias de obstação válida (15..24/01) = 2025-02-10 -> em 08/02 ainda vigente!
        self.assertEqual(res["deadline_date"], "2025-02-10")
        self.assertFalse(res["extinguished"])
        self.assertTrue(any("207" in w for w in res["warnings"]))

    def test_fazenda_dl20910_sumula_383_stf_half_restart_with_5y_floor(self):
        # Interrupção precoce com 1 ano de curso não reduz o prazo aquém dos 5 anos originais (Súmula 383/STF).
        early = check_limitation({
            "profile": "dl20910_art1_5anos",
            "start_date": "2020-01-10",
            "interrupcoes": [{"date": "2021-01-10", "reason": "protesto"}],
            "reference_date": "2024-12-01",
        })
        self.assertEqual(early["deadline_date"], "2025-01-10")
        self.assertFalse(early["extinguished"])

        # Interrupção tardia com 4 anos de curso recomeça por 2 anos e meio (30 meses).
        late = check_limitation({
            "profile": "dl20910_art1_5anos",
            "start_date": "2020-01-10",
            "interrupcoes": [{"date": "2024-01-10", "reason": "protesto"}],
            "reference_date": "2026-06-01",
        })
        self.assertEqual(late["deadline_date"], "2026-07-10")
        self.assertFalse(late["extinguished"])

    def test_tax_ctn_150_p4_vs_173_i_and_lef_art40_1mais5_tema_566_568(self):
        d150 = check_limitation({
            "profile": "ctn_art150_p4_decadencia",
            "start_date": "2019-05-15",
            "reference_date": "2024-05-16",
        })
        self.assertTrue(d150["extinguished"])

        d173 = check_limitation({
            "profile": "ctn_art173_i_decadencia",
            "start_date": "2019-05-15",  # 1º dia exercício seguinte = 2020-01-01 -> fim em 2024-12-31
            "reference_date": "2024-05-16",
        })
        self.assertEqual(d173["dies_a_quo"], "2020-01-01")
        self.assertEqual(d173["deadline_date"], "2024-12-31")
        self.assertFalse(d173["extinguished"])

        lef = check_limitation({
            "profile": "lef_art40_intercorrente_1mais5",
            "start_date": "2018-03-10",  # 1 ano susp até 2019-03-10 + 5 anos até 2024-03-10
            "interrupcoes": [{"date": "2022-05-01", "effective": False, "reason": "mero pedido de Sisbajud infrutífero"}],
            "reference_date": "2024-03-11",
        })
        self.assertEqual(lef["one_year_suspension_end"], "2019-03-10")
        self.assertEqual(lef["deadline_date"], "2024-03-10")
        self.assertTrue(lef["extinguished"])
        self.assertTrue(any("568" in w for w in lef["warnings"]))

    def test_improbidade_lei_14230_8y_and_4y_intercorrente_and_cpc_921(self):
        lia = check_limitation({
            "profile": "l8429_art23_8anos_e_4anos_intercorrente",
            "start_date": "2022-01-10",
            "interrupcoes": [{"date": "2023-05-10", "reason": "ajuizamento da ação de improbidade"}],
            "reference_date": "2027-05-11",  # > 4 anos após ajuizamento -> prescrição intercorrente consumada!
        })
        self.assertEqual(lia["deadline_date"], "2027-05-10")
        self.assertTrue(lia["extinguished"])

        cpc921 = check_limitation({
            "profile": "cpc_art921_intercorrente",
            "start_date": "2022-02-01",
            "underlying_years": 3,
            "reference_date": "2026-02-02",  # 1 ano susp + 3 anos = 2026-02-01
        })
        self.assertTrue(cpc921["extinguished"])
        self.assertGreaterEqual(len(PROFILES), 15)

        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(limitation_main(["--list-profiles"]), 0)


class DataJudLookupTests(unittest.TestCase):
    def test_resolve_endpoint_routes_tjsp_trf5_trt4_tjdft_stj_tst_tse_stm(self):
        cases = [
            (make_cnj("1000123", "2023", "8", "26", "0100"), "tjsp"),
            (make_cnj("0800001", "2022", "4", "05", "8300"), "trf5"),
            (make_cnj("0000713", "2010", "5", "04", "0029"), "trt4"),
            (make_cnj("0700100", "2024", "8", "07", "0001"), "tjdft"),
            (make_cnj("0600050", "2024", "6", "26", "0000"), "tre-sp"),
            (make_cnj("0010000", "2024", "3", "00", "0000"), "stj"),
            (make_cnj("0020000", "2024", "5", "00", "0000"), "tst"),
            (make_cnj("0030000", "2024", "6", "00", "0000"), "tse"),
            (make_cnj("0040000", "2024", "7", "00", "0000"), "stm"),
        ]
        for cnj, expected_alias in cases:
            with self.subTest(alias=expected_alias):
                res = resolve_endpoint(cnj)
                self.assertEqual(res["alias"], expected_alias)
                self.assertEqual(
                    res["endpoint_url"],
                    f"https://api-publica.datajud.cnj.jus.br/api_publica_{expected_alias}/_search",
                )
                self.assertEqual(len(res["numero_processo_digits"]), 20)

        with self.assertRaises(ValueError):
            resolve_endpoint("1000123-00.2023.8.26.0100")  # DV inválido
        with self.assertRaises(ValueError):
            resolve_endpoint(make_cnj("0000100", "2024", "1", "00", "0000"))  # STF sem DataJud público

    def test_parse_datajud_hit_sorts_movimentos_and_flattens_nested_assuntos(self):
        sample = {
            "hits": {
                "total": {"value": 1},
                "hits": [{
                    "_source": {
                        "numeroProcesso": "10001237720238260100",
                        "tribunal": "TJSP",
                        "grau": "G1",
                        "dataAjuizamento": "2023-02-10T14:22:00.000Z",
                        "classe": {"codigo": 7, "nome": "Procedimento Comum Cível"},
                        "assuntos": [[{"codigo": 10433, "nome": "Indenização por Dano Moral"}]],
                        "orgaoJulgador": {"codigo": 100, "nome": "1ª Vara Cível", "codigoMunicipioIBGE": 3550308},
                        "movimentos": [
                            {"codigo": 51, "nome": "Conclusão", "dataHora": "2023-03-01T10:00:00.000Z"},
                            {"codigo": 26, "nome": "Distribuição", "dataHora": "2023-02-10T14:25:00.000Z"},
                        ],
                    }
                }],
            }
        }
        parsed = parse_datajud_hit(sample)
        self.assertTrue(parsed["found"])
        self.assertEqual(parsed["classe"]["codigo"], 7)
        self.assertEqual(parsed["assuntos"], [{"codigo": 10433, "nome": "Indenização por Dano Moral"}])
        self.assertEqual([m["codigo"] for m in parsed["movimentos"]], [26, 51])

    def test_lookup_process_writes_verified_http_receipt_compatible_with_source_records(self):
        cnj = make_cnj("1000123", "2023", "8", "26", "0100")
        raw_json = json.dumps({
            "hits": {"hits": [{"_source": {
                "numeroProcesso": build_query_payload(cnj)["query"]["match"]["numeroProcesso"],
                "tribunal": "TJSP",
                "classe": {"codigo": 7, "nome": "Procedimento Comum Cível"},
                "assuntos": [{"codigo": 7779, "nome": "Obrigação de Fazer / Não Fazer"}],
                "orgaoJulgador": {"codigo": 1, "nome": "1ª Vara Cível"},
                "dataAjuizamento": "2023-05-01T12:00:00Z",
                "movimentos": [],
            }}]}
        }).encode("utf-8")

        fake_resp = MagicMock()
        fake_resp.__enter__.return_value = fake_resp
        fake_resp.read.return_value = raw_json
        fake_resp.headers = Message()
        fake_resp.headers["Content-Type"] = "application/json; charset=utf-8"

        secret = "SUPER_SECRET_DATAJUD_TOKEN_123"
        with tempfile.TemporaryDirectory() as tmp, patch("scripts.datajud_lookup.urlopen", return_value=fake_resp):
            out_dir = Path(tmp)
            res = lookup_process(cnj, output=out_dir, api_key=secret)
            capture_id = res["receipt"]["capture_id"]
            saved_json_path = out_dir / "research_sources" / f"{capture_id}.json"
            self.assertTrue(saved_json_path.is_file())
            saved_text = saved_json_path.read_text(encoding="utf-8")
            self.assertNotIn(secret, saved_text)
            inspection = inspect_source_record(json.loads(saved_text), out_dir)
            self.assertEqual(inspection["errors"], [])
            self.assertEqual(inspection["evidence_level"], "verified_http")

    def test_cli_resolve_only_and_parse_file_offline(self):
        cnj = make_cnj("1000123", "2023", "8", "26", "0100")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = datajud_main(["--cnj", cnj, "--resolve-only"])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(buf.getvalue())["alias"], "tjsp")

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "hit.json"
            p.write_text('{"hits": {"hits": []}}', encoding="utf-8")
            buf2 = io.StringIO()
            with redirect_stdout(buf2):
                rc2 = datajud_main(["--parse-file", str(p)])
            self.assertEqual(rc2, 0)
            self.assertFalse(json.loads(buf2.getvalue())["found"])

    def test_dual_import_direct_script_execution(self):
        script_path = CORE / "scripts" / "civil_monetary_engine.py"
        proc = subprocess.run(
            [sys.executable, str(script_path), "--compare-bank-rate", "4.50", "2.00"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(proc.stdout)
        self.assertTrue(data["exceeds_objective_threshold"])


if __name__ == "__main__":
    unittest.main()
