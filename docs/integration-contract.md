# Integration Contract

Release 0.5 provides a vendor-neutral integration boundary. It supports GRC platforms, workflow tools, and custom applications without treating any external system as the system of record.

## Generic events

Events follow the CloudEvents 1.0 envelope. `data.record` contains the original ERIR record and `data.contract_version` is `1.0`. A receiver may verify the payload using `X-ERIR-Content-SHA256`; when the caller supplies a shared signing key, the sender also includes an HMAC-SHA256 value in `X-ERIR-Signature`.

The repository creates events and provides a small HTTP dispatch helper, but does not transmit anything unless an explicit endpoint is supplied by the caller.

## GRC import package

`erir export-grc` produces a JSON object with `records` and `relationships`. Relationships retain the trace from source to obligation, control, evidence, and applicability assessment. A target adapter maps these records to its own object types while preserving ERIR identifiers, provenance, and human-review status.

## OnSpring proof of concept

OnSpring mapping is deferred until a target environment and approved object model are available. The generic package is the stable proof-of-concept contract and avoids embedding vendor credentials, endpoints, or proprietary schemas in this reference repository.
