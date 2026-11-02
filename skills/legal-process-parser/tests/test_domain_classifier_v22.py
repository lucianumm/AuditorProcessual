"""Classificação de área: limite de palavra, ruído de qualificação e número único CNJ."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.helpers import Page, classify_legal_domain, classify_process, cnj_check_digits, parse_cnj_numbers


def pages(*texts: str) -> list[Page]:
    return [Page(pdf_page=index + 1, text=text, document_id=f"doc{index + 1}") for index, text in enumerate(texts)]


class WordBoundaries(unittest.TestCase):
    def test_labor_claim_of_bank_employee_is_not_administrative(self):
        text = ("Reclamante foi empregada do Banco X, residente no Município de Campinas, Estado de São Paulo, "
                "estado civil casada. Pleiteia adicional noturno, adicional de insalubridade, horas extras e FGTS. "
                "Houve reunião com a gerência.")
        result = classify_legal_domain(pages(text))
        self.assertEqual(result["primary_key"], "trabalhista")
        keys = {item["key"]: item for item in result["candidates"]}
        self.assertNotIn("constitucional", keys, "'adi' não pode casar com 'adicional'")
        self.assertNotIn("penal", keys, "'reu' não pode casar com 'reunião'")
        self.assertNotIn("administrativo", keys, "endereço e estado civil não indicam Direito Administrativo")

    def test_civil_defendant_is_not_criminal_case(self):
        text = "Ação de cobrança. O réu descumpriu o contrato de compra e venda; pede-se indenização por dano material."
        self.assertEqual(classify_legal_domain(pages(text))["primary_key"], "civil")

    def test_generic_bank_word_does_not_outweigh_consumer_facts(self):
        text = "O autor, consumidor, teve cobrança indevida no cartão do banco e negativação no Serasa."
        self.assertEqual(classify_legal_domain(pages(text))["primary_key"], "consumidor")


class CnjNumber(unittest.TestCase):
    def test_check_digits_match_a_published_number(self):
        # E-ED-RR-713-03.2010.5.04.0029 (SDI-1 do TST, Lei 14.905/2024), citado em labor_authorities.json.
        self.assertEqual(cnj_check_digits("0000713", "2010", "5", "04", "0029"), "03")
        found = parse_cnj_numbers("E-ED-RR-713-03.2010.5.04.0029")[0]
        self.assertEqual(found["number"], "0000713-03.2010.5.04.0029")
        self.assertTrue(found["check_digits_valid"])
        self.assertEqual(found["court"], "Tribunal Regional do Trabalho da 4ª Região")

    def test_segment_routes_labor_and_fills_justice(self):
        digits = cnj_check_digits("0001234", "2024", "5", "15", "0001")
        number = f"0001234-{digits}.2024.5.15.0001"
        classification = classify_process(pages("Processo " + number + ". Autor pede indenização por dano moral contra empresa."))
        self.assertEqual(classification["legal_domain"], "trabalhista")
        self.assertEqual(classification["justica"], "Justiça do Trabalho")
        self.assertEqual(classification["tribunal"], "Tribunal Regional do Trabalho da 15ª Região")

    def test_invalid_check_digits_are_reported_and_not_used_to_fill_court(self):
        digits = cnj_check_digits("1000123", "2023", "8", "26", "0100")
        wrong = "00" if digits != "00" else "01"
        classification = classify_process(pages(f"Autos 1000123-{wrong}.2023.8.26.0100. Ação de cobrança contratual."))
        self.assertFalse(classification["numeros_cnj"][0]["check_digits_valid"])
        self.assertEqual(classification["justica"], "Não identificado nos autos")

    def test_state_court_codes_follow_alphabetical_federation_units(self):
        digits = cnj_check_digits("1000123", "2023", "8", "26", "0100")
        self.assertEqual(parse_cnj_numbers(f"1000123-{digits}.2023.8.26.0100")[0]["court"], "Tribunal de Justiça (SP)")
        digits = cnj_check_digits("0800001", "2022", "4", "05", "8300")
        self.assertEqual(parse_cnj_numbers(f"0800001-{digits}.2022.4.05.8300")[0]["court"], "Tribunal Regional Federal da 5ª Região")


if __name__ == "__main__":
    unittest.main()
