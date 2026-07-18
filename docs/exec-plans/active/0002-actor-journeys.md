# ExecPlan 0002: Actor-complete registry tracer

## Purpose and observable outcome

Complete the Stack tracer as a product journey: a theory author and two independent
package authors publish one honest finite local graph; a theory consumer browses
meaning and exact imports; a package consumer resolves Realizations under an explicit
policy/profile; and a failed exact successor demonstrates staleness and recovery.

The observable release is one documented fresh-clone command that exercises every
journey against the same canonical records without converting unknown, challenging,
inapplicable, or stale Evidence into assurance.

## Context and repository map

Read the constitution, `ARCHITECTURE.md`, `docs/design/core-model.md`,
`docs/design/evidence-model.md`, `docs/design/compatibility.md`,
`docs/design/lifecycle.md`, `docs/design/system-map.md`,
`docs/design/user-journeys.md`, and ExecPlan 0001. Wave 4 and W4-G1 are the executable
upstream substrate.

## Non-goals and constraints

- no hosted registry, authentication, database, remote acquisition, or production
  search/security boundary;
- no registry-driven build or command execution;
- no `.pspec` authoring claim until elaboration exists;
- no semantic-version compatibility, declaration lineage, namespace merge, or inferred
  refinement;
- no universal proof, transport, evidence ranking, or interoperation mechanism;
- preserve claim lifecycle, Evidence review/result/applicability, and assurance as
  separate axes;
- preserve semantic compatibility separately from directional realization compatibility;
- derive every resolver/browser view from one curated finite exact-version source set.

## Specification and governance changes

ADR 0011 replaces a single serial development lifecycle with a scaled evidence-bearing
spine and explicit change profiles. The system map is a derived architectural
projection. The user-journey contract makes actor terminal outcomes the primary
acceptance surface; implementation packages remain subordinate nodes.

## Revisioned work DAG

```text
J0 vocabulary/lifecycle/map gate
  -> J1 theory-author publication
  -> J2 independent package registration
  -> J3 curated honest graph
       -> J4P package resolver
       -> J4T theory projection/import
  J4P + J4T -> J5 successor/staleness recovery
  J5 + release-governance support -> JG journey-complete release
```

