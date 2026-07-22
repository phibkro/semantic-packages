# OrderedMap exact deployment-profile choice

## Scope and authority

This document records the bounded product contract released by the
[deployment-profile probe](../research/deployment-profile-choice.md). It selects no new
semantic domain and adds no profile inheritance, version range, preference score, or
Evidence-transfer rule. It specializes the accepted OrderedMap `0.1.0` meaning to two
exact deployment envelopes and keeps the O8 source set as the append-only predecessor.

The P2a records and plans remain reviewed campaign inputs, not product authority.
P3 produced fresh profile-bound reports and accepted Evidence before P4 constructed
the exact profile-choice manifest. Consumer acceptance now comes only from replaying
that authenticated authority through the closed actor; presence, path, runtime
metadata, or schema validity alone still grants no acceptance.

## Exact P2a inputs

| Role | Exact path/address | Raw SHA-256 | Canonical SHA-256 |
|---|---|---|---|
| native profile | `registry/ordered-map/profile-choice/profiles/records/ordered-map-native-process.json`; `realizationProfile/ordered-map-native-process/0.1.0` | `788481758572ec2d94d3e97b009b9ca30e0322d07b93dcb37b6417243fffc450` | not separately pinned |
| Deno profile | `registry/ordered-map/profile-choice/profiles/records/ordered-map-deno-sandbox.json`; `realizationProfile/ordered-map-deno-sandbox/0.1.0` | `4629a98d62ae9ab59bebefcab5eab2306eeef8df0b19f80b6cc594f1f5adb1bf` | not separately pinned |
| native policy | `registry/ordered-map/profile-choice/consumers/records/ordered-map-native-process-policy.json`; `consumerPolicy/ordered-map-native-process-policy/0.1.0` | `1370368902b920743bdf3a24f6eab637fbee27d4e1d99e864104feeafc0b03fc` | not separately pinned |
| Deno policy | `registry/ordered-map/profile-choice/consumers/records/ordered-map-deno-sandbox-policy.json`; `consumerPolicy/ordered-map-deno-sandbox-policy/0.1.0` | `4266acfe9a658420805f0ce16ed0e49454e0ecb557f49bcb9c094960947b9df1` | not separately pinned |
| native campaign plan | `contracts/ordered-map/profile-choice/native-conformance-plan.json` | `4ad983583dc4558c9321d3c2b7a8089f7f41aa25e391b5ffeac5875a9a28d932` | `8cd414cf900f571994e081788cebf5f5c7c73964efd43f7384c2089b1fb0b472` |
| Deno campaign plan | `contracts/ordered-map/profile-choice/deno-conformance-plan.json` | `bedd5199c9958ea127c77f4f8646a71a282305b88487854cd2ce4338d76ad0d9` | `57cdeb9d881a272e9c591920cc6bf43d426cbd6310951a99c90797aa91cdb5b4` |

The profile bytes exactly promote the two P1 research candidates. Each policy differs
from `ordered-map-bounded-policy/0.1.0` only in its own ID and exact requested profile.
Required law, persistence, and effect concerns; accepted campaign mechanism; assurance
token; effect prohibition and scope; and optional unsupported performance all remain
unchanged. Each plan differs from the O6 plan only in its exact profile path, address,
and raw digest. The seven cases, semantic domains, bounds, effect contract,
Specification binding, protocol, and attribution remain unchanged.

The Specification's current performance proposition still names the old profile's
workload and cost measure. The new profiles repeat that vocabulary so future
profile-specific performance work can identify the intended measure, but this slice
does not assert a refinement relation or make that proposition applicable. Both new
policies must render performance as optional and unsupported.

## Final append-only graph contract

P4 constructed `registry/ordered-map/profile-choice-manifest.json` only after P3
produced every authorized record. Its raw SHA-256 is
`d6be0eec8439e02434a4f39a021a3c0abcc20f98ff10a02c3749359c1b78f8c7`.
It extends the exact 35-member O8 successor graph;
it does not branch from, rewrite, or replace either accepted predecessor manifest.
The final graph has exactly 69 members and ten sources:

