# Arbitragem, Mediação e Métodos Adequados de Solução de Disputas

Catálogo: `domain_catalogs/arbitragem_mediacao.json`.

## Enquadramento e escopo
Rege convenções de arbitragem, tutelas pré-arbitrais, cartas arbitrais, impugnação de árbitros, ação anulatória e cumprimento de sentença arbitral, homologação de laudos estrangeiros no STJ (Lei 9.307/1996 c/ Lei 13.129/2015), mediação (Lei 13.140/2015), cláusulas escalonadas (*med-arb*) e *dispute boards* (Lei 14.133/2021, arts. 151–154). Pretensões: `arb_specific_performance_kompetenz`, `arb_pre_arbitral_relief_letter`, `arb_arbitrator_disclosure_challenge`, `arb_annulment_arbitral_award`, `arb_award_enforcement_impugnation`, `arb_foreign_award_homologation_stj`, `arb_public_administration`, `arb_mediation_settlement_enforcement`, `arb_multi_tier_med_arb_clause`, `arb_dispute_boards_infrastructure`, `arb_confidentiality_court_secrecy`, `arb_early_evidence_without_urgency` e `arb_corporate_collective_extension`.

## Polo ativo (requerente arbitral, exequente ou autor de anulatória)
- **Convenção e urgência pré-arbitral:** invoque autonomia da cláusula e *Kompetenz-Kompetenz* (Lei 9.307/1996, art. 8º, parágrafo único), reservando a ação do art. 7º apenas à cláusula vazia resistida. Obtida cautelar estatal pré-arbitral (art. 22-A), requeira a instituição da arbitragem em **30 dias** da efetivação sob pena de perda automática de eficácia.
- **Execução e homologação:** execute sentença arbitral nacional como título judicial (CPC, art. 515, VII, c/c § 1º). No STJ, instrua homologação de sentença arbitral estrangeira com laudo e convenção apostilados/traduzidos e prova de citação regular (arts. 37–39; Decreto 4.311/2002).

## Polo passivo (requerido, executado ou réu em anulatória)
- **Preliminar cogente e provas sem urgência:** argua convenção de arbitragem em preliminar de contestação estatal sob pena de renúncia tácita (CPC, art. 337, X e § 6º), inclusive para afastar produção antecipada de provas sem urgência do art. 381, II–III, do CPC. Em adesão, confira destaque/assinatura específica (art. 4º, § 2º).
- **Defesa contra anulatória:** oponha **decadência peremptória de 90 dias** da notificação da sentença arbitral ou da decisão de esclarecimentos (art. 33, § 1º), preclusão por falta de arguição na primeira oportunidade na arbitragem (art. 20) e vedação absoluta de revisão do mérito (*error in judicando*) fora do rol taxativo do art. 32.

## Magistratura e gabinete (CPC, art. 489, § 1º)
- Extinguir o feito estatal sem mérito diante de convenção válida (CPC, art. 485, VII) e cumprir cartas arbitrais sem incursão no mérito arbitral (arts. 237, IV, e 260, § 3º). Em arbitragens com a Administração Pública, conferir disponibilidade patrimonial, julgamento exclusivo de direito, publicidade (Lei 9.307/1996, art. 2º, § 3º) e pagamento via precatório/RPV.

## Marcos intertemporais
- **Lei 13.129/2015 (26/07/2015):** arbitragem na Administração Pública, arbitragem societária (art. 136-A da LSA), tutelas pré-arbitrais (arts. 22-A/22-B) e carta arbitral (art. 22-C).
- **Lei 13.140/2015 (26/12/2015):** mediação, confidencialidade estrita (art. 30) e cláusula escalonada (arts. 22–23).
- **Lei 14.133/2021 (arts. 151–154):** arbitragem, mediação e *dispute boards* em contratações públicas.

## Prova indispensável vs. prova futura
- **Indispensável no protocolo:** cláusula compromissória/compromisso, regulamento da câmara, termo de arbitragem, revelações dos árbitros, sentença arbitral integral e comprovante datado de recebimento da notificação final.
- **Prova futura/instrutória:** perícias e oitivas perante o tribunal arbitral ou *dispute board*; na anulatória estatal, prova restrita a vício formal/imparcialidade do art. 32.

## Integração com os motores determinísticos
Use `domain_catalog.py --domain arbitragem_mediacao`, selecione peças (`requerimento_instauracao_arbitragem`, `carta_arbitral`, `acao_anulatoria_sentenca_arbitral`, `homologacao_decisao_estrangeira`) em `procedural_catalog.py`, audite os prazos fatais de 30 dias (art. 22-A) e 90 dias decadenciais (art. 33, § 1º) em `deadline_calculator.py` e `limitation_checker.py`, confira cálculos em `civil_monetary_engine.py` e valide citações em `response_research.py`.