| Node | Owner, dependencies, write boundary | Evidence, downstream gate, status |
|---|---|---|
| J0-A actor/architecture audit | independent read-only reviewer; depends on W4-G1 | four-actor gap matrix, system-plane/trust audit, and lifecycle challenge; supports J0-G; complete |
| J0-L lifecycle successor | lead integrator; exclusive `CONTRIBUTING.md`, lifecycle, ADR 0011 | scaled change profiles, refute-first micro-loop, anti-self-ratification; integrates into J0-G; implementation checkpoint |
| J0-M system/journey map | lead integrator; exclusive system map, journey design, README, checker, this plan | authority map, executable/designed/planned states, actor terminal outcomes and acceptance DAG; integrates into J0-G; implementation checkpoint |
| J0-R1 design convergence | independent read-only reviewer; depends on J0-L/J0-M | BLOCK: assurance and publication status were overstated, ADR 0011 self-accepted, status authority was stale, and this plan was not dispatch-ready; retained predecessor |
| J0-S1 documentation successor | lead integrator; depends on J0-R1; same exclusive J0-L/J0-M surfaces | exact-bound Evidence replaces “assurance graph”; loading/conformance are not publication; ADR remains proposed; both active plans own explicit status scopes; commands, reviewers, scopes, packets, decisions, and reopen triggers added; implementation checkpoint |
| J0-R2 successor convergence | independent read-only reviewer; depends on J0-S1 | BLOCK: earlier status/authority/lifecycle blockers close, but J1 assigns consumer policy/profile to the theory author and PR-G/JG lack exact planned check/no-write scope |
| J0-S2 ownership/readiness successor | lead integrator; depends on J0-R2; same exclusive J0 surfaces | consumer policy/profile stay consumer-owned; PR-G gets exact local/remote observations; JG is read-only with no repository writes; implementation checkpoint |
| J0-R3 successor-history review | independent read-only reviewer; depends on J0-S2 | BLOCK: substantive R2 corrections and all R1 boundaries pass, but the plan had not retained R2/S2 and therefore erased a failed review from its DAG |
| J0-S3 retained-history successor | lead plan integrator; depends on J0-R3; exclusive ExecPlan 0002 | retains R2/S2/R3 and predeclares R4 rather than retroactively relabeling a predecessor; implementation checkpoint |
| J0-R4 final successor convergence | independent read-only reviewer; depends on J0-S3 | PASS: all R1–R3 blockers replay closed; rejected nodes/successors remain visible; no new authority, status, lifecycle, registry, assurance, journey, or compatibility contradiction |
| J0-G journey-contract gate | lead acceptance; depends on J0-R4 and G0 | accepted: exact repository gate and diff check pass, governing docs agree, and material concerns are disposed; J1 released |
| J1-P0 publication preflight | independent read-only concern owner; depends on J0-G | complete: freezes three theory-authored records plus one dependency-labeled profile, Stack-specific read-only inspection, nine falsifier classes, explicit proof execution, proof-fixture digest bridge, and J1→J2 handoff |
| J1-F1 publication controls | bounded fixture owner; depends on J1-P0; exclusive `registry/stack/theory/**`, `tests/journeys/test_j1_*` | complete red checkpoint: four curated records are byte-identical to accepted sources and graph-valid; 12 tests yield one missing-module failure and 11 successor skips; predecessor G0 remains green |
| J1-F1R control review | fresh independent product-graph reviewer; depends on J1-F1 | BLOCK: curated graph/proof/red boundary pass, but only diagnostic codes are frozen, extra valid Specification/Profile addresses can escape, and hard-coded/default process launch is not intercepted |
| J1-F2 publication-control successor | original bounded fixture owner; depends on J1-F1R; same exclusive fixture/test scope | complete red successor: 14 tests yield one missing-module failure/13 skips; exact signatures/order, valid extra Specification/Profile addresses, and process launch boundaries are frozen; predecessor G0 remains green |
| J1-F2R successor control review | fresh independent product-graph reviewer; depends on J1-F2 | BLOCK: all F1R gaps close, but only Specification proof drift is rejected; schema-valid Claim drift and other frozen-source mutations can retain accepted identities |
| J1-F3 immutable-source successor | original bounded fixture owner; depends on J1-F2R; same exclusive test scope | complete red successor: 17 tests yield one missing-module failure/16 skips; schema/link-valid mutations of all four fixed addresses require exact proof/source-digest failures while byte-preserving rename remains valid |
| J1-F3R immutable-source review | fresh independent product-graph reviewer; depends on J1-F3 | BLOCK: all prior bindings pass, but a byte-identical symlink can bypass governed loader discovery while preserving digest/address |
| J1-F4 filesystem-boundary successor | original bounded fixture owner; depends on J1-F3R; same exclusive test scope | complete red successor: 18 tests yield one missing-module failure/17 skips; byte-identical symlink rejects exactly while ordinary rename remains accepted |
| J1-F4R final publication-control review | fresh independent product-graph reviewer; depends on J1-F4 | BLOCK: file symlink closes, but a symlinked `records/` directory component can still bypass a leaf-only check |
| J1-F5 directory-boundary successor | original bounded fixture owner; depends on J1-F4R; same exclusive test scope | complete red successor: 19 tests yield one missing-module failure/18 skips; leaf and directory-component symlinks reject exactly while ordinary rename remains accepted |
| J1-F5R final publication-control review | fresh independent product-graph reviewer; depends on J1-F5 | PASS: all F1R–F4R blockers replay closed; root-symlink identity remains an explicit exclusion; J1-I1 released |
| J1-I1 publication implementation | internal fallback implementation owner; depends on accepted J1-F5R; isolated `/tmp/semantic-packages-j1-i1`, exclusive `semantic_packages/publication.py` | complete: frozen 19-test suite passed, but J1-I1R retained two completeness blockers |
| J1-I1R publication implementation review | independent read-only implementation reviewer; depends on J1-I1 | BLOCK: discovery ignored valid records at the source root and sibling subtrees, and an unrelated graph error could suppress a missing approved Evidence address |
| J1-F6 publication-completeness successor | lead-owned contract integration; depends on J1-I1R; exclusive `tests/journeys/test_j1_*` | complete: root/sibling policy records and missing-Evidence-plus-duplicate behavior are frozen; successor suite totals 22 tests |
| J1-I2 publication successor | internal implementation owner; depends on J1-F6; isolated implementation scope then lead integration | complete: whole-root discovery plus explicit curated child checks and address-specific missing suppression make all 22 focused tests pass in the documented Nix Python environment |
| J1-I2R publication successor review | independent read-only product-boundary reviewer; depends on J1-I2 | BLOCK: I1R defects close, but directory symlinks in unknown and nested subtrees are silently ignored, so the supplied tree can hide uninspected external content |
| J1-F7 directory-symlink completeness successor | lead-owned contract integration; depends on J1-I2R; exclusive `tests/journeys/test_j1_*` | complete red checkpoint: two exact reject-without-following attacks fail while the prior 22 tests pass |
| J1-I3 publication filesystem successor | internal implementation owner; depends on J1-F7; isolated `semantic_packages/publication.py` scope | complete: lstat-before-scandir, no-follow recursion, stable read errors, and exact diagnostic dedup make all 24 focused tests pass |
| J1-I3R publication successor review | independent read-only product-boundary reviewer; depends on J1-I3 | PASS: all 24 controls and root/sibling/nested/leaf no-follow probes pass; deterministic read errors and phase barrier hold; private loader coupling and quiescent-tree assumption retained |
| J1-G theory publication | lead acceptance; depends on J1-I3R, explicit proof reproduction, and G0 | accepted: 24/24 publication controls pass and the curated Evidence reproduces with Lean 4.30.0 as `Proof is valid: 0 diagnostics.`; releases J2 while general/hosted publication remains excluded |
| J2-P0 package-registration preflight | independent read-only concern owner; depends on J1-G/W4-G1 | complete: each package contributes nine byte-identical W4 records to a graph-valid 13-record union with the accepted four-record theory root; recommends one shared no-follow finite-source primitive plus Stack-specific allowlists |
| J2-RF1 Rust curated-record fixture | bounded package-record owner; depends on J2-P0; exclusive `registry/stack/packages/rust/**` | complete: exactly nine byte-identical accepted records; digests match and the 13-record Rust/theory union is graph-valid with zero diagnostics |
| J2-TF1 TypeScript curated-record fixture | bounded package-record owner; depends on J2-P0; exclusive `registry/stack/packages/typescript/**` | complete: exactly nine byte-identical accepted records; digests match and the 13-record TypeScript/theory union is graph-valid with zero diagnostics |
| J2-F1 registration falsifiers | bounded contract owner; depends on J2-RF1/J2-TF1; exclusive `tests/journeys/test_j2_*` | complete red: 13 discovered, byte/digest control passes, one failure is solely missing `semantic_packages.registration`, and 11 successors skip; full finite-registration matrix frozen |
| J2-SF0 finite-source extraction controls | shared-boundary contract owner; depends on J2-F1; exclusive `tests/journeys/test_j2_finite_source.py` | complete red: 11 discovered, one failure is solely missing `_finite_source`, 10 successors skip; labeled roots, alias/overlap, phase/no-follow/error/hash/snapshot/no-exec controls frozen and J1 remains 24/24 |
| J2-F1R/SF0R registration/helper control review | independent read-only boundary reviewer; depends on J2-F1/J2-SF0 | BLOCK: accepted-input no-exec, theory consumption, Claim/Evidence rename, record shape, duplicate semantic address, logical collision, raw-byte hash, no-target-traversal, canonical-entrypoint no-exec controls incomplete; snapshot test over-prescribes mutable dicts |
| J2-F2/SF1 control successors | original bounded contract owner; depends on J2-F1R/SF0R; same exclusive test surfaces | complete red: 31 combined tests yield one fixture pass, exactly two missing-module failures, and 28 skips; all retained attacks frozen and snapshot stability is representation-neutral |
| J2-F2R/SF1R successor review | independent read-only boundary reviewer; depends on J2-F2/SF1 | BLOCK: prior gaps close, but theory Claim/Evidence/Profile renames, package selector/root mismatch, resolved symlink target traversal, nested snapshot aliasing, and reverse-overlap determinism remain open |
| J2-F3/SF2 final control successor | original bounded contract owner; depends on J2-F2R/SF1R; same exclusive test surfaces | complete red: 33 combined tests yield one fixture pass, exactly two missing-module failures, and 30 skips; all retained provenance/selection/no-follow/deep-snapshot/order attacks frozen |
| J2-F3R/SF2R final control review | independent read-only boundary reviewer; depends on J2-F3/SF2 | PASS: all retained provenance/selection/no-follow/deep-snapshot/order attacks close; exact red is one fixture pass, two missing modules, and 30 skips; releases J2-SI1 |
| J2-SI1 finite-source extraction | single shared-boundary integrator; depends on accepted J2-F3R/SF2R; exclusive `semantic_packages/_finite_source.py` and `semantic_packages/publication.py` migration | complete implementation checkpoint: all frozen 16 helper and 24 J1 controls pass; retained predecessor pending successor review |
| J2-SR1 finite-source successor review | independent read-only boundary reviewer; depends on J2-SI1 | BLOCK: frozen controls pass and no product policy leaks, but `//absolute` aliases collide, roots beneath symlinked ancestors can be traversed, and one special-root message drifts from ADR-0007 behavior |
| J2-SF3 ADR-0007 successor controls | bounded contract owner; depends on J2-SR1; exclusive `tests/journeys/test_j2_finite_source.py` | complete red checkpoint: prior 16 controls stay green and exactly three new controls fail for `//absolute`, symlink-ancestor target access, and special-root message drift |
| J2-SI2 finite-source boundary successor | original shared-boundary integrator; depends on J2-SF3; same isolated source scope | complete: governed lexical normalization, strict-ancestor `lstat`, and predecessor diagnostics make all 19 helper plus 24 J1 controls pass |
| J2-SR2 final finite-source review | independent read-only boundary reviewer; depends on J2-SI2 | PASS: all SR1 attacks and 43 retained controls replay; helper remains policy-free and preserves J1; quiescent-tree and trusted-label exclusions retained |
| J2-I1 Stack registration implementation | Claude Sonnet 5 package-registration integrator; depends on J2-SR2; isolated exclusive `semantic_packages/registration.py` | complete checkpoint: 60/60 focused controls pass; no execution/assurance; retained candidate pending ownership successor |
| J2-R1 registration boundary review | independent read-only product reviewer; depends on J2-I1 | BLOCK: most boundaries pass, but record role derives from `dependencies/` path spelling, so cross-directory byte-preserving renames change observable ownership; unknown-selector behavior is also uncommitted TDD debt |
| J2-F4 ownership/totality successor controls | original bounded contract owner; depends on J2-R1; exclusive `tests/journeys/test_j2_package_registration.py` | complete checkpoint: 19 candidate tests yield 18 passes and exactly one ownership failure; stable no-I/O unknown selector is green and retained as earlier TDD debt |
| J2-I2 registration ownership successor | Claude Sonnet 5 package-registration integrator; depends on J2-F4; isolated registration-only scope | complete checkpoint: within-theory cross-directory roles are address-stable and all 62 controls pass; retained candidate pending successor review |
| J2-R2 registration successor review | independent read-only product reviewer; depends on J2-I2 | BLOCK: within-root role leak closes, but combined allowlist accepts exact theory records moved into package root and package records moved into theory root, silently changing owner |
| J2-F5 cross-root ownership controls | original bounded contract owner; depends on J2-R2; same registration test scope | complete red checkpoint: one consolidated control rejects all 26 exact cross-root moves; prior 19 controls remain green and candidate has exactly one failure |
| J2-F5R explanatory-ownership tightening | original bounded contract owner; depends on J2-F5; same test scope | complete: all 26 misplaced records must retain their original address-owned role in the explanatory inventory; candidate remains exactly one red control |
| J2-I3 root-scoped registration successor | Claude Sonnet 5 package-registration integrator; depends on J2-F5R; isolated registration-only scope | complete checkpoint: separate root predicates produce exact missing/unexpected diagnostics for all 26 moves, but explanatory roles remain relabeled by observed root |
| J2-I4 explanatory-role successor | Claude Sonnet 5 package-registration integrator; depends on J2-I3/F5R; same isolated scope | complete: roles derive from accepted address ownership while root-scoped validity remains separate; all 20 registration controls pass |
| J2-R3 final registration review | independent read-only product reviewer; depends on J2-I4 | PASS: 63/63 registration/helper/J1 controls and an independent 26-move matrix replay; root validity, address ownership, phase barriers, and no-execution boundary hold |
| J2-E1 package Evidence reproduction | independent Evidence reviewer; depends on J2-I4/R3 and accepted W4 gate | PASS: exact 18-record curated/W4 byte bridge, 18/18 candidate controls, two fresh matching reports, and eight declaration-scoped Evidence bindings reproduce in the pinned environment |
| J2-G package registration | lead acceptance; depends on J2-R3/J2-E1 and full gate | accepted: both independent nine-record packages register with the four-record theory set; full locked gate passes, no performance Evidence or assurance is manufactured, and J3 is released |
| J3-P0 graph-authority preflight | internal GPT-5 read-only concern owner plus Claude Fable 5 read-only challenger; depends on J2-G | BLOCK current 22-record framing: manifest authority converges, but separately reviewed ConsumerPolicy and importing Specification are absent; releases J3-D0 only |
| J3-D0 manifest/consumer-authority design | lead design integrator; depends on J3-P0; exclusive ADR 0012, journey/system-map status, and this plan | retained checkpoint: proposed one-manifest authority and 24-record graph, but J3-DR0 found importer-authority, role-projection, schema, query-input, and cache/failure ambiguities |
| J3-DR0 manifest-design review | independent read-only graph/authority reviewer; depends on J3-D0 | BLOCK: Specification authorship moved to the theory consumer, canonical role/source constraints and J1 projection were absent, imports-only content is schema-invalid, and query/snapshot behavior was under-specified |
| J3-D1 manifest-authority successor | lead design integrator; depends on J3-DR0; same design surfaces | implementation checkpoint: importer returns to theory-author authority with meaningful content; canonical role/source constraints and legacy J1 view are explicit; manifest-first uncached snapshots and exact J4 selectors are frozen in intent |
| J3-DR1 manifest-design successor review | independent read-only graph/authority reviewer; depends on J3-D1 | BLOCK narrowly: mechanical DR0 issues close, but two phrases still misassign the importer to consumer authority and treat actor selectors as graph-derived inputs |
| J3-D2 authority/query wording successor | lead design integrator; depends on J3-DR1; same design surfaces | implementation checkpoint: policy and importer nodes are explicitly package-consumer versus theory-author owned; only canonical record bytes derive from the graph while exact selectors remain actor inputs |
| J3-DR2 final manifest-design review | independent read-only graph/authority reviewer; depends on J3-D2 | PASS: both DR1 authority phrases close, all DR0 boundaries remain intact, diff check passes, and the immediately preceding replay retained 63/63 J1/J2/helper controls; releases J3-C1/T1 |
| J3-C1 ConsumerPolicy candidate | package-consumer concern owner; depends on accepted J3-DR2; exclusive `registry/stack/consumers/package/**` | complete candidate: exact Stack/profile, required W4 mechanisms, optional unsupported performance, and `io.*` prohibition form a graph-valid 24-record union; retained pending review disposition |
| J3-T1 importing-Specification candidate | theory-author composition concern owner; depends on accepted J3-DR2; exclusive `registry/stack/compositions/theory/**` | PASS in J3-CR1 and diverse review: meaningful `UndoHistory` carrier plus exact Stack import is current-schema valid, graph-valid, and adds no namespace/refinement/compatibility semantics |
| J3-CR1 consumer-record review | independent internal policy/import reviewer; depends on J3-C1/T1 | mixed: J3-T1 PASS; J3-C1 BLOCK because empty/omitted mechanism meaning and `adapter-invocation-trace` Evidence matching were not normatively machine-bound |
| J3-CR1D diverse semantic challenge | Claude Fable 5 high-effort read-only reviewer; depends on J3-C1/T1 | PASS both with gates: importer is the smallest honest edge; policy bytes are defensible, but empty-mechanism uniqueness is refuted and durable empty/omitted plus J4P falsifiers are required |
| J3-C2 policy mechanism/scope design | lead design integrator; depends on J3-CR1/CR1D; exclusive ADR 0013, core/evidence model, and this plan | implementation checkpoint: fail-closed mechanism-set semantics and exact W4 adapter-trace classification proposed; performance successor accepts permitted proof methods while remaining unsupported |
| J3-C2R policy-semantics review | independent read-only policy/Evidence reviewer; depends on J3-C2 | BLOCK: mechanism-set semantics and outcome-independent proof route pass, but scope depended on external W4 gate state and minimum assurance remained opaque English |
| J3-C2S graph-only policy-semantics successor | lead design integrator; depends on J3-C2R; same design surfaces | implementation checkpoint: scope classifier uses only canonical proposition/profile/adapter/mechanism/declaration/plan fields; W4 reproduction returns to release evidence; exact per-declaration assurance token prevents missing-Claim vacuity |
| J3-C2SR policy-semantics successor review | independent read-only policy/Evidence reviewer; depends on J3-C2S | BLOCK narrowly: graph-only scope/plan trust and assurance algorithm pass, but optional-performance token coverage contradicted prose and profile applicability leaked into scope classification |
| J3-C2SS policy-axis wording successor | lead design integrator; depends on J3-C2SR; same design surfaces | implementation checkpoint: every non-ignored concern states the token; absent/unknown assurance fails closed; scope binds coherent Claim/Evidence profiles while actor comparison stays applicability; all matching Claims/Evidence prevent challenge cherry-pick |
| J3-C2SSR final policy-semantics review | independent read-only policy/Evidence reviewer; depends on J3-C2SS | BLOCK status-only: all semantic axes pass, but ADR status still named rejected C2S/C2SR rather than current C2SS/final review |
| J3-C2ST policy-status successor | lead documentation integrator; depends on J3-C2SSR; ADR status only | complete checkpoint: proposal lineage names C2SS and acceptance points prospectively to C2STR; no semantic criterion changes |
| J3-C2STR policy-status review | independent read-only policy/Evidence reviewer; depends on J3-C2ST | PASS: ADR/plan lineage is truthful, all graph-only scope and policy-axis semantics remain green, and diff check passes; releases J3-C3 |
| J3-C3 ConsumerPolicy successor | package-consumer concern owner; depends on accepted J3-C2STR; same exclusive record path | complete: SHA `f814cf6…`; performance accepts Specification-permitted proof/proof-audit, every non-ignored concern uses the exact assurance token, and all concern/profile/campaign/prohibition bindings remain exact |
| J3-C3R final ConsumerPolicy review | independent read-only policy reviewer; depends on J3-C3 | PASS: exact 24-record graph has zero diagnostics; both candidate Evidence sets, graph-only effect scope, optional unsupported performance, proof non-substitution, token/status lineage, and fixture exclusion replay |
| J3-F1 manifest/graph falsifiers | bounded contract owner; depends on accepted J3-C3R and J3-T1; exclusive `tests/journeys/test_j3_*` | complete red predecessor: 18 tests yielded one exact 24-record/zero-link precondition pass, one missing-`semantic_packages.graph` failure, and 16 successor skips |
| J3-F1R graph-control review | internal read-only preflight plus lead artifact audit; depends on J3-F1 | BLOCK: exact oracle and graph/resolver separation passed, but the draft demanded hidden role/source oracles contrary to manifest authority, patched one private helper instead of observable no-I/O, and omitted shape, internal-symlink, schema/link-phase attacks; an external Fable artifact review was started but stopped without output when the user replaced micro-node dispatch with the journey-continuity canary |
| J3-F2 graph-control successor | journey continuity owner; depends on J3-F1R; same test scope | complete red successor: 22 tests yielded one precondition pass, one missing-module failure, and 20 skips; allowed manifest role changes are live, source moves use missing/unexpected membership, observable no-I/O and no-follow boundaries plus manifest/record/link phases are frozen |
| J3-I1 manifest and graph assembly | journey continuity owner; depends on J3-F2; exclusive `registry/stack/manifest.json`, manifest schema, `semantic_packages/graph.py` | complete: one explicit five-source manifest assembles deterministic per-call snapshots, returns only manifest/input/schema/link/membership phase conclusions, and all 22 J3 controls pass without resolver or execution behavior |
| J3-M1 J1/J2 derivation migration | same journey continuity owner; depends on J3-I1; exclusive `semantic_packages/publication.py` and `semantic_packages/registration.py` | complete: both views derive selection, digest, and roles from a manifest-only projection; no canonical address/digest literals remain in either module; J1 24/24 and J2 39/39 remain green |
| J3-R1 graph/provenance convergence | lead deterministic audit plus persistent Fable 5 product-advisor challenge; depends on J3-M1 | PASS: all 22 J3 attacks, retained 63 J1/J2 controls, zero product-map census, graph/resolver separation, and no-execution boundary replay; advisor independently spot-checked the manifest and migrated modules, found no J4 blocker, and requested one bounded post-gate trust-boundary falsification pass |
| J3-E1 graph Evidence reproduction | locked repository gate; depends on J3-R1 | PASS: exact 24-record graph, 85 actor journeys, two fresh W4 reports/eight Evidence records, and 49 proof contract groups reproduce; graph validity remains distinct from Evidence and assurance |
| J3-G honest graph | lead acceptance; depends on J3-R1/E1 and strategic advisor checkpoint | accepted predecessor then reopened by J3-R2's two concrete authority escapes; J3-F3/I2/E2 are green and successor reacceptance awaits bounded J3-R3 confirmation before J4P implementation |
| J3-R2 bounded post-gate falsification | persistent read-only Fable 5 advisor; depends on J3-G; nonblocking support/challenge edge to J4P | BLOCK: slash-bearing source IDs spoof source attribution through logical-path prefix parsing, and J1/J2 derived invalid members while discarding cached manifest diagnostics; other no-follow, phase, snapshot, no-execution, digest, and second-selector attacks held |
| J3-F3 authority-escape successor controls | journey continuity owner; depends on J3-R2; exclusive J3 tests | complete red: a slash source ID with every member reference coherently updated escaped the manifest phase, and both legacy views observed nonexistent roots instead of returning an injected duplicate-member manifest diagnostic |
| J3-I2 fail-closed authority successor | journey continuity owner; depends on J3-F3; exclusive manifest schema, publication, and registration | complete: source IDs are path-segment safe, and both legacy views return cached manifest diagnostics with zero records before selector or root observation; J1 24/24, J2 39/39, and J3 23/23 pass |
| J3-R3 bounded authority successor review | persistent read-only Fable 5 advisor; depends on J3-I2 | PASS against exact commit `64968ad`: slash IDs reject in the manifest phase, the exact legacy-view control proves no root observation, both entry-point gates precede other behavior, and the two R2 counterexamples close without expanding scope |
| J3-E2 successor Evidence reproduction | locked repository gate; depends on J3-I2 | PASS: 86 actor journeys, two fresh W4 reports/eight Evidence records, and 49 proof contract groups reproduce after both authority fixes |
| J3-G2 honest graph successor acceptance | lead acceptance; depends on J3-R3/E2 | accepted: J3 is reclosed with 23/23 controls, all 63 J1/J2 controls, exact advisor provenance, and the full locked gate; J4P is released under the one-owner/advisor canary |
| J4P-F1 package-resolution controls | journey continuity owner; depends on J3-G2; exclusive `tests/journeys/test_j4p_*` | complete intentional red: 11 tests yielded one canonical-graph pass, one missing-resolver failure, and nine successor skips; graph-only exact selectors, canonical/negative semantic outcomes, policy/provenance failures, directional boundary, and no-I/O behavior frozen |
| J4P-I1 bounded resolver checkpoint | same journey continuity owner; depends on J4P-F1; exclusive `semantic_packages/resolver.py` | complete at `1676a5c`: 11/11 J4P and 97/97 actor journeys plus the full locked gate passed; retained predecessor pending advisor challenge |
| J4P-R1 product-outcome falsification | persistent read-only Fable 5 advisor in Herdr; depends on J4P-I1 | BLOCK: accepted inconclusive/error, inapplicable, rejected/unselected, explicit accept-none, absent, and unacceptable-mechanism Evidence collapsed into indistinguishable explanations; zero Specification declarations vacuously satisfied a policy concern |
| J4P-F2 outcome/coverage successor controls | journey continuity owner; depends on J4P-R1; same J4P test scope | complete red: 17 controls produced the expected missing-vocabulary errors and one exact `satisfied`-instead-of-`no-coverage` failure; final 18-control successor also distinguishes empty observation scope and absent Evidence without weakening graph validity |
| J4P-I2 explainable fail-closed successor | journey continuity owner; depends on J4P-F2; resolver, J4P tests, ADR 0013 clarification, and required-file gate | complete at `1435869`: exact Evidence outcome buckets and reason tokens retain every unmet path; zero coverage is visible and blocks only required concerns; profile-set comparison is order-independent; J4P 18/18 and actor journeys 104/104 pass |
| J4P-R2 bounded successor replay | persistent read-only Fable 5 advisor; depends on J4P-I2 | PASS against exact `1435869`: both R1 blockers close, empty/omitted/matching/nonmatching policy cases remain distinct, challenge selection and graph/no-execution boundaries hold, and no introduced material regression is found |
| J4P-E1 resolver Evidence reproduction | locked repository gate; depends on J4P-I2/R2 | PASS: 104 actor journeys, 20 governance checks, two fresh W4 reports/eight Evidence records, and 49 proof contract groups reproduce; resolution does not execute or treat release reproduction as runtime state |
| J4P-G package resolution | lead acceptance; depends on J4P-R2/E1 | accepted: ADR 0013 moves to Accepted at its no-coverage successor revision; both canonical Realizations are explainably acceptable under exact selectors, required failures remain fail-closed, optional performance remains visible/nonblocking, and semantic status stays separate from directional NDJSON composition; releases J4T |
| J4T-F1 theory-projection controls | journey continuity owner after J4P; depends on J3-G2/J4P-G; exclusive `tests/journeys/test_j4t_*` | complete intentional red: 11 tests yielded one two-theory graph pass, one missing-projection failure, and nine successor skips; exact meaning/import/proof/unknown/contradiction, stable-reference, missing-import, scope, and no-I/O outcomes frozen |
| J4T-I1 exact theory projection | same journey continuity owner; depends on J4T-F1; exclusive `semantic_packages/theory_projection.py` plus required-file gate | complete at `f9f5f62`: exact declaration content and stable IDs, separate import edges, specification-scoped Claim/Evidence qualifications, contradictions, and unknowns derive from one graph snapshot without assurance or composition inference; J4T 11/11 and actor journeys 115/115 pass |
| J4T-R1 product-outcome falsification | persistent read-only Fable 5 advisor in Herdr; depends on J4T-I1 | PASS against exact `f9f5f62`: assurance language, cross-scope leakage, category collisions, import completeness, position independence, contradictions/unknowns, selectors, invalid graph, and purity hold; dead always-true import availability flag plus rejected/error/snapshot control top-ups are deferred to J5 |
| J4T-E1 projection Evidence reproduction | locked repository gate; depends on J4T-I1/R1 | PASS: 115 actor journeys, 20 governance checks, two fresh W4 reports/eight Evidence records, and 49 proof contract groups reproduce; projection does not execute proof or realization artifacts |
| J4T-G theory projection | lead acceptance; depends on J4T-R1/E1 | accepted: Stack meaning/proof/unknowns and UndoHistory's exact Stack import are browsable without namespace merge, acquisition, compatibility, refinement, lineage, policy, or assurance inference; all four actor terminal outcomes are now executable and J5 is released |
| J5-D0 successor-source authority | journey continuity owner; depends on J4P-G/J4T-G; exclusive ADR 0014 and this plan | proposed: immutable predecessor manifest/bytes plus an explicit append-only successor manifest sharing roots, actor-owned successor packets, exact nonselection as bounded staleness, no overlay/latest/freshness engine; releases falsifiers only, not records |
| J5-DR0 successor-authority consultation | persistent read-only Fable 5 advisor in Herdr; depends on J5-D0 candidate | PASS design with required field-identical predecessor-source/member invariant, red-first census successor, seven-record/no-Evidence inventory, profile 0.1.0 reuse, ADR 0014, and stop on any predecessor/default/migration/evidence-authority escape |
| J5-F0 Evidence-migration preflight | journey continuity owner; depends on J5-DR0; exclusive J5 tests | complete before product records: a temporary coherent 0.2.0 Specification/Realization/Claim plus re-pointed accepted 0.1.0 Evidence is rejected by exact `LINK_EVIDENCE_SPECIFICATION_MISMATCH` and `LINK_EVIDENCE_REALIZATION_MISMATCH` diagnostics before membership or resolution; central nonmigration boundary holds |
| J5-F1 successor/recovery controls | journey continuity owner; depends on J5-F0; exclusive J5 tests and reviewed successors to frozen census controls | complete intentional red: 12 J5 tests yield migration/predecessor passes, exactly two missing successor-manifest/maintenance failures, and eight successor skips; cross-manifest mutation, exact seven-record inventory, same-world recovery, no Evidence lineage/latest, projection, lifecycle separation, and no-I/O outcomes frozen before records/code |
| J5-I1 successor snapshot and recovery | journey continuity owner; depends on J5-F1; exclusive `registry/stack/successors/**`, `registry/stack/successor-manifest.json`, `semantic_packages/maintenance.py` | complete checkpoint: seven actor-owned 0.2.0 records and zero Evidence extend the immutable 24-member predecessor to an explicit 31-member snapshot; exact comparison plus existing resolver/projection retain nine stale predecessor Evidence records, expose the unsupported successor, and recover both acceptable predecessor Realizations without automatic selection, execution, lineage, or freshness inference; J5 12/12 passes |
| J5-R1/G maintenance convergence | persistent read-only Fable 5 advisor plus lead acceptance; depends on J5-I1 and locked gate | accepted: advisor PASS against exact `56c4114` closes all ten falsification targets without a specialist escalation; 127 actor journeys, 20 governance checks, two fresh W4 reports/eight Evidence records, and 49 proof groups pass; ADR 0014 is Accepted, failed successor and nine stale predecessor Evidence remain visible, and JG is released subject to PR-G and fresh-checkout convergence |
| PR-GP0 governance preflight | independent read-only concern owner; depends on J0-G | complete: range-scoped Conventional Commit/PR-body policy, red matrix, locked-Nix CI route, security boundary, and operator-only remote convergence |
| PR-GF1 governance controls | bounded fixture owner; depends on PR-GP0; exclusive `fixtures/governance/**`, `tests/governance/**` | complete red checkpoint: 3 valid/8 rejected commit and 1 valid/9 rejected PR cases; 7 tests yield one missing-checker failure and six successor skips; all fixtures parse and diff check passes |
| PR-GF1R control review | fresh independent governance reviewer; depends on PR-GF1 | BLOCK: base-range and real-merge controls are non-decisive; 72/title parity, malformed events, adversarial Markdown, education/template binding, and exact CLI stderr are incomplete |
| PR-GF2 governance-control successor | original bounded fixture owner; depends on PR-GF1R; same exclusive fixture/test scope | complete red successor: 14 tests yield one missing-checker failure/13 skips; legacy-base/real-merge range, 72/title parity, total event/Markdown parsing, education/template parity, and exact clean CLI diagnostics are frozen |
| PR-GF2R successor control review | fresh independent governance reviewer; depends on PR-GF2 | BLOCK: most GF1R gaps close, but ranges can validate only HEAD or use triple-dot, malformed nonobject envelopes can crash, and near-miss/indented headings can satisfy loose parsing |
| PR-GF3 total-range/parser successor | original bounded fixture owner; depends on PR-GF2R; same exclusive fixture/test scope | complete red successor: 15 tests yield one missing-checker failure/14 skips; invalid non-HEAD ordering, divergent two-dot range, total envelope shapes, and exact top-level heading near misses are frozen |
| PR-GF3R final control review | fresh independent governance reviewer; depends on PR-GF3 | BLOCK: all prior range/parser gaps close, but empty/whitespace commit and PR-title descriptions remain accepted by the frozen grammar |
| PR-GF4 description successor | original bounded fixture owner; depends on PR-GF3R; same exclusive fixture/test scope | complete red successor: empty and whitespace-only descriptions reject symmetrically for commits/PR titles; 15 tests retain one missing-checker failure/14 skips |
| PR-GF4R final governance-control review | fresh independent governance reviewer; depends on PR-GF4 | BLOCK: description cases close, but present empty/whitespace scopes can pass a permissive optional-scope regex |
| PR-GF5 scope successor | original bounded fixture owner; depends on PR-GF4R; same exclusive fixture/test scope | complete red successor: empty/whitespace scopes reject for commits and PR titles; 15 tests retain one missing-checker failure/14 skips |
| PR-GF5R final governance-control review | fresh independent governance reviewer; depends on PR-GF5 | BLOCK: grammar/range/parser blockers close, but only three of eleven declared allowed types have positive commit/title coverage, permitting an over-restrictive checker |
| PR-GF6 finite-type successor | original bounded fixture owner; depends on PR-GF5R; same exclusive fixture/test scope | complete red successor: exact positive commit/title coverage for all and only eleven declared types; 15 tests retain one missing-checker failure/14 skips |
| PR-GF6R final governance-control review | fresh independent governance reviewer; depends on PR-GF6 | PASS: all GF1R–GF5R blockers replay closed; further spelling/scope enumeration would expand rather than test accepted policy; PR-GI1 released |
| PR-GI1 metadata implementation | internal fallback implementation owner; depends on accepted PR-GF6R; isolated `/tmp/semantic-packages-pr-gi1`, exclusive `scripts/check_change_metadata.py`, `.github/pull_request_template.md`; lead integrates shared docs/gates | complete: 14/15 frozen tests pass; only the lead-owned guidance anchor remains red |
| PR-GI1R metadata implementation review | independent read-only governance reviewer; depends on PR-GI1 | BLOCK: fenced comment syntax can poison parser state, multiple placeholder-only lines/headings pass as substance, and non-UTF-8 events leak a traceback |
| PR-GF7 parser-totality successor | lead-owned contract integration; depends on PR-GI1R; exclusive `tests/governance/**` | complete: the three review attacks are frozen; successor suite totals 18 tests |
| PR-GI2 metadata successor | internal implementation owner; depends on PR-GF7; isolated `scripts/check_change_metadata.py` scope | complete: all GF7 attacks and the original 18-test integration suite pass |
| PR-GI2R metadata successor review | independent read-only governance reviewer; depends on PR-GI2 | BLOCK: comment deletion can manufacture headings, invalid fences can hide duplicates, syntax-only content passes as substance, and non-UTF-8 Git subjects leak a traceback |
| PR-GF8 rendered-substance/UTF-8 successor | lead-owned contract integration; depends on PR-GI2R; exclusive `tests/governance/**` | complete red checkpoint: exact comment/fence/heading/wrapper/entity/link/reference and raw-Git-byte attacks fail without disturbing prior controls |
| PR-GI3 metadata totality successor | internal implementation owner; depends on PR-GF8; isolated `scripts/check_change_metadata.py` scope | complete: bounded rendered-substance normalization, valid-fence recognition, column-preserving comments, and per-commit byte decoding make all 19 integrated tests pass |
| PR-GI3R metadata successor review | independent read-only governance reviewer; depends on PR-GI3 | BLOCK: prior attacks close, but Unicode-only prose and literal inline code reject while Setext-only and multiline link-reference syntax pass as substance |
| PR-GF9 adjacent Markdown successor | lead-owned contract integration; depends on PR-GI3R; exclusive `tests/governance/**` | complete red checkpoint: two positive rendered-content and two negative syntax-only cases are frozen |
| PR-GI4 metadata rendering successor | internal implementation owner; depends on PR-GF9; isolated `scripts/check_change_metadata.py` scope | complete: Unicode-aware normalized prose, bounded inline-code preservation, Setext removal, and multiline reference normalization make all 20 integrated controls pass |
| PR-GI4R metadata successor review | independent read-only governance reviewer; depends on PR-GI4 | BLOCK: all earlier gaps close, but inline-code wrapping makes placeholder-only `TBD`/`TODO` count as substance |
| PR-GF10 inline-placeholder successor | lead-owned contract integration; depends on PR-GI4R; exclusive `tests/governance/**` | complete red checkpoint: single- and multi-backtick placeholder-only spans reject while literal code remains positive |
| PR-GI5 metadata placeholder successor | internal implementation owner; depends on PR-GF10; isolated `scripts/check_change_metadata.py` scope | complete: normalized inline-code literals now share Unicode placeholder evaluation and all 20 controls pass |
| PR-GI5R final metadata review | independent read-only governance reviewer; depends on PR-GI5 | PASS: inline placeholders reject while real/Unicode code and all prior grammar/range/parser/UTF-8/template/security controls remain green; releases PR-GT1 |
| PR-GT1 hosted toolchain | single CI/toolchain integrator; depends on PR-GI5R; exclusive `flake.nix`, `flake.lock`, `.github/workflows/quality-gates.yml` | BLOCK: first locked draft passes its toolchain check but nixpkgs `a418a0f…` supplies glibc 2.42-67 and changes four accepted Wave 4 Rust binary digests; draft remains uncommitted and unreleased |
| PR-GT2 GCC provenance successor | independent read-only provenance researcher plus lead toolchain integrator; depends on PR-GT1; same exclusive integration surface | complete: signed release pin `e8210c6…`, `mkShellNoCC`, and explicit wrapper-variable clearing reproduce accepted GCC/glibc closure and Rust binary SHA `55f234bd…` |
| PR-GR1 CI/security review | independent read-only reviewer; depends on PR-GT1 | BLOCK: all tool/lock/fork/permission/evidence boundaries pass except privileged installer selection used mutable `source-tag: v3.21.7`; exact signed commit successor required |
| PR-GT3 installer immutability successor | lead CI integrator; depends on PR-GR1; same exclusive CI surface | complete checkpoint: exact signed revision closes mutable tag; actionlint/flake pass and full gate has only registration red |
| PR-GR2 CI/security successor review | independent read-only reviewer; depends on PR-GT3 | BLOCK: pinned action still sends correlated runner identity on an unconditional check-in/artifact request despite disabled diagnostics; zero-telemetry claim remains false |
| PR-GT4 uncorrelated installer successor | lead CI integrator; depends on PR-GR2; same exclusive CI surface | complete checkpoint: installer action removed; official v3.21.7 release binary fixed at SHA-256 `dce336…`; action-level correlation eliminated |
| PR-GR3 direct-installer security review | independent read-only reviewer; depends on PR-GT4 | BLOCK: action correlation is gone, but installer client telemetry remains enabled unless its separate hard kill-switch survives root execution |
| PR-GT5 installer telemetry successor | lead CI integrator; depends on PR-GR3; same exclusive CI surface | complete: `DETSYS_IDS_TELEMETRY=disabled` is constructed inside both privileged child environments; empty diagnostic endpoint retained as defense-in-depth |
| PR-GR4 final CI/security review | independent read-only reviewer; depends on PR-GT5 | PASS: fixed hash fails closed before privilege, action and installer transports are no-op, and all lock/tool/evidence/fork/permission/range/shell boundaries replay |
| PR-GO operator convergence | operator; depends on accepted PR-GR4 | complete hosted-policy checkpoint on 2026-07-19 after explicit user authorization: original 59-commit DAG branch retained, clean `agent/actor-complete-tracer` branch prepared from `master` as one conventional squash, merge/rebase disabled, squash PR-title/PR-body defaults enabled, Actions SHA pinning required, and active no-bypass ruleset `19155146` requires PR-only squash, linear history, no deletion/force-push, resolved conversations, and strict `prospective metadata` plus `repository contract` checks; advisory app permissions remain unchanged pending observable PR activity |
| PR-GG release-governance gate | lead acceptance; depends on PR-GR4, PR-GO, local/hosted gates | accepted hosted checkpoint on draft PR 4: initial `3bb74fe` and status successor `c24f355` both pass; latest `prospective metadata` is 1m33s and `repository contract` 2m42s, active ruleset `19155146` reports no bypass, and the PR is CLEAN. One synchronize run cancelled when the PR-body edit superseded it and contributes no failure evidence; CodeRabbit/Claude produced no observable review while draft and remain advisory |
| JG-R1 independent fresh-clone review | independent internal reviewer; depends on PR-GG/J5 and exact published `3bb74fe`; read-only `/tmp/semantic-packages-pr4-fresh` | BLOCK despite exact checkout, clean tree, sole Conventional Commit, prospective range, full 127-journey/20-governance/2-report/8-Evidence/49-proof gate, and diff hygiene passing: stale system-map and user-journey status prose contradicted accepted executable J2–J5 state |
| JG-S1 status-memory successor | journey continuity owner; depends on JG-R1; exclusive system map, user journeys, and this plan | implementation checkpoint: stale “next/designed/open” claims now state J1–J5 executable while keeping hosted release and cold-human acceptance open; rejected JG-R1 retained rather than relabeled |
| JG-R2 fresh-clone successor review | same independent internal reviewer; depends on JG-S1 and republished exact `c24f355` | PASS: exact published checkout and origin, clean tree, two linear Conventional Commits, prospective range, diff hygiene, 127 journeys, 20 governance checks, two fresh reports/eight Evidence records, and 49 proof groups reproduce; JG-R1 remains retained, status contradictions close, hosted/automatic exclusions hold, and the cold-human recommendation remains explicitly unobserved |
| JG journey release | lead acceptance; depends on JG-R2 plus J5 and PR-GG; read-only fresh-checkout acceptance with no repository write scope and ephemeral outputs only under an allocated temporary directory | all four terminal outcomes and bounded maintenance reproduce without hosted/automatic overclaim; cold human journey remains a pre-merge recommendation; pending |

