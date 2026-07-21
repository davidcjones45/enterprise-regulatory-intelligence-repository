# Logical Data Model

## Core entities

| Entity | Purpose |
|---|---|
| Regulatory Source | Identifies the authoritative publication and temporal/legal status |
| Obligation | Atomic normalized requirement or recommendation |
| Applicability Assessment | Reasoned decision linking an obligation to an enterprise asset |
| Control | Enterprise mechanism intended to address one or more obligations |
| Evidence | Artifact or observation supporting control operation |
| Ledger Event | Immutable record of what was observed, by whom, and when |

## Core relationships

```text
Regulatory Source 1 --- * Obligation
Obligation        1 --- * Applicability Assessment
Obligation        * --- * Control
Control           1 --- * Evidence
Any Record        1 --- * Ledger Event
```

## Important distinctions

- A source is not an obligation.
- An obligation is not an applicability decision.
- An applicability decision is not a legal opinion.
- A control design is not proof that a control operated.
- Evidence existence is not proof that the evidence is sufficient.
- A proposed rule must not be represented as effective law.
