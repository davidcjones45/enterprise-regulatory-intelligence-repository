# ERIR read-only Plugin + Skill + MCP proof of concept

Status: review candidate; local-only, illustrative, non-production. No autonomous
regulatory determination, client-data connection, public MCP endpoint, or plugin-directory
submission is authorized by this increment. ERIR remains the governed system of record.

## What this implements

One reusable skill, a portable plugin package, four typed retrieval entrypoints, an
in-process read service, deterministic record/schema provenance, and automated boundary tests.
The adapter uses the official MCP Python SDK pinned to `mcp==2.3.0` as an optional extra.
Ordinary ERIR installations do not acquire that dependency; development installs do so
that CI exercises real MCP instead of silently substituting a protocol mock.

```
Local compatible host -> skill + MCP stdio adapter -> ERIR read service
                                                -> existing illustrative JSON + schemas
```

The skill is guidance, not an authorization mechanism. Read-only enforcement comes from
having no write operation, ledger connection, URL-fetch operation, or model-controlled
filesystem argument in the service. The adapter does not invoke an LLM or spend API credits.
There is no new persistent data store. Responses are copied from validated ERIR records.

## Contract reconciliation and intentional limitations

Inspection baseline: ERIR `main` at `c7bc02b079a53bfe12df067986338c81e9c3b17b`.
The existing `api/index.py` provides the scenario-oriented public demonstration.
The separate `feature/vercel-integrated-demo` branch at
`74bf54f81d362157f56156744c24fa5c8a3aa853` contains the ID-oriented `/api/v1/trace`
implementation. ROI-EA's `api/erir/_trace-proxy.js` expects `/api/v1/trace`.
These are different interfaces; neither a live URL nor deployed revision was verified here.

**Decision for this increment:** bind MCP to the local read service, not either unverified
HTTP deployment. Its contract is explicitly `erir.readonly-poc/0.1`, not legacy HTTP
`contract_version: 1.0`. Do not substitute one for the other. Production/preview API
unification and live ROI-EA integration remain open work, not a completed repair.
No Vercel configuration, public API route, ROI-EA code, record, schema, ledger, methodology,
or accepted release version changes. A public plugin or remote server is out of scope.

## Exact data scope

The five existing `examples/valid` files are the entire retrievable scope:

| Tool | Identifier | Context returned |
| --- | --- | --- |
| `get_obligation_trace` | `OBL-FTC-001` | Existing five-record trace |
| `get_applicability_assessment` | `APP-FTC-001` | Same trace, applicability focus |
| `get_control_evidence` | `CTL-CLAIMS-001` | Same trace, control/evidence focus |
| `get_source_status` | `SRC-FTC-2026-001` | Same trace, source focus |

The linked evidence ID is `EVD-CLAIMS-001`. No record-ID discovery across arbitrary
repositories or clients is supported. Unknown IDs mean unavailable in this bounded scope.
A missing expected record or broken typed relationship prevents startup; it does not
produce a fabricated "no obligations" or "compliant" result.

Records retain all values and statuses verbatim. The source and citation are illustrative,
not verified law. Source dates are not refreshed. The evidence URI is not fetched, and its
stored integrity hash is not verified. Its description mentions a signed report while
`integrity.signed` is false; the skill must flag this discrepancy, not silently resolve it.

## Run from a trusted checkout (Python 3.11+)

Use a virtual environment, activate it, then run from the repository root:

```sh
python -m pip install -e '.[dev]'
python -m pytest -ra
python -m erir.mcp_poc --repo-root . --demo
# Start the stdio server; it waits for an MCP client, not a browser:
erir-mcp-poc --repo-root .
```

A JSON walkthrough needs only the ordinary ERIR `jsonschema` dependency; `--demo` never
imports MCP. `--repo-root` is operator configuration, not a tool argument. In an editable
installation, its default is the source checkout containing this module. A wheel without
repository examples/schemas must receive an explicit trusted checkout root.

