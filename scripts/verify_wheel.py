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
        for resource in ("references/legal_domain_profiles.json", "schemas/legal_review.schema.json", "templates/vision_review.json"):
            assert (target / resource).is_file(), resource
        environment = dict(os.environ, PYTHONPATH=str(target), PYTHONIOENCODING="utf-8")
        code = "from scripts.helpers import build_pages, classify_process; p,_=build_pages(['Reclamação trabalhista. Horas extras. FGTS. CLT.']); c=classify_process(p); assert c.get('legal_domain'); print('Installed wheel imports and domain resources OK')"
        result = subprocess.run([sys.executable, "-c", code], cwd=root, env=environment, capture_output=True, text=True, encoding="utf-8")
        assert result.returncode == 0, result.stderr
        print(result.stdout.strip())


if __name__ == "__main__":
    verify(Path(sys.argv[1]).resolve())
