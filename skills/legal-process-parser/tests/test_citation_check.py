"""Offline checks of cited provisions; the fixture is a cut of the official CLT page."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock, patch

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.case_memory import atomic_json, identity
from scripts.citation_check import check_citation, parse_citations, prose_citation_gaps, segment_articles, version_markers
from scripts.research_sources import SourceBlocked, capture, source_text
from scripts.source_records import inspect_source_record, same_source_url
from scripts.response_research import begin_response, consult_http, record_unavailable_attempt, validate_response, verify_session
from scripts.legal_review import norm_citation_checks
from tests import test_response_research as response_tests

FIXTURE = CORE / "tests" / "fixtures" / "planalto_clt_excerpt.html"


def clt_text() -> str:
    return source_text(FIXTURE.read_bytes(), "text/html", "cp1252")


def fake_response(raw: bytes, content_type: str = "text/html", status: int = 200, headers: dict | None = None):
    response = MagicMock()
    response.__enter__.return_value = response
    response.geturl.return_value = "https://www.tst.jus.br/sumulas"
    response.status = status
    message = Message()
    message["Content-Type"] = content_type
    for key, value in (headers or {}).items():
        message[key] = value
    response.headers = message
    response.read.return_value = raw
    opener = MagicMock()
    opener.open.return_value = response
    return opener


class Citations(unittest.TestCase):
    def test_parse_structured_citations(self):
        found = parse_citations("Art. 7º, XIII, da CF; art. 71, § 4º, da CLT; art. 59-A; Súmula 437 do TST; "
                                "OJ 394 da SBDI-1; Tema 1046 do STF; ADI 5.766; NR-15; IN 41/2018 do TST; LC 150/2015; Lei nº 13.467/2017")
        keys = {(c["kind"], c["number"]) for c in found}
        self.assertTrue({("article", "7"), ("article", "71"), ("article", "59-A"), ("sumula", "437"), ("oj", "394"),
                         ("tema", "1046"), ("control", "ADI 5766"), ("nr", "15"), ("instruction", "41"),
                         ("law", "150/2015"), ("law", "13467/2017")} <= keys)
        self.assertEqual(next(c for c in found if c["number"] == "71")["paragraph"], "4")

    def test_official_text_segments_and_markers(self):
        text = clt_text()
        self.assertEqual([s["number"] for s in segment_articles(text)], ["58", "71", "384"])
        revoked = check_citation(text, "Art. 384")
        self.assertEqual([f["code"] for f in revoked["findings"]], ["provision_revoked"])
        intrajornada = check_citation(text, "CLT, art. 71, § 4º", "apenas do período suprimido, com acréscimo de 50%",
                                      fact_dates=["2016-03-01"])
        self.assertTrue(intrajornada["located"])
        self.assertIn("wording_changed_after_facts", [f["code"] for f in intrajornada["findings"]])
        self.assertEqual(check_citation(text, "art. 71, § 4º", "apenas do período suprimido, com acréscimo de 50%",
                                        fact_dates=["2019-03-01"])["status"], "located_no_marker")

    def test_quote_outside_provision_or_missing_article_blocks(self):
        text = clt_text()
        outside = check_citation(text, "art. 71, caput", "apenas do período suprimido, com acréscimo de 50%")
        self.assertIn("quote_outside_provision", [f["code"] for f in outside["findings"]])
        self.assertEqual(outside["status"], "blocking")
        missing = check_citation(text, "art. 9999", "apenas do período suprimido")
        self.assertIn("provision_not_found", [f["code"] for f in missing["findings"]])
        self.assertIn("paragraph_not_found", [f["code"] for f in check_citation(text, "art. 71, § 9º")["findings"]])
        self.assertIn("quote_too_short", [f["code"] for f in check_citation(text, "art. 71", "intervalo")["findings"]])
        self.assertEqual(check_citation(text, "Regra de teste")["status"], "located_no_marker")

    def test_struck_wording_is_not_current_text(self):
        html = ("<p>Art. 10 - Texto vigente sintético da regra de teste.</p>"
                "<p><strike>Art. 10 - Redação anterior sintética já substituída.</strike></p>"
                "<p>Art. 11 - Outra regra sintética.</p>").encode("utf-8")
        text = source_text(html, "text/html", "utf-8")
        self.assertIn("quote_in_struck_text", [f["code"] for f in check_citation(text, "art. 10", "Redação anterior sintética já substituída")["findings"]])
        self.assertEqual(check_citation(text, "art. 10", "Texto vigente sintético da regra")["status"], "located_no_marker")

    def test_precedent_identifier_and_status(self):
        page = "Súmula nº 450 do TST (cancelada) - Res. sintética. Texto sintético de teste sobre férias."
        result = check_citation(page, "Súmula 450 do TST", "Texto sintético de teste")
        self.assertIn("precedent_cancelled_or_revoked", [f["code"] for f in result["findings"]])
        self.assertIn("precedent_not_found", [f["code"] for f in check_citation(page, "Súmula 338 do TST")["findings"]])
        self.assertIn("tema_status_not_observed", [f["code"] for f in check_citation("Tema 1046 - descrição sintética.", "Tema 1046")["findings"]])
        self.assertEqual(version_markers("(Vide ADI nº 5.766)")[0]["action"], "ADI 5766")

    def test_prose_citation_requires_linked_norm(self):
        norm = {"title": "CLT", "provision": "art. 71, § 4º", "quote": "apenas do período suprimido",
                "official_text": "(Redação dada pela Lei nº 13.467, de 2017)"}
        gaps = prose_citation_gaps("Incide o art. 71, § 4º, da CLT (Lei 13.467/2017) e a Súmula 437 do TST.", [norm])
        self.assertEqual([g["label"] for g in gaps], ["Súmula 437"])
        self.assertEqual(prose_citation_gaps("O art. 5º do contrato de trabalho previa prêmio.", []), [])

    def test_url_comparison_ignores_www_fragment_and_slash_only(self):
        self.assertTrue(same_source_url("https://www.planalto.gov.br/a/b.htm#art71", "https://planalto.gov.br/a/b.htm"))
        self.assertFalse(same_source_url("https://portal.stf.jus.br/tema.asp?num=1046", "https://portal.stf.jus.br/tema.asp?num=725"))


class PortalBlocks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)

    def test_waf_challenge_and_security_page_are_not_captures(self):
        cases = [fake_response(b"", status=202, headers={"x-amzn-waf-action": "challenge"}),
                 fake_response("<html><title>Verificação de segurança — Senado Federal</title><p>Aguarde</p></html>".encode()),
                 fake_response(b"   ", content_type="text/plain")]
        for opener in cases:
            with self.subTest(opener=opener), patch("scripts.research_sources.build_opener", return_value=opener):
                with self.assertRaises(SourceBlocked):
                    capture("https://www.tst.jus.br/sumulas", self.output)
        self.assertFalse((self.output / "research_sources").exists())

    def test_json_official_series_is_captured(self):
        opener = fake_response(b'[{"data":"01/10/2026","valor":"0.66"}]', content_type="application/json")
        with patch("scripts.research_sources.build_opener", return_value=opener):
            receipt = capture("https://api.bcb.gov.br/dados/serie/bcdata.sgs.4390/dados/ultimos/1?formato=json", self.output)
        self.assertIn("0.66", receipt["text"])
        self.assertEqual(inspect_source_record(receipt, self.output)["errors"], [])

    def test_edited_text_with_recomputed_hashes_is_rejected(self):
        opener = fake_response(FIXTURE.read_bytes())
        with patch("scripts.research_sources.build_opener", return_value=opener):
            receipt = capture("https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm", self.output)
        self.assertEqual(inspect_source_record(receipt, self.output)["errors"], [])
        forged = {k: v for k, v in receipt.items() if k != "capture_id"}
        forged["text"] = receipt["text"].replace("Revogado", "Vigente")
        forged["text_hash"] = hashlib.sha256(forged["text"].encode("utf-8")).hexdigest()
        forged["capture_id"] = identity(forged)
        (self.output / "research_sources" / (forged["capture_id"] + ".source")).write_bytes(FIXTURE.read_bytes())
        self.assertIn("texto registrado não corresponde à resposta bruta preservada", inspect_source_record(forged, self.output)["errors"])


class SessionVerification(unittest.TestCase):
    # Reuse the synthetic case without re-running the inherited test methods.
    setUp = response_tests.ResponseResearch.setUp
    fake_http = response_tests.ResponseResearch.fake_http
    researched = response_tests.ResponseResearch.researched

    def test_blocked_portal_is_recorded_as_unavailable(self):
        state = begin_response(self.output, ["I1"], "synthetic-block")
        with patch("scripts.response_research.capture", side_effect=SourceBlocked("desafio anti-robô")):
            row = consult_http(self.output, state["response_id"], "I1", "N1", "https://www.tst.jus.br/sumulas", purpose="Fixture")
        self.assertEqual((row["status"], row["reason_code"]), ("unavailable", "blocked_by_portal"))
        attempt = record_unavailable_attempt(self.output, state["response_id"], "I1", "N1", url="https://portal.stf.jus.br/",
                                             reason="Portal bloqueou o navegador da sessão", attempt_reference="synthetic-attempt",
                                             purpose="Fixture")
        self.assertEqual(attempt["reason_code"], "blocked_by_portal")
        self.assertTrue(all(r["status"] == "unavailable" for r in verify_session(self.output, state["response_id"], self.review)))

    def test_consulted_url_must_be_the_norm_source(self):
        payload = self.researched()
        self.assertFalse(validate_response(self.output, payload, self.review)["errors"])
        review = copy.deepcopy(self.review)
        review["norms"][0]["url"] = "https://www.planalto.gov.br/outra-lei"
        payload["artifact_hash"] = __import__("scripts.response_research", fromlist=["target_hash"]).target_hash(review)
        self.assertTrue(any("difere da URL" in e for e in validate_response(self.output, payload, review)["errors"]))

    def test_v4_norm_quote_must_sit_in_its_provision(self):
        review = copy.deepcopy(self.review)
        text = clt_text()
        review["norms"][0].update(official_text=text, provision="art. 71, caput",
                                  quote="apenas do período suprimido, com acréscimo de 50%")
        self.assertEqual(norm_citation_checks(review)["N1"]["status"], "blocking")
        review["norms"][0]["provision"] = "art. 71, § 4º"
        review["normative_map"][0]["relevant_dates"] = [{"date": "2016-03-01", "reason": "Fixture", "fact_ids": ["F1"]}]
        codes = [f["code"] for f in norm_citation_checks(review)["N1"]["findings"]]
        self.assertEqual(codes, ["wording_changed_after_facts"])


if __name__ == "__main__":
    unittest.main()