Parallel work is read-only or owns non-overlapping paths. From J3-F2 onward, the user
authorized a bounded process canary for this small repository: one continuity owner
carries each actor journey end to end, persists a high-level checkpoint between
journeys, and consults one persistent read-only Fable 5 product advisor asynchronously
through an observable Herdr tab. J4P precedes J4T in that canary even though the product
DAG permits parallelism. Specialist agents remain available for a demonstrated
material boundary; they are not the default micro-node owner. The hypothesis is that
continuity reduces dispatch/reconciliation latency without weakening deterministic
gates or protected intent. Revert to bounded multi-owner delegation if context
saturation, shared-surface mistakes, missed concerns, or advisor dependence becomes
observable. The advisor contributes `supports`/`challenges` evidence and cannot ratify
the lead's work. Every actual delegated brief still supplies the full contract required
by `AGENTS.md`; cross-provider launches use `agent-dispatch`, and model identity grants
neither authority nor assurance.

Every J1–J5 handoff packet retains governing revisions, exact commands and inputs,
expected and observed positive/negative results, changed paths, tool provenance,
assumptions, exclusions, failed attempts, reviewer disposition, recovery path, and
reopen triggers. The lead is escalation owner for ordinary boundary conflicts; the
user is escalation owner for protected intent, success weakening, or irreversible
product-policy changes.

