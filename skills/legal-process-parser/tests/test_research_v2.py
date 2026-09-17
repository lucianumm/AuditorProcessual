"""Source provenance tests use synthetic text and mocked HTTP responses only."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock, patch

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))

from scripts.capabilities import select_source_route
from scripts.research_sources import capture
from scripts.source_records import (
    inspect_norm_source,
    inspect_source_record,
    official_url,
    record_browser_observation,
    record_unavailable_source,
)


class SourceRecordsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.output = Path(self.temp.name)
        self.url = "https://www.planalto.gov.br/fixture"
        self.text = "Art. 1º Regra inteiramente sintética de teste."
        self.norm = {"url": self.url, "accessed_on": "2026-09-16", "official_text": self.text,
                     "quote": "Regra inteiramente sintética"}

    def tearDown(self):
        self.temp.cleanup()

    def test_http_receipt_checks_preserved_bytes_and_does_not_upload(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = self.url
        response.headers = Message()
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        response.read.return_value = self.text.encode("utf-8")
        opener = MagicMock()
        opener.open.return_value = response
        with patch("scripts.research_sources.build_opener", return_value=opener):
            receipt = capture(self.url, self.output)
        request = opener.open.call_args.args[0]
        self.assertIsNone(request.data)
        self.assertEqual(request.full_url, self.url)
        norm = {**self.norm, "accessed_on": receipt["accessed_on"], "capture_id": receipt["capture_id"]}
        result = inspect_norm_source(norm, self.output)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["evidence_level"], "verified_http")
        (self.output / "research_sources" / f"{receipt['capture_id']}.source").write_bytes(b"adulterado")
        result = inspect_norm_source(norm, self.output)
        self.assertIn("resposta oficial bruta ausente ou alterada", result["errors"])
        self.assertEqual(result["evidence_level"], "invalid")

    def test_browser_observation_remains_unattested_and_detects_changes(self):
        record = record_browser_observation(
            self.output, url=self.url, accessed_on="2026-09-16", text=self.text,
            context="Trecho do artigo sintético consultado na página indicada.",
            tool_reference="host-tool-result-001", observed_by="host-agent",
            coverage_scope="excerpt", locator="Art. 1º",
        )
        result = inspect_norm_source({**self.norm, "source_record_id": record["source_record_id"]}, self.output)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["evidence_level"], "self_recorded_unverified")
        self.assertTrue(any("não atesta" in item for item in result["warnings"]))
        record["text"] = "Texto trocado por afirmação diferente."
        path = self.output / "research_sources" / f"{record['source_record_id']}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        result = inspect_norm_source({**self.norm, "source_record_id": record["source_record_id"]}, self.output)
        self.assertEqual(result["evidence_level"], "invalid")
        self.assertTrue(any("identidade" in error for error in result["errors"]))

    def test_browser_record_cannot_claim_http_verification(self):
        record = record_browser_observation(
            self.output, url=self.url, accessed_on="2026-09-16", text=self.text,
            context="Contexto", tool_reference="tool-1", observed_by="host-agent",
        )
        record["evidence_level"] = "verified_http"
        result = inspect_source_record(record, self.output)
        self.assertEqual(result["evidence_level"], "invalid")
        self.assertTrue(any("atestado" in error for error in result["errors"]))

    def test_browser_missing_real_reference_rejected_at_recording(self):
        with self.assertRaisesRegex(ValueError, "tool_reference"):
            record_browser_observation(
                self.output, url=self.url, accessed_on="2026-09-16", text=self.text,
                context="Contexto", tool_reference="", observed_by="host-agent",
            )

    def test_unavailable_source_is_recorded_but_cannot_support_norm(self):
        record = record_unavailable_source(
            self.output, url=self.url, accessed_on="2026-09-16",
            reason="A página não respondeu.", attempt_reference="browser-error-1", issue_ids=["I1"],
        )
        self.assertEqual(inspect_source_record(record, self.output)["evidence_level"], "unavailable")
        result = inspect_norm_source({**self.norm, "source_record_id": record["source_record_id"]}, self.output)
        self.assertEqual(result["evidence_level"], "invalid")
        self.assertIn("fonte inacessível não sustenta norma", result["errors"])

    def test_routes_need_observed_capability(self):
        self.assertEqual(select_source_route()["method"], "source_unavailable")
        self.assertEqual(select_source_route(local_http=False, host_browsing=True)["method"], "browser_observation")
        self.assertEqual(select_source_route(local_http=True, host_browsing=True)["method"], "official_http_capture")
        self.assertFalse(official_url("https://planalto.gov.br.evil.example/fixture"))


if __name__ == "__main__":
    unittest.main()
