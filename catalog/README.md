# Regulatory Source Catalog

This directory contains source-level metadata for authoritative AI legislation, laws,
regulations, policies, and frameworks. Records are intended to support discovery and
traceability; they do not substitute for the source text or legal analysis.

## Review levels

- `unreviewed`: metadata has not been checked against the cited source.
- `source_verified`: identifying metadata and lifecycle dates were checked against an
  authoritative publication.
- `substantive_reviewed`: a qualified reviewer also assessed the record's substantive
  characterization.

The included records are `source_verified`. Their applicability and legal interpretation have
not been substantively reviewed.

## Query examples

```powershell
erir validate catalog/sources
erir sources list
erir sources list --jurisdiction Colorado --status effective
erir sources list --binding-effect nonbinding --format json
```