## Implementation order and decisive falsifiers

1. Freeze J0 terminology and lifecycle. Refute any wording that equates local loading
   with hosted publication, graph validity with assurance, or a phase list with a
   mandatory waterfall.
2. Create a curated product source set. First prove that pointing the product command
   at the existing mixed fixture tree exposes obsolete fixture-only support.
3. Add bounded publication/registration commands or manifest semantics without
   acquisition or automatic execution.
4. Build the smallest resolver over the curated graph. Start with fixtures where
   operational composition must lose to semantic policy and where semantic acceptance
   needs a non-direct boundary.
5. Build the smallest derived theory projection. Start with an exact missing import and
   an unknown performance concern that must remain visible.
6. Publish one exact successor and deliberately fail its evidence refresh. Require the
   old acceptable version and the failure explanation to remain available.
7. Converge hosted and local release gates without allowing advisory model review to
   replace deterministic checks.

## Quality gates and required evidence

The planned scenario commands are stable acceptance entrypoints; their implementation
may be the smallest local test/CLI projection and must not become a universal transport:

| Node | Command | Expected observation |
|---|---|---|
| J0 | `python3 scripts/check_repo.py` | repository gate passes and the independent J0 successor review reports no material status/authority contradiction |
| J1 | `python3 -m unittest discover -s tests/journeys -p 'test_j1_*.py' -v` | valid theory records publish to the curated source set; malformed, duplicate, dangling, or wrong-version attempts fail stably; proof reproduces |
| J2 | `python3 -m unittest discover -s tests/journeys -p 'test_j2_*.py' -v` | both independent packages register with reproducible declaration Evidence; breaker outcomes and unknown performance remain honest |
| J3 | `python3 -m unittest discover -s tests/journeys -p 'test_j3_*.py' -v` | one curated graph validates, history fixtures are absent, canonical record bytes originate only in its manifest, and actor-supplied exact selectors remain explicit |
| J4P | `python3 -m unittest discover -s tests/journeys -p 'test_j4p_*.py' -v` | required concern outcomes, semantic decision, and directional boundary explanation match the policy/profile controls |
| J4T | `python3 -m unittest discover -s tests/journeys -p 'test_j4t_*.py' -v` | theory projection exposes exact meaning/evidence/imports/unknowns and rejects the missing import without inferred composition |
| J5 | `python3 -m unittest discover -s tests/journeys -p 'test_j5_*.py' -v` | predecessor remains usable, stale Evidence cannot migrate silently, failed successor and recovery explanation remain visible |
| PR-G | `python3 -m unittest discover -s tests/governance -v`; `gh api repos/phibkro/semantic-packages --jq '{allow_merge_commit,allow_rebase_merge,allow_squash_merge}'`; `gh api repos/phibkro/semantic-packages/rulesets` | local controls teach and reject nonconventional commits/PR titles and incomplete PR descriptions; hosted settings expose squash-only merge and required deterministic checks; authentication/app changes remain operator actions |
| JG | `python3 scripts/check_repo.py` plus the documented clean-environment workflow | local and hosted gates run every journey and retain exact release evidence |

