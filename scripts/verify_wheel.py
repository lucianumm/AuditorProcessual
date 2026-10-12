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
                         "references/labor_topics.json","templates/labor_calculation_example.json"):
            assert (target / resource).is_file(), resource
        environment = dict(os.environ, PYTHONPATH=str(target), PYTHONIOENCODING="utf-8")
        code = "from scripts.helpers import build_pages, classify_process; from scripts.task_context import resolve_context; from scripts.precision_validation import validate_precision; p,_=build_pages(['Reclamação trabalhista. Horas extras. FGTS. CLT.']); c=classify_process(p); assert c.get('legal_domain'); r=resolve_context('generic','petition',triggers=['initial'],specialization_ids=['trabalho_emprego']); assert r['specializations'][0]['regime']=='clt'; print('Installed wheel imports, routing and v4 resources OK')"
        result = subprocess.run([sys.executable, "-c", code], cwd=root, env=environment, capture_output=True, text=True, encoding="utf-8")
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
