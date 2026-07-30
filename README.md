# Enterprise Regulatory Intelligence Repository

A vendor-neutral reference implementation for converting regulatory source material into normalized, traceable, testable obligations and compliance evidence.

## Purpose

The repository demonstrates the missing operating layer between regulatory sources, governance frameworks, enterprise policies, controls, accountable owners, and evidence. It is designed as a portfolio-grade reference implementation rather than a production legal-compliance platform.

The reference implementation answers five core questions:

1. What requirements may apply to a product, system, data flow, organization, or jurisdiction?
2. Why does the repository believe they apply?
3. What authoritative source supports each conclusion?
4. Which policy, control, owner, and evidence item address each obligation?
5. Can the conclusion be reconstructed and independently reviewed?

## Current capabilities

- JSON Schema validation for sources, obligations, applicability assessments, controls, and evidence.
- A queryable federal and state regulatory source catalog with lifecycle and review metadata.
- A Python command-line validator.
- A SQLite evidence ledger with append-only event semantics.
- Valid and invalid example records.
- Automated tests.
- GitHub Actions continuous integration.
- Vendor-neutral data structures suitable for later graph, vector, API, or GRC integration.
- A local, read-only demonstration interface that shows source-to-evidence traceability.
- Authoritative-source snapshots with SHA-256 integrity values, change detection, and review queues.

## Repository structure

```text
src/erir/                 Python package and CLI
schemas/                  JSON Schemas
catalog/sources/          Source-verified public regulatory metadata
examples/valid/           Valid worked examples
examples/invalid/         Deliberately invalid examples
sql/                      SQLite schema and reconstruction query
tests/                    Automated tests
docs/                     Architecture, data model, governance, roadmap
.github/workflows/        Continuous integration
```

## Quick start

Requires Python 3.11 or later.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
erir validate examples/valid
erir validate catalog/sources
erir sources list
erir sources list --jurisdiction Colorado --status effective
erir ingest-source SRC-US-NIST-AI-RMF-1-0
erir ingestion-queue
erir validate examples/invalid
erir init-ledger erir.db
erir load-examples erir.db examples/valid
erir reconstruct erir.db OBL-FTC-001
erir screen-profile examples/valid/subject_profile.json examples/valid/applicability_rule.json
erir serve-demo
```

macOS or Linux:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
pytest
erir validate examples/valid
erir sources list --binding-effect nonbinding
```

## Source catalog

Release 0.2 includes a small representative catalog covering a federal voluntary framework
and enacted laws in Colorado and Texas. The catalog is intentionally limited: it demonstrates
the ingestion, lifecycle, review, validation, and query workflow without claiming comprehensive
coverage.

`source_verified` means identifying metadata was checked against the linked authoritative
publication. It does not mean the record received legal review or that an organization is in
scope. Applicability and normalized obligations remain separate records and review decisions.

## Demonstration interface

Run `erir serve-demo` and open `http://127.0.0.1:8765` in a browser. The local
interface presents one illustrative path from source to normalized obligation,
subject profile, fact-based applicability screen, mapped control, and evidence.

The screening result is intentionally limited to `potentially_applies` or
`undetermined`. It is not a legal conclusion, and human review remains required.
Reviewer dispositions are written to a local SQLite ledger (`demo-review.db`),
which is ignored by Git. The local demonstration is not an authenticated
production workflow.

## Source ingestion

`erir ingest-source <source-id>` retrieves the catalog record's official URL, stores an
immutable content-addressed snapshot, and queues new or changed material for extraction review.
The tool only records machine-generated candidate text when its source snapshot, pinpoint, and
generator identity are retained. It never approves a candidate or creates a legal conclusion.

For a concise, client-facing walkthrough, see [the ten-minute demonstration
script](docs/demo-script.md). It preserves the distinction between illustrative
examples and verified source material.

## Design principles

- **Authoritative-source traceability:** every normalized obligation retains links to its source and pinpoint citation.
- **Proposed-law awareness:** proposals and rulemaking may inform architecture without being mislabeled as binding law.
- **Separation of facts and judgments:** source facts, normalized obligations, applicability reasoning, and control assertions remain distinct.
- **Temporal correctness:** publication, effective, compliance, supersession, and retrieval dates are modeled independently.
- **Reconstructability:** a reviewer can reproduce why an obligation was considered applicable and what evidence supported compliance.
- **Human accountability:** automated extraction and classification may assist, but accountable humans approve material legal and compliance conclusions.
- **Vendor neutrality:** no dependency on a particular GRC, cloud, vector database, or graph platform.

## Non-goals

This repository does not:

- provide legal advice;
- guarantee regulatory coverage or compliance;
- replace counsel, regulators, risk owners, control owners, or auditors;
- redistribute paywalled standards;
- treat proposed legislation or voluntary standards as binding law.

## License

Software and repository content are licensed under the Apache License 2.0 unless a file states otherwise.

Copyright 2026 David C. Jones.
