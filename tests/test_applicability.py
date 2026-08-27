from pathlib import Path

import pytest

from erir.applicability import ApplicabilityRuleError, screen_profile
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


def test_v2_predicates_are_strict_and_support_numeric_and_membership_conditions():
    profile = {
        **PROFILE,
        "facts": {
            "quantity": 1001,
            "role": "carrier",
            "training_complete": True,
            "regions": ["US-MS", "US-TN"],
            "mode": "highway",
        },
    }
    rule = {
        **RULE,
        "expression": {
            "all": [
                {"fact": "quantity", "operator": "greater_than_or_equal", "value": 1001},
                {"fact": "quantity", "operator": "greater_than", "value": 1000},
                {"fact": "quantity", "operator": "less_than_or_equal", "value": 1001},
                {"fact": "quantity", "operator": "less_than", "value": 1002},
                {"fact": "role", "operator": "in", "value": ["offeror", "carrier"]},
                {"fact": "mode", "operator": "not_in", "value": ["air", "rail"]},
                {"fact": "regions", "operator": "contains", "value": "US-MS"},
                {"fact": "training_complete", "operator": "not_equals", "value": False},
            ]
        },
    }
    rule.pop("criteria")
    result = screen_profile(profile, rule)
    assert result["screening_decision"] == "potentially_applies"
    assert len(result["matched_criteria"]) == 8


def test_v2_nested_boolean_and_negation_preserve_unknown_facts():
    profile = {**PROFILE, "facts": {"role": "dispenser", "product_status": "normal"}}
    rule = {
        **RULE,
        "expression": {
            "all": [
                {
                    "any": [
                        {"fact": "role", "operator": "equals", "value": "dispenser"},
                        {"fact": "role", "operator": "equals", "value": "wholesaler"},
                    ]
                },
                {"not": {"fact": "product_status", "operator": "equals", "value": "illegitimate"}},
                {"fact": "authorized_partner", "operator": "equals", "value": True},
            ]
        },
    }
    rule.pop("criteria")
    result = screen_profile(profile, rule)
    assert result["screening_decision"] == "undetermined"
    assert result["missing_facts"] == [
        {
            "fact": "authorized_partner",
            "operator": "equals",
            "expected": True,
            "actual": None,
            "fact_present": False,
            "evaluation": "missing",
        }
    ]
    assert result["legal_conclusion"] is False


def test_v2_rejects_invalid_type_operator_combinations_without_coercion():
    rule = {**RULE, "expression": {"fact": "quantity", "operator": "greater_than", "value": 10}}
    rule.pop("criteria")
    with pytest.raises(ApplicabilityRuleError, match="numeric"):
        screen_profile({**PROFILE, "facts": {"quantity": "10"}}, rule)

    rule["expression"] = {"fact": "quantity", "operator": "equals", "value": 10}
    with pytest.raises(ApplicabilityRuleError, match="matching types"):
        screen_profile({**PROFILE, "facts": {"quantity": "10"}}, rule)


def test_v2_schema_rejects_malformed_expressions(tmp_path):
    root = Path(__file__).resolve().parents[1]
    validator = RepositoryValidator(root / "schemas")
    invalid_rule = {**RULE, "expression": {"all": []}}
    invalid_rule.pop("criteria")
    path = tmp_path / "invalid-rule.json"
    path.write_text(__import__("json").dumps(invalid_rule), encoding="utf-8")
    finding = validator.validate_file(path)
    assert finding.valid is False
    assert any("not valid under any" in message or "should be non-empty" in message for message in finding.messages)


def test_hazmat_and_medication_reference_fixtures_are_generic_and_qualified():
    root = Path(__file__).resolve().parents[1]
    validator = RepositoryValidator(root / "schemas")

    hazmat_profile = load_json(root / "examples" / "valid" / "subject_profile_hazmat_synthetic.json")
    hazmat_rule = load_json(root / "examples" / "valid" / "applicability_rule_hazmat_placarding.json")
    medication_profile = load_json(root / "examples" / "valid" / "subject_profile_medication_synthetic.json")
    medication_rule = load_json(root / "examples" / "valid" / "applicability_rule_drug_distribution.json")

    for name in [
        "obligation_hazmat_placarding.json",
        "obligation_hazmat_training.json",
        "obligation_drug_distribution.json",
        "obligation_drug_controlled_registration.json",
        "subject_profile_hazmat_synthetic.json",
        "applicability_rule_hazmat_placarding.json",
        "subject_profile_medication_synthetic.json",
        "applicability_rule_drug_distribution.json",
        "applicability_rule_drug_controlled_registration.json",
    ]:
        assert validator.validate_file(root / "examples" / "valid" / name).valid, name

    hazmat_result = screen_profile(hazmat_profile, hazmat_rule)
    medication_result = screen_profile(medication_profile, medication_rule)
    assert hazmat_result["screening_decision"] == "potentially_applies"
    assert medication_result["screening_decision"] == "potentially_applies"
    assert hazmat_result["legal_conclusion"] is False
    assert medication_result["legal_conclusion"] is False


def test_hazmat_exceptions_and_missing_medication_registration_remain_qualified():
    root = Path(__file__).resolve().parents[1]
    hazmat_profile = load_json(root / "examples" / "valid" / "subject_profile_hazmat_synthetic.json")
    hazmat_rule = load_json(root / "examples" / "valid" / "applicability_rule_hazmat_placarding.json")
    controlled_rule = load_json(root / "examples" / "valid" / "applicability_rule_drug_controlled_registration.json")
    medication_profile = load_json(root / "examples" / "valid" / "subject_profile_medication_synthetic.json")

    exception_profile = {
        **hazmat_profile,
        "facts": {**hazmat_profile["facts"], "placarding_exception_applies": True},
    }
    exception_result = screen_profile(exception_profile, hazmat_rule)
    assert exception_result["screening_decision"] == "undetermined"
    assert exception_result["legal_conclusion"] is False

    unresolved_registration = screen_profile(medication_profile, controlled_rule)
    assert unresolved_registration["screening_decision"] == "undetermined"
    assert unresolved_registration["missing_facts"][0]["fact"] == "dea_registration_active"

    non_controlled_profile = {
        **medication_profile,
        "facts": {**medication_profile["facts"], "is_controlled_substance": False},
    }
    non_controlled_result = screen_profile(non_controlled_profile, controlled_rule)
    assert non_controlled_result["screening_decision"] == "potentially_applies"
    assert non_controlled_result["legal_conclusion"] is False
