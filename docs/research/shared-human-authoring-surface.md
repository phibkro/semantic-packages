# Shared human authoring surface probe

## Question

What do the accepted Stack and OrderedMap lifecycles require a human-facing authoring
surface to preserve before the project chooses `.pspec` grammar, elaboration rules, or
defaults?

This is a boundary probe, not a language proposal. Canonical JSON remains authoritative
for the accepted tracer descendants: ADR 0003's formal decision scope is ExecPlan 0001,
while later accepted plans retained rather than superseded its temporary interchange
boundary. Replacing it still requires a new migration decision. The existing
`specs/stack.pspec` remains illustrative.

## Exact inputs

| Input | SHA-256 |
|---|---|
| `specs/stack.pspec` | `86f60cc9415353b951b21d1993430b0bd4369a6e560359aaeb67af7cc682596a` |
| Stack Specification `0.1.0` | `dd083a71a4631cc44be051a16b8e20ff0cee7199e46d3823322665d1fdeec6c1` |
| OrderedMap Specification `0.1.0` | `6049d371603cbdac0e722685f1fd25c7369872f7d963ae2e4f4bae90cce7fd7f` |
| Specification schema | `c77c1089e61f4b4c88b5e9a93429ea121753ab5753c76c11889a285c0265cd84` |

The executable probe is
`tests/research/test_shared_human_authoring_surface_probe.py`.

## Observations

The two domains share a real structural authoring envelope: exact Specification
identity/version; explicit local declaration IDs; carriers, operations, observations,
equivalences, laws, effects, resources, and profile-bound performance propositions.
Stack additionally uses a derived observation. The accepted records contain 11 and 18
flat declaration IDs respectively. The probe enumerates their exact per-family sets,
equivalence-carrier references, operation families, and workload/cost-measure profile
and local IDs. Both exact inputs omit `imports`; a future input that uses imports must
preserve its exact typed addresses under the separately accepted canonical rule. IDs,
declaration categories, and present references cannot be invented from spelling or
array position.

The current Stack sketch is not a lossless source for its canonical record. It does
not explicitly supply canonical IDs such as `stack-equivalence`, `pop-empty`,
`pop-push`, `stack-effects`, or `push-amortized-constant`, and it omits descriptive
canonical payloads. Inferring those values would introduce hidden naming/default
rules. There is no OrderedMap `.pspec` source from which to test the same rules.

The canonical schema deliberately treats signatures, derived-observation definitions,
equivalence definitions, law statements, resource rules, and performance predicates as
nonempty strings. A surface parser can preserve these hosted payloads, but it cannot
claim to elaborate or type-check their meaning until a separately governed semantic
language exists. Choosing one universal hosted logic would violate the plural-
mathematics boundary.

## Result

The cheapest falsifier rejects “implement the illustrative parser” as the next step.
The shared need is an explicit, lossless authoring contract that distinguishes:

- stable structural identity and exact references that an elaborator must check;
- domain-semantic payloads that are currently hosted text and must remain visibly
  unchecked unless a selected logic/checker owns them;
- author conveniences that may desugar only through documented, falsifiable rules;
- canonical output and diagnostics that must be identical for Stack and OrderedMap
  inputs expressing the same accepted records.

Here “identical canonical output” means equality of the parsed canonical record
document, including exact addresses, declaration IDs, references, and values. It does
not require retaining JSON whitespace, member order, or the input surface's bytes;
deterministic serialization is a separate A2/A3 question.

No syntax, file extension, serialization, parser library, hosted logic, implicit ID
rule, or default is selected by this result. The next gate must compare reversible
contract options against exact two-domain round-trip and missing/ambiguous-ID
falsifiers. If that comparison leaves multiple materially different author experiences
with no product evidence to choose among them, the choice returns to the operator.

## Reopen triggers

Reopen this census when a canonical Specification declaration family, identity rule,
import/refinement rule, or semantic payload representation changes; when an eligible
human-author observation reveals a missing task; or when a proposed surface can
demonstrate exact two-domain round trips without hidden defaults.
