"""Request cycle (CRIP) scenarios on synthetic records; no model, portal or expert run."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from unittest.mock import patch

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.case_memory import atomic_bytes, atomic_json, identity, update_memory
from scripts.ingest_document import run_ingest
from scripts.petition_workspace import assemble, initialize, save_chapter, set_status
from scripts.request_cycle import (begin_cycle, close_cycle, compute_scope, cycle_markdown, load_cycle,
                                   reread_batch, sweep, validate_cycle)
from scripts.research_memory import register_source_record
from scripts.response_research import begin_response, consult_http, utc_now
from tests.test_incremental_petition import chapter_fixture
from tests.test_labor_workflow import synthetic_case

save_chapter = partial(save_chapter, require_response=False)
DOCUMENT = "REGISTRO INTEIRAMENTE SINTÉTICO. Holerite de teste: salário de R$ 2.500,00 na competência 08/2026."
FINDINGS = [{"id": "A1", "severity": "material", "reviewer": "same_model_clean_context",
             "objection": "A parte contrária dirá que o salário do holerite difere do relato.",
             "resolution": "O capítulo indica a competência de cada valor."}]


class RequestCycle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output, self.review, _ = synthetic_case(self.root, documents=1, document_text=DOCUMENT)
        initialize(self.output, self.review)
        norm = self.review["norms"][0]
        self.original = json.loads((self.output / "research_sources" / (norm["capture_id"] + ".json")).read_text(encoding="utf-8"))
        self.raw = (self.output / "research_sources" / (norm["capture_id"] + ".source")).read_bytes()

    def fake_http(self, url, output, *, response_id=None):
        # Controlled fixture: reuses preserved bytes; never a real HTTP call.
        record = {k: v for k, v in self.original.items() if k != "capture_id"}
        record.update(requested_url=url, url=url, captured_at=utc_now(),
                      accessed_on=datetime.now(timezone.utc).date().isoformat(), response_id=response_id)
        record["capture_id"] = identity(record)
        atomic_bytes(output / "research_sources" / (record["capture_id"] + ".source"), self.raw)
        atomic_json(output / "research_sources" / (record["capture_id"] + ".json"), record)
        register_source_record(output, record)
        return record

    def response(self):
        state = begin_response(self.output, ["I1"], "synthetic-request")
        with patch("scripts.response_research.capture", side_effect=self.fake_http):
            consult_http(self.output, state["response_id"], "I1", "N1", self.review["norms"][0]["url"], purpose="Teste estrutural.")
        return state["response_id"]

    def atoms(self, **changes):
        rows = []
        for row in self.review["assertion_reviews"]:
            atoms = dict(row["atoms"], **changes.get(row["fact_id"], {}))
            rows.append({"fact_id": row["fact_id"], "atoms": atoms, "source_page": "relida", **(
                {"treatment": changes["treatment"]} if "treatment" in changes else {})})
        return rows

    def read_all(self, cid):
        batch = reread_batch(self.output, cid, max_chars=2000)
        while batch["next_offset"] is not None:
            batch = reread_batch(self.output, cid, offset=batch["next_offset"], max_chars=2000)

    def chapter(self, cid="salary", second="O registro sintético aponta salário de R$ 2.500,00 na competência 08/2026."):
        record = chapter_fixture(self.review, cid)
        record["paragraphs"][0]["text"] = "A parte recebia salário de R$ 2.200,00. Requer o acolhimento do pedido sintético."
        record["paragraphs"].append({"id": "P2", "text": second, "fact_ids": ["F2"], "norm_ids": [], "issue_ids": ["I1"],
                                     "request_ids": [], "assertions": [{"fact_id": "F2", "fields": {"actor": "Parte do cenário"}}]})
        return record

    def full_cycle(self, record, *, request="Desenvolva diferenças salariais"):
        cycle = begin_cycle(self.output, request, ["I1"])
        scope = compute_scope(self.output, cycle["cycle_id"])
        self.read_all(cycle["cycle_id"])
        sweep(self.output, cycle["cycle_id"])
        review = [{"page_id": p, "assessment": "context"} for p in load_cycle(self.output, cycle["cycle_id"])["counter_evidence_sweep"]["pages_outside_perimeter"]]
        closed = close_cycle(self.output, cycle["cycle_id"], atoms=self.atoms(), findings=FINDINGS, sweep_review=review,
                             chapter=record, response_id=self.response())
        return scope, closed

    def test_scope_includes_cited_pages_facts_and_chapters(self):
        cycle = begin_cycle(self.output, "Analise o salário", ["I1"])
        scope = compute_scope(self.output, cycle["cycle_id"])
        self.assertEqual(scope["fact_ids"], ["F1", "F2"])
        self.assertEqual(scope["norm_ids"], ["N1"])
        self.assertTrue(scope["reread_plan"] and all(r["mandatory"] for r in scope["reread_plan"]))
        self.assertIn("01/06/2026", scope["entities"])

    def test_close_requires_every_pass_of_integral_mode(self):
        cycle = begin_cycle(self.output, "Desenvolva diferenças salariais", ["I1"])
        compute_scope(self.output, cycle["cycle_id"])
        with self.assertRaises(ValueError) as error:
            close_cycle(self.output, cycle["cycle_id"], chapter=self.chapter())
        message = str(error.exception)
        for expected in ("P1: páginas obrigatórias", "varredura de contraprova", "P2: reextrair", "P3: vincular", "P5: registrar"):
            self.assertIn(expected, message)

    def test_full_cycle_binds_chapter_and_save_records_it(self):
        record = self.chapter()
        _, closed = self.full_cycle(record)
        self.assertEqual(closed["status"], "closed")
        self.assertTrue(all(r["status"] == "same" for r in closed["fact_diff"]))
        self.assertEqual(closed["citation_recheck"][0]["result"], "checked")
        self.assertEqual(closed["request_cards"][0]["request_id"], "R1")
        self.assertIn("Reconferência deste pedido", cycle_markdown(closed))
        self.assertIn("## Histórico de ciclos", (self.output / "relatorio_processual.md").read_text(encoding="utf-8"))
        record["request_cycle"] = {"cycle_id": closed["cycle_id"]}
        saved = save_chapter(self.output, record)
        self.assertEqual(saved["cycle_policy"], "cycle_closed")
        changed = copy.deepcopy(record)
        changed["paragraphs"][0]["text"] += " Acréscimo posterior ao ciclo."
        self.assertTrue(validate_cycle(self.output, record["request_cycle"], changed))
        with self.assertRaisesRegex(ValueError, "outro conteúdo"):
            save_chapter(self.output, changed)

    def test_divergent_fact_requires_treatment(self):
        cycle = begin_cycle(self.output, "Revise o salário", ["I1"])
        compute_scope(self.output, cycle["cycle_id"])
        self.read_all(cycle["cycle_id"])
        sweep(self.output, cycle["cycle_id"])
        response_id = self.response()
        with self.assertRaisesRegex(ValueError, "F1 divergent em amount sem tratamento"):
            close_cycle(self.output, cycle["cycle_id"], atoms=self.atoms(F1={"amount": "2500.00"}), findings=FINDINGS,
                        chapter=self.chapter(), response_id=response_id)
        closed = close_cycle(self.output, cycle["cycle_id"], atoms=self.atoms(F1={"amount": "2500.00"}, treatment="Atualizar a análise-base e reabrir o capítulo."),
                             findings=FINDINGS, chapter=self.chapter(), response_id=response_id)
        self.assertEqual(next(r for r in closed["fact_diff"] if r["fact_id"] == "F1")["status"], "divergent")

    def test_new_chapter_with_other_salary_conflicts_with_saved_chapter(self):
        record = self.chapter()
        _, closed = self.full_cycle(record)
        record["request_cycle"] = {"cycle_id": closed["cycle_id"]}
        save_chapter(self.output, record)
        other = self.chapter("salary_b", second="O registro sintético aponta salário de R$ 2.500,00.")
        other["paragraphs"] = [other["paragraphs"][1] | {"request_ids": ["R1"]}]
        with self.assertRaisesRegex(ValueError, "P6: Parâmetro com valores diferentes"):
            self.full_cycle(other, request="Desenvolva o capítulo B")

    def test_late_contradictory_upload_reopens_reading_and_facts(self):
        record = self.chapter()
        self.full_cycle(record)
        late = self.root / "tardio.txt"
        late.write_text("REGISTRO SINTÉTICO TARDIO. A reclamada afirma que pagou o salário de R$ 2.200,00 com recibo em 01/06/2026.", encoding="utf-8")
        run_ingest(late, self.output, task="analyze")
        update_memory(self.output)
        cycle = begin_cycle(self.output, "Revise com o novo documento", ["I1"])
        self.assertTrue(any(d["kind"] == "upload" for d in cycle["delta_since_last"]))
        scope = compute_scope(self.output, cycle["cycle_id"])
        self.assertTrue(any(r["priority"] == "new" for r in scope["reread_plan"]))
        self.read_all(cycle["cycle_id"])
        found = sweep(self.output, cycle["cycle_id"])
        self.assertTrue(any(q["query"] in {"recibo", "pagamento", "pago"} or q["kind"] == "entity" for q in found["queries"]))
        with self.assertRaisesRegex(ValueError, "Corpus mudou|page_reviews"):
            close_cycle(self.output, cycle["cycle_id"], atoms=self.atoms(), findings=FINDINGS, chapter=record, response_id=None)

    def test_assembly_requires_closed_cycle_and_accepts_legacy_chapters(self):
        record = self.chapter()
        _, closed = self.full_cycle(record)
        record["request_cycle"] = {"cycle_id": closed["cycle_id"]}
        save_chapter(self.output, record)
        set_status(self.output, "salary", "approved", "synthetic-user-reference")
        with self.assertRaisesRegex(ValueError, "Ciclo de reanálise ausente"):
            assemble(self.output, ["salary"], require_response=False, require_cycle=True)
        preview = assemble(self.output, ["salary"], require_response=False, preview=True)
        cycle = begin_cycle(self.output, "Consolide a peça", ["I1"])
        compute_scope(self.output, cycle["cycle_id"])
        self.read_all(cycle["cycle_id"])
        sweep(self.output, cycle["cycle_id"])
        done = close_cycle(self.output, cycle["cycle_id"], atoms=self.atoms(), findings=FINDINGS, artifact=preview, response_id=self.response())
        self.assertEqual(done["content_kind"], "assembly")
        result = assemble(self.output, ["salary"], require_response=False, require_cycle=True, cycle=done["cycle_id"])
        self.assertEqual(result["cycle_policy"], "cycle_closed")
        self.assertEqual(result["legacy_no_cycle"], [])

    def test_rapid_mode_needs_only_citations(self):
        cycle = begin_cycle(self.output, "O que diz a norma N1?", ["I1"], depth="rapido")
        compute_scope(self.output, cycle["cycle_id"])
        closed = close_cycle(self.output, cycle["cycle_id"], response_id=self.response())
        self.assertEqual(closed["content_kind"], "analysis")
        self.assertIn("passe P5 (modo rapido)", closed["not_executed"])

    def test_tampered_cycle_is_rejected(self):
        cycle = begin_cycle(self.output, "Analise", ["I1"], depth="rapido")
        path = self.output / "request_cycles" / cycle["cycle_id"] / "cycle.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["depth"] = "integral"
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "alterado"):
            load_cycle(self.output, cycle["cycle_id"])


if __name__ == "__main__":
    unittest.main()
