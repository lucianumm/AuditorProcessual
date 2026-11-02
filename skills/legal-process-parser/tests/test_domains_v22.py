"""v0.22.0: catálogos por ramo, peças por domínio, rota normas.leg.br e marcas da compilação da Câmara (sem rede)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.citation_check import check_citation, parse_citations, segment_articles, version_markers
from scripts.contracts import validate_contract
from scripts.domain_catalog import (catalogs, claim_brief, domain_index_markdown, index_files, integrity_errors,
                                    select_claims, thesis_map_markdown)
from scripts.labor_catalog import claim_brief as labor_brief, claim_catalog as labor_claims
from scripts.legislation_lookup import article_report, detail, lookup, parse_act, resolve
from scripts.procedural_catalog import candidates, canonical
from scripts.task_context import resolve_context

REFS = CORE / "references"
CAMARA_EXCERPT = """CÂMARA DOS DEPUTADOS
Art. 384. (Revogado pela Lei nº 13.467, de 13/7/2017, publicada no DOU de 14/7/2017, em vigor 120 dias após a publicação)
Art. 442. Contrato individual de trabalho é o acordo tácito ou expresso, correspondente à relação de emprego.
§ 1º Qualquer que seja o ramo de atividade da sociedade cooperativa, não existe vínculo empregatício entre ela e seus associados. (Parágrafo único acrescido pela Lei nº 8.949, de 9/12/1994, transformado em § 1º pela Lei nº 14.647, de 4/8/2023)
§ 2º Não existe vínculo empregatício entre entidades religiosas e ministros de confissão religiosa. (Parágrafo acrescido pela Lei nº 14.647, de 4/8/2023)
Art. 899. Os recursos serão interpostos por simples petição. (“Caput” do artigo com redação dada pela Lei nº 5.442, de 24/5/1968)
"""
CIVIL_EXCERPT = "Art. 1.693. Texto anterior.\nArt. 1.694. Podem os parentes, os cônjuges ou companheiros pedir uns aos outros os alimentos.\nArt. 1.695. Outro.\n"


class CamaraMarkers(unittest.TestCase):
    def test_revocation_inclusion_and_amendment_markers(self):
        self.assertEqual([m["type"] for m in version_markers("(Revogado pela Lei nº 13.467, de 13/7/2017, publicada no DOU de 14/7/2017)")], ["revoked"])
        kinds = {m["type"]: m for m in version_markers("(Parágrafo único acrescido pela Lei nº 8.949, de 9/12/1994, transformado em § 1º pela Lei nº 14.647, de 4/8/2023)")}
        self.assertEqual(kinds["included"]["year"], "1994")
        self.assertEqual(kinds["renumbered"]["act_number"], "14647")
        amended = version_markers("(“Caput” do artigo com redação dada pela Lei nº 5.442, de 24/5/1968)")[0]
        self.assertEqual((amended["type"], amended["year"]), ("amended", "1968"))
        self.assertEqual(version_markers("(Redação dada pela Lei nº 13.467, de 13 de julho de 2017)")[0]["catalogued_effective_date"], "2017-11-11")

    def test_article_report_reads_whole_article_revocation(self):
        self.assertTrue(article_report(CAMARA_EXCERPT, "384")["whole_article_revoked_or_vetoed"])
        report = article_report(CAMARA_EXCERPT, "442")
        self.assertFalse(report["whole_article_revoked_or_vetoed"])
        self.assertIn("2", {m["unit"] for m in report["markers"]})
        self.assertFalse(article_report(CAMARA_EXCERPT, "443")["located"])

    def test_thousands_separator_is_one_article(self):
        self.assertEqual([s["number"] for s in segment_articles(CIVIL_EXCERPT)], ["1693", "1694", "1695"])
        self.assertEqual(parse_citations("CC, art. 1.694, § 1º")[0]["number"], "1694")
        self.assertEqual(check_citation(CIVIL_EXCERPT, "CC, art. 1.693", "Podem os parentes")["status"], "blocking")
        self.assertEqual(check_citation(CIVIL_EXCERPT, "CC, art. 1.694", "Podem os parentes")["status"], "located_no_marker")


class LegislationLookup(unittest.TestCase):
    def test_parse_act_formats(self):
        self.assertEqual(parse_act("LEI:14647:2023"), ("LEI", "14647", "2023"))
        self.assertEqual(parse_act("LC:150:2015")[0], "LCP")
        self.assertEqual(parse_act("CF"), ("CON", "", "1988"))
        with self.assertRaises(ValueError):
            parse_act("LEI:abc:2023")

    def test_resolve_and_detail_flag_repealed_norm(self):
        senado = {"ListaDocumento": {"documentos": {"documento": [{"id": "1", "norma": "LEI-7102-1983-06-20", "normaNome": "Lei nº 7.102 de 20/06/1983", "ementa": "x"}]}}}
        normas = {"headline": "Lei nº 7.102", "legislationDate": "1983-06-20", "datePublished": "1983-06-21", "legislationLegalForce": "NotInForce",
                  "@reverse": {"legislationRepeals": [{"@id": "https://normas.leg.br/?urn=urn:lex:br:federal:lei:2024-09-09;14967"}]},
                  "encoding": [{"version": "Current", "contentUrl": "https://normas.leg.br/api/binario/abc/texto", "additionalType": "CompilacaoMonoVigenteNaCD"}]}
        with patch("scripts.legislation_lookup._get_json", side_effect=[senado, normas]):
            resolved = resolve("LEI", "7102", "1983")
            meta = detail(resolved["urn"])
        self.assertEqual(resolved["urn"], "urn:lex:br:federal:lei:1983-06-20;7102")
        self.assertEqual(meta["legal_force"], "NotInForce")
        self.assertEqual(meta["revoked_by"], ["urn:lex:br:federal:lei:2024-09-09;14967"])
        self.assertIn("/api/public/binario/", meta["content_url"])

    def test_original_publication_is_labelled(self):
        payload = {"encoding": {"version": "Original", "contentUrl": "https://normas.leg.br/api/binario/x/texto", "additionalType": "PublicacaoOriginal"}}
        with patch("scripts.legislation_lookup._get_json", return_value=payload):
            meta = detail("urn:lex:br:federal:lei:2023-08-04;14647")
        self.assertIn("publicação original", meta["legal_value_note"])

    def test_lookup_captures_with_receipt_and_warns(self):
        senado = {"ListaDocumento": {"documentos": {"documento": {"id": "1", "norma": "DEL-5452-1943-05-01"}}}}
        normas = {"legislationLegalForce": "NotInForce", "encoding": [{"version": "Current", "contentUrl": "https://normas.leg.br/api/binario/a/texto"}]}
        receipt = {"capture_id": "c" * 64, "url": "https://normas.leg.br/api/public/binario/a/texto", "accessed_on": "2026-11-02",
                   "raw_content_hash": "a" * 64, "text_hash": "b" * 64, "method": "official_http_capture", "text": CAMARA_EXCERPT}
        with tempfile.TemporaryDirectory() as tmp, patch("scripts.legislation_lookup._get_json", side_effect=[senado, normas]), \
                patch("scripts.legislation_lookup.capture", return_value=receipt) as mocked:
            result = lookup(Path(tmp), "DL:5452:1943", ["384"])
        self.assertIn("/api/public/binario/", mocked.call_args.args[0])
        self.assertTrue(result["articles"][0]["whole_article_revoked_or_vetoed"])
        self.assertIn("warning", result)


class DomainCatalogs(unittest.TestCase):
    def test_catalogs_follow_schema_and_links_resolve(self):
        self.assertGreaterEqual(len(catalogs()), 19)
        for key, catalog in catalogs().items():
            with self.subTest(domain=key):
                self.assertEqual(validate_contract(catalog, "domain_catalog.schema.json"), [])
        self.assertEqual(validate_contract(json.loads((REFS / "domain_authorities.json").read_text(encoding="utf-8")), "domain_authorities.schema.json"), [])
        self.assertEqual(integrity_errors(), [])
        for path, text in index_files().items():
            self.assertEqual(path.read_text(encoding="utf-8"), text, path.name)

    def test_brief_resolves_authorities_with_polo_labels(self):
        brief = claim_brief(["pen_custody"], "ativo")
        claim = brief["claims"][0]
        self.assertEqual(claim["claimant_theses"]["label"], "Teses da defesa")
        self.assertNotIn("defense_theses", claim)
        ids = {a["id"] for t in claim["claimant_theses"]["theses"] for a in t["authorities"]}
        self.assertIn("cpp_art312", ids)
        with self.assertRaises(ValueError):
            select_claims(["inexistente"])
        with self.assertRaises(ValueError):
            select_claims(["pen_custody"], "familia")

    def test_revised_stj_sumula_and_pending_precedents_are_explicit(self):
        auth = {a["id"]: a for a in json.loads((REFS / "domain_authorities.json").read_text(encoding="utf-8"))["authorities"]}
        self.assertEqual(auth["stj_sumula_545"]["status"], "alterada")
        self.assertEqual(auth["stj_sumula_309"]["status"], "alterada")
        self.assertEqual(auth["stj_sumula_323"]["status"], "vigente")
        self.assertEqual(auth["tema_stf_1199"]["status"], "pendente_conferencia_oficial")
        self.assertEqual(auth["l8666_art1"]["status"], "sem_vigencia")
        self.assertEqual(auth["sv_24"]["verified"]["method"], "official_browser_observation")
        text = thesis_map_markdown(["adm_improbity"])
        self.assertIn("2021-10-26", text)
        self.assertIn("pendente de conferência", text)

    def test_domain_index_lists_only_one_domain(self):
        text = domain_index_markdown("tributario")
        self.assertIn("trib_limitation", text)
        self.assertNotIn("pen_custody", text)


class LaborDepth(unittest.TestCase):
    def test_new_labor_claims_and_markers(self):
        claims = labor_claims()
        self.assertIn("bem_guarantee", claims)
        self.assertIn("expatriate_transfer", claims)
        brief = labor_brief(["notice_period"], "ambos")
        markers = {m["id"] for m in brief["claims"][0]["temporal_markers"]}
        self.assertIn("lei_12506_aviso_proporcional", markers)
        auth = {a["id"]: a for a in json.loads((REFS / "labor_authorities.json").read_text(encoding="utf-8"))["authorities"]}
        self.assertEqual(auth["l7102_art1"]["status"], "sem_vigencia")
        self.assertEqual(auth["nr_2"]["status"], "revogado")
        self.assertEqual(auth["sumula_tst_441"]["status"], "pendente_conferencia_oficial")
        self.assertEqual(auth["sv_22"]["status"], "vigente")
        self.assertTrue(all(len(c["evidence"]) >= 2 for c in claims.values()))


class ProceduralDomains(unittest.TestCase):
    def test_penal_has_no_civil_contestation_and_has_own_appeals(self):
        found = {c["id"] for c in candidates("penal", "conhecimento")["candidates"]}
        self.assertNotIn("contestacao", found)
        self.assertIn("resposta_acusacao", found)
        self.assertIn("apelacao_criminal", {c["id"] for c in candidates("penal", "sentenca")["candidates"]})

    def test_family_is_a_domain_with_specific_pieces(self):
        self.assertEqual(canonical("Família e Sucessões"), "familia")
        found = {c["id"] for c in candidates("familia", "preprocessual")["candidates"]}
        self.assertTrue({"acao_alimentos", "acao_divorcio", "inventario_arrolamento"} <= found)
        self.assertNotIn("inicial_juizado", found)

    def test_routing_adds_guide_and_index_of_selected_domain_only(self):
        context = resolve_context("generic", "analyze", domain="Família")
        paths = [r["path"] for r in context["references"]]
        self.assertTrue(any(p.endswith("domain_guides/familia.md") for p in paths))
        self.assertTrue(any(p.endswith("domain_catalogs/familia_index.md") for p in paths))
        self.assertFalse(any(p.endswith("domain_guides/penal.md") for p in paths))
        self.assertIn("domain_catalog", context["triggers"])
        claims = resolve_context("generic", "analyze", domain_claims=["trib_limitation"])
        self.assertEqual(claims["domain_catalogs"], ["tributario"])


if __name__ == "__main__":
    unittest.main()
