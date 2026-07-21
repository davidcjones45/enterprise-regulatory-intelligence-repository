from __future__ import annotations

from pathlib import Path
from typing import Iterable
import json

from jsonschema import Draft202012Validator, FormatChecker, RefResolver

from .models import ValidationFinding, load_json


SCHEMA_BY_RECORD_TYPE = {
    "regulatory_source": "regulatory-source.schema.json",
    "obligation": "obligation.schema.json",
    "applicability_assessment": "applicability-assessment.schema.json",
    "control": "control.schema.json",
    "evidence": "evidence.schema.json",
}


class RepositoryValidator:
    def __init__(self, schema_dir: Path):
        self.schema_dir = schema_dir
        self._schemas = self._load_schemas()

    def _load_schemas(self) -> dict[str, dict]:
        schemas: dict[str, dict] = {}
        for path in self.schema_dir.glob("*.schema.json"):
            with path.open("r", encoding="utf-8") as handle:
                schemas[path.name] = json.load(handle)
        return schemas

    def validate_file(self, path: Path) -> ValidationFinding:
        try:
            instance = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            return ValidationFinding(str(path), False, None, (f"Unreadable JSON: {exc}",))

        record_type = instance.get("record_type") if isinstance(instance, dict) else None
        schema_name = SCHEMA_BY_RECORD_TYPE.get(record_type)
        if not schema_name:
            return ValidationFinding(
                str(path),
                False,
                None,
                (f"Unknown or missing record_type: {record_type!r}",),
            )

        schema = self._schemas[schema_name]
        store = {
            loaded_schema.get("$id", name): loaded_schema
            for name, loaded_schema in self._schemas.items()
        }
        store.update(self._schemas)
        resolver = RefResolver.from_schema(schema, store=store)
        validator = Draft202012Validator(
            schema,
            resolver=resolver,
            format_checker=FormatChecker(),
        )
        errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
        messages = tuple(
            f"{'.'.join(str(item) for item in error.path) or '<root>'}: {error.message}"
            for error in errors
        )
        return ValidationFinding(str(path), not errors, schema_name, messages)

    def validate_paths(self, paths: Iterable[Path]) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        for path in paths:
            if path.is_dir():
                candidates = sorted(path.rglob("*.json"))
            else:
                candidates = [path]
            findings.extend(self.validate_file(candidate) for candidate in candidates)
        return findings
