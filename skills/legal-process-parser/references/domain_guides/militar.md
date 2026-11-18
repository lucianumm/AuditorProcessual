# Direito Militar (Penal, Processual e Administrativo Castrense)

Catálogo: `domain_catalogs/militar.json`.

## 1. Regime e competência
- **Justiça Militar da União (CF, art. 124 — STM e Auditorias):** julga crimes militares do CPM (DL 1.001/1969, art. 9º c/ **Lei 13.491/2017**, abrangendo delitos da legislação penal comum nas condições do art. 9º), inclusive civis em tempo de paz quando atentarem contra instituições militares federais.
- **Justiça Militar Estadual (CF, art. 125, §§ 4º e 5º):** julga exclusivamente militares estaduais (PM e Bombeiros — **Súmula 53 TJM/STJ veda julgar civis na esfera estadual**) e ações judiciais contra atos disciplinares militares; crimes dolosos contra a vida de civil vão ao Tribunal do Júri (ressalvada a hipótese restrita do § 4º do art. 9º do CPM para militares das Forças Armadas em operações federais, observada a jurisprudência do STF). Questões remuneratórias, reforma e licenciamento de militares federais tramitam na **Justiça Federal Comum**.

## 2. Teses da defesa penal militar ou do militar administrado
- **Defesa no processo penal militar (CPM/CPPM):** argua incompetência da Justiça Militar quando ausente vínculo funcional ou afetação à administração castrense (interpretação restritiva pós-Lei 13.491/2017), **interrogatório como último ato da instrução** por força constitucional do contraditório (**Tema 522 / Plenário STF**, superando a ordem literal do art. 302 do CPPM), excludentes de culpabilidade/estado de necessidade na deserção (CPM, art. 187 — caso fortuito ou força maior comprovada), insignificância na posse ínfima ou lesão levíssima compatível com a jurisprudência constitucional e aplicação de institutos despenalizadores quando não houver incompatibilidade com a hierarquia e disciplina.
- **Militar temporário enfermo, reforma e pensão (Lei 6.880/1980):** impeça o licenciamento *ex officio* de militar temporário incapacitado temporariamente (com ou sem nexo causal, assegurada **reintegração como adido** para tratamento médico-hospitalar e remuneração — **Tema 1088 STJ**), postule reforma com proventos integrais do grau imediato na invalidez total e permanente para qualquer trabalho (Lei 6.880/1980, arts. 106–110, c/ Lei 13.954/2019), nulidade de Conselho de Justificação/Disciplina por cerceamento de defesa e habilitação à pensão militar conforme a lei vigente na data do óbito (Súmula 340 STJ; Lei 3.765/1960).

## 3. Teses do Ministério Público Militar ou da União/Estado
- **Tutela da hierarquia e disciplina:** sustente a especialidade do CPM (afastando em regra a Lei 9.099/1995 por força do art. 90-A e o ANPP na ótica do STM/STF em crimes propriamente militares), a consumação formal da deserção após 8 dias de ausência (CPM, art. 187), a discricionariedade do licenciamento por conveniência do serviço de militar temporário apto ou cuja enfermidade sem relação de causa e efeito permita o exercício de atividades civis (**Tema 1088 STJ**), o não cabimento de *habeas corpus* para exame do mérito de punição disciplinar (CF, art. 142, § 2º, restrito aos pressupostos de legalidade, competência e forma) e a prescrição quinquenal (Decreto 20.910/1932).

## 4. Magistratura e gabinete (CPC, art. 489, § 1º; CPPM, art. 438)
- Verificar a regular composição do Conselho Especial ou Permanente de Justiça (juiz federal da JMU ou juiz de direito na JME + oficiais sorteados, salvo crimes de militares estaduais contra civis julgados singularmente pelo juiz de direito — CF, art. 125, § 5º). Nas ações de reforma, distinguir incapacidade definitiva apenas para o serviço militar de invalidez total para todo e qualquer trabalho.

## 5. Marcos intertemporais e motores
- **16/10/2017 (Lei 13.491/2017 — ampliação dos crimes militares por extensão no art. 9º, II, CPM)** · **17/12/2019 (Lei 13.954/2019 — Sistema de Proteção Social dos Militares, pensão e reforma de temporários, art. 109 da Lei 6.880/1980)**.
- Motores: `deadline_calculator.py` (`rito="penal"` para CPPM ou `business_days` c/ dobra Fazendária no cível administrativo), `penal_dosimetry.py`, `limitation_checker.py` e `domain_catalog.py`.
