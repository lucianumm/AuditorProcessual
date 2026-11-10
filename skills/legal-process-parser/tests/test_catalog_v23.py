"""v0.23.0: catálogos ampliados, precedentes lidos nos portais, busca por fatos e peças novas (sem rede)."""
from __future__ import annotations

import http.client
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

CORE = Path(__file__).resolve().parents[1]
ROOT = CORE.parents[1]
sys.path.insert(0, str(CORE))
from scripts.claim_search import fold, search, terms  # noqa: E402
from scripts.domain_catalog import catalogs, claim_brief, integrity_errors  # noqa: E402
from scripts.labor_catalog import claim_brief as labor_brief, claim_catalog as labor_claims  # noqa: E402
from scripts.legislation_lookup import _get_json  # noqa: E402
from scripts.procedural_catalog import candidates  # noqa: E402

REFS = CORE / "references"
WARNING_WORDS = ("cancelad", "cancelament", "revogad", "perdeu eficácia", "fatos anteriores", "até 10/11/2017", "antes de", "sem vigência")


def authorities(name: str) -> dict:
    return {a["id"]: a for a in json.loads((REFS / name).read_text(encoding="utf-8"))["authorities"]}


class ExpandedCatalogs(unittest.TestCase):
    def test_counts_and_minimum_depth_per_branch(self):
        self.assertGreaterEqual(len(labor_claims()), 123)
        per_branch = {key: len(c["claims"]) for key, c in catalogs().items()}
        self.assertGreaterEqual(sum(per_branch.values()), 257)
        self.assertTrue(all(n >= 5 for n in per_branch.values()), per_branch)
        self.assertEqual(integrity_errors(), [])

    def test_new_labor_claims_resolve_and_load_their_guides(self):
        brief = labor_brief(["social_security_limbo", "partner_veil", "rescission_action"], "ambos")
        ids = {a["id"] for c in brief["claims"] for side in ("claimant_theses", "defense_theses") for t in c[side] for a in t["authorities"]}
        self.assertTrue({"l8213_art63", "clt_art855a", "cpc_art966", "sumula_tst_100"} <= ids)
        for claim in labor_claims().values():
            if claim.get("reference"):
                self.assertTrue((REFS / claim["reference"]).is_file(), claim["reference"])

    def test_theses_citing_cancelled_precedents_say_so(self):
        auth = authorities("labor_authorities.json")
        for claim in labor_claims().values():
            for thesis in claim["claimant_theses"] + claim["defense_theses"]:
                dead = [a for a in thesis["authority_ids"] if auth[a]["status"] in ("cancelada", "revogado", "sem_vigencia")]
                if dead:
                    self.assertTrue(any(w in thesis["label"].lower() for w in WARNING_WORDS), (thesis["id"], dead))

    def test_portal_readings_are_recorded_with_hash_and_source(self):
        for name in ("labor_authorities.json", "domain_authorities.json"):
            for a in authorities(name).values():
                verified = a["verified"]
                if verified["method"] == "official_browser_observation" and verified["on"] == "2026-11-10":
                    self.assertRegex(verified.get("capture_text_hash", ""), r"^[0-9a-f]{64}$", a["id"])
                    self.assertTrue(verified.get("source_url", "").startswith("https://"), a["id"])
        labor = authorities("labor_authorities.json")
        self.assertEqual(labor["sumula_tst_90"]["status"], "cancelada")
        self.assertEqual(labor["sumula_tst_372"]["status"], "alterada")
        self.assertIn("10/11/2026", labor["sumula_tst_372"]["status_note"])
        domain = authorities("domain_authorities.json")
        self.assertEqual(domain["tema_stf_987"]["status"], "tese_firmada")
        self.assertIn("não reproduz a tese", domain["tema_stf_987"]["status_note"])

    def test_statutes_added_in_this_version_were_located_in_official_text(self):
        domain = authorities("domain_authorities.json")
        for ident in ("l12732_art2", "l9504_art36", "l4591_art43a", "l13445_art50", "lc76_art3", "l8245_art19"):
            self.assertEqual(domain[ident]["verified"]["method"], "normas_leg_br_http_capture", ident)
            self.assertTrue(domain[ident]["verified"]["located"], ident)

    def test_branch_brief_carries_new_temporal_markers(self):
        claim = claim_brief(["imob_distrato"], "ambos")["claims"][0]
        self.assertIn("lei_13786_distrato", {m["id"] for m in claim["temporal_markers"]})


