from pathlib import Path

from erir.validator import RepositoryValidator

ROOT = Path(__file__).resolve().parents[1]


def test_valid_examples_pass():
    validator = RepositoryValidator(ROOT / "schemas")
    findings = validator.validate_paths([ROOT / "examples" / "valid"])
    assert findings
    assert all(finding.valid for finding in findings), findings


def test_invalid_examples_fail():
    validator = RepositoryValidator(ROOT / "schemas")
    findings = validator.validate_paths([ROOT / "examples" / "invalid"])
    assert findings
    assert any(not finding.valid for finding in findings)
