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


if __name__ == "__main__":
    target = Path(sys.argv[1]).resolve()
    wheels = sorted(target.glob("legal_process_parser-*.whl")) if target.is_dir() else [target]
    assert len(wheels) == 1, f"Expected one legal-process-parser wheel, got {wheels}"
    verify(wheels[0])
