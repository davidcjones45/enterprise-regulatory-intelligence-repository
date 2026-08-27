# Applicability Rule v2

Applicability Rule v2 extends the repository's generic, fact-based screening language. It does not create industry-specific schemas and does not determine legal applicability, authorization, compliance, or a violation.

## Compatibility

Existing `criteria` arrays remain supported and retain their v1 meaning: every criterion must be supported. New records may instead provide one nested `expression`. A rule provides exactly one of those forms.

## Predicates

Leaf predicates have `fact`, `operator`, and (except `exists`) `value`.

| Operator | Supported fact shape |
| --- | --- |
| `equals`, `not_equals` | matching scalar types, including explicit `null` equality |
| `contains` | string or array |
| `exists` | any non-null present fact |
| `greater_than`, `greater_than_or_equal`, `less_than`, `less_than_or_equal` | numbers only; booleans are not numbers |
| `in`, `not_in` | scalar compared with an array of matching-type values |

`all`, `any`, and `not` can compose leaf predicates or other groups recursively.

## Missing and incompatible facts

A missing fact, an explicit null where an operator needs a value, or an unsupported condition makes the relevant expression **unknown**, not false. The screening result is therefore `undetermined` unless the expression is supported as true. Values are not coerced: for example, the string `"1001"` is not the number `1001`, and `true` is not `1`.

The engine reports `missing_facts` and an `evaluation_trace` for review. A false fact can prevent a potential match; a missing fact does not silently become a negative conclusion.

## Reference fixtures

The HazMat and prescription/controlled-medication examples in `examples/valid/` use only ordinary `subject_profile`, `obligation`, `regulatory_source`, and `applicability_rule` records. They are deliberately small, synthetic, and source-scoped.

- HazMat examples identify a limited federal HMR screening context, training, registration, and HMSP review topics; they are not a classification or transport-compliance engine.
- Medication examples distinguish a supply-distribution/tracing screen from patient-specific dispensing and preserve a separate controlled-substance registration fact screen. State pharmacy law, patient-specific authorization, and delivery legality are out of scope.

Every result is a qualified review cue. Qualified legal, compliance, operational, and, where applicable, clinical review remains required.
