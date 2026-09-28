"""Unpack each distribution and execute it without imports from the checkout."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def verify(directory):
    count = 0
    for package in sorted(directory.iterdir()):
        if package.suffix not in {".zip", ".skill"}:
            continue
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with zipfile.ZipFile(package) as archive:
                names = archive.namelist()
                assert "LICENSE" in names, package.name
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
            ]
            for command in commands:
                result = subprocess.run([sys.executable, *command], cwd=root, env=environment, capture_output=True, text=True, encoding="utf-8")
                assert result.returncode == 0, (package.name, command, result.stderr, result.stdout)
            review = root / "invalid.json"
            review.write_text("{}")
            result = subprocess.run([sys.executable, str(core / "scripts/legal_review.py"), str(output), "--review", str(review)], cwd=root, env=environment, capture_output=True, text=True, encoding="utf-8")
            assert result.returncode == 1 and "Traceback" not in result.stderr, (package.name, result.stderr)
            router_path = root / "routing/task-router.json"
            if router_path.exists():
                router = json.loads(router_path.read_text(encoding="utf-8"))
                for task in router["tasks"].values():
                    for reference in task["references"]:
                        assert (root / reference).is_file(), (package.name, reference)
            count += 1
            print(f"OK isolated: {package.name}")
    assert count == 9, f"Expected 9 archives, got {count}"
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    verify(parser.parse_args().directory.resolve())
