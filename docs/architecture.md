# Reference Architecture

## Architectural intent

The reference implementation separates regulatory intelligence into distinct layers so that facts, interpretations, decisions, controls, and evidence are not collapsed into one opaque record.

```text
Authoritative Sources
        |
        v
Source Registration and Integrity
        |
        v
Extraction and Normalization
        |
        v
Human Review and Approval
        |
        v
Applicability Reasoning
        |
        v
Policy and Control Mapping
        |
        v
Evidence Collection and Assessment
        |
        v
Reconstruction, Reporting, and Audit
```

## Logical components

### 1. Source registry

Stores authoritative source identity, issuing authority, jurisdiction, temporal status, official URL, retrieval date, and integrity metadata.

### 2. Obligation normalization service

Converts source language into atomic records with:

- subject;
- action;
- object;
- condition;
- exception;
- deadline;
- obligation type;
- binding status;
- pinpoint citation;
- review status.

### 3. Applicability engine

Evaluates an obligation against structured facts describing an enterprise, product, system, data flow, deployment, role, and jurisdiction. Rules or models may assist, but the output must retain facts, assumptions, reasoning, confidence, assessor, and approval state.

### 4. Control mapping service

Maps obligations to enterprise policies and controls without implying that a single control necessarily proves compliance.

### 5. Evidence ledger

Records immutable observations about source records, assessments, controls, and evidence. The initial implementation uses SQLite but preserves a portable event-oriented contract.

### 6. Reconstruction service

Returns the obligation, source, applicability assessments, mapped controls, and evidence required to understand a conclusion.

## Deployment evolution

The initial implementation is deliberately local and low-cost:

1. Python package and JSON files.
2. SQLite evidence ledger.
3. Optional API service.
4. PostgreSQL or managed relational database.
5. Graph projection for relationship analysis.
6. Vector index for semantic retrieval.
7. Workflow orchestration.
8. GRC integration, including a potential OnSpring adapter.

The relational ledger remains the system of record even when graph and vector projections are introduced.