| Source | Role(s) | Root |
|---|---|---|
| the six O8 predecessor sources | unchanged | unchanged from `successor-manifest.json` |
| `ordered-map-profile-choice-profiles` | `dependency` | `profile-choice/profiles/records` |
| `ordered-map-profile-choice-rust` | `package-authored` | `profile-choice/packages/rust/records` |
| `ordered-map-profile-choice-typescript` | `package-authored` | `profile-choice/packages/typescript/records` |
| `ordered-map-profile-choice-consumer` | `package-consumer-authored` | `profile-choice/consumers/records` |

The 34 additions are exactly two profiles, two policies, and two package sets of
fifteen records. Each package set uses version `0.2.0` of its existing IDs: one
Realization, Claims for `lookup-empty`, `lookup-put-other`, `lookup-put-same`,
`put-existing-position`, `put-new-appends`, `persistence`, and
`ordered-map-effects`, plus the seven corresponding `-conformance` Evidence IDs.
The Rust successor supports only the native profile; the TypeScript successor supports
only the Deno profile. All Claims and Evidence in a package set have the same singleton
applicable-profile set as that Realization.

Plans and reports are not graph members. Their exact paths and digests remain Evidence
provenance. P2b must reject any final census other than 69, any source expansion, any
version other than the named exact versions, or any missing predecessor member before
record loading can produce a product conclusion.

## Actor and decision contract

The public actor is the zero-argument
`inspect_ordered_map_profile_choices()`. It captures the one pinned profile-choice
manifest once and makes exactly two decisions in this order:

1. native policy/profile selects only `realization/ordered-map-rust/0.2.0`;
2. Deno policy/profile selects only `realization/ordered-map-typescript/0.2.0`.

Each selected candidate requires five law, one persistence, and one effect Claim with
one accepted applicable supporting Evidence record per declaration and no selected
challenge. The effect Evidence also satisfies the existing `io.*` prohibition scope.
Performance is visible as optional, unsupported, and nonblocking. Runtime metadata or
profile membership is never counted as Evidence. Each result separately renders the
directional `consumer-to-realization` `child-process-ndjson` boundary as non-direct.

For each decision the applicability ledger covers all 28 Claims and 28 Evidence
records in the final graph:

- seven Claims and seven Evidence records for the selected package/profile are
  `selected-applicable`;
- the 14 predecessor Claims and 14 predecessor Evidence records are `inapplicable`;
- the other new profile's seven Claims and seven Evidence records are `inapplicable`.

Thus every decision renders exact counts of 7 selected and 21 inapplicable for both
Claims and Evidence. Inapplicable support is neither challenge nor assurance. The O8
zero-candidate successor remains observable through its own maintenance actor and is
not silently recovered, ranked, or selected by this actor.

## Maintenance controls and exclusions

The frozen P2b suite now guards the implemented actor boundary. It covers exact
artifact and predecessor bytes, 69-member/ten-source authority, zero-argument and
one-capture behavior, no discovery or execution, immutable detached replay, both
terminal decisions, the 7/21 applicability ledgers, all Evidence result/review axes,
optional performance, the separate directional boundary, and unchanged O6--O8 and
Stack actors.

Controls fail closed for a missing or extra member/source, wrong exact selector,
omitted version, range or implicit-latest spelling, profile-swapped Claim or Evidence,
broadened applicability set, report/plan/profile digest mismatch, false performance
promotion, candidate cross-selection, and any attempt to pass authority or selector
overrides to the public actor. A targeted swapped-profile control must remain valid
Evidence for its own exact profile while becoming inapplicable and blocking assurance
under the requested profile.

The same suite retains the accepted 33-member OrderedMap decision, the O8 35-member
zero-candidate successor and nonautomatic predecessor recovery, and the Stack actor
without calling Stack resolution from the new actor. Reports reproduce independently;
Evidence records are derived from their exact accepted bytes; the repository-wide gate
runs both checks alongside all actor regressions.

This contract does not authorize profile refinement, Evidence migration, benchmarking,
runtime interoperability, Specification `0.2.0` recovery, a generic resolver language,
or changes to Stack.
