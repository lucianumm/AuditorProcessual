"""Catalog v2 integrity, candidate authorities and official series; no live network."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.capabilities import select_source_route
from scripts.citation_check import check_citation
from scripts.contracts import validate_contract
from scripts.labor_catalog import claim_brief, claim_catalog, index_markdown, thesis_map_markdown
from scripts.labor_research import research_agenda
from scripts.official_indices import accumulate, fetch_series, parse_series
from scripts.research_sources import source_text
from scripts.source_registry import access_tier, portal_for, routes
from scripts.task_context import resolve_context

REFS = CORE / "references"


class Catalog(unittest.TestCase):
    def test_catalogs_follow_their_schemas(self):
        for data, schema in (("labor_claims.json", "labor_claims.schema.json"), ("labor_authorities.json", "labor_authorities.schema.json")):
            with self.subTest(data=data):
                self.assertEqual(validate_contract(json.loads((REFS / data).read_text(encoding="utf-8")), schema), [])

    def test_every_claim_has_both_parties_and_resolved_authorities(self):
        claims = claim_catalog()
        self.assertGreaterEqual(len(claims), 90)
        for claim in claims.values():
            self.assertTrue(claim["claimant_theses"] and claim["defense_theses"], claim["id"])
        brief = claim_brief(["overtime", "intrajornada"], "reclamada")
        self.assertNotIn("claimant_theses", brief["claims"][0])
        labels = {a["label"] for t in brief["claims"][0]["defense_theses"] for a in t["authorities"]}
        self.assertIn("EC 141/2026, art. 8º", labels)
        with self.assertRaises(ValueError):
            claim_brief(["overtime"], "terceiro")

    def test_cancelled_precedents_carry_their_status(self):
        authorities = {a["id"]: a for a in json.loads((REFS / "labor_authorities.json").read_text(encoding="utf-8"))["authorities"]}
        for sid in ("sumula_tst_90", "sumula_tst_437", "sumula_tst_450", "oj_sdi1_355"):
            self.assertEqual(authorities[sid]["status"], "cancelada", sid)
        self.assertEqual(authorities["clt_art384"]["status"], "revogado")
        self.assertEqual(authorities["tema_stf_1291"]["status"], "merito_pendente")

    def test_index_and_thesis_map_are_generated(self):
        self.assertEqual((REFS / "labor_claims_index.md").read_text(encoding="utf-8"), index_markdown())
        text = thesis_map_markdown(["commute_time"])
        self.assertIn("Teses da defesa", text)
        self.assertIn("planalto.gov.br", text)
        self.assertIn("2017-11-11", text)

    def test_agenda_points_to_specific_authorities(self):
        agenda = research_agenda(["intrajornada"], [])
        ids = {a["id"] for a in agenda["queries"][0]["candidate_authorities"]}
        self.assertTrue({"clt_art71", "sumula_tst_437"} <= ids)
        self.assertIn("reforma_trabalhista_2017", agenda["queries"][0]["temporal_marker_ids"])

    def test_routing_loads_index_and_claim_guides_only(self):
        context = resolve_context("generic", "analyze", labor_claims=["occupational_damage"])
        paths = [r["path"] for r in context["references"]]
        self.assertTrue(any(p.endswith("labor_claims_index.md") for p in paths))
        self.assertTrue(any(p.endswith("occupational_strategy_rules.md") for p in paths))
        self.assertFalse(any(p.endswith("labor_authorities.json") or p.endswith("labor_claims.json") for p in paths))
        self.assertIn("source_verification", context["triggers"])


class ConstitutionalAmendment(unittest.TestCase):
    def test_ec_141_wording_is_detected_against_older_facts(self):
        text = source_text((CORE / "tests/fixtures/planalto_cf_art7_excerpt.html").read_bytes(), "text/html", "cp1252")
        current = "duração do trabalho normal não superior a 8 (oito) horas diárias e 40 (quarenta) horas semanais"
        result = check_citation(text, "CF, art. 7º, XIII", current, fact_dates=["2025-03-01"])
        self.assertEqual([f["code"] for f in result["findings"]], ["wording_changed_after_facts"])
        old = "duração do trabalho normal não superior a oito horas diárias e quarenta e quatro semanais"
        self.assertEqual(check_citation(text, "CF, art. 7º, XIII", old)["status"], "blocking")


class Registry(unittest.TestCase):
    def test_portal_tiers_and_routes(self):
        self.assertEqual(access_tier("https://www.planalto.gov.br/ccivil_03/x.htm"), "http_capture")
        self.assertEqual(access_tier("https://www.tst.jus.br/sumulas"), "browser_only")
        self.assertEqual(portal_for("https://www.trt15.jus.br/")["id"], "trt")
        self.assertIsNone(portal_for("https://www.gov.br/inss/pt-br"))
        self.assertEqual(routes("precedent")[0]["id"], "tst")
        self.assertEqual(select_source_route(local_http=True, url="https://portal.stf.jus.br/")["method"], "source_unavailable")
        self.assertEqual(select_source_route(local_http=True, url="https://www.planalto.gov.br/")["method"], "official_http_capture")


class OfficialIndices(unittest.TestCase):
    def test_series_parse_and_accumulation(self):
        points = parse_series('[{"data":"01/07/2026","valor":"1.22"},{"data":"01/08/2026","valor":"1.09"}]')
        self.assertEqual(points[0], {"date": "2026-07-01", "value": "1.22"})
        self.assertEqual(accumulate(points, mode="compound")["factor"], "1.023232980000")
        self.assertEqual(accumulate(points, mode="simple")["factor"], "1.023100000000")
        with self.assertRaises(ValueError):
            accumulate(points, mode="automatic")

    def test_fetch_uses_receipted_capture(self):
        fake = {"capture_id": "c" * 64, "url": "https://api.bcb.gov.br/x", "accessed_on": "2026-10-21",
                "text": '[{"data":"01/09/2026","valor":"1.08"}]'}
        with tempfile.TemporaryDirectory() as temporary, patch("scripts.official_indices.capture", return_value=fake) as mocked:
            result = fetch_series(Path(temporary), "4390", "2026-09-01", "2026-09-30")
        self.assertIn("dataInicial=01/09/2026", mocked.call_args.args[0])
        self.assertEqual(result["points"][0]["value"], "1.08")
        with self.assertRaises(ValueError):
            fetch_series(Path("."), "4390", "2026-10-01", "2026-09-01")


if __name__ == "__main__":
    unittest.main()
