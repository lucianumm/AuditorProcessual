"""Suíte de testes para busca semântico-lexical BM25/sinônimos, case_search v2.1, docx_exporter e mcp_server."""
from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CORE = Path(__file__).resolve().parents[1]
REPO_ROOT = CORE.parents[1]
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from scripts.case_memory import update_memory  # noqa: E402
from scripts.case_search import extract_entities, fold_accents, search_client_records, search_memory  # noqa: E402
from scripts.claim_search import clear_cache, fold, search, stem_pt, terms  # noqa: E402
from scripts.client_intake import receive_accounts  # noqa: E402
from scripts.document_formats import extract_office, inspect_format  # noqa: E402
from scripts.docx_exporter import SAFETY_NOTICE, export_markdown_to_docx  # noqa: E402
from scripts.ingest_document import run_ingest  # noqa: E402
from scripts.mcp_server import MCPServer, handle_request, main as mcp_main, serve_stdio  # noqa: E402

NS_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class ClaimSearchUpgradesTests(unittest.TestCase):
    def test_backwards_compatibility_with_v23_queries(self) -> None:
        self.assertEqual(fold("Previdenciário"), "previdenciario")
        self.assertNotIn("de", terms("alta do INSS e recusa de retorno"))
        with self.assertRaises(ValueError):
            search("de a o")

        cases = {
            "INSS deu alta e a empresa não deixou voltar ao trabalho": "social_security_limbo",
            "banco cobrou juros acima da média e capitalização": "banc_interest_fees",
            "atraso na entrega do apartamento na planta": "imob_delay_delivery",
            "busca domiciliar sem mandado": "pen_search_recognition",
        }
        for query, expected_id in cases.items():
            with self.subTest(query=query):
                res = search(query)
                self.assertEqual(res["legal_status"], "candidate_claims_only")
                self.assertEqual(res["results"][0]["id"], expected_id)

    def test_colloquial_queries_across_multiple_branches(self) -> None:
        colloquial_expectations = (
            ("sujaram meu nome no serasa sem dever nada", {"cons_credit_bureau", "cons_undue_charge"}),
            ("cai num golpe do pix central falsa", {"banc_fraud"}),
            ("descontaram rmc cartao consignado na minha aposentadoria", {"banc_consigned"}),
            ("plano de saude negou home care e terapia aba tea", {"cons_health_coverage_roll", "cons_health_plan"}),
            ("construtora atrasou entrega das chaves na planta", {"imob_delay_delivery"}),
            ("quero fazer distrato e desistir do apartamento", {"imob_distrato"}),
            ("pai nao paga pensao atrasada pedir prisao civil", {"fam_alimony_enforcement", "fam_alimony"}),
            ("fui contratado como pj mei mas tinha subordinacao", {"employment"}),
            ("levei justa causa injusta por abandono de emprego", {"just_cause"}),
            ("execucao fiscal de cda prescrita redirecionamento socio", {"trib_enforcement_defense", "trib_partner_liability", "trib_limitation"}),
            ("bpc loas negado para autismo baixa renda", {"prev_bpc"}),
            ("trava bancaria na recuperacao judicial", {"emp_recovery", "emp_recovery_creditor"}),
            ("seguradora negou sinistro da apolice", {"civ_insurance"}),
            ("marca copiada no inpi colidencia", {"emp_trademark", "emp_unfair_competition"}),
            ("print de whatsapp sem cadeia de custodia", {"pen_evidence_nullity", "pen_digital_evidence_whatsapp_chain", "not_notarial_deed_digital_evidence"}),
        )
        for query, allowed_top_ids in colloquial_expectations:
            with self.subTest(query=query):
                res = search(query, limit=3)
                top_ids = {r["id"] for r in res["results"][:2]}
                self.assertTrue(top_ids & allowed_top_ids, f"{query!r} retornou {top_ids}")
                self.assertTrue(res["domains_represented"])

    def test_morphological_stemming_unifies_portuguese_inflections(self) -> None:
        self.assertEqual(stem_pt("negativacoes"), stem_pt("negativacao"))
        self.assertEqual(stem_pt("indenizacoes"), stem_pt("indenizacao"))
        self.assertEqual(stem_pt("bancario"), stem_pt("banco"))
        self.assertEqual(stem_pt("inss"), "inss")
        self.assertEqual(stem_pt("loas"), "loas")

    def test_polo_hint_and_domains_represented_and_cache_clear(self) -> None:
        clear_cache()
        res = search("horas extras e banco de horas", polo="reclamada", limit=5)
        self.assertEqual(res["polo"], "reclamada")
        self.assertIn("trabalhista", res["domains_represented"])
        with self.assertRaises(ValueError):
            search("horas extras", polo="invalido")

    def test_direct_query_terms_outrank_synonym_only_matches(self) -> None:
        direct = search("negativação e cadastros de crédito", limit=3)
        synonym_only = search("spc scpc boa vista", limit=3)
        self.assertEqual(direct["results"][0]["id"], "cons_credit_bureau")
        self.assertIn("cons_credit_bureau", [r["id"] for r in synonym_only["results"]])
        self.assertGreater(direct["results"][0]["score"], synonym_only["results"][0]["score"])

    def test_claim_search_cli_execution_and_error_exit(self) -> None:
        ok_proc = subprocess.run(
            [sys.executable, str(CORE / "scripts" / "claim_search.py"), "golpe do pix", "--limit", "2", "--polo", "ativo"],
            capture_output=True,
            text=True,
            check=True,
        )
        parsed = json.loads(ok_proc.stdout)
        self.assertEqual(parsed["results"][0]["id"], "banc_fraud")

        err_proc = subprocess.run(
            [sys.executable, str(CORE / "scripts" / "claim_search.py"), "de a o"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(err_proc.returncode, 1)


class CaseSearchUpgradesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.output = self.base / "caso"
        doc1 = self.base / "peca1.txt"
        doc1.write_text(
            "Processo nº 0012345-67.2024.8.26.0100. Autor CPF 123.456.789-00 contra Ré CNPJ 12.345.678/0001-99.\n"
            "Requer indenização por danos morais de R$ 15.430,50 desde 15/08/2025 conforme Art. 927 do CC e Súmula 392.",
            encoding="utf-8",
        )
        run_ingest(doc1, self.output, task="ingest")

        doc2 = self.base / "ocr_sem_acento.txt"
        doc2.write_text(
            "Sentenca julgou procedente o pedido de indenizacao no valor de R$ 8.000,00 nos termos da Lei nº 8.078/1990 e Tema 952.",
            encoding="utf-8",
        )
        run_ingest(doc2, self.output, task="ingest")

        pages_path = self.output / "pages.jsonl"
        existing_pages = [json.loads(line) for line in pages_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        p1 = dict(existing_pages[0], pdf_page=1, piece="Sentença de Mérito", text="Relatório inicial da sentença.")
        p2 = dict(existing_pages[0], pdf_page=2, piece="Sentença de Mérito", text="Dispositivo: condeno ao pagamento de R$ 22.500,00 em 20/10/2025.")
        p3 = dict(existing_pages[0], pdf_page=3, piece="Sentença de Mérito", text="Publique-se. Registre-se. Intimem-se.")
        pages_path.write_text("\n".join(json.dumps(p, ensure_ascii=False) for p in (p1, p2, p3)) + "\n", encoding="utf-8")
        update_memory(self.output)

    def test_accent_insensitive_search_tokens_and_substring(self) -> None:
        self.assertEqual(fold_accents("Indenização Cível"), "indenizacao civel")
        for mode in ("tokens", "substring"):
            accented_q = search_memory(self.output, "indenização", mode=mode)
            unaccented_q = search_memory(self.output, "indenizacao", mode=mode)
            self.assertEqual(accented_q["total"], unaccented_q["total"])
            self.assertGreaterEqual(accented_q["total"], 1)

    def test_client_records_accent_insensitive_search(self) -> None:
        receive_accounts(self.output, {
            "schema_version": "1.0",
            "entries": [{
                "id": "RELATO-01",
                "text": "Cliente relatou retenção indevida de pensão alimentícia.",
                "conversation_reference": "atendimento-01",
            }],
        })
        hits = search_client_records(self.output, "retencao pensao alimenticia")
        self.assertEqual(hits["total"], 1)

    def test_entity_extraction_and_filtering(self) -> None:
        sample = (
            "Autos 0012345-67.2024.8.26.0100, CPF 123.456.789-00, valor R$ 15.430,50 "
            "em 15/08/2025, Art. 186, Súmula 54 e Lei nº 8.078/1990."
        )
        ents = extract_entities(sample)
        self.assertIn("R$ 15.430,50", ents["money"])
        self.assertIn("15/08/2025", ents["date"])
        self.assertIn("0012345-67.2024.8.26.0100", ents["cnj"])
        self.assertIn("123.456.789-00", ents["cpf_cnpj"])
        self.assertTrue(any("Art. 186" in c for c in ents["citation"]))

        money_hits = search_memory(self.output, "", entity_type="money")
        self.assertGreaterEqual(money_hits["total"], 2)
        for page in money_hits["pages"]:
            self.assertIn("money", page["extracted_entities"])

        cnj_hits = search_memory(self.output, "", entity_type="cnj")
        self.assertEqual(cnj_hits["total"], 1)
        self.assertEqual(cnj_hits["pages"][0]["extracted_entities"]["cnj"], ["0012345-67.2024.8.26.0100"])

        with self.assertRaises(ValueError):
            search_memory(self.output, "", entity_type="desconhecido")

    def test_piece_substring_filter_and_context_window(self) -> None:
        res = search_memory(self.output, "condeno", piece="sentenca", context_window=1)
        self.assertEqual(res["total"], 1)
        hit = res["pages"][0]
        self.assertEqual(hit["pdf_page"], 2)
        adj_pages = [item["pdf_page"] for item in hit["context_window"]]
        self.assertEqual(adj_pages, [1, 3])
        self.assertIn("Relatório inicial", hit["context_window"][0]["snippet"])

    def test_case_search_date_range_and_pagination_with_entities(self) -> None:
        dated = search_memory(self.output, "", date_from="2025-10-01", date_to="2025-10-31", entity_type="date")
        self.assertEqual(dated["total"], 1)
        self.assertIn("20/10/2025", dated["pages"][0]["extracted_entities"]["date"])


class DocxExporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_forensic_docx_roundtrip_and_ooxml_structure(self) -> None:
        markdown = """# EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO

## I. SÍNTESE FÁTICA
O **autor** celebrou *contrato bancário* sob regência do `art. 51 do CDC` e ***boa-fé objetiva***.

> "Art. 422. Os contratantes são obrigados a guardar, assim na conclusão do contrato,
> como em sua execução, os princípios de probidade e boa-fé."

### II. DEMONSTRATIVO DO INDÉBITO
| Rubrica | Valor Cobrado | Situação |
|---|---|---|
| Tarifa de cadastro | R$ 1.250,00 | Indevida |
| Seguro prestamista | R$ 890,00 | Venda casada |

- Tutela de urgência liminar;
1. Condenação à restituição integral.
"""
        out_docx = self.root / "minuta_forense.docx"
        receipt = export_markdown_to_docx(markdown, out_docx, title="Ação Revisional")
        self.assertTrue(out_docx.is_file())
        self.assertEqual(receipt["tables"], 1)
        self.assertEqual(receipt["headings"], 3)
        self.assertEqual(receipt["blockquotes"], 1)
        self.assertTrue(receipt["draft_watermark"])
        self.assertEqual(inspect_format(out_docx), "docx")

        texts, warnings = extract_office(out_docx)
        extracted = texts[0]
        self.assertIn(SAFETY_NOTICE, extracted)
        self.assertIn("EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO", extracted)
        self.assertIn("O autor celebrou contrato bancário sob regência do art. 51 do CDC", extracted)
        self.assertIn("princípios de probidade e boa-fé", extracted)
        self.assertIn("Tarifa de cadastro | R$ 1.250,00 | Indevida", extracted)
        self.assertIn("Página 1 de 1", extracted)
        self.assertFalse(any("VISUAL_REVIEW_REQUIRED" in w for w in warnings))

        with zipfile.ZipFile(out_docx) as zf:
            names = set(zf.namelist())
            expected_parts = {
                "[Content_Types].xml",
                "_rels/.rels",
                "word/document.xml",
                "word/_rels/document.xml.rels",
                "word/styles.xml",
                "word/header1.xml",
                "word/footer1.xml",
                "docProps/core.xml",
            }
            self.assertTrue(expected_parts <= names)
            self.assertFalse(any(n.lower().endswith("vbaproject.bin") for n in names))
            for name in names:
                raw = zf.read(name)
                self.assertNotIn(b"<!DOCTYPE", raw.upper())
                self.assertNotIn(b"<!ENTITY", raw.upper())

            doc_xml = ET.fromstring(zf.read("word/document.xml"))
            sect = doc_xml.find(f".//{NS_W}sectPr")
            self.assertIsNotNone(sect)
            pg_sz = sect.find(f"{NS_W}pgSz")
            pg_mar = sect.find(f"{NS_W}pgMar")
            self.assertEqual(pg_sz.attrib[f"{NS_W}w"], "11906")
            self.assertEqual(pg_sz.attrib[f"{NS_W}h"], "16838")
            self.assertEqual(pg_mar.attrib[f"{NS_W}top"], "1701")
            self.assertEqual(pg_mar.attrib[f"{NS_W}left"], "1701")
            self.assertEqual(pg_mar.attrib[f"{NS_W}bottom"], "1134")
            self.assertEqual(pg_mar.attrib[f"{NS_W}right"], "1134")

            inds = [el.attrib.get(f"{NS_W}left") for el in doc_xml.findall(f".//{NS_W}ind")]
            self.assertIn("2268", inds)

    def test_docx_cli_and_invalid_extension(self) -> None:
        md_file = self.root / "entrada.md"
        md_file.write_text("# Relatório\n\nTexto válido.", encoding="utf-8")
        out_docx = self.root / "saida_cli.docx"
        proc = subprocess.run(
            [sys.executable, str(CORE / "scripts" / "docx_exporter.py"), str(md_file), "--output", str(out_docx), "--title", "Teste CLI"],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["title"], "Teste CLI")
        self.assertTrue(out_docx.is_file())

        with self.assertRaises(ValueError):
            export_markdown_to_docx("# Erro", self.root / "invalido.txt")

    def test_docx_exporter_fenced_code_hr_and_no_banner_mode(self) -> None:
        md = "Parágrafo [Portal](https://www.planalto.gov.br).\n\n---\n\n```text\nMEMÓRIA DE CÁLCULO\n```"
        out_docx = self.root / "sem_tarja.docx"
        rec = export_markdown_to_docx(md, out_docx, title="Parecer Técnico", draft_banner=False)
        self.assertFalse(rec["draft_watermark"])
        texts, _ = extract_office(out_docx)
        self.assertIn("MEMÓRIA DE CÁLCULO", texts[0])
        self.assertIn("Parecer Técnico", texts[0])


class MCPServerAndAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mcp = MCPServer()

    def test_initialize_notifications_ping_and_tools_list(self) -> None:
        init = self.mcp.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "unit", "version": "1.0"}},
        })
        self.assertEqual(init["result"]["protocolVersion"], "2025-03-26")
        self.assertEqual(init["result"]["serverInfo"]["name"], "auditor-processual")
        self.assertIsNone(self.mcp.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertEqual(self.mcp.handle_request({"jsonrpc": "2.0", "id": 2, "method": "ping"})["result"], {})

        tools_res = self.mcp.handle_request({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
        tool_names = {t["name"] for t in tools_res["result"]["tools"]}
        expected_tools = {
            "ingest_process",
            "read_case_batch",
            "search_case_records",
            "search_legal_claims",
            "get_domain_claim_brief",
            "get_labor_claim_brief",
            "list_procedural_pieces",
            "lookup_official_indices",
            "verify_official_citation",
            "export_forensic_docx",
            "calculate_procedural_deadline",
            "calculate_monetary_update",
            "calculate_social_security_time",
            "calculate_penal_dosimetry",
            "check_limitation_timeline",
            "pseudonymize_lgpd",
        }
        self.assertEqual(tool_names, expected_tools)

    def test_resources_list_and_read(self) -> None:
        res_list = self.mcp.handle_request({"jsonrpc": "2.0", "id": 10, "method": "resources/list"})
        uris = {r["uri"] for r in res_list["result"]["resources"]}
        self.assertIn("auditor://entrypoint", uris)
        self.assertIn("auditor://routing/task-router", uris)

        read_ok = self.mcp.handle_request({
            "jsonrpc": "2.0",
            "id": 11,
            "method": "resources/read",
            "params": {"uri": "auditor://routing/task-router"},
        })
        router_json = json.loads(read_ok["result"]["contents"][0]["text"])
        self.assertIn("tasks", router_json)

        read_err = self.mcp.handle_request({
            "jsonrpc": "2.0",
            "id": 12,
            "method": "resources/read",
            "params": {"uri": "auditor://inexistente"},
        })
        self.assertEqual(read_err["error"]["code"], -32602)

    def test_tools_call_search_catalogs_pieces_indices_and_citations(self) -> None:
        def call_tool(name: str, arguments: dict) -> tuple[bool, dict]:
            resp = handle_request({"jsonrpc": "2.0", "id": 99, "method": "tools/call", "params": {"name": name, "arguments": arguments}})
            return resp["result"]["isError"], json.loads(resp["result"]["content"][0]["text"])

        err, claims = call_tool("search_legal_claims", {"query": "golpe do pix central falsa", "limit": 2})
        self.assertFalse(err)
        self.assertIn(claims["results"][0]["id"], {"banc_fraud", "banc_pix_fraud_social_engineering"})

        err, dom_brief = call_tool("get_domain_claim_brief", {"claim_ids": ["banc_fraud"], "polo": "ativo"})
        self.assertFalse(err)
        self.assertEqual(dom_brief["claims"][0]["id"], "banc_fraud")

        err, lab_brief = call_tool("get_labor_claim_brief", {"claim_ids": ["social_security_limbo"], "polo": "reclamante"})
        self.assertFalse(err)
        self.assertEqual(lab_brief["claims"][0]["id"], "social_security_limbo")

        err, pieces = call_tool("list_procedural_pieces", {"domain": "civil", "phase": "conhecimento"})
        self.assertFalse(err)
        self.assertTrue(pieces["candidates"])

        err, indices = call_tool("lookup_official_indices", {"list_only": True})
        self.assertFalse(err)
        self.assertIn("4390", indices["known_series"])

        official_sample = (
            "Art. 186. Aquele que, por ação ou omissão voluntária, negligência ou imprudência, "
            "violar direito e causar dano a outrem, ainda que exclusivamente moral, comete ato ilícito.\n"
            "Art. 384. (Revogado pela Lei nº 13.467, de 2017)\n"
        )
        err, cite_ok = call_tool("verify_official_citation", {
            "provision": "Art. 186",
            "source_text": official_sample,
            "quote": "violar direito e causar dano a outrem",
        })
        self.assertFalse(err)
        self.assertTrue(cite_ok["located"])

        err, cite_rev = call_tool("verify_official_citation", {
            "provision": "Art. 384",
            "source_text": official_sample,
            "fact_dates": ["2020-05-01"],
        })
        self.assertFalse(err)
        self.assertTrue(any(m["type"] == "revoked" for m in cite_rev["markers"]))

    def test_tools_call_ingest_read_search_docx_and_lgpd_end_to_end(self) -> None:
        src = self.root / "autos.txt"
        src.write_text("João CPF 111.222.333-44 pagou R$ 4.500,00 em 10/04/2025 referente à indenização.", encoding="utf-8")
        out_dir = self.root / "caso_mcp"
        docx_out = self.root / "minuta_mcp.docx"

        def call_tool(name: str, arguments: dict) -> tuple[bool, dict]:
            resp = self.mcp.handle_request({"jsonrpc": "2.0", "id": 50, "method": "tools/call", "params": {"name": name, "arguments": arguments}})
            return resp["result"]["isError"], json.loads(resp["result"]["content"][0]["text"])

        err, ing = call_tool("ingest_process", {"source_path": str(src), "output_dir": str(out_dir)})
        self.assertFalse(err, ing)

        err, batch = call_tool("read_case_batch", {"output_dir": str(out_dir), "offset": 0, "max_chars": 4000})
        self.assertFalse(err, batch)
        self.assertTrue(batch["receipt_id"])

        err, found = call_tool("search_case_records", {"output_dir": str(out_dir), "query": "indenizacao", "entity_type": "money"})
        self.assertFalse(err, found)
        self.assertEqual(found["total"], 1)
        self.assertIn("R$ 4.500,00", found["pages"][0]["extracted_entities"]["money"])

        err, docx_rec = call_tool("export_forensic_docx", {
            "output_path": str(docx_out),
            "markdown_text": "# MINUTA\n\nParágrafo com **destaque**.",
            "title": "Minuta MCP",
        })
        self.assertFalse(err, docx_rec)
        self.assertTrue(docx_out.is_file())

        err, lgpd = call_tool("pseudonymize_lgpd", {
            "text": "João da Silva, CPF 111.222.333-44, e-mail joao@teste.com.br.",
            "custom_names": ["João da Silva"],
        })
        self.assertFalse(err, lgpd)
        self.assertNotIn("111.222.333-44", lgpd["redacted_text"])
        self.assertIn("[CPF_001]", lgpd["redacted_text"])

    def test_mcp_lazy_calculators_dispatch_live(self) -> None:
        def call_tool(name: str, arguments: dict) -> tuple[bool, dict]:
            resp = self.mcp.handle_request({"jsonrpc": "2.0", "id": 60, "method": "tools/call", "params": {"name": name, "arguments": arguments}})
            return resp["result"]["isError"], json.loads(resp["result"]["content"][0]["text"])

        err, dl = call_tool("calculate_procedural_deadline", {
            "base_date": "2026-03-10",
            "days": 15,
            "rito": "civel",
            "intimation_mode": "dje",
        })
        self.assertFalse(err, dl)
        self.assertIn("dies_ad_quem", dl)

        err, dosim = call_tool("calculate_penal_dosimetry", {
            "min_penalty": {"years": 1, "months": 0, "days": 0},
            "max_penalty": {"years": 4, "months": 0, "days": 0},
            "unfavorable_circumstances_count": 0,
        })
        self.assertFalse(err, dosim)

        err, lim = call_tool("check_limitation_timeline", {
            "profile": "cpc_art921_intercorrente",
            "start_date": "2018-01-10",
            "reference_date": "2026-05-01",
        })
        self.assertFalse(err, lim)
        self.assertTrue(lim["extinguished"])

    def test_security_path_validation_and_unknown_tool_errors(self) -> None:
        bad_path = self.mcp.handle_request({
            "jsonrpc": "2.0",
            "id": 70,
            "method": "tools/call",
            "params": {"name": "ingest_process", "arguments": {"source_path": "/etc/passwd", "output_dir": str(self.root / "x")}},
        })
        self.assertTrue(bad_path["result"]["isError"])

        unknown = self.mcp.handle_request({
            "jsonrpc": "2.0",
            "id": 71,
            "method": "tools/call",
            "params": {"name": "executar_shell", "arguments": {}},
        })
        self.assertTrue(unknown["result"]["isError"])

    def test_dual_stdio_framing_and_cli_flags(self) -> None:
        req1 = b'{"jsonrpc":"2.0","id":101,"method":"ping"}\n'
        body2 = json.dumps({
            "jsonrpc": "2.0",
            "id": 102,
            "method": "tools/call",
            "params": {"name": "list_procedural_pieces", "arguments": {"domain": "trabalhista", "phase": "conhecimento"}},
        }).encode("utf-8")
        req2 = f"Content-Length: {len(body2)}\r\n\r\n".encode("ascii") + body2

        stdin_buf = io.BytesIO(req1 + req2)
        stdout_buf = io.BytesIO()
        serve_stdio(stdin=stdin_buf, stdout=stdout_buf, server=self.mcp)
        output_text = stdout_buf.getvalue().decode("utf-8")
        self.assertIn('"id": 101', output_text)
        self.assertIn("Content-Length:", output_text)
        self.assertIn('"id": 102', output_text)

        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(mcp_main(["--list-tools"]), 0)
            self.assertEqual(mcp_main(["--self-test"]), 0)
        self.assertIn('"tools"', buf.getvalue())

    def test_mcp_batch_requests_and_malformed_json_recovery(self) -> None:
        batch = b'[{"jsonrpc":"2.0","id":201,"method":"ping"},{"jsonrpc":"2.0","method":"notifications/initialized"}]\n'
        broken = b'not-valid-json\n{"jsonrpc":"2.0","id":202,"method":"ping"}\n'
        stdin_buf = io.BytesIO(batch + broken)
        stdout_buf = io.BytesIO()
        serve_stdio(stdin=stdin_buf, stdout=stdout_buf, server=self.mcp)
        lines = [json.loads(line) for line in stdout_buf.getvalue().decode("utf-8").splitlines() if line.strip()]
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0][0]["id"], 201)
        self.assertEqual(lines[1]["error"]["code"], -32700)
        self.assertEqual(lines[2]["id"], 202)

    def test_mcp_json_and_antigravity_adapter_files(self) -> None:
        mcp_cfg = json.loads((REPO_ROOT / ".mcp.json").read_text(encoding="utf-8"))
        self.assertIn("auditor-processual", mcp_cfg["mcpServers"])
        self.assertTrue((REPO_ROOT / "adapters" / "antigravity" / "README.md").is_file())
        self.assertTrue((REPO_ROOT / "adapters" / "antigravity" / "INSTRUCTIONS.md").is_file())
        for md in (REPO_ROOT / "adapters" / "antigravity").glob("*.md"):
            lower = md.read_text(encoding="utf-8").lower()
            self.assertNotIn("chame outra ia", lower)
            self.assertNotIn("call another ai", lower)


if __name__ == "__main__":
    unittest.main()
