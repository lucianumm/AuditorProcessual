"""Unpack each distribution and execute it without imports from the checkout."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
import hashlib
from datetime import datetime, timezone


def verify(directory):
    count = 0
    results = []
    for package in sorted(directory.iterdir()):
        if package.suffix not in {".zip", ".skill"}:
            continue
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with zipfile.ZipFile(package) as archive:
                names = archive.namelist()
                assert "LICENSE" in names, package.name
                assert len(set(names)) == len(names), "duplicate package entry"
                assert all(not n.startswith("/") and ".." not in Path(n).parts for n in names), "unsafe archive entry"
                assert not any(".ci-artifacts/" in n or "/outputs/" in n or n.endswith(".pyc") for n in names)
                archive.extractall(root)
            entrypoints = list(root.rglob("scripts/ingest_document.py"))
            assert len(entrypoints) == 1, (package.name, entrypoints)
            core = entrypoints[0].parent.parent
            environment = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PYTHONHOME"}}
            environment["PYTHONIOENCODING"] = "utf-8"
            source = root / "fixture.txt"
            source.write_text("O pagamento foi realizado.", encoding="utf-8")
            output = root / "case"
            commands = [
                [str(entrypoints[0]), str(source), "--output", str(output), "--task", "analyze"],
                [str(core / "scripts/validate_extraction.py"), str(output)],
                [str(core / "scripts/validate_links.py"), str(output)],
                [str(core / "scripts/case_memory.py"), str(output), "--limit", "1"],
                [str(core / "scripts/case_packet.py"), str(output), "--max-chars", "1000"],
                [str(core / "scripts/review_skeleton.py"), str(output)],
                [str(core / "scripts/procedural_catalog.py"), "--domain", "trabalhista", "--phase", "sentenca"],
                [str(core / "scripts/task_context.py"), "--platform", "generic", "--task", "analyze", "--trigger", "local_contract"],
                [str(core / "scripts/task_context.py"), "--platform", "generic", "--task", "analyze", "--domain", "trabalhista", "--labor-topic", "working_time"],
                [str(core / "scripts/labor_calculations.py"), str(core / "templates/labor_calculation_example.json"), "--output", str(root / "labor_case")],
                [str(core / "scripts/client_intake.py"), str(core / "templates/client_intake_example.json"), "--output", str(root / "intake_case")],
                [str(core / "scripts/client_intake.py"), "--output", str(root / "intake_case"), "--read", "--max-chars", "73"],
                [str(core / "scripts/case_memory.py"), str(root / "intake_case"), "--accounts", "--query", "sintético"],
                [str(core / "scripts/review_skeleton.py"), str(root / "intake_case"), "--task", "petition", "--domain", "trabalhista", "--labor-workflow"],
                [str(core / "scripts/task_context.py"), "--platform", "generic", "--task", "petition", "--labor-intake", "--labor-claim", "overtime", "--labor-sector", "banking"],
                [str(core / "scripts/labor_ledger.py"), str(core / "templates/labor_ledger_example.json")],
                [str(core / "scripts/petition_workspace.py"), "--help"],
                [str(core / "scripts/response_research.py"), str(root / "intake_case"), "begin", "--id", "PACKAGE-SMOKE", "--issue", "SMOKE", "--request-reference", "synthetic package smoke, no legal consultation"],
                [str(core / "scripts/response_research.py"), "--help"],
                [str(core / "scripts/labor_parameters.py"), "--profile", "overtime"],
                [str(core / "scripts/labor_parameters.py"), "--transformation", "percent_to_factor", "--value", "50"],
                [str(core / "scripts/labor_research.py"), "--claim", "fgts", "--trt", "15"],
                [str(core / "scripts/time_bank.py"), str(core / "templates/time_bank_example.json")],
                [str(core / "scripts/labor_events.py"), str(core / "templates/labor_events_example.json"), "--output", str(root / "intake_case")],
            ]
            for command in commands:
                result = subprocess.run([sys.executable, *command], cwd=root, env=environment, capture_output=True, text=True, encoding="utf-8")
                assert result.returncode == 0, (package.name, command, result.stderr, result.stdout)
            labor_result = json.loads((root / "labor_case/calculo_trabalhista.json").read_text(encoding="utf-8"))
            assert labor_result["total"] == "140.00", (package.name,"labor arithmetic")
            account_memory = json.loads((root / "intake_case/case_memory.json").read_text(encoding="utf-8"))
            assert account_memory["documents"] == [] and len(account_memory["client_records"]) == 1
            assert (root / "intake_case/relato_cliente.md").is_file()
            research_session = json.loads((root / "intake_case/response_research/PACKAGE-SMOKE/session.json").read_text(encoding="utf-8"))
            assert research_session["status"] == "awaiting_consultation" and research_session["consultations"] == []
            for resource in ("references/local_response_workflow.md", "references/labor_parameter_profiles.json", "schemas/response_research.schema.json", "schemas/labor_parameters.schema.json",
                             "scripts/numeric_criteria.py", "scripts/labor_case_state.py", "scripts/prose_review.py", "scripts/research_locator.py"):
                assert (core / resource).is_file(), (package.name, resource)
            review = root / "invalid.json"
            review.write_text("{}")
            result = subprocess.run([sys.executable, str(core / "scripts/legal_review.py"), str(output), "--review", str(review)], cwd=root, env=environment, capture_output=True, text=True, encoding="utf-8")
            assert result.returncode == 1 and "Traceback" not in result.stderr, (package.name, result.stderr)
            for router_path in root.rglob("routing/task-router.json"):
                router = json.loads(router_path.read_text(encoding="utf-8"))
                routing_root = router_path.parent.parent
                for task in router["tasks"].values():
                    for reference in task["references"]:
                        assert (routing_root / reference).is_file(), (package.name, reference)
                for item in router.get("conditional_references", []):
                    for reference in item["references"]:
                        assert (routing_root / reference).is_file(), (package.name, reference)
            environment["PYTHONPATH"] = str(core)
            imports = "from scripts.precision_validation import validate_precision; from scripts.document_formats import extract_office; from scripts.research_memory import research_revision; from scripts.document_relations import record_relation; from scripts.legal_index import build_legal_index; print('v4 modules import in isolation')"
            imports += "; from scripts.numeric_criteria import quantities; assert [q['unit'] for q in quantities('50 dias; cinquenta por cento')] == ['days', 'percent']; from scripts.labor_case_state import case_state; assert case_state({})['timeline'] == []"
            result = subprocess.run([sys.executable,"-c",imports],cwd=root,env=environment,capture_output=True,text=True,encoding="utf-8")
            assert result.returncode == 0, (package.name,result.stderr)
            count += 1
            results.append({"package":package.name,"sha256":hashlib.sha256(package.read_bytes()).hexdigest(),
                            "package_structure":"passed","isolated_local_execution":"passed",
                            "live_platform_upload":"not_run","real_process_expert_review":"not_run"})
            print(f"OK isolated: {package.name}")
    assert count == 9, f"Expected 9 archives, got {count}"
    report = {"schema_version":"1.0","checked_at":datetime.now(timezone.utc).isoformat(),"packages":results,
              "scope":"Local synthetic execution only; no provider calls, login, live upload or legal merit certification."}
    (directory / "platform_validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    verify(parser.parse_args().directory.resolve())