class ClaimSearch(unittest.TestCase):
    def test_terms_fold_accents_and_drop_stopwords(self):
        self.assertEqual(fold("Previdenciário"), "previdenciario")
        self.assertNotIn("de", terms("alta do INSS e recusa de retorno"))

    def test_search_finds_the_matching_claim_first(self):
        cases = {"INSS deu alta e a empresa não deixou voltar ao trabalho": "social_security_limbo",
                 "banco cobrou juros acima da média e capitalização": "banc_interest_fees",
                 "atraso na entrega do apartamento na planta": "imob_delay_delivery",
                 "busca domiciliar sem mandado": "pen_search_recognition"}
        for query, expected in cases.items():
            with self.subTest(query=query):
                self.assertEqual(search(query)["results"][0]["id"], expected)

    def test_domain_filter_and_empty_query(self):
        result = search("prescrição", domain="tributario")
        self.assertTrue(result["results"])
        self.assertTrue(all(r["domain"] == "tributario" for r in result["results"]))
        self.assertEqual(result["legal_status"], "candidate_claims_only")
        with self.assertRaises(ValueError):
            search("de a o")


class NewPieces(unittest.TestCase):
    def test_electoral_and_lease_pieces_are_candidates(self):
        self.assertIn("aime", {c["id"] for c in candidates("eleitoral", "conhecimento")["candidates"]})
        self.assertIn("acao_renovatoria_locacao", {c["id"] for c in candidates("imobiliario", "preprocessual")["candidates"]})
        self.assertIn("dissidio_coletivo", {c["id"] for c in candidates("trabalhista", "preprocessual")["candidates"]})
        self.assertIn("habeas_corpus", {c["id"] for c in candidates("migratorio", "administrativo")["candidates"]})


class TruncatedOfficialResponse(unittest.TestCase):
    def test_get_json_retries_incomplete_read(self):
        good = MagicMock()
        good.__enter__.return_value.read.return_value = b'{"ok": true}'
        bad = MagicMock()
        bad.__enter__.return_value.read.side_effect = http.client.IncompleteRead(b"{")
        with patch("scripts.legislation_lookup.urlopen", side_effect=[bad, good]):
            self.assertEqual(_get_json("https://normas.leg.br/api/x"), {"ok": True})
        with patch("scripts.legislation_lookup.urlopen", side_effect=[bad, bad, bad]):
            with self.assertRaises(OSError):
                _get_json("https://normas.leg.br/api/x")


@unittest.skipUnless((ROOT / "scripts" / "catalog_intake.py").is_file(), "ferramenta de manutenção fora do pacote")
class CatalogIntake(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import catalog_intake
        self.ci = catalog_intake
        self.record = {"act": "LEI:8245:1991", "meta": {"text_version": "Current", "legal_force": None, "revoked_by": [],
                                                        "page_url": "https://normas.leg.br/?urn=urn:lex:br:federal:lei:1991-10-18;8245"},
                       "text": "Art. 18. Outro assunto.\nArt. 19. Não havendo acordo, o locador ou locatário, após três anos de vigência do contrato, poderão pedir revisão judicial do aluguel.\nArt. 20. Fim.\n",
                       "text_hash": "a" * 64, "accessed_on": "2026-11-10", "source_url": "https://normas.leg.br/api/public/binario/x/texto"}

    def test_subject_must_appear_inside_the_article(self):
        item = {"id": "l8245_art19", "act": "LEI:8245:1991", "article": "19", "law": "Lei 8.245/1991", "short": "Lei 8.245/1991",
                "subject": "Revisional após três anos.", "expect": ["tres anos", "revisao judicial"]}
        with patch.object(self.ci, "load_act", return_value=self.record):
            entry, problem = self.ci.verify(item, Path("."))
            self.assertIsNone(problem)
            self.assertEqual(entry["status"], "localizado_no_texto_oficial")
            self.assertEqual(entry["label"], "Lei 8.245/1991, art. 19")
            wrong, problem = self.ci.verify(dict(item, article="18"), Path("."))
            self.assertIsNone(wrong)
            self.assertEqual(problem["problem"], "assunto_nao_confere")
            missing, problem = self.ci.verify(dict(item, article="77"), Path("."))
            self.assertEqual(problem["problem"], "artigo_nao_localizado")


if __name__ == "__main__":
    unittest.main()
