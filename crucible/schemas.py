"""Schema loading and validation for CRUCIBLE records."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from .paths import schemas_dir

SCHEMA_KINDS = {
    "task-template": "task_template.schema.json",
    "task-instance": "task_instance.schema.json",
    "verification-manifest": "verification_manifest.schema.json",
    "claims": "claims.schema.json",
    "event": "event.schema.json",
    "system-card": "system_card.schema.json",
}


class SchemaValidationError(Exception):
    """Raised when a record fails schema validation."""

    def __init__(self, kind: str, errors: list[str]):
        self.kind = kind
        self.errors = errors
        super().__init__(f"{kind} validation failed with {len(errors)} error(s)")


def load_schema(kind: str, root: Path | None = None) -> dict:
    if kind not in SCHEMA_KINDS:
        raise KeyError(f"Unknown schema kind '{kind}'. Known: {sorted(SCHEMA_KINDS)}")
    path = schemas_dir(root) / SCHEMA_KINDS[kind]
    return json.loads(path.read_text(encoding="utf-8"))


def load_record(path: Path) -> Any:
    """Load a YAML or JSON record from disk."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def validate_record(kind: str, record: Any, root: Path | None = None) -> list[str]:
    """Validate *record* against the named schema. Returns a list of error strings."""
    schema = load_schema(kind, root)
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for err in sorted(validator.iter_errors(record), key=lambda e: list(e.absolute_path)):
        location = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{location}: {err.message}")
    return errors


def validate_file(kind: str, path: Path, root: Path | None = None) -> list[str]:
    return validate_record(kind, load_record(path), root)


def assert_valid(kind: str, record: Any, root: Path | None = None) -> None:
    errors = validate_record(kind, record, root)
    if errors:
        raise SchemaValidationError(kind, errors)
