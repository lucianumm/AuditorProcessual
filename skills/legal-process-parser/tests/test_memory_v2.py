"""Corpus updates and retrieval must remain correct after separate uploads."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))

from scripts.case_memory import atomic_json, atomic_text, query_memory, update_memory
from scripts.case_search import INDEX_NAME, search_memory
from scripts.contracts import validate_contract
from scripts.ingest_document import run_ingest


class CumulativeMemoryV2(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.output = self.base / "saída"
        self.first = self.base / "primeiro.txt"
        self.first.write_text("Maria recebeu R$ 150 em 10/03/2025. Termo singularABC.", encoding="utf-8")
        run_ingest(self.first, self.output, task="ingest")

    def test_real_pagination_filters_and_legacy_query(self):
        for number in range(2):
            source = self.base / f"outro{number}.txt"
            source.write_text(f"Maria recebeu R$ {number} em 12/03/2025. Termo singularABC.", encoding="utf-8")
            run_ingest(source, self.output, task="ingest")
        self.assertTrue((self.output / INDEX_NAME).is_file())
        first = search_memory(self.output, "singularABC", limit=1, person="Maria",
                              date_from="2025-03-10", date_to="2025-03-12")
        self.assertEqual(first["total"], 3)
        self.assertEqual(first["next_offset"], 1)
        self.assertEqual(len(first["pages"]), 1)
        self.assertIn("snippet", first["pages"][0])
        self.assertNotIn("text", first["pages"][0])
        with patch.object(Path, "read_text", side_effect=AssertionError("JSON was reloaded")):
            second = search_memory(self.output, "singularABC", offset=1, limit=1)
        self.assertEqual(second["total"], 3)
        self.assertNotEqual(first["pages"][0]["page_id"], second["pages"][0]["page_id"])
        self.assertEqual(len(query_memory(self.output, "gularABC")), 3)
        self.assertEqual(search_memory(self.output, "", amount="R$ 150")["total"], 1)

    def test_changed_page_propagates_declared_dependencies(self):
        memory = json.loads((self.output / "case_memory.json").read_text(encoding="utf-8"))
        document = memory["documents"][0]
        page = document["pages"][0]
        page_id = f"{document['sha256']}:1"
        review = {"corpus_revision": memory["corpus_revision"],
                  "facts": [{"id": "F1", "sources": [{"source_sha256": document["sha256"], "pdf_page": 1}]}],
                  "issues": [{"id": "I1", "fact_ids": ["F1"], "norm_ids": ["N1"]}],
                  "requests": [{"id": "R1", "issue_ids": ["I1"]}],
                  "paragraphs": [{"id": "P1", "request_ids": ["R1"]}]}
        atomic_json(self.output / "legal_review.json", review)
        page["vision"] = {"description": "Fotografia acrescida após revisão."}
        atomic_text(self.output / "pages.jsonl", json.dumps(page, ensure_ascii=False) + "\n")
        refreshed = update_memory(self.output)
        self.assertEqual(refreshed["update"]["changed_pages"], [page_id])
        impact = refreshed["update"]["impacted_elements"]
        self.assertEqual(impact["fact_ids"], ["F1"])
        self.assertEqual(impact["issue_ids"], ["I1"])
        self.assertEqual(impact["request_ids"], ["R1"])
        self.assertEqual(impact["paragraph_ids"], ["P1"])
        self.assertEqual(impact["unmapped_page_ids"], [])
        self.assertTrue(refreshed["update"]["requires_legal_reassessment"])
        self.assertEqual(validate_contract(refreshed, "case_memory.schema.json"), [])

    def test_new_source_without_declared_link_requires_corpus_comparison(self):
        source = self.base / "novo.txt"
        source.write_text("Outra Maria recebeu R$ 150.", encoding="utf-8")
        run_ingest(source, self.output, task="ingest")
        memory = json.loads((self.output / "case_memory.json").read_text(encoding="utf-8"))
        self.assertEqual(len(memory["documents"]), 2)
        self.assertEqual(len(memory["update"]["changed_pages"]), 1)
        self.assertEqual(memory["update"]["changed_pages"], memory["update"]["impacted_elements"]["unmapped_page_ids"])
        self.assertTrue((self.output / "versions").is_dir())
        self.assertEqual(validate_contract(memory, "case_memory.schema.json"), [])


if __name__ == "__main__":
    unittest.main()