- **J0:** Markdown links, repository structural checks, independent semantic/governance
  review, and explicit implemented/designed/planned labels.
- **J1–J3:** exact schema/link diagnostics, source-set provenance, proof/campaign
  reproduction, broken publication/registration controls, and graph derivation.
- **J4P:** per-concern selected Evidence, visible unsupported/contested/inapplicable
  outcomes, semantic verdict, and separate directional boundary result.
- **J4T:** stable exact references, proof/unknown/exclusion projection, exact import and
  failure behavior, and no inferred composition semantics.
- **J5:** immutable predecessor, stale-input rejection, retained failure and
  contradiction, lifecycle/result separation, and recovery explanation.
- **JG:** `python3 scripts/check_repo.py`, the documented fresh-clone route, hosted
  required checks, and actor-journey scenario packets all pass.

## Progress

- [x] W4 independent Realizations and declaration-scoped Evidence
- [x] Four-actor research audit
- [x] Scaled lifecycle consultation and ADR draft
- [x] System-plane/trust-boundary audit and map draft
- [x] Actor journey contract draft
- [x] J0-R1 independent convergence review rejected with five retained blockers
- [x] J0-R2 successor review rejected with two retained blockers
- [x] J0-R3 successor-history review rejected with one retained blocker
- [x] J0-R4 final successor convergence review
- [x] J0 repository gate and acceptance
- [x] J1-P0 theory-publication preflight
- [x] J1-F1 publication falsifier checkpoint and review
- [x] J1 theory-author local publication
- [x] J2 package-author registration in curated graph
- [x] J3 honest product graph
- [x] J4P package-consumer resolver
- [x] J4T theory-consumer projection/import
- [x] J5 successor/staleness recovery
- [x] PR-GP0 release-governance preflight
- [x] PR-GF1 governance falsifier checkpoint and review
- [x] PR/release governance convergence
- [ ] JG journey-complete release

