from __future__ import annotations

from typing import Any


def screen_profile(profile: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    """Perform a fact-based applicability screen, never a legal conclusion.

    A matching screen result is deliberately limited to ``potentially_applies``.
    An accountable reviewer must determine legal applicability and approve any
    resulting applicability assessment.
    """
    facts = profile["facts"]
    matches: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []

    for criterion in rule["criteria"]:
        fact = criterion["fact"]
        actual = facts.get(fact)
        operator = criterion["operator"]
        expected = criterion.get("value")
        if operator == "exists":
            matched = fact in facts and actual is not None
        elif operator == "equals":
            matched = actual == expected
        elif operator == "contains":
            matched = isinstance(actual, list) and expected in actual
        else:  # The schema prevents this branch; retained for safe direct use.
            raise ValueError(f"Unsupported operator: {operator}")

        result = {"fact": fact, "operator": operator, "expected": expected, "actual": actual}
        (matches if matched else gaps).append(result)

    screened_in = not gaps
    return {
        "profile_id": profile["id"],
        "rule_id": rule["id"],
        "obligation_id": rule["obligation_id"],
        "screening_decision": "potentially_applies" if screened_in else "undetermined",
        "human_review_required": True,
        "legal_conclusion": False,
        "rationale": rule["rationale"],
        "matched_criteria": matches,
        "unmatched_or_missing_criteria": gaps,
    }
