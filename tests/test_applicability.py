from pathlib import Path

from erir.applicability import screen_profile
from erir.models import load_json
from erir.validator import RepositoryValidator

PROFILE = {
    "record_type": "subject_profile",
    "id": "SYS-NORTHSTAR-001",
    "title": "Illustrative Northstar Care reporting service",
    "facts": {"jurisdiction": "US-CO", "uses_ai": True, "deployment_roles": ["deployer"]},
    "profile_owner": "Product owner",
    "updated_at": "2026-07-29T12:00:00Z",
}

RULE = {
    "record_type": "applicability_rule",
    "id": "RULE-CO-AI-001",
    "obligation_id": "OBL-CO-AI-001",
    "criteria": [
        {"fact": "jurisdiction", "operator": "equals", "value": "US-CO"},
        {"fact": "uses_ai", "operator": "equals", "value": True},
        {"fact": "deployment_roles", "operator": "contains", "value": "deployer"},
    ],
    "rationale": "Illustrative screening rule only; a qualified reviewer must determine applicability.",
    "review_status": "analyst_reviewed",
}


def test_matching_profile_is_only_potentially_applicable():
    result = screen_profile(PROFILE, RULE)
    assert result["screening_decision"] == "potentially_applies"
    assert result["human_review_required"] is True
    assert result["legal_conclusion"] is False
    assert len(result["matched_criteria"]) == 3


def test_missing_fact_remains_undetermined():
    profile = {**PROFILE, "facts": {"jurisdiction": "US-CO", "uses_ai": True}}
    result = screen_profile(profile, RULE)
    assert result["screening_decision"] == "undetermined"
    assert result["unmatched_or_missing_criteria"][0]["fact"] == "deployment_roles"


def test_valid_demonstration_records_screen_without_a_legal_conclusion():
    root = Path(__file__).resolve().parents[1]
    validator = RepositoryValidator(root / "schemas")
    profile_path = root / "examples" / "valid" / "subject_profile.json"
    rule_path = root / "examples" / "valid" / "applicability_rule.json"
    assert validator.validate_file(profile_path).valid
    assert validator.validate_file(rule_path).valid
    result = screen_profile(load_json(profile_path), load_json(rule_path))
    assert result["screening_decision"] == "potentially_applies"
    assert result["legal_conclusion"] is False
