# ADR 0016: Representation-neutral authoring boundary

## Status

Accepted for ExecPlan 0006 A3/A4.

## Context

The accepted Stack and OrderedMap Specification records share exact structural
identity and references but retain domain-semantic signatures, definitions, laws,
resource rules, and predicates as hosted text. The illustrative Stack `.pspec` cannot
produce all accepted canonical IDs without hidden rules, and there is no OrderedMap
surface.

A2 compared direct canonical-record input, an explicit lossless surface adapter, a
separate authoring IR, and inferred defaults. Direct canonical JSON is the only current
two-domain executable control, but ordinary decoding collapses duplicate members and
some invalid payloads lack author-local diagnostics. A separate IR would duplicate the
structural model before a second frontend or non-identity transformation needs it.
Selecting final surface grammar without author evidence would be premature.

## Decision

Define one authoring boundary independently of surface grammar:

```text
source bytes + exact format token + opaque source label
  -> exact canonical Specification document | ordered diagnostics
```

- The exact control format token is `canonical-spec-json-v1`. Unknown tokens fail
  closed; there is no implicit default or content sniffing.
- The source label exists only to locate diagnostics and record provenance. Changing
  it cannot alter, fill, infer, override, or select canonical identity, local IDs,
  references, content, ordering, or authority.
- Success returns one schema- and link-valid canonical Specification document and no
  diagnostics. Failure returns no document and one or more ordered diagnostics. Raw
  decoding precedes record validation and rejects invalid UTF-8, malformed JSON,
  duplicate object members, and unsupported formats explicitly.
- Every canonical root/local ID and reference is authored explicitly. No spelling,
  path, declaration category, array position, or source label creates identity.
- An adapter preserves explicit source declaration order in canonical arrays so exact
  record-document equality is deterministic. Array position remains non-addressing and
  has no semantic identity.
- Hosted semantic payloads remain text unless a separately governed logic/checker owns
  their interpretation. Successful parsing does not establish semantic truth or
  Evidence.
- `canonical-spec-json-v1` is the first conformance-control adapter, not the final
  human surface. ExecPlan 0006 cannot close without a non-control human-facing adapter
  and an eligible uninvolved author completing both retained domain tasks.
- Do not introduce an independent authoring IR until a second useful frontend or a
  non-identity semantic transformation demonstrates a shared intermediate need.

## Consequences

- A3 can freeze exact format dispatch, raw-parse precedence, all-or-none outcomes,
  label metamorphism, source-local diagnostics, two-domain round trips, and ordering
  without choosing `.pspec` grammar.
- A4 can implement the canonical JSON control through that boundary while preserving
  a stable contract for a later surface adapter.
- Existing record schemas and checkers remain canonical decision-plane components;
  the authoring boundary coordinates them rather than creating another authority.
- Coarse schema diagnostics exposed by A2 become explicit red A3 cases and must improve
  before the author journey can accept them.
- Human-facing grammar and workflow remain open. If evidence cannot decide among
  materially different author experiences, that later choice escalates to the
  operator.

## Rejected alternatives

- **Infer IDs/defaults from the illustrative sketch:** violates exact identity and
  cannot reproduce the accepted Stack record.
- **Make canonical JSON the final human surface now:** human ergonomics are unobserved
  and ADR 0003 retained JSON only as temporary interchange.
- **Create a separate authoring IR now:** adds drift and migration without a second
  frontend or non-identity transformation.
- **Choose a universal hosted logic:** violates plural mathematics and conflates
  parsing with evidence-bearing semantic checking.

## Reopen triggers

Reopen when a second frontend or non-identity transformation demonstrates IR reuse;
when canonical Specification identity, reference, or ordering rules change; when a
human-author observation falsifies the boundary; or when a proposed surface requires a
different outcome/diagnostic contract.
