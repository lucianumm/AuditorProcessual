"""Property checks with fixed seeds (standard library only): invariants, not legal correctness."""
from __future__ import annotations

import random
import sys
import unittest
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.deadline_calculator import calculate_deadline
from scripts.global_consistency import check_consistency
from scripts.piece_assembly import brl, claim_value
from scripts.prose_dates import find_dates

SEED = 20261127


class DeadlineProperties(unittest.TestCase):
    def cases(self, count=60):
        rng = random.Random(SEED)
        for _ in range(count):
            base = date(2024, 1, 1) + timedelta(days=rng.randrange(0, 900))
            yield base, rng.randrange(1, 30), rng.choice(["civel", "trabalhista"])

    def test_monotonic_in_days_and_counts_exactly(self):
        for base, days, rito in self.cases():
            short = calculate_deadline({"days": days, "base_date": base.isoformat(), "rito": rito})
            longer = calculate_deadline({"days": days + 1, "base_date": base.isoformat(), "rito": rito})
            self.assertLess(short["dies_ad_quem"], longer["dies_ad_quem"], (base, days, rito))
            counted = [d for d in short["audit_trail"] if d["counted"]]
            self.assertEqual(len(counted), short["effective_days"], (base, days, rito))
            self.assertEqual(counted[-1]["date"], short["dies_ad_quem"])
            self.assertTrue(all(d["is_business_day"] for d in counted))
            self.assertEqual(len({d["date"] for d in counted}), len(counted), "dia contado duas vezes")

    def test_never_ends_before_start(self):
        for base, days, rito in self.cases():
            result = calculate_deadline({"days": days, "base_date": base.isoformat(), "rito": rito})
            self.assertLessEqual(result["dies_a_quo"], result["dies_ad_quem"])
            self.assertLess(base.isoformat(), result["dies_a_quo"])


class ControlProperties(unittest.TestCase):
    def test_dates_round_trip_in_every_format(self):
        rng = random.Random(SEED)
        for _ in range(200):
            day = date(1990, 1, 1) + timedelta(days=rng.randrange(0, 15000))
            iso = day.isoformat()
            for text in (day.strftime("%d/%m/%Y"), iso, day.strftime("%d.%m.%Y")):
                self.assertEqual([d["value"] for d in find_dates("Fato em " + text + ".")], [iso], text)

    def test_claim_value_is_additive_and_ignores_subsidiaries(self):
        rng = random.Random(SEED)
        for _ in range(50):
            amounts = [Decimal(rng.randrange(1, 10 ** 7)) / 100 for _ in range(rng.randrange(1, 6))]
            requests = [{"id": f"R{i}", "issue_ids": ["I1"], "priority": rng.choice(["principal", "subsidiary"]), "condition": "se"}
                        for i in range(len(amounts))]
            items = [{"request_ids": [f"R{i}"], "expected_result": str(a), "include_in_total": True} for i, a in enumerate(amounts)]
            review = {"requests": requests, "labor_review": {"calculation_set": {"items": items}}}
            expected = sum((a for a, r in zip(amounts, requests) if r["priority"] == "principal"), Decimal("0"))
            self.assertEqual(Decimal(claim_value(review, [r["id"] for r in requests])["total"]), expected)
            self.assertTrue(brl(expected).startswith("R$ "))

    def test_consistency_is_order_independent(self):
        rng = random.Random(SEED)
        values = ["2.200,00", "2.500,00", "3.100,00"]
        for _ in range(30):
            chapters = [{"id": f"C{i}", "issue_ids": ["I1"], "request_ids": [],
                         "paragraphs": [{"id": "P1", "text": f"Salário de R$ {rng.choice(values)}.", "fact_ids": [], "norm_ids": [],
                                         "issue_ids": ["I1"], "request_ids": []}]} for i in range(4)]
            first = check_consistency(chapters, {"requests": []})
            shuffled = chapters[:]
            rng.shuffle(shuffled)
            second = check_consistency(shuffled, {"requests": []})
            self.assertEqual(first["blocking_count"], second["blocking_count"])
            distinct = {p["text"] for c in chapters for p in c["paragraphs"]}
            self.assertEqual(first["blocking_count"] > 0, len(distinct) > 1)


if __name__ == "__main__":
    unittest.main()
