# Implementation Roadmap

## Release 0.1 - Repository foundation

- JSON Schemas.
- Validator CLI.
- Valid and invalid examples.
- SQLite evidence ledger.
- Reconstruction query.
- Unit tests and CI.

## Release 0.2 - Source registry

- Queryable federal and state source catalog.
- Legal status and lifecycle history.
- Binding-effect and review-level classifications.
- Representative source-verified public records.
- Command-line jurisdiction and status filters.

## Release 0.2.1 - Source ingestion automation

- Authoritative document download and integrity verification. (complete)
- Change detection against previously retrieved content. (complete)
- Extraction work queue. (complete)
- Provenance for machine-generated obligation candidates. (complete)

## Release 0.3 - Applicability rules

- Product and system profile schema.
- Bounded, explainable fact predicates.
- Screening results limited to `potentially_applies` or `undetermined`.
- Explicit human-review boundary; no automated legal conclusion.
- Regression tests for matching and incomplete facts.

## Release 0.4 - API and user interface

- Read-only local demonstration interface for the source-to-evidence trace.
- Local review queue with reviewer, status, rationale, and review history.
- Local SQLite persistence for review dispositions.
- Downloadable JSON evidence package for an illustrative scenario.
- Authenticated workflow, broader obligation trace view, evidence sufficiency
  dashboard, and production API remain future work.

## Release 0.5 - Integration adapters

- Generic webhook/event interface. (complete)
- GRC import/export contract. (complete)
- OnSpring adapter proof of concept. (deferred pending an approved target object model and environment)
- Graph and vector projections.
