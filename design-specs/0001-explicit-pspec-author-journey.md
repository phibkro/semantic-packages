# Design spec 0001: explicit PSpec author journey

## Contract status

Active draft for one feature and one future pull request. This contract freezes when
that pull request opens. Any contract change before or after that point is recorded in
the revision history with the observation that required it; implementation never
silently changes the target.

## Felt user journey

A theory author can express either accepted tracer domain in one readable `.pspec`
file, invoke one command with every external dependency named explicitly, and receive
the exact canonical Specification document or deterministic, source-local diagnostics.

The repository provides complete Stack and OrderedMap examples. From a clean checkout,
the author can run:

```text
nix develop --command python3 -m semantic_packages author \
  specs/stack.pspec \
  --dependency registry/stack/theory/dependencies/stack-profile.json \
  --output /tmp/stack-spec.json

nix develop --command python3 -m semantic_packages author \
  specs/ordered-map.pspec \
  --dependency registry/ordered-map/theory/dependencies/ordered-map-profile.json \
  --output /tmp/ordered-map-spec.json
```

Each successful command exits zero, names the authored exact record and destination,
and writes a canonical JSON document equal as a document to the corresponding accepted
record. An author can change an explicit law, identity, or reference and immediately
see either the changed valid output or an actionable diagnostic at the relevant source
path and record pointer.

## Goal

Make the semantic Specification—not a realization or handwritten canonical JSON—the
primary artifact a human edits for both Stack and OrderedMap. Demonstrate the complete
author feedback loop without granting the surface authority to infer identity, acquire
dependencies, interpret hosted logic, or establish Evidence.

## Values and priorities

1. **Semantic exactness over terseness.** Every canonical identity, version, local ID,
   reference, declaration, and hosted payload remains authored and inspectable.
2. **Visible authority over convenience magic.** Source, dependency inputs, and output
   destination are explicit command arguments; nearby files and naming conventions do
   not affect the result.
3. **Useful human feedback over parser leakage.** Failures are stable diagnostics with
   source path, canonical pointer, code, and actionable detail rather than tracebacks.
4. **Plural semantics over premature checking.** Law, equivalence, resource, effect,
   and performance text round-trips unchanged unless a separately governed checker is
   selected.
5. **Reversibility over format permanence.** PSpec v1 is the first usable adapter, not
   a claim that one syntax or author workflow is universal or final.

## Observable contract

### PSpec v1 source

- A `.pspec` file is UTF-8 TOML whose top-level keys and nested tables map losslessly
  to one canonical Specification record.
- `kind = "specification"`, root `id`, and `version` are mandatory and explicit.
- Declaration arrays use TOML array-of-table syntax in authored order. Every local
  declaration ID and every local or typed record reference is explicit.
- Canonical JSON field names are used verbatim. Comments and TOML formatting have no
  canonical meaning. No additional PSpec-only semantic fields enter the output.
- Hosted semantic strings may use TOML multiline strings and are preserved as values;
  successful authoring does not claim they are true, typed, proved, or executable.
- Duplicate keys, invalid UTF-8, invalid TOML, non-JSON TOML values, and unsupported
  source shapes fail before schema or link conclusions.

### Author command

- `python3 -m semantic_packages author SOURCE --dependency DEP ... --output OUTPUT`
  is the documented entry point. `SOURCE`, at least the option spelling for every
  dependency, and `OUTPUT` are explicit; there is no extension sniffing or ambient
  lookup.
- Each `--dependency` names one canonical JSON record. Repeated options preserve input
  order for deterministic dependency diagnostics but confer no semantic priority.
- The command composes with the accepted representation-neutral authoring boundary.
  It does not duplicate schema/link authority or create a second canonical model.
- Success writes exactly one canonical Specification JSON document using stable,
  human-readable serialization and a trailing newline. The document, not whitespace,
  equals the accepted Stack or OrderedMap record.
- Output publication is atomic. A failed run creates no new output and does not alter
  a pre-existing output file.
- Success exits `0`. Author, input, schema, or link failure exits `1` without a Python
  traceback. Command-usage failure exits `2` using the standard command help boundary.
- Each failure line has the stable observable shape
  `CODE PATH#POINTER: MESSAGE`. Diagnostics retain their accepted deterministic order.

### Exact examples and maintenance

- `specs/stack.pspec` and `specs/ordered-map.pspec` are complete author inputs, not
  illustrative fragments.
- Their outputs equal, respectively,
  `registry/stack/theory/records/stack-spec.json` and
  `registry/ordered-map/theory/records/ordered-map-spec.json` when supplied the exact
  documented profile dependency.
- The README provides copy-paste commands, expected success observations, one failure
  exercise, limitations, and recovery. The complete examples are guarded against drift
  by the repository gate.

## Constraints and protected boundaries

- Preserve every accepted Stack and OrderedMap canonical record byte in the repository;
  generated comparison output is disposable and never rewrites accepted authority.
- Preserve ADR 0016's all-or-none authoring result and ADR 0017's explicit finite
  dependency context. The core `canonical-spec-json-v1` adapter remains unchanged and
  available as the conformance control.
