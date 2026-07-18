# ADR 0013: Bounded policy mechanism and observation-scope matching

## Status

Accepted by J4P-G in ExecPlan 0002 after J3-C2STR, the frozen J3/J4P falsifiers,
successor `1435869`, the bounded J4P-R2 advisor replay, and the full locked repository
gate passed. The accepted revision includes the post-proposal `no-coverage` rule; the
advisor's PASS supports but does not ratify this lead acceptance act.

## Context

The J3 ConsumerPolicy candidate correctly names the Stack concerns and accepted Wave 4
campaign mechanism, but its first version relied on two meanings that schemas alone do
not provide. An empty `acceptedMechanisms` array was intended as “accept none,” while
omission could be mistaken for a wildcard. Its `adapter-invocation-trace` prohibition
scope also has no same-named Evidence field: the observation boundary is carried by the
governed campaign/adapter contract, exact provenance, assumptions, and exclusions.

Graph validity cannot decide either question. Allowing a future resolver's truthiness
or string-matching idiom to decide them would make incidental implementation behavior
into policy semantics. Rewriting the accepted eight Wave 4 Evidence records merely to
add a redundant label would reopen their exact byte/provenance bridge without first
demonstrating that a general scope taxonomy is needed.

## Decision

`acceptedMechanisms`, when present, is a closed exact set. An empty array explicitly
accepts no Evidence mechanism. When the field is absent, mechanism acceptance is
unspecified: the resolver reports the policy entry incomplete and selects no Evidence
for satisfaction. Absence is never a wildcard. Every non-`ignored` concern in the Stack
product policy states the field explicitly. This preserves the existing rule that
assertion Evidence contributes only when `assertion` is explicitly accepted.

Priority and support remain separate. An optional concern with no acceptable or
available Evidence remains visible as unknown/unsupported without blocking candidate
selection. A policy names mechanisms it would accept independently of whether matching
Evidence currently exists; it is not tailored to manufacture the desired current
outcome. The J3 successor policy therefore accepts the Specification-permitted
`proof` and `proof-audit` mechanisms for optional performance. Performance remains
unsupported because the graph contains no realization-scoped performance Claim or
Evidence.

The Stack product policy uses one closed `minimumAssurance` token for every non-ignored
concern:

```text
per-declaration-one-accepted-applicable-support-no-selected-challenge
```

When `minimumAssurance` is omitted or is not this accepted tracer token, the policy
entry is incomplete and selects no Evidence for satisfaction. It never falls back to a
default threshold. The product policy states the token explicitly for every non-ignored
concern, including optional performance.

Concern-to-declaration coverage is derived from the selected exact Specification, not
from whichever Claims happen to exist: `law.conformance` covers every law;
`resource.persistence` covers every resource rule; `effect.conformance` covers the
effect declaration; and `performance` covers every performance proposition. For every
covered declaration and selected Realization, the token requires one exact active Claim
with the selected profile, at least one applicable `accepted`/`supports` Evidence item
using an accepted mechanism, and no selected applicable `accepted`/`challenges` item.
A missing Claim therefore fails rather than making an empty set vacuously satisfy the
threshold. `inconclusive` and `error` do not support it.

Zero derived declarations never satisfy a non-`ignored` policy entry vacuously. The
resolver reports a distinct `no-coverage` disposition; it blocks a `required` concern
and remains visible without blocking a `preferred` or `optional` concern.

`acceptedEvidenceScope` is also a closed set of exact policy tokens. A token matches
only through a governed evidence-mechanism boundary classification; it is never inferred
from prose, path spelling, or substring matching. The Stack tracer defines one token:

```text
adapter-invocation-trace
```

For the current graph, an Evidence record can provide that scope only when all of the
following hold:

1. the policy prohibition targets an exact effect declaration and its `eventPattern`
   is declared by that effect contract;
2. the Claim has concern `effect.conformance`, targets the same exact declaration and
   Specification, and declares an exact applicable-profile set;
