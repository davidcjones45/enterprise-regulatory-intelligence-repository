# Ten-Minute Demonstration Script

## From regulatory source to governed operating practice

### Purpose

Use this demonstration to show how a regulatory-intelligence operating model
can turn a traceable source record into a governed decision trail. The
repository is a reference implementation. It is not legal advice, a claim of
complete coverage, or a production compliance system.

### Before the meeting

1. Start the local interface with `erir serve-demo`.
2. Open `http://127.0.0.1:8765`.
3. If useful, clear or retain the local review history according to the purpose
   of the meeting. The demonstration ledger is local to the machine.
4. State at the outset that the demonstrated scenario is illustrative. Do not
   describe its source, obligation, or applicability result as client-specific
   legal advice.

## Walkthrough

### 0:00–1:00 — Frame the business problem

“Organizations frequently have a source document, policy owners, technical
teams, and evidence repositories, but no common record that connects them. The
result is delay, duplicated interpretation, and decisions that are difficult to
reconstruct. This demonstration shows the operating record that joins those
pieces without automating legal judgment.”

### 1:00–2:00 — Start with the source

Select **Source**. Point out the source identifier, lifecycle information,
authoritative link, and review metadata. Explain that a real deployment should
begin with an official source pack and retain retrieval and verification
provenance.

### 2:00–3:00 — Show the normalized obligation

Select **Obligation**. Explain that the repository separates the source text
from a structured, reviewable statement of the operational obligation. This
makes it possible to map work, ownership, controls, and evidence without
losing the pinpoint reference to the source.

### 3:00–4:00 — Establish the facts about the service

Select **Profile**. Describe the profile as a bounded collection of known facts
about a product, system, organization, data flow, or jurisdiction. Emphasize
that a profile is not an interpretation of law; it is the factual input to a
reviewable screening process.

### 4:00–5:30 — Demonstrate bounded applicability screening

Select **Screening** and first display the **Consumer claims** scenario. Explain
that a match returns only **Potentially applies**, never “applies” or “compliant.”
Then select **Internal service** or **Non-U.S. service** to show how a missing
or non-matching fact produces **Undetermined**. The point is disciplined
triage: automation makes its factual rationale visible and leaves the legal or
compliance conclusion to accountable people.

### 5:30–7:00 — Connect the decision to an operating control

Select **Control** and then **Evidence**. Explain that an obligation does not
create value merely by being identified. The enterprise needs an accountable
control, a practical activity, and evidence that the control operated. This is
the bridge from regulatory intelligence to governed operating practice.

### 7:00–8:30 — Record accountable human review

Open the review panel. Enter a reviewer name, select an appropriate disposition,
and give a concise rationale. Submit it and show the review history. Explain
that the review is written as an append-only event in the local SQLite ledger,
so the decision and its rationale can be reconstructed rather than inferred
from a conversation or spreadsheet.

### 8:30–9:30 — Export the trace

Use **Download evidence package**. Explain that the export includes the
illustrative source-to-evidence chain and the review history. In a production
implementation, the equivalent package would be governed by client retention,
access, confidentiality, and records-management requirements.

### 9:30–10:00 — Close and transition

“The demonstration does not replace counsel or a compliance owner. It makes
their work more visible, repeatable, and auditable. The next practical step is
to choose a narrow business domain and build a verified source pack, controlled
vocabulary, ownership model, and review workflow around it.”

## Demonstration boundaries

- The supplied scenarios are illustrative and must remain labelled as such.
- `potentially_applies` and `undetermined` are screening outcomes, not legal
  conclusions.
- A verified client or market source pack should use official publications,
  recorded retrieval dates, source-specific review, and appropriate legal or
  compliance-owner approval.
- Do not load client-confidential material into a local demonstration instance
  without an agreed handling, retention, and access-control approach.