## Discoveries and changed assumptions

- The package-author path is the strongest current journey; package and theory
  consumption are absent product edges rather than documentation gaps.
- The current valid fixture tree mixes product-capable records with historical
  validation data and cannot itself be called the curated registry.
- The current loader is deterministic local discovery, not publication or acquisition.
- Wave 4 Evidence binding is strong but tracer-specific; it is not the future general
  policy resolver.
- J1 preflight fixes the smallest theory set at the Stack Specification,
  specification-scoped `pop-empty` Claim/Evidence, and one supplied profile dependency.
  The profile is required by exact performance-vocabulary references but remains
  consumer-owned rather than a theory-author policy selection.
- The accepted proof manifest still binds fixture paths. J1 must exact-bind curated
  copies byte-for-byte to those inputs while proof execution remains explicit; moving
  proof provenance is a later cross-boundary successor, not a silent J1 rewrite.
- J2 preflight found that each independent package is exactly nine accepted W4 records
  and that each 13-record union with the accepted theory root is graph-valid with zero
  diagnostics. The records can remain byte-identical; rewriting fixture-backed
  provenance would unnecessarily reopen W4. J2 registration inspection stays
  non-executing and composes with, but never substitutes for, the explicit Wave 4
  candidate and Evidence-reproduction gate.
- A second copy of J1's private loader/no-follow logic would create a drift-prone
  filesystem boundary. J2 therefore introduces a separately reviewed internal
  finite-source extraction node, replaying all 24 J1 controls, while publication and
  registration inventories/roles/diagnostics remain Stack-specific.
- J2-SR1 found that green focused controls had not carried forward two ADR-0007
  invariants: Linux `/path` and `//path` aliases must be idempotent, and a requested
  root beneath a symlinked ancestor must reject before target traversal. J2-SF3/SI2
  retain the failed extraction checkpoint and add refute-first successor controls.
- J2-R1 found a separate representation leak after the first Claude registration
  candidate made 60/60 focused tests pass: deriving owner role from the literal
  `dependencies/` subdirectory lets a byte-identical rename change ownership while
  registration stays valid. J2-F4 freezes address-stable roles; the exact digest maps
  remain bounded tracer gate predicates until J3 supplies one canonical manifest.
- J2-R2 found that combining theory and package allowlists erased source-root
  ownership: all 26 exact records could cross the theory/package boundary while
  remaining silently accepted. The final boundary therefore uses root-scoped
  predicates for validity and address-scoped predicates only for explanatory
  authorship. Misplaced exact records retain their original role while producing both
  missing-from-owner and unexpected-in-observed-root diagnostics.
- J2-E1 re-established the distinction between registration and Evidence after the
  non-executing inspector passed: all 18 package records bridge byte-for-byte to W4,
  both language campaigns reproduced fresh committed reports, and all eight
  declaration-scoped Evidence records rebound their Claim, Realization, profile,
  toolchain, assumptions, exclusions, result, and independent review. Neither a green
  registration nor a green report is itself Evidence, and no performance or assurance
  conclusion was created.
