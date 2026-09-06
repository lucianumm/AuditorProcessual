"""Runtime JSON Schema validation for the authored legal review."""
from pathlib import Path
import json


def validate_contract(value, name):
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        return ["Instale jsonschema (pip install jsonschema>=4.23) para validar a revisão jurídica; ingestão não exige esta dependência."]
    path = Path(__file__).resolve().parent.parent / "schemas" / name
    schema = json.loads(path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [f"Contrato {name} /{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in validator.iter_errors(value)]