3. the Evidence exact-links that Claim, Specification, Realization, adapter, and
   the same applicable-profile set; has scope `realization`; and uses
   `bounded-conformance-campaign`; and
4. its canonical provenance names the same declaration and the accepted Wave 4 plan
   digest `e055eab406683a01a32e8b563ef2e299169ddb2745685b5ad3ffae3297d93f6c`,
   whose ADR 0010 mechanism contract makes the declaration outcome and event list
   observations inside one adapter invocation boundary.

Scope classification uses only those canonical graph fields plus the governed mechanism
contract. It does not inspect free-form method/review prose, execute files, or depend on
a remembered gate result. Review state, result, applicability, and freshness remain
separate axes: after scope classification, selection still requires accepted/applicable
Evidence and evaluates supports, challenges, inconclusive, and error distinctly.

Applicability then compares the coherent Claim/Evidence profile set to the actor's exact
selected policy/profile input. For each covered declaration, evaluation selects every
matching active Claim for the selected Realization and every linked applicable Evidence
record admitted by the mechanism/scope policy. It cannot cherry-pick a supporting Claim
or hide a selected challenge when multiple records target the same declaration.

The independent Wave 4 reproduction is release evidence that the exact canonical
provenance remains honest; it is never hidden resolver state or a runtime predicate.
The resolver reports the selected Evidence's completeness assumption and external-effect
exclusion and limits any absence conclusion to the adapter-invocation trace. A missing,
stale, inapplicable, unaccepted, inconclusive, erroneous, challenging, differently
scoped, or unknown-token record cannot prove the prohibition.

This is a tracer-specific mechanism classification, not a universal scope registry.
J3 controls must show that invented concern/mechanism/scope tokens do not select current
Evidence, and J4P controls must distinguish empty, omitted, matching, and nonmatching
mechanism/scope cases without truthiness shortcuts.

## Alternatives and dissent

- Treating omitted mechanisms as “no filter” is convenient, but would implicitly admit
  assertion Evidence and contradict explicit consumer acceptance. It is rejected.
- Requiring `minItems: 1` would remove a legitimate explicit accept-none policy. The
  schema continues to allow empty while evaluation remains fail-closed.
- Keeping `acceptedMechanisms: []` for optional performance is structurally valid, but
  it expresses refusal of every future mechanism and was chosen in response to current
  Evidence absence. Accepting the Specification's permitted proof mechanisms states a
  more stable consumer standard while preserving the same current unsupported outcome.
- Matching `acceptedEvidenceScope` to Evidence's coarse `scope: realization` would
  overstate the boundary and hide the explicit external-effects exclusion.
- Adding an Evidence-side scope label is clearer for a future general resolver, but it
  would reopen eight exact Wave 4 records and can still drift from the mechanism that
  produced the observations. The bounded classifier is smaller for this tracer.
- Trusting method or assumption prose as the classifier was rejected. Those fields
  remain displayed qualifications; exact mechanism/provenance binding supplies the
  classification.

## Consequences

- Policy incompleteness, explicit accept-none, absent Evidence, and unacceptable
  mechanism are distinct explanations even when none supports a concern.
- The product policy can remain honest before performance Evidence exists and can
  evaluate future proof Evidence without a policy rewrite.
- The `io.*` result is explicitly limited to the reviewed adapter boundary and cannot
  become a whole-process or external-effects claim.
- The exact assurance token is decidable without parsing English and cannot pass
  vacuously when a required declaration lacks a Claim.
- J3/J4P gain exact negative controls without modifying accepted W4 record bytes.
- Mechanism and scope classification joins the resolver's trusted policy-evaluation
  boundary and must remain independently reviewed.

## Revisit conditions

Revisit before adding another conformance mechanism, observation boundary, general
scope taxonomy, unsigned/unreviewed Evidence source, or policy composition. Reopen if
the Wave 4 plan/runner/report binding changes, if Evidence must declare scope independent
of its mechanism, or if a resolver cannot distinguish absent and empty fields without
weakening fail-closed behavior.