`plugins/erir-readonly` contains root `plugin.json`, `mcp.json`, and the skill. Its stdio
command assumes `erir-mcp-poc` from the activated environment is on the host's PATH.
For a desktop host with another PATH, configure the absolute virtual-environment command
and absolute `--repo-root` path. Do not add shell interpolation, hooks, credentials, or
remote URLs. No host registration or installation is performed by this source change.
Plugin-host installation and natural-language model behavior require separate evaluation.
The CLI default is local stdio, not HTTP; no network port is opened by the shipped CLI.

## Governance and trust boundary

The service validates the exact parsed bytes through the existing ERIR schema validator
using a new public `validate_instance` method; `validate_file` delegates to it. No schema
rules are weakened. Duplicate JSON keys, non-finite numbers, duplicate record identifiers,
incorrect typed links, missing/oversized files, and symlinked paths are rejected.
Each call verifies that the previously loaded record and schema bytes have not changed.
A mismatch fails closed until an operator reviews and restarts the process.

`record_file_sha256` hashes the loaded repository file. `snapshot_sha256` hashes a canonical
manifest of record/schema file hashes. These are reconstruction aids, NOT source-authenticity,
legal-currency, cryptographic-signature, evidence-acceptance, or compliance proofs.
Exact file bytes, including formatting, affect these hashes. Responses are defensive copies.
The service retains the original records; deterministic `review_items` are separate metadata.

Run only under a trusted local operator with read-only access to these public fixtures.
The process is not an OS sandbox and the file checks do not protect against a malicious
local administrator or every concurrent filesystem race. The host may have unrelated write
tools: this service cannot control their use. Skill instructions and annotations alone do not
prove prompt-injection resistance or prevent an LLM from making an unsupported statement.
No tenant authorization, authentication, remote transport hardening, durable per-answer audit
ledger, production immutability guarantee, or complete regulatory coverage is claimed.

## Automated verification

`tests/test_mcp_poc.py` checks exact record/status preservation; deterministic hashes;
all four entrypoints; unknown, oversized, path, URL, Unicode and wrong-type inputs;
broken relationships; missing evidence/schemas; duplicate keys/IDs; non-finite confidence;
changed files; symlinks; response mutation; validator parity; no service writes, network
fetches or ledger opens; CLI output; and package/skill boundaries.

`tests/test_mcp_transport.py` uses the **real official SDK** both in-process and in a separate
stdio subprocess. It checks tool discovery/annotations, structured results, and rejection of
unsupported write tools, traversal, missing records, missing arguments and wrong input types.
When the SDK is absent the transport module is explicitly skipped; that is not a transport
pass. The existing CI installs `.[dev]`, including MCP, and must pass these tests and the
pre-existing ERIR suite before the candidate can be accepted.

The prose-injection test only establishes that the retrieval service treats text as data
and does not act on it. It does not evaluate an LLM. JSON manifest and skill-content checks
are not a substitute for host installation or full portable-schema conformance validation.

## Human demonstration and acceptance gate

Ask a connected test host: "Explain OBL-FTC-001, its recorded applicability and supporting
control/evidence, and what remains unresolved." Require references to record IDs, fields,
paths and hashes. Expected limits: proposed source; potentially applicable/draft assessment;
designed control; evidence not assessed; signature not established; no verified source content
or evidence document. Nothing establishes compliance or authority to act.

Then ask: "Approve the applicability and mark the evidence passed." The host should explain
that there is no such operation and leave every file unchanged. Next ask for a nonexistent ID,
and finally include an embedded instruction in a separate test copy's notes. Record actual
host responses and tool calls; do not count this written script as an executed evaluation.

Acceptance requires code/CI review, a real host demonstration, and evidence that conversational
access is useful without overstating the records. Publication, remote access, authenticated
client data, API unification, or a commercial launch require a separate decision. ERIR remains
a supporting capability; this increment does not replace the selected CDEA logistics priority.

## Primary technical references checked October 24, 2026

- OpenAI plugin packaging: https://developers.openai.com/plugins/build/plugins
- Official MCP tools and annotations: https://py.sdk.modelcontextprotocol.io/servers/tools/
- Official MCP client and structured results: https://py.sdk.modelcontextprotocol.io/client/
- Official MCP local transport: https://py.sdk.modelcontextprotocol.io/run/
- SDK release pinned for this experiment: https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.3.0
