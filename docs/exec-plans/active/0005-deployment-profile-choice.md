# ExecPlan 0005: exact deployment-profile choice

## Purpose and observable outcome

Demonstrate a consumer choosing between two genuinely differentiated OrderedMap
deployment profiles while retaining every nonmatching Claim and Evidence item as
inapplicable rather than transferring assurance by resemblance. The completed actor
must replay one append-only authority, make two exact policy/profile decisions, select
one independently represented package for each profile, explain every required
concern, and keep the realization boundary separate from semantic acceptance.

Success is bounded to exact native-process and Deno-sandbox profiles over the existing
OrderedMap meaning. It does not establish automatic profile refinement, version-range
compatibility, runtime interoperability, performance superiority, or arbitrary-domain
generality.

## Context and constraints

ExecPlan 0004 closed the two-domain lifecycle and left deployment-profile choice as
the first backlog item. The accepted 33-member OrderedMap graph and O8 successor are
immutable predecessors. Stack resolution and all Stack records remain untouched.

The [deployment-profile probe](../../research/deployment-profile-choice.md) freezes the
first material finding: retained reports and Evidence bind
`ordered-map-ascii-fold/0.1.0`, so they cannot be relabelled for a new runtime-specific
profile. New acceptable candidates require append-only Realization, Claim, Evidence,
policy, report, and authority facts. The two candidate profile records remain research
fixtures until a reviewed design gate releases their final registry paths and bytes.

No policy may reduce the accepted OrderedMap required concerns merely to obtain a
green candidate. Performance stays optional and unsupported unless new exact Evidence
supports it. Exact profile selection is not version compatibility and must not add
implicit `latest`, ranges, preference scoring, or profile inheritance.

## Revisioned DAG

```text
P0 roadmap selection
  -> P1 differentiated-profile falsifier
  -> P-R1 independent research review
  -> P-G1 profile-contract gate
  -> P2 exact records, plans, actor journeys, and red controls
  -> P-R2 independent red-control review
  -> P3 profile-specific campaigns, reports, Claims, and Evidence
  -> P-R3 independent evidence review
  -> P4 append-only authority, exact resolution, and inspection
  -> P-R4 independent implementation review
  -> P5 maintenance and predecessor-regression observation
  -> P-R5 independent end-to-end review
  -> P-G final lead-acceptance gate
```

| Node | Owner and boundary | Required evidence and downstream gate |
|---|---|---|
| P0 roadmap selection | lead; read-only backlog/vision census | complete: backlog priority 1 chosen ahead of refinement and a third domain |
| P1 differentiated-profile falsifier | lead; exclusive research fixtures, probe test, research note, and this plan | successor candidate: two schema-valid profiles hold meaning constant and differ at the runtime boundary; executable controls freeze all 14 Claims, 14 Evidence records, two Realizations, and two reports as exact to the old profile, with relabel/addition sensitivity |
| P-R1 independent research review | uninvolved read-only reviewer | review profile differentiation, exact-applicability falsifier, implementation release, exclusions, and absence of hidden refinement; PASS releases P-G1, BLOCK retains concerns here |
| P-G1 profile-contract gate | lead acceptance after P-R1 | accept or revise the exact actor contract; no canonical product records before PASS |
| P2 exact design and red controls | lead/integrator; exclusive new profile-choice artifacts and journey controls | freeze paths, addresses, manifest census, two policies, campaign bindings, output, inapplicability controls, no-override entrypoint, and unchanged predecessor behavior |
| P-R2 red-control review | uninvolved read-only reviewer | confirm tests fail only at absent implementation and cover authority, exactness, evidence axes, negative controls, Stack, and O6--O8 bytes |
| P3 evidence production | lead/integrator; exclusive new plans/reports/successor records | two fresh reproducible campaigns; exact report-to-Evidence derivation; required law/resource/effect support; optional performance remains unsupported; targeted cross-profile breaker |
| P-R3 evidence review | uninvolved read-only reviewer | independently reproduce reports and reject profile swapping, stale bytes, mismatched applicability, and false performance promotion |
| P4 authority and actor | lead/integrator; exclusive new manifest, resolver, inspection, and tests | one capture, two exact decisions, one acceptable package per profile, visible inapplicable Evidence, separate directional boundary, fail-closed diagnostics |
| P-R4 implementation review | uninvolved read-only reviewer | inspect trust boundary, data flow, selector closure, evidence disposition, and generality wording; execute focused checks |
| P5 maintenance/regression | lead/integrator; exclusive plan/docs and maintenance controls | append-only preservation and recovery behavior; unchanged accepted OrderedMap and Stack decisions; known exclusions recorded |
| P-R5 end-to-end review | uninvolved read-only reviewer | independently confirm actor outcome, negative controls, reproducibility, exclusions, and exact claim boundary |
| P-G final gate | lead | focused, full repository, change-governance, and hosted checks green; move plan to completed and merge by squash convention |

## Progress and decision log

- 2026-07-22: P0 complete. ExecPlan 0004 is closed and backlog priority 1 is the next
  product node; refinement and domain 3 remain downstream.
- 2026-07-22: P1 candidate complete. Two research profiles isolate deployment from
  semantic workload. The initial executable probe proved only accepted persistence
  Evidence and both reports remained exact to the old profile.
- 2026-07-22: P-R1 BLOCK retained. The facts and successor route were sound, but the
  probe sampled two persistence Evidence records while the plan promised every
  nonmatching Claim and Evidence item across required law/resource/effect concerns.
- 2026-07-22: P1 successor candidate closes the scope gap by freezing the exact 14
  Claim + 14 Evidence census, concern distribution, links, profile sets, both
  Realizations, both reports, and relabel/addition sensitivity.
- 2026-07-22: P-R1 successor review PASS. The independent reviewer reproduced all six
  focused controls, confirmed the per-package 7 Claim + 7 Evidence split and exact
  concern/link/applicability census, and found no material residual. P2 retains the
  future manifest, presentation, and full actor negative-control obligations.
- 2026-07-22: P-G1 PASS. Lead acceptance releases the bounded exact-profile actor
  contract to P2. Candidate fixture bytes remain research inputs, not accepted registry
  members, until P2 freezes final paths, addresses, authority, and red controls.
- 2026-07-22: The first hosted prospective-metadata run at `8d9267b` BLOCKED before
  repository checks because `research` is not an allowed Conventional Commit type.
  Reclassify the executable probe checkpoint as `test(profiles)` and rerun hosted gates;
  no product or accepted-record bytes change in this correction.

## Verification

P1 runs:

```text
python3 -m unittest tests.research.test_ordered_map_profile_choice_probe
python3 scripts/check_repo.py
```

Later nodes add their focused commands here before closure. Every merge must also pass
the repository's hosted conventional-commit and squash-only governance.