- Do not derive IDs, versions, references, profiles, defaults, declaration identity,
  or dependency selection from spelling, paths, order, or nearby files.
- Do not interpret hosted semantic text, create Claims or Evidence, publish to the
  registry, choose realizations, or report semantic truth.
- Do not introduce an independently governed authoring IR. Internal transient parser
  values are implementation details only and cannot become a second source of truth.
- Keep semantic compatibility separate from realization/interoperation compatibility.
- The command reads only the exact source and dependency paths supplied by the author
  and writes only the exact output path supplied by the author.

## Mechanism freedom

The contract does not prescribe parser architecture, helper APIs, tokenization,
in-memory representation, serialization implementation, module layout, or optimization
strategy. Any mechanism is acceptable if the observable journey and falsifiers below
hold while the protected boundaries remain intact.

## Falsifiers

The feature is false if any of these observations occur:

1. Either complete example cannot produce a document equal to its accepted canonical
   Specification with the documented dependency.
2. Renaming a source or dependency path changes successful canonical content.
3. Omitting, replacing, duplicating, or corrupting a required dependency succeeds,
   searches elsewhere, or produces nondeterministic diagnostics.
4. A missing or duplicate root/local identity, dangling or wrong-kind reference,
   invalid UTF-8/TOML, duplicate key, or blank required hosted string escapes as a
   traceback, produces output, or lacks an actionable source-local diagnostic.
5. An ordinary TOML value outside the JSON data model reaches canonical output or
   crashes the command.
6. Reordering authored declaration blocks is silently canonicalized or changes their
   exact local addresses.
7. Hosted semantic text is normalized, parsed as one privileged logic, or described as
   checked Evidence.
8. A failed run creates, truncates, or replaces the requested output.
9. The command discovers a dependency, format, identity, version, reference, or output
   location that the author did not explicitly provide.
10. Existing Stack/OrderedMap consumer, resolver, campaign, Evidence, proof, or record
    checks regress.
11. A later eligible uninvolved-author observation cannot be retained truthfully,
    silently disappears from maintenance, or reports a blocking ambiguity that does
    not reopen the smallest affected contract or implementation successor.

## Definition of done

- Both documented commands are experienceable from a clean checkout and their output
  documents equal the two accepted canonical records.
- Focused journey tests derive directly from every falsifier, including output atomicity
  and the no-discovery negative controls.
- The complete repository gate passes without weakening predecessor assertions.
- Documentation states the exact experience, authority boundaries, exclusions,
  recovery, and reopen triggers.
- An independent A-R5 review attacks the journey, diagnostics, protected boundaries,
  and generality claim; every material concern is incorporated, falsified, retained as
  risk with an owner/trigger, or escalated.
- The eligible uninvolved-author protocol and exact candidate-revision authority are
  public. The experienceable feature PR may open before a participant is available,
  but ExecPlan convergence remains open. Timing, assistance, blocking ambiguity, and
  privacy-bounded observations are retained truthfully without relabeling usability as
  semantic Evidence; a failure reopens the smallest affected successor.
- ExecPlan 0006 records A5, A-R5, the post-open A5-H observation, and A-G before moving
  to completed. The next design-spec may stack after this PR opens without implying
  that A5-H or A-G passed or that this PR is merge-ready.
- One pull request maps 1:1 to this design spec, opens only after the complete journey
  is experienceable, and uses its description as the operator report: felt feature,
  exact copy-paste experience steps, and one line explaining what is real underneath.

## Known exclusions

- PSpec v1 authors Specification records only; it does not author profiles, claims,
  evidence, realizations, policies, or manifests.
- Dependencies are explicit canonical JSON inputs. Authoring or acquiring them through
  another human surface is future work.
- No registry publication, browser UI, language-server integration, live preview,
  automatic formatting, semantic type checker, proof construction, migration promise,
  or arbitrary-domain generality is claimed.
- Passing Stack and OrderedMap establishes one shared two-domain author journey, not a
  universal specification language or proven usability for all theory authors.

## Recovery and reopen triggers

The feature is recoverable by reverting its eventual single squash commit; accepted
canonical records and the JSON control boundary remain usable. A failed command leaves
its destination intact, so authors can correct the source or dependency and retry.

Reopen this contract if human observation shows TOML structure blocks the retained
tasks, a third domain cannot be represented losslessly, a second frontend or non-
identity transformation justifies an authoring IR, canonical ordering/identity rules
change, or an independently governed dependency acquisition workflow becomes necessary.

## Revision history

- **2026-07-22, revision 1:** Initial active contract. Selects the smallest reversible
  explicit lossless surface admitted by A2, freezes the two-domain command journey and
  its falsifiers, and leaves realization mechanisms free. Not yet frozen for PR.
- **2026-07-22, revision 2:** The operator's resume directive requires the complete,
  experienceable journey to open as one PR and the next design-spec to stack without
  waiting. The live uninvolved-author run therefore moves from a PR-opening gate to
  post-open convergence evidence: A-G and merge remain open until it is retained.
  Its public protocol, exact candidate authority, truthful retention, and reopen
  obligation remain; no participant result is invented and no executable behavior or
  protected boundary changes. Not yet frozen for PR.
