# Evidence model

## Assurance is multidimensional

A single “verified” badge is insufficient. Evidence is indexed by concern and mechanism.

| Concern | Example mechanisms |
|---|---|
| algebraic correctness | proof, property tests |
| protocol safety | model checking, trace tests |
| memory safety | language guarantee, proof, sanitizer evidence |
| performance | complexity proof, benchmark |
| security | formal model, fuzzing, audit |
| interoperability | conformance and differential tests |

## Status lifecycle

Evidence review may use workflow states:

```text
unverified → pending → accepted
                    ↘ rejected
accepted → superseded/revoked
```

This workflow is distinct from both the evidence result and assurance strength. An
accepted benchmark can still fail its threshold, and an accepted counterexample can
challenge a claim.

Evidence results are:

```text
supports | challenges | inconclusive | error
```

An author assertion is represented as evidence with mechanism `assertion`. It may be
acceptable under a permissive policy, but it does not turn the claim itself into an
"asserted truth."

## Validity, applicability, and coverage

The resolver evaluates distinct stages rather than overloading the result field:

| Stage or condition | Treatment |
|---|---|
| dangling, wrong-kind, duplicate, or scope-incoherent reference | invalid input; link error |
| valid evidence outside the requested claim/profile/environment | inapplicable; retained and explained |
| rejected, revoked, or superseded under the selected policy | retained but not selected |
| no acceptable applicable evidence | unsupported coverage, not an evidence result |
| applicable accepted `supports` | candidate support |
| applicable accepted `challenges` | visible conflict; blocks a required concern while selected |
| applicable `inconclusive` or `error` | no support; retain the attempted check |
| assertion-only support | contributes only if the policy accepts `assertion` |

Mixed supporting and challenging evidence produces a visible contested outcome; it
does not collapse to a verified badge. A required concern is satisfied only when the
selected policy derives satisfaction from acceptable applicable evidence with no
selected challenge. Preferred and optional concerns need not block selection but keep
their unmet, unknown, or contested state visible. Ignored concerns remain inspectable
and do not affect the decision.

Semantic prohibitions are required negative obligations, not evidence priorities.
Absence of observations supports such an obligation only within the evidence record's
declared boundary and exclusions; missing evidence never proves absence.

## Required metadata

Every evidence record must expose:

- claim identifier;
- governing specification version;
- realization and adapter versions when the claim or mechanism concerns a realization;
- method and toolchain;
- assumptions;
- environment or generated domain;
- result and timestamp;
- exclusions;
- provenance/signature where available.

Specification-only proof evidence omits realization and adapter references. Evidence
that executes or evaluates a realization requires both. Any redundant subject,
specification, realization, adapter, or profile reference must agree with the claim's
scope; contradiction is a link error. A valid evidence record may still be
inapplicable to a different consumer-requested profile.

For executable evidence, provenance includes the checker or runner version, command
or invocation descriptor, input artifact digests, and result artifact digest. For
proof evidence, it also identifies the trusted kernel and whether checking completed
successfully.

## Formal verification qualification

“Formally verified” means a proposition was proved relative to a model, assumptions, logic, and trusted kernel. It does not mean the specification captures every intended real-world property.

## Policy evaluation

Evidence is selected per claim, concern, profile, freshness rule, and accepted
mechanism. The resolver reports every applicable supporting, challenging, and
inconclusive record used in its decision. The prototype does not impose a universal
linear ranking across proof, testing, benchmarking, audit, and assertion.
