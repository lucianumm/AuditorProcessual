"""Verify wheel resources and imports away from the repository."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def verify(wheel):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        target = root / "installed"
        subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", "--target", str(target), str(wheel)], check=True, capture_output=True)
        for resource in ("references/legal_domain_profiles.json", "schemas/legal_review.schema.json", "templates/vision_review.json",
                         "references/legal_specializations.json","references/procedural_catalog.json","routing/task-router.json",
                         "scripts/precision_validation.py","scripts/case_packet.py","scripts/labor_analysis.py",
                         "scripts/labor_calculations.py","schemas/labor_review.schema.json","schemas/labor_calculation.schema.json",
                         "references/labor_topics.json","templates/labor_calculation_example.json",
                         "scripts/client_intake.py","scripts/labor_workflow.py","scripts/labor_ledger.py",
                         "references/labor_claims.json","references/labor_sectors.json",
                         "references/labor_sectors/banking.md","references/labor_sectors/domestic.md",
                         "schemas/labor_workflow.schema.json","schemas/client_intake.schema.json",
                         "templates/client_intake_example.json","templates/labor_ledger_example.json",
                         "scripts/petition_workspace.py","scripts/labor_events.py","scripts/labor_research.py","scripts/time_bank.py",
                         "schemas/petition_chapter.schema.json","schemas/labor_events.schema.json","schemas/time_bank.schema.json",
                         "references/incremental_petition_rules.md","references/labor_details/pay_detail_rules.md",
                         "references/labor_details/working_time_detail_rules.md"):
            assert (target / resource).is_file(), resource
        for resource in ("scripts/response_research.py", "scripts/labor_parameters.py",
                         "scripts/numeric_criteria.py", "scripts/labor_case_state.py", "scripts/prose_review.py", "scripts/research_locator.py",
                         "schemas/response_research.schema.json", "schemas/labor_parameters.schema.json",
                         "references/response_research_rules.md", "references/local_response_workflow.md",
                         "references/labor_parameter_profiles.json", "references/labor_details/career_and_variable_pay_rules.md",
                         "references/labor_details/contract_scenarios_rules.md", "references/labor_details/procedure_and_settlement_rules.md"):
            assert (target / resource).is_file(), resource
        environment = dict(os.environ, PYTHONPATH=str(target), PYTHONIOENCODING="utf-8")
        code = "from scripts.helpers import build_pages, classify_process; from scripts.task_context import resolve_context; from scripts.precision_validation import validate_precision; p,_=build_pages(['Reclamação trabalhista. Horas extras. FGTS. CLT.']); c=classify_process(p); assert c.get('legal_domain'); r=resolve_context('generic','petition',triggers=['initial'],specialization_ids=['trabalho_emprego']); assert r['specializations'][0]['regime']=='clt'; print('Installed wheel imports, routing and v4 resources OK')"
        result = subprocess.run([sys.executable, "-c", code], cwd=root, env=environment, capture_output=True, text=True, encoding="utf-8")
        assert result.returncode == 0, result.stderr
        print(result.stdout.strip())

        workflow_code = "import json; from pathlib import Path; from scripts.client_intake import receive_accounts, account_packet; from scripts.labor_ledger import apportion_workdays; from scripts.task_context import resolve_context; import scripts.labor_ledger as ll; core=Path(ll.__file__).resolve().parents[1]; out=Path('intake'); receive_accounts(out,json.loads((core/'templates/client_intake_example.json').read_text(encoding='utf-8'))); assert account_packet(out,max_chars=73)['next_offset'] is not None; data=json.loads((core/'templates/labor_ledger_example.json').read_text(encoding='utf-8')); result=apportion_workdays(data); assert result['days'][0]['physical_minutes']=='480'; assert result['payroll'][0]['difference_recorded']=='60'; context=resolve_context('generic','petition',labor_claims=['overtime'],labor_sectors=['banking'],labor_intake=True); assert not any('labor_sectors/domestic.md' in x['path'] for x in context['references']); print('Installed intake, ledger and sector routing OK')"
        result = subprocess.run([sys.executable,"-c",workflow_code],cwd=root,env=environment,capture_output=True,text=True,encoding="utf-8")
        assert result.returncode == 0, result.stderr
        print(result.stdout.strip())
        labor_code = "import json; from pathlib import Path; import scripts.labor_calculations as lc; from scripts.task_context import resolve_context; data=json.loads((Path(lc.__file__).resolve().parents[1]/'templates/labor_calculation_example.json').read_text(encoding='utf-8')); assert lc.compute_calculations(data)['total']=='140.00'; context=resolve_context('generic','analyze',domain='trabalhista',labor_topics=['working_time']); assert not any('labor_health_rules' in x['path'] for x in context['references']); print('Installed labor calculator, schemas and selective routing OK')"
        result = subprocess.run([sys.executable,"-c",labor_code],cwd=root,env=environment,capture_output=True,text=True,encoding="utf-8")
        assert result.returncode == 0, result.stderr
        print(result.stdout.strip())

        response_code = "from pathlib import Path; from scripts.response_research import begin_response, load_session; from scripts.labor_parameters import transform; from scripts.task_context import resolve_context; state=begin_response(Path('intake'),['SMOKE'],'synthetic installed wheel fixture',response_id='WHEEL-SMOKE'); assert state['consultations']==[]; assert load_session(Path('intake'),'WHEEL-SMOKE')['status']=='awaiting_consultation'; assert str(transform('50','percent_to_factor'))=='1.5'; context=resolve_context('generic','petition',labor_claims=['profit_sharing']); assert any('response_research_rules' in x['path'] for x in context['references']); assert any('career_and_variable_pay_rules' in x['path'] for x in context['references']); print('Installed per-response session, parameters and selective claims OK')"
        result = subprocess.run([sys.executable,"-c",response_code],cwd=root,env=environment,capture_output=True,text=True,encoding="utf-8")
        assert result.returncode == 0, result.stderr
        print(result.stdout.strip())

        for resource in ("scripts/citation_check.py", "scripts/source_registry.py", "scripts/official_indices.py",
                         "references/labor_authorities.json", "references/official_source_registry.json",
                         "references/citation_verification_rules.md", "references/labor_claims_index.md",
                         "schemas/labor_claims.schema.json", "schemas/labor_authorities.schema.json"):
            assert (target / resource).is_file(), resource
        citation_code = "from scripts.citation_check import check_citation, parse_citations; from scripts.labor_catalog import claim_brief; from scripts.source_registry import access_tier; text='Art. 384 - (Revogado pela Lei nº 13.467, de 2017)\\nArt. 385 - Regra sintética de teste.'; assert [f['code'] for f in check_citation(text,'CLT, art. 384')['findings']]==['provision_revoked']; assert parse_citations('Súmula 437 do TST')[0]['number']=='437'; brief=claim_brief(['overtime']); assert brief['claims'][0]['defense_theses'][0]['authorities']; assert access_tier('https://www.tst.jus.br/sumulas')=='browser_only'; print('Installed citation checker, source registry and claim catalog v2 OK')"
        result = subprocess.run([sys.executable,"-c",citation_code],cwd=root,env=environment,capture_output=True,text=True,encoding="utf-8")
        assert result.returncode == 0, result.stderr
        print(result.stdout.strip())


if __name__ == "__main__":
    target = Path(sys.argv[1]).resolve()
    wheels = sorted(target.glob("legal_process_parser-*.whl")) if target.is_dir() else [target]
    assert len(wheels) == 1, f"Expected one legal-process-parser wheel, got {wheels}"
    verify(wheels[0])
