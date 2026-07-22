# Shared human authoring contract options

## Decision to prepare

Choose the smallest reversible contract that lets Stack and OrderedMap authors produce
the accepted canonical Specification documents with explicit identity, exact
references, and useful diagnostics. This comparison does not choose the final surface
syntax or claim human usability.

## Acceptance criteria

An admissible route must:

1. cover every accepted field in both canonical Specification records;
2. require exact root identity, local declaration IDs, and typed/local references;
3. preserve hosted semantic payloads without pretending to check their meaning;
4. produce canonical record-document equality with deterministic declaration-array
   order while keeping array position semantically irrelevant;
5. reject missing, duplicate, dangling, and wrong-kind identity/reference inputs with
   source-local, stable diagnostics, including invalid bytes, duplicate serialized
   members, unsupported formats, and parse failures before record validation;
6. avoid a second semantic authority or undocumented desugaring defaults;
7. remain reversible until an eligible human-author observation supports a final
   workflow.

## Executable control observations

`tests/research/test_shared_human_authoring_options.py` exercises the current canonical
JSON path as a control, not as the final author experience:

- both accepted records schema- and link-check with their exact profiles;
- a missing root ID reports `SCHEMA_MISSING_FIELD` at `#/id`;
- a duplicate local declaration reports `LINK_DUPLICATE_DECLARATION_ID` at the second
  ID plus the consequent dangling operation-family edge; dangling carrier/profile-
  member references report their exact nested paths;
- a blank hosted law statement currently collapses to `SCHEMA_INVALID` at `#`, which
  is too coarse for the authoring outcome and is a concrete improvement trigger;
- ordinary `json.loads` silently keeps the last duplicate object member, while invalid
  UTF-8 and malformed JSON escape as host exceptions rather than author diagnostics;
- unknown record kind and wrong-kind local references are exact, and repeated graph
  diagnostics are deterministic;
- reordering declaration arrays changes record-document equality while leaving exact
  local addresses and link validity unchanged. An authoring boundary must therefore
  preserve or deterministically define output order without assigning semantic meaning
  to position.

## Option matrix

| Option | Exactness and diagnostics | Additional authority / reversibility | Disposition |
|---|---|---|---|
| O1 direct canonical-record input | executable for both domains; exact identity/reference checks; hosted-payload diagnostics are not yet uniformly source-local | no new model; current JSON serialization remains temporary; human ergonomics unobserved | retain as the conformance control and first adapter, not the final surface |
| O2 explicit lossless surface adapter | can require every ID/reference and preserve hosted text; needs two-domain grammar, source mapping, ambiguity, and round-trip controls | noncanonical adapter is reversible; exact syntax materially affects author workflow | retain as the only current surface candidate; do not choose grammar before controls and author evidence |
| O3 independent authoring IR plus frontends | could isolate syntax, but duplicates the current structural model before a second frontend or semantic transformation exists | creates another drift/authority boundary and migration burden | reject now; reopen when two frontends or a non-identity semantic transformation demonstrates the need |
| O4 infer IDs/defaults from the illustrative sketch | cannot reproduce accepted Stack IDs and has no OrderedMap comparison | hidden rules become accidental authority | reject under A1/A2 exactness constraints |

## Candidate route for A-R2

Freeze one representation-neutral authoring boundary before implementation:

```text
explicit source bytes + declared source format + opaque source label
  -> exact canonical Specification document | ordered source-local diagnostics
```

The source label is provenance for diagnostics only. It can never fill, infer,
override, or select canonical `(kind, id, version)`, local IDs, references, content, or
authority. A3 must prove that changing only a label leaves successful output identical
and changes only the permitted label field in diagnostics.

The boundary owns validation/elaboration outcome shape, exact document equality,
duplicate-member rejection, diagnostic ordering, source-order preservation, unsupported-
format handling, and the statement that hosted payloads remain unchecked text. It does
not own a grammar. A4 may implement the existing
canonical JSON format as the first control adapter. A future explicit surface adapter
must pass the same A3 contract and may be selected only after its grammar and author
experience receive their own evidence. No independent IR is introduced until more than
one adapter or a real semantic transformation needs it.

The JSON control cannot close this ExecPlan or satisfy its human-facing outcome. Final
convergence requires at least one non-control human-facing adapter plus an eligible,
uninvolved author completing the retained Stack and OrderedMap author tasks. This is a
separate observation from ExecPlan 0003's consumer inspection and requires operator
coordination only when that later node is ready.

This route is reversible and does not decide the final author workflow. A-R2 must
challenge whether the boundary is genuinely representation-neutral, whether the JSON
control would accidentally become permanent, and whether raw/coarse diagnostics require
a separate successor before A3. If those concerns cannot be resolved without choosing
between materially different human experiences, A-G2 stops for the operator.

## Recovery and reopen triggers

Remove this research route without changing canonical records or accepted actors.
Reopen O3 on a second independently useful frontend or non-identity transformation;
reopen surface selection after eligible author observation; reopen the ordering rule if
canonical records stop treating array position as non-addressing metadata.
