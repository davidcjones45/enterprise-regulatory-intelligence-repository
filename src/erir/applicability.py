from __future__ import annotations

from typing import Any, Literal


TruthValue = Literal[True, False, None]


class ApplicabilityRuleError(ValueError):
    """Raised when a directly supplied applicability expression is malformed.

    Repository records should normally be rejected by the JSON Schema before an
    evaluation is attempted.  This exception protects callers that construct a
    rule in memory and prevents any implicit type coercion.
    """


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _same_type(left: Any, right: Any) -> bool:
    return type(left) is type(right)


def _criterion_result(
    facts: dict[str, Any], criterion: dict[str, Any], leaves: list[dict[str, Any]]
) -> TruthValue:
    allowed = {
        "equals",
        "not_equals",
        "contains",
        "exists",
        "greater_than",
        "greater_than_or_equal",
        "less_than",
        "less_than_or_equal",
        "in",
        "not_in",
    }
    fact = criterion.get("fact")
    operator = criterion.get("operator")
    if not isinstance(fact, str) or not fact:
        raise ApplicabilityRuleError("A criterion requires a non-empty string fact.")
    if operator not in allowed:
        raise ApplicabilityRuleError(f"Unsupported operator: {operator!r}")
    if operator == "exists" and "value" in criterion:
        raise ApplicabilityRuleError("The exists operator does not accept a value.")
    if operator != "exists" and "value" not in criterion:
        raise ApplicabilityRuleError(f"The {operator} operator requires a value.")

    present = fact in facts
    actual = facts.get(fact)
    expected = criterion.get("value")
    result: dict[str, Any] = {
        "fact": fact,
        "operator": operator,
        "expected": expected,
        "actual": actual,
        "fact_present": present,
    }

    if not present:
        result["evaluation"] = "missing"
        leaves.append(result)
        return None

    if operator == "exists":
        matched = actual is not None
    elif actual is None:
        # A known null is not silently treated as a false predicate.  It is an
        # unresolved input for every comparison except an explicit null equality.
        if operator == "equals" and expected is None:
            matched = True
        elif operator == "not_equals" and expected is None:
            matched = False
        else:
            result["evaluation"] = "missing"
            leaves.append(result)
            return None
    elif operator in {"equals", "not_equals"}:
        if not _same_type(actual, expected):
            raise ApplicabilityRuleError(
                f"{operator} requires matching types for fact {fact!r}; "
                f"received {type(actual).__name__} and {type(expected).__name__}."
            )
        matched = actual == expected
        if operator == "not_equals":
            matched = not matched
    elif operator == "contains":
        if isinstance(actual, str):
            if not isinstance(expected, str):
                raise ApplicabilityRuleError(f"contains requires a string value for string fact {fact!r}.")
            matched = expected in actual
        elif isinstance(actual, list):
            matched = any(_same_type(item, expected) and item == expected for item in actual)
        else:
            raise ApplicabilityRuleError(
                f"contains requires a string or array fact; {fact!r} is {type(actual).__name__}."
            )
    elif operator in {"greater_than", "greater_than_or_equal", "less_than", "less_than_or_equal"}:
        if not _is_number(actual) or not _is_number(expected):
            raise ApplicabilityRuleError(f"{operator} requires numeric values for fact {fact!r}.")
        matched = {
            "greater_than": actual > expected,
            "greater_than_or_equal": actual >= expected,
            "less_than": actual < expected,
            "less_than_or_equal": actual <= expected,
        }[operator]
    else:  # in / not_in
        if not isinstance(expected, list):
            raise ApplicabilityRuleError(f"{operator} requires an array value for fact {fact!r}.")
        if any(not _same_type(actual, item) for item in expected):
            raise ApplicabilityRuleError(
                f"{operator} requires array values matching the type of fact {fact!r}."
            )
        matched = any(actual == item for item in expected)
        if operator == "not_in":
            matched = not matched

    result["evaluation"] = "matched" if matched else "not_matched"
    leaves.append(result)
    return matched


def _evaluate_expression(
    facts: dict[str, Any], expression: dict[str, Any], leaves: list[dict[str, Any]]
) -> TruthValue:
    if not isinstance(expression, dict):
        raise ApplicabilityRuleError("An applicability expression must be an object.")
    keys = set(expression)
    if "all" in expression:
        if keys != {"all"} or not isinstance(expression["all"], list) or not expression["all"]:
            raise ApplicabilityRuleError("all requires one non-empty array of expressions.")
        results = [_evaluate_expression(facts, item, leaves) for item in expression["all"]]
        if any(result is False for result in results):
            return False
        return None if any(result is None for result in results) else True
    if "any" in expression:
        if keys != {"any"} or not isinstance(expression["any"], list) or not expression["any"]:
            raise ApplicabilityRuleError("any requires one non-empty array of expressions.")
        results = [_evaluate_expression(facts, item, leaves) for item in expression["any"]]
        if any(result is True for result in results):
            return True
        return None if any(result is None for result in results) else False
    if "not" in expression:
        if keys != {"not"} or not isinstance(expression["not"], dict):
            raise ApplicabilityRuleError("not requires one nested expression.")
        nested = _evaluate_expression(facts, expression["not"], leaves)
        return None if nested is None else not nested
    return _criterion_result(facts, expression, leaves)


def screen_profile(profile: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    """Perform a fact-based applicability screen, never a legal conclusion.

    Rules using the legacy ``criteria`` array retain its all-conditions behavior.
    Rule v2 may use one declarative ``expression`` tree (``all``, ``any``, or
    ``not``).  Unknown or missing facts yield ``undetermined`` rather than a
    false or legal conclusion.
    """
    facts = profile["facts"]
    if not isinstance(facts, dict):
        raise ApplicabilityRuleError("A subject profile requires an object of facts.")
    if "expression" in rule:
        expression = rule["expression"]
    elif "criteria" in rule:
        criteria = rule["criteria"]
        if not isinstance(criteria, list) or not criteria:
            raise ApplicabilityRuleError("Legacy criteria requires a non-empty array.")
        expression = {"all": criteria}
    else:
        raise ApplicabilityRuleError("A rule requires criteria or an expression.")

    leaves: list[dict[str, Any]] = []
    outcome = _evaluate_expression(facts, expression, leaves)
    matches = [leaf for leaf in leaves if leaf["evaluation"] == "matched"]
    gaps = [leaf for leaf in leaves if leaf["evaluation"] != "matched"]
    missing = [leaf for leaf in leaves if leaf["evaluation"] == "missing"]
    return {
        "profile_id": profile["id"],
        "rule_id": rule["id"],
        "obligation_id": rule["obligation_id"],
        "screening_decision": "potentially_applies" if outcome is True else "undetermined",
        "human_review_required": True,
        "legal_conclusion": False,
        "rationale": rule["rationale"],
        "matched_criteria": matches,
        "unmatched_or_missing_criteria": gaps,
        "missing_facts": missing,
        "evaluation_trace": leaves,
    }