- J3-P0's diverse consultations agreed that the manifest must own membership, exact
  digest, source ownership, and explicit role while records retain semantic identity
  and content; source roots are explicit but per-member filenames remain provenance.
  Claude Fable 5 recommended deferring policy to J4P, while the internal consumer audit
  found that doing so would make J4P mutate or bypass J3 and that J4T also lacks its
  required importing Specification. The lead retains the stronger objection: J3 grows
  from the accepted 22 records to 24 through a reviewed package-consumer policy node
  and theory-author composition node; the graph integrator cannot invent either artifact.
- J3-DR0 retained the 24-record direction but blocked the first design draft: it had
  silently moved Specification authorship to the theory consumer, left canonical
  role/source constraints and J1's legacy role view undefined, proposed content that
  the current Specification schema rejects, and under-specified exact J4 selectors and
  manifest snapshot failure behavior. J3-D1 returns composition semantics to a theory
  author, forbids schema weakening/empty-array loopholes, defines four canonical roles
  plus source constraints and one explicit legacy view, and makes manifest-first
  per-call graph snapshots distinct from the shared immutable J1/J2 projection.
- J3-DR1 found the D1 mechanics implementation-ready but retained two authority phrases:
  the importer was still collectively labeled consumer-owned, and graph derivation was
  still stated as covering actor query selectors. J3-D2 narrows these without changing
  the design: only the policy is package-consumer-authored, the importer is
  theory-author-authored, canonical record bytes come only from the graph, and actors
  explicitly choose exact policy/profile/Specification addresses.
- J3-CR1 and the diverse Fable challenge both accepted the `UndoHistory` import edge,
  but disagreed on whether the first policy bytes could pass before J4P. The internal
  reviewer retained the stronger machine-readability objection: empty mechanism meaning
  and adapter-trace scope were not yet normative, graph validity accepted invented
  tokens, and minimum assurance was opaque prose. Fable refuted only the claimed
  uniqueness of empty mechanisms and required durable semantics/falsifiers. J3-C2
  therefore became a design successor rather than retroactively passing C1.
- J3-C2R accepted fail-closed empty/omitted semantics and a future-facing performance
  proof policy, then blocked hidden reliance on a previously executed W4 gate and
  missing-Claim-vacuous assurance prose. J3-C2S classifies scope only from canonical
  semantic/provenance fields plus the governed plan contract, keeps review/result as
  separate selection axes, returns W4 reproduction to release Evidence, and defines one
  exact per-declaration threshold token.
- J3-C2SR accepted that graph-only trust correction and the exact plan selector, then
  retained two cross-axis wording defects: optional performance lacked the otherwise
  required assurance token, and actor-profile applicability appeared inside scope
  classification. J3-C2SS makes every non-ignored assurance threshold explicit and
  fail-closed, defers actor-profile comparison to applicability, and requires all
  matching Claims/Evidence so a challenge cannot be hidden by cherry-picking support.
- J3-F1R found that a test can itself reintroduce the second truth it is intended to
  prevent: demanding a product-side role mismatch for a manifest-allowed role change
  requires a hidden role oracle, and a dedicated source-mismatch shortcut obscures the
  more honest missing/unexpected observations. J3-F2 makes allowed roles live manifest
  data, freezes only the closed global vocabulary and source-declared subset, and
  strengthens observable manifest/no-follow/phase attacks without naming graph internals.
- J3-I1/M1 establish one five-source, 24-record manifest as the only runtime membership,
  digest, source, and role authority. The graph reloads an explicit supplied manifest
  per call; J1/J2 take a manifest-only module snapshot for their legacy views. Both
  product modules retain their actor APIs and all 63 controls while containing no
  canonical address or digest literals. The full locked gate now reports 85 actor
  journeys, two fresh W4 reports/eight Evidence records, and 49 proof contract groups.
- Repeated micro-node dispatch and review waiting exceeded the size of the J3-F1
  artifact. The user authorized a J4 canary with one continuity execution owner and a
  persistent read-only Fable 5 product advisor in Herdr. The advisor's initial baseline
  independently identified review recursion as the leading tracer-budget risk and
  recommended thin J4P before J4T. The canary preserves deterministic gates,
  journey-boundary checkpoints, and specialist escalation for material concerns; it
  reopens on context saturation, shared-surface errors, missed concerns, or advisor
  dependence.
- The Fable advisor's J3 checkpoint reports PASS to release J4P and independently
  confirms the zero-literal migration and observation-only manifest. It retains one
  nonblocking material-boundary falsification pass over J3 and names J5 as the reopen
  owner for fixture-backed proof provenance and Stack-specific manifest pressure.
  Either a concrete J3 trust-boundary counterexample or an ADR-0013 disposition that
  cannot be computed from the 24-record graph stops J4P and opens a design successor.
- J3-R2 exercised that reopen trigger twice. A slash-bearing source ID let the graph
  mistake one labeled source for another, recurring the J2 ownership class through the
  manifest namespace. Separately, J1/J2 ignored an invalid manifest projection and
  derived last-write-wins maps even though graph inspection failed closed. J3-F3/I2
  restrict source IDs to one safe logical segment and make both legacy views surface
  cached manifest diagnostics before any selector/root behavior. All 86 actor journeys
  and the full Evidence/proof gate now pass. J3-R3 replays both attacks against exact
  commit `64968ad` and reports PASS, so J3-G2 recloses the journey.
- J4P's first green resolver made correct canonical decisions but its explanation
  vocabulary erased accepted inconclusive/error attempts, inapplicable and unselected
  Evidence, explicit accept-none, and absent work into the same unsupported view. The
  persistent Fable advisor also found that a graph-valid successor with no declarations
  for a policy concern could satisfy that concern vacuously. J4P-F2/I2 retain the
  rejected predecessor, classify every non-supporting path visibly, and introduce a
  fail-closed `no-coverage` disposition. Exact successor `1435869`, J4P-R2, and the full
  locked gate pass; ADR 0013 is accepted at the revision containing that rule. J4T
  inherits the lesson that unknowns and contradictions are terminal actor output, not
  discarded intermediate state.
- J4T completes the fourth actor with a graph-only projection over exact Specification
  selectors. The Fable advisor found no material escape: realization-scoped package
  Claims cannot leak into the specification proof view, declaration IDs are globally
  unique behind graph validity, reorder controls remove array-position meaning, and a
  missing import retains its exact graph diagnostic. J5 inherits two nonblocking
  top-ups (the constitutively true import-availability flag and rejected/error/snapshot
  controls) plus a material framing constraint: successor records must revise the
  frozen 24-member census deliberately rather than quietly edit predecessor authority.
- J5 makes maintenance executable without inventing version lineage: an explicit
  31-record snapshot field-identically repeats the immutable 24-member predecessor and
  adds seven 0.2.0 records with no Evidence. Exact nonselection leaves nine predecessor
  Evidence records historical, the successor explainably unacceptable, its theory
  declarations unclaimed, and both acceptable 0.1.0 Realizations recoverable inside
  the same observation without automatic choice. The read-only Fable 5 advisor reports
  PASS at `56c4114`; requested and runtime-resolved provenance is
  `claude-fable-5`, high effort, `agent-dispatch --read-only`, pagu-box strict
  plan mode, and public-repository disclosure only; its review was static and did not
  reproduce the gate. Carry the earlier J4T rejected/error/snapshot top-up and a cold
  human journey run into the JG punch list rather than expanding J5.
- During J1-F3 evidence collection, one unchanged TypeScript breaker process produced
  a timeout/extra-output failure; immediate candidate and full-gate replays passed.
  Retain this as an environment/load-sensitive reopen signal rather than attributing
  it to J1 or silently treating the first run as green.
- J1-I1 and PR-GI1 requested exact `claude-sonnet-5` at high effort through
  `agent-dispatch`, writable isolated worktrees, pagu-box strict, and public-repository
  disclosure only. The first PR child returned success without edits after denied,
  unnecessary git-status probes; its retry and the parallel J1 child produced no
  output or edits during the bounded window and exited 130 when stopped. Internal
  isolated fallbacks now own the unchanged exclusive scopes; the provider attempts
  contribute no implementation evidence.
- J1-I2R exposed directory symlinks that the general loader intentionally ignored.
  J1-I3 therefore adds a publication-specific lstat/no-follow scan rather than
  changing loader semantics. The accepted boundary conservatively rejects every
  encountered symlink, assumes a quiescent tree, and retains private-loader coupling
  as maintenance debt.
- J1-G reproduced the curated Evidence through the exact Lean 4.30.0 proof boundary
  with `Proof is valid: 0 diagnostics.` after all 24 positive, negative, drift,
  completeness, filesystem, and no-execution publication controls passed.
- The first post-integration full-gate replay reached the Wave 4 toolchain boundary
  but used a stale garbage-collected GCC wrapper path; candidate and Evidence checks
  failed before execution with an explicit unavailable-`CC` diagnostic. Re-run with
  the extant exact GCC 15.2.0 wrapper; this is environment evidence, not a product pass.
- The hosted workflow originally lacked the expanded toolchain and did not close the
  release gate. Its accepted locked Nix successor now reproduces the complete gate on
  draft PR 4: metadata passes in 1m32s and the repository contract in 2m55s.
- The first PR-GT1 pin selected the correct compiler releases but not the accepted GCC
  wrapper closure: nixpkgs `bbacb131…` moved glibc from 2.42-61 to 2.42-67 and changed
  four Wave 4 Rust binary hashes. Signed release pin `e8210c6…` realizes the exact
  accepted `/nix/store/788mx…-gcc-wrapper-15.2.0`; PR-GT2 uses that pin only for GCC
  while retaining the newer Python, Rust, Deno, and separately pinned Lean inputs.
  The shell must also avoid ambient `NIX_*` compiler-wrapper flags: identical compiler
  paths inside `mkShellNoCC` still changed the binary from accepted `55f234bd…` to
  `71d6b4b…`. Clearing the six observed compiler/linker wrapper variables restored the
  exact accepted hash; the successor makes that clean evidence environment explicit.
- The completed branch is 59 commits ahead of `master`: 30 pre-governance subjects
  fail the accepted Conventional Commit grammar and 29 pass. Because the hosted job
  checks every commit in the prospective `base..head` range, publishing this branch
  directly would fail by design. The smallest reversible normalization is a new branch
  from `master` containing one conventional squash commit while the detailed ExecPlans
  and PR body retain the development/review lineage; rewriting the 30 subjects retains
  more commit granularity but carries substantially more history-rewrite risk. The
  operator owns that choice.
- GitHub read-only preflight on 2026-07-19 found public default branch `master`
  unprotected, all merge/rebase/squash methods enabled, zero rulesets, Actions enabled
  for all actions without SHA-pinning enforcement, read-only default workflow token
  permissions, and no Wave 5 PR. These observations make PR-GO a real hosted-policy
  boundary rather than an assumed documentation task.
- The operator authorized the recommended reversible normalization and hosted settings.
  `agent/actor-complete-tracer` begins at `master`, preserves the exact completed tree
  as one prospective Conventional Commit, and leaves the 59-node development branch
  intact as reviewable project history. Read-back confirms squash-only merge with PR
  title/body defaults, full-SHA Actions enforcement, and active no-bypass ruleset
  `19155146` requiring PRs, linear history, resolved conversations, strict deterministic
  checks, and no deletion or force-push. CodeRabbit/Claude remain advisory and their
  permissions were not expanded without actual PR evidence.
- JG-R1 independently reproduced the exact published `3bb74fe` checkout, sole
  Conventional Commit, prospective range, diff hygiene, and full locked gate, but
  correctly BLOCKed technical release because early system-map and user-journey prose
  still called accepted J2–J5 work open or merely designed. JG-S1 changes only those
  stale status claims, retains the rejected review, and requires a fresh successor
  replay rather than treating executable evidence as permission to ignore conflicting
  project memory.
- JG-R2 independently replays exact published successor `c24f355` and reports PASS:
  both Conventional Commits, diff hygiene, the full locked gate, corrected status
  claims, exclusions, and retained JG-R1 history agree. The matching hosted successor
  passes metadata in 1m33s and the repository contract in 2m42s. A zero-second stale
  check display traced to a concurrency-cancelled run superseded by the PR-body edit;
  the CI inspection helper found no live failure and no code change was warranted.
- `CONTRIBUTING.md` encoded a serial all-stages lifecycle while the governing lifecycle
  uses proportional revisioned DAG nodes; J0 makes them consistent.

## Decision log

| Question and options | Concerns and evidence | Decision, dissent, and reopen observation |
|---|---|---|
| acceptance surface: implementation layers, prose personas, or actor terminal journeys | the read-only four-actor audit found strong package-author substrate but missing consumer completion; layer-green work can still leave every actor blocked | use journey IDs as primary acceptance and subordinate packages to them; no retained dissent; reopen if journey packaging prevents independent concern work or cannot be made executable |
| tracer registry: existing fixture tree, curated finite set, or hosted service | fixtures mix product-capable and historical data; loader performs local discovery only; hosted acquisition/security is a declared non-goal | use one curated finite exact-version set and reserve hosted semantics; dissent that this is not yet a full registry is incorporated in the qualified definition; reopen before acquisition, indexing, signing, or remote execution |
| change lifecycle: mandatory serial stages or common spine with class profiles | lifecycle consultations found continuous verification, optional optimization, containment-first incidents, and characterization-based refactors incompatible with one waterfall | propose the common evidence spine and default refute-first micro-loop in ADR 0011; no protected intent changes; reopen on measured ceremony or a recurring class that does not fit |
| PR governance: block all J1 work or support product work and block final release | current hosted CI is incomplete, but making process automation the product's first dependency would displace actor value | run PR-G in parallel after J0 and require it at JG; remote rules/apps remain operator work; reopen if unsafe/unreviewable changes reach shared branches before JG |
| J1 proof provenance: rewrite manifest/checker now, ignore fixture binding, or bridge exact bytes/digests | fixture-backed proof provenance is architectural debt, but changing the proof boundary expands J1 across accepted Wave 3 artifacts; ignoring it would let curated meaning drift | bridge exact curated Specification/Claim/Evidence bytes and digests to accepted proof inputs, run proof explicitly, and retain the debt; reopen when publication must become the proof's primary source |
| commit enforcement: full history, legacy allowlist, or successor PR range | 31 commits predate the approved policy; retroactive failure or a hidden allowlist would violate successor-only governance | validate every commit in `base..head`, reject merge/fixup/squash, and send legacy normalization to PR-GO; reopen after the pre-governance stack is squash-merged or deliberately rewritten |
| J3 graph authority: 22 records with downstream policy/import, one 24-record manifest, or consumer-side overlays | deferring policy/import leaves J4 consumers owning canonical mutations or reading outside J3; embedding decisions in the manifest lets the graph integrator author policy | accept ADR 0012: one 24-record manifest owns source membership/digests/roles, while separate package-consumer and theory-author records retain their semantic authorship; 22 J3 and 63 retained J1/J2 controls plus the full locked gate pass; reopen on a second runtime selector or hosted/federated need |
| execution topology after J3: micro-node crew, one continuity owner, or unreviewed solo work | micro-node dispatch preserved dissent but imposed visible waiting/reconciliation cost on small artifacts; unreviewed solo work would allow self-ratification; the Fable advisor independently flags review recursion as the leading tracer risk | canary one continuity owner per end-to-end journey plus an asynchronous read-only product advisor and deterministic gates; advisors challenge but cannot ratify, specialist delegation returns for material boundaries; reopen on context saturation, missed cross-concern defects, shared-surface errors, or advisor dependence |
| J5 successor authority: mutate predecessor, copy records, overlay manifests, or select an append-only snapshot | mutation erases selectable history, copies create drifting byte truths, and overlay/latest semantics introduce an unreviewed merge authority; exact reference checking already rejects predecessor Evidence migration | accept ADR 0014: one explicit manifest per observation, field-identical predecessor entries, seven actor-owned successor records with zero Evidence, and exact nonselection as bounded staleness; reopen before a third manifest, hosted acquisition, composition, implicit discovery, signatures, or time/TTL semantics |

## Result and remaining work

J0-R1, R2, and R3 rejected successive documentation/governance checkpoints; J0-S1,
S2, and S3 retain their corrections without relabeling a predecessor. J0-R4 and the
exact repository gate pass, so J0-G closes. J1 accepts the finite curated theory
publication. J2 now accepts two independent exact package registrations after four
implementation successors, three product reviews, fresh W4 Evidence reproduction, and
the full locked repository gate. J3-G initially accepted one manifest as the exact
24-record product graph, then J3-R2 reopened it with two authority escapes. J3-F3/I2
close both behind red controls, the full locked successor gate passes, and J3-R3
reports PASS against exact commit `64968ad`; J3-G2 therefore recloses the journey and
releases J4P. J4P-R1 then rejected the first green resolver's incomplete outcome
vocabulary and vacuous zero-coverage behavior; J4P-F2/I2 close both, J4P-R2 and the
full locked gate pass, and J4P-G accepts the package-consumer journey. J4T then passes
its exact projection controls, advisor falsification, and locked gate, completing all
four actor terminal outcomes. J5 then retains the immutable predecessor inside an
explicit 31-record successor snapshot, rejects Evidence migration, exposes the failed
0.2.0 result through both consumer views, and reports exact 0.1.0 recovery candidates
without selecting one. J5-R1 and the full locked gate pass at `56c4114`; ADR 0014 and
J5-G are accepted. PR-GO and PR-GG then converge squash-only protected hosted policy
and both required checks on draft PR 4. The first independent fresh-checkout reviewer
reproduces every executable gate but BLOCKs on contradictory status prose; JG-S1
reconciles that durable memory without changing product behavior. JG-R2 and both
hosted successor checks then pass at `c24f355`. JG now waits only on the retained
cold-human pre-merge recommendation, not further product-journey implementation or
release-governance automation.

## Stop and escalation conditions

- stop if a source-set or projection becomes a second canonical truth;
- stop if graph validity or a green report is treated as policy satisfaction;
- stop if resolution conflates semantic acceptability with interoperation;
- stop before automatic build/execution, remote acquisition, hosted registry security,
  namespace composition, or inferred version compatibility;
- escalate any protected-intent weakening, consequential self-ratifying gate change,
  irreversible migration, or remote GitHub setting/app installation requiring operator
  authority.
