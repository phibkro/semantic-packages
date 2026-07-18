# ExecPlan 0001: End-to-end tracer bullet

## Purpose and observable outcome

Produce a local prototype where a user can load the example Stack specification, see its claims and two registered realizations, run conformance checks, and receive an explainable compatibility result.

## Context

Read `AGENTS.md`, `ARCHITECTURE.md`, `docs/design/core-model.md`,
`docs/design/spec-language.md`, `docs/design/evidence-model.md`,
`docs/design/compatibility.md`, and `docs/design/tracer-bullet.md` first.

## Non-goals

- final language syntax;
- production authentication or hosting;
- automatic proof synthesis;
- general package resolver;
- performance optimization.

## Constraints

- Preserve representation independence; conformance compares declared observations,
  not host-language object identity or layout.
- Keep claim lifecycle, evidence review, evidence result, and assurance separate.
- Keep semantic satisfaction separate from realization interoperability.
- Retain failed, challenging, unknown, and inapplicable evidence.
- Use JSON as the temporary canonical interchange format while the `.pspec` surface
  syntax remains illustrative.
- Treat registry indexes and browser/API views as projections of canonical records,
  not separately maintained facts.

## Coordination model

The user retains mission and product-priority authority. This plan is a revisioned
work-dependency DAG: governing decisions authorize bounded work packages; hard
dependency edges order them; evidence and challenge edges may feed any affected
package or convergence gate; and passed gates release their declared dependents. The
lead owns graph framing, concern disposition, shared-surface integration assignment,
and convergence acceptance. Package owners may close reversible local nodes using
predeclared checks or delegated review without lead relay. Shared-file changes retain
one named integrator, and concurrent writers require disjoint paths or isolated
worktrees. The current broad audit changes must be captured as a stable baseline before
implementation writers begin.

Current cross-provider routing is operational policy for this plan, not architectural
authority: use Claude Sonnet 5 with explicit high effort for bounded routine execution,
and the Claude Fable 5 profile with explicit high effort for complex consultation or
skeptic review. Consultations are read-only and normally attach through `supports` or
`challenges`; implementation writers receive isolated worktrees and exclusive scope.
All launches use `agent-dispatch`. The lead integrates and accepts against repository
evidence, regardless of model. Each external node records the data scope approved for
disclosure and both its requested selector and runtime-reported model ID.

Planned gated waves:

| Wave | Delegated concerns | Integration gate |
|---|---|---|
| 1. design closure | identity/references; Stack observations and adapter boundary; profile/cost and evidence policy | reviewer ambiguity/counterexample matrix has no undisposed incompatible interpretation |
| 2. records | six linked schemas; independently authored positive/negative fixtures and gate wiring | schema and reference-integrity gates pass red-then-green |
| 3. execution substrate | loader/link checker; reference adapter; bounded proof probe | stable diagnostics and one named law evidence packet |
| 4. independent realizations | Rust and TypeScript implementations by separate authors; shared conformance reviewer | both satisfy the same external contract; broken variants fail |
| 5. product slice | evidence graph; compatibility explanation; browser/CLI projection | unknown, challenging, and unsupported results remain visible |
| 6. release and learning | fresh-clone reproduction; retrospective and next plan | gates reproduce and durable memory reflects discoveries |

Wave numbers communicate the dominant dependency order, not global barriers. Within
and across waves, a node may start when all declared hard predecessors have closed; it
need not wait for unrelated work. A convergence gate must close before another node
depends on its integrated result. Failed gates create successor revision nodes and
retain their observations. Owners, reviewers, dependencies, and exclusive paths are
recorded in delegation briefs rather than guessed in advance.

### Current design-closure DAG: DC1 revision 1

| Node | Edges and owner | Scope / write boundary | Evidence and status |
|---|---|---|---|
| DC1-I1 identity consultation | supports/challenges DC1-L1; Claude Sonnet 5 | read-only identity/reference analysis | exact typed-reference proposal and falsifiers returned; one contradictory ID-uniqueness statement rejected by the lead |
| DC1-S1 semantic skeptic | challenges DC1-L1 and DC1-G1; Claude Fable 5 | read-only Stack, adapter, effect, profile, and policy analysis | ambiguity matrix and O1–O8 obligations returned; conservative conflict/prohibition defaults retained |
| DC1-GPT1 diverse skeptic | challenges DC1-L1 and DC1-G1; internal Codex collaboration agent | read-only review of the same Wave-1 concerns | independently separated prohibition from priority and recommended blocking schema authorization until normative text lands |
| DC1-L1 integration | depends on the three concern packets; lead Codex | exclusive writer for affected design docs, ADRs, Stack sketch, and this plan | rejected by DC1-R1: cost semantics and conditional evidence scope remained ambiguous |
| DC1-R1 convergence review | challenges DC1-L1; independent Codex reviewer | read-only actual-diff audit | blocked the gate with two line-specific findings; all other concern dispositions passed |
| DC1-L2 successor integration | depends on DC1-R1; lead Codex | same exclusive shared surfaces | exact tracer cost predicate and conditional specification/realization evidence scope landed |
| DC1-R2 successor review | challenges/supports DC1-L2; same independent Codex reviewer | read-only focused regression review | both prior blockers closed; no new actionable finding |
| DC1-G1 convergence | depends on DC1-L2, DC1-R2, and G0 | lead acceptance owner | passed; Wave 2 schema/fixture work authorized |

The external consultations used Claude Code 2.1.212 through
`agent-dispatch --read-only`, pagu-box `strict`, the repository PWD, and explicit high
effort. Requested and runtime primary models matched: `claude-sonnet-5` for DC1-I1 and
`claude-fable-5` for DC1-S1; Claude also reported auxiliary
`claude-haiku-4-5-20251001` usage. Both briefs prohibited edits, delegation, and web
research. External disclosure was limited to the governing semantic-packages documents,
the schema/Stack scaffolds, and brief revision 1. Herdr remained lead-side and its
control socket was unavailable inside the sandbox.

### Current operational-memory DAG: MPW revision 1

| Node | Edges and owner | Scope / write boundary | Evidence and status |
|---|---|---|---|
| MPW-L1 runbook authoring | informed by the DC1 provider probes; lead Codex | exclusive writes to agent guidance, operations/lifecycle docs, README, checker, and this plan | capability/status matrix, secure dispatch patterns, reusable briefs, provenance, fusion, and failure handling authored |
| MPW-R1 requirements audit | challenges MPW-L1; independent Codex reviewer | read-only capability and governance inventory | required conditional claims, provenance, fusion rules, and anti-patterns returned |
| MPW-R2 convergence review | challenges MPW-L1; same independent reviewer | read-only actual-diff audit | blocked on a Herdr child-boundary contradiction, flattened verification status, unsupported route wording, and missing plan evidence |
| MPW-L2 successor integration | depends on MPW-R2; lead Codex | same exclusive shared surfaces | child-side `HERDR_*` is now a stop condition; verified, advertised-but-unprobed, and unsupported routes are distinct; this DAG retains the failed review |
| MPW-R3 successor review | challenges/supports MPW-L2; independent Codex reviewer | read-only focused regression review | passed after one final mandatory-entrypoint wording correction; no material objection remains |
| MPW-G1 repository-memory convergence | depends on MPW-L2, MPW-R3, and G0 | lead acceptance owner | passed; `git diff --check` and Nix-backed `python3 scripts/check_repo.py` both passed |

### Current record-schema DAG: W2 revision 1

| Node | Edges and owner | Scope / write boundary | Closure evidence |
|---|---|---|---|
| W2-S1 schema realization | depends on DC1-G1; Claude Sonnet 5 | isolated `agent/wave2-schemas` worktree; exclusive `schemas/` writer | seven-file family returned; exact primary runtime `claude-sonnet-5`; lead metaschema validation passed |
| W2-GPT1 schema skeptic | challenges W2-S1/W2-G1; internal Codex collaboration agent | read-only same governing concern | 26-case counterexample matrix returned; exposed hidden seventh Adapter-record risk |
| W2-L1 schema integration | depends on W2-S1 and W2-GPT1; lead Codex | exclusive shared-surface integrator | adapter fixed as nested Realization descriptor; strict schema interfaces frozen for fixtures |
| W2-F1 fixture authoring | depends on W2-L1; independent GPT fixture writer | exclusive `fixtures/records/` | 8 valid records, 11 schema-negative records, and 8 isolated link-negative graphs returned; schema controls passed |
| W2-D1 diagnostic-oracle review | challenges W2-F1/W2-G1; independent internal Codex reviewer | read-only fixture and expected-diagnostic audit | blocked checkpoint: wrong-kind/version and reference-surface controls were missing, and diagnostics were not yet actionable exact oracles |
| W2-R1 semantic convergence review | challenges/supports W2-L1/W2-F1; Claude Fable 5 | read-only actual-diff audit | no schema redesign blocker; exposed Claim-state, adapter-shape, profile-set, policy-event, date-format, and expected-reason gaps retained for the successor |
| W2-L2 successor integration | depends on W2-D1/W2-R1; lead Codex | exclusive schema, core-model, dependency, and plan surfaces | bounded Claim lifecycle, exact profile-set semantics, policy event resolution, and asserted date validation landed; lead schema controls pass |
| W2-F2 successor fixture oracle | depends on W2-L2; independent GPT fixture writer | exclusive `fixtures/records/` | complete: 15 schema-negative controls with expected reasons and 21 isolated link graphs with actionable exact diagnostics |
| W2-D2 successor oracle review | challenges W2-L2/W2-F2; same independent internal Codex reviewer | read-only actual-diff regression review | blocked checkpoint: order-independent profile-set equality and typed reference-role paths still lacked decisive controls |
| W2-F3 final oracle successor | depends on W2-D2; independent GPT fixture writer | exclusive `fixtures/records/` | complete: one zero-diagnostic order-independence graph and eight remaining typed-role/coherence falsifiers; 15 schema and 29 link negatives total |
| W2-D3 checkpoint review | challenges/supports W2-F3; same independent reviewer | read-only focused regression review | passed; all W2-D2 gaps closed with isolated exact controls |
| W2-P1 reviewed checkpoint | depends on W2-L2, W2-F3, W2-D3, and lead controls | lead acceptance owner | passed for checkpoint: 7 metaschemas, 8 flat valid records, 15 schema negatives, 29 link negatives, 1 valid link graph, 105 parsed JSON; does not imply W2-G1 acceptance |
| W2-C1 durable record gate | depends on W2-P1; Claude Sonnet 5 plus lead integration | isolated checker worktree; exclusive `scripts/` writer | implementation passed all checkpoint fixtures under lead execution; child correctly reported execution-blocked because Python/Nix were unavailable |
| W2-CR1 checker generality review | challenges W2-C1; independent internal Codex reviewer | read-only actual-code review plus novel temporary counterexamples | blocked convergence: conditional Evidence scope, profile-member uniqueness, policy event roles, and schema type errors were unsound; reference/CLI diagnostics also incomplete |
| W2-F4 checker falsifiers | depends on W2-CR1; independent GPT fixture writer | exclusive `fixtures/records/` successor controls | complete: 4 schema, 6 link-negative, 1 link-valid, and one two-diagnostic candidate control made W2-C1 red |
| W2-C2 checker successor | depends on W2-F4; Claude Sonnet 5 plus lead integration | same isolated checker worktree and exclusive `scripts/` scope | implementation execution-blocked in child; lead exact gate, compile, CLI input, and candidate controls pass |
| W2-CR2 checker successor review | challenges W2-C2; independent reviewer | read-only actual-code and 280-case mutation regression | blocked: non-string kind crashed, duplicate indexes caused false role cascades, and multi-kind candidates were truncated |
| W2-F5 final generality controls | depends on W2-CR2; independent GPT fixture writer | exclusive `fixtures/records/` | complete: kind type, referenced duplicate, and multi-kind/version controls; 20 schema and 38 link negatives total |
| W2-C3 final checker integration | depends on W2-F5; lead Codex | exclusive `scripts/` integrator | kind typing, category-set indexes, and complete plural candidate diagnostics landed; exact lead gate passes |
| W2-CR3 final checker review | challenges/supports W2-C3; same independent reviewer | read-only mutation and actual-code regression | passed with no dissent: 280 wrong-type mutations, duplicate cascades, multi-candidates, and all prior blockers rechecked |
| W2-CG1 durable-checker convergence | depends on W2-C3, W2-CR3, and G0 | lead acceptance owner | passed: exact fixture gate, repository gate, compilation, CLI red controls, and diff check |
| W2-R2 final records convergence | challenges/supports W2-P1/W2-CG1; Claude Fable 5 | read-only integrated actual-diff audit | passed static convergence review with no material schema, documentation, checker, determinism, or resolution objection; child execution remained unavailable and was independently supplied by the lead |
| W2-G1 records gate | depends on W2-P1, W2-CG1, W2-R2, and G0 | lead acceptance owner | passed: seven schema files defining six canonical record kinds, 8 flat valid records, 20 schema negatives, 38 link negatives, 2 link-valid graphs, and the durable repository gate converge |

The published design baseline is commit `d0fa6d0` and draft PR #1. Wave 2 runs on a
stacked isolated branch so schema implementation cannot silently expand that review.
Delegated briefs retain the same approved external disclosure scope as DC1 and add only
the schema/fixture/checker artifacts created in this worktree.

W2-S1 used Claude Code 2.1.212 through `agent-dispatch`, pagu-box `strict`, read-write
PWD mode in the isolated worktree, explicit high effort, and no web research. The
requested and runtime primary model was `claude-sonnet-5`; Claude also reported
auxiliary `claude-haiku-4-5-20251001` usage. Its exclusive scope was `schemas/` and the
lead independently reran the repository and JSON Schema metaschema gates.

W2-R1 used Claude Code 2.1.212 through `agent-dispatch --read-only`, pagu-box
`strict`, the isolated worktree PWD, explicit high effort, and no web research. The
requested and runtime primary model was `claude-fable-5`; auxiliary
`claude-haiku-4-5-20251001` usage was reported. Git/Python probes were denied inside
the child, so its manual artifact review does not replace lead-executed validation.
W2-D1 was an independent internal Codex collaboration node and did execute the fixture
shape controls. Both reviews received the same governing worktree independently and
neither model identity nor Fable's PASS overrode W2-D1's decisive missing falsifiers.

W2-C1 and W2-C2 used Claude Code 2.1.212 through `agent-dispatch`, pagu-box
`strict`, writable PWD mode in the isolated checker worktree, the exact requested and
runtime primary model `claude-sonnet-5`, and an exclusive `scripts/` boundary. Both
dispatches requested high effort; the C1 narrative self-reported “medium-high/default”
despite the explicit dispatcher request, so that mismatch is retained rather than
treated as runtime proof of effort. Structured output reported auxiliary
`claude-haiku-4-5-20251001` usage. Python, Nix, and git probes were unavailable or
denied inside the children; both correctly returned execution-blocked, and the lead
ran the exact pinned controls. Disclosure remained limited to the approved
semantic-packages worktree and versioned briefs; neither child delegated or used web
research.

W2-R2 used Claude Code 2.1.212 through `agent-dispatch --read-only`, pagu-box
`strict`, the isolated Wave 2 worktree, explicit high effort, and no web research or
delegation. The requested and runtime primary model was `claude-fable-5`; structured
provenance also reported auxiliary `claude-haiku-4-5-20251001` usage despite the
narrative reporting no auxiliary model, so the structured provenance and mismatch are
retained. Git, Python, and Nix were denied inside the child. Its static actual-diff
review found no material contradiction, false acceptance, erased concern,
nondeterminism, or network-dependent resolution; lead-executed gates supply the
required runtime evidence. Disclosure remained limited to the approved
semantic-packages worktree and the versioned review brief.

### Current execution-substrate DAG: W3 revision 1

| Node | Edges and owner | Scope / write boundary | Evidence and status |
|---|---|---|---|
| W3-S1 loader semantics | challenges/supports W3-L0; independent internal GPT reviewer | read-only governing docs, checker, and fixtures | complete: thin deterministic local source-set contract, phase barriers, visible-edge import semantics, and 12 decisive falsifiers proposed |
| W3-S2 diverse loader skeptic | challenges/supports W3-L0; Claude Fable 5 | read-only actual-code and governing-document audit | complete static packet: supports thin loader and deterministic phase boundary; challenges with a proposed import DAG, realpath symlink following, and duplicate-import schema rule |
| W3-F1 red-first design | challenges/supports W3-L0/W3-A0; independent internal GPT fixture specialist | read-only loader and Stack reference-model oracle design | complete: loader fixture layout plus minimal pure-model controls; proposed cycle rejection retained as dissent and adapter-dependent controls correctly blocked on protocol freeze |
| W3-L0 loader/import contract | depends on W2-G1; informed by W3-S1, W3-S2, and W3-F1; lead Codex | exclusive design, ADR, plan, and backlog integration | accepted provisionally: lexical source normalization, recursive lowercase JSON discovery, symlink rejection, phase barriers, and exact visible import edges; self/cyclic/diamond/repeated imports are valid until stronger semantics exist |
| W3-LF1 loader falsifiers | depends on W3-L0; independent internal GPT fixture owner | exclusive `fixtures/loader/` and `scripts/loader_fixture_check.py` | complete red checkpoint: 19 data/oracle files and 14 subprocess observations across 9 contract groups; current checker fails on directory discovery, aliases/overlap, extension and symlink policy, phase barriers, and directory-loaded import graphs while G1 remains green |
| W3-L1 loader implementation | depends on W3-LF1; Claude Sonnet 5 plus lead integration | isolated worktree; child exclusively edited `scripts/record_check.py`, lead owns gate/README/plan integration | implementation checkpoint green under lead execution: 9 loader contract groups, accepted 8/20/38/2 record gate, and compilation pass; child execution was unavailable |
| W3-LR1 loader review | challenges W3-L1; independent internal GPT reviewer | read-only actual-code and private-temp novel counterexamples | blocked convergence despite green authored gates: directory scan errors traceback, failing aliases and overlapping discovery duplicate diagnostics, empty-set labels depend on argv order, intermediate symlinks are followed, and base `/` labels remain absolute |
| W3-LF2 loader successor falsifiers | depends on W3-LR1; same independent fixture owner | exclusive `fixtures/loader/` and loader harness scope | complete: 16 contract groups cover prior controls plus scan errors, failing-alias/overlap idempotence, intermediate symlinks, argv-independent empty labels, root-base labels, and unsupported special files |
| W3-L2 loader successor | depends on W3-LF2; Claude Sonnet 5 plus lead integration | same exclusive loader/checker implementation paths | implementation checkpoint green: loader 16, accepted 8/20/38/2 record gate, compilation, two link-valid direct probes, and negative CLI; not converged because W3-LR2 found novel gaps |
| W3-LR2 loader successor review | challenges W3-L2; independent internal GPT reviewer | read-only actual-code and prior/novel regression | blocked: exact `//` aliases duplicate one Linux source, per-entry classification errors traceback, and a regular-to-symlink concurrent substitution is followed |
| W3-LF3 loader boundary successor | depends on W3-LR2 and lead exclusion disposition; independent fixture owner | exclusive loader harness scope | complete red checkpoint: prior 16 groups pass; POSIX double-slash idempotence and injected per-entry classification-error containment fail exactly as intended; concurrent mutation remains an explicit quiescent-tree exclusion in ADR 0007 |
| W3-L3 loader boundary implementation | depends on W3-LF3; Claude Sonnet 5 plus lead verification | exclusive `scripts/record_check.py`; lead owns docs/gates | complete: all 18 loader groups, 8/20/38/2 record gate, compilation, direct CLI, and diff hygiene pass |
| W3-LR3 loader boundary review | challenges W3-L3; independent internal GPT reviewer | read-only prior and novel regression | passed: all LR1/LR2 blockers and six novel quiescent-tree probes pass; no special-casing, nondeterminism, traceback, or record regression found |
| W3-LG1 loader convergence | depends on W3-L3, W3-LR3, and G1 | lead acceptance owner | accepted: ADR/docs/checker/harness agree on deterministic local source-set semantics and explicit quiescent-tree/security exclusions |
| W3-A0 adapter consultation | supports/challenges W3-A0L1; Claude Sonnet 5 | read-only protocol and reference-model boundary | complete static packet: separated the in-process semantic model from the canonical child-process adapter, proposed NDJSON framing, handles, events, and controls |
| W3-A0R1 adapter skeptic | challenges W3-A0/W3-A0L1; independent internal GPT reviewer | read-only observable-semantics and trust-boundary audit | blocked the initial packet: normative handle freshness leaked representation, lifecycle/error behavior was incomplete, shared oracle code would be tautological, and performance instrumentation needed an explicit exclusion |
| W3-A0L1 adapter contract successor | depends on DC1-G1, W2-G1, and the blocking W3-A0R1 review; informed by W3-A0; lead Codex | exclusive adapter design, ADR, plan, and guidance integration | accepted provisionally: independent harness oracle and Realization, child-process NDJSON, EOF lifecycle, opaque stable-denotation handles with fresh/interned tokens both valid, ordered reported events, and separate challenge/error classifications |
| W3-AF1 model/adapter falsifiers | depends on W3-A0L1; independent internal GPT fixture owner | exclusive `tests/adapter/` and `fixtures/adapters/` | complete red checkpoint: future runner API plus semantic, persistence, event, transport, execution-error, and liar matrix; actual `python -m semantic_packages.stack_adapter` is required, and current failure is the missing product package |
| W3-A1 reference realization and adapter | depends on W3-AF1; Claude Sonnet 5 | isolated worktree; exclusive `semantic_packages/**` | implementation checkpoint green: independent persistent realization, child adapter, and runner pass all 9 AF1 tests, compile, actual EOF probe, and full repository gate |
| W3-AR1 adapter review | challenges W3-A1; independent internal GPT reviewer | read-only actual-code and novel observable-semantics/lifecycle audit | blocked despite AF1 green: EOF nonzero/hang/extra-output failures are accepted, process start escapes, stderr provenance is discarded, and a nonempty pushed source can be rebound undetected |
| W3-AF2 adapter lifecycle successor | depends on W3-AR1; independent fixture owner | exclusive adapter fake/test scope | complete red checkpoint: prior 9 plus unterminated-line regression pass; six controls fail exactly on EOF exit/hang/extra-output, start error, stderr retention, and nonempty-source persistence |
| W3-A2 adapter successor | depends on W3-AF2; Claude Sonnet 5 | exclusive `semantic_packages/**` | implementation checkpoint green on 16 tests: lifecycle outcomes, raw stderr, start failure, and every pushed source are retained; W3-AR2 still blocked convergence |
| W3-AR2 adapter successor review | challenges W3-A2; independent internal GPT reviewer | read-only prior and novel regression | blocked: cleanup opens two fresh timeout windows after the declared deadline, unterminated post-EOF bytes are discarded, and empty command raises `IndexError` |
| W3-AF3 adapter boundary successor | depends on W3-AR2; independent fixture owner | exclusive adapter fake/test scope | complete red checkpoint: 15 unaffected tests pass; calibrated one-deadline ceiling, post-EOF unterminated bytes, and empty command fail exactly as intended |
| W3-A3 adapter boundary implementation | depends on W3-AF3; Claude Sonnet 5 | exclusive `semantic_packages/stack_runner.py` | complete: all 18 tests pass; timeout signals immediately then uses one cleanup grace, buffered EOF bytes fail, and empty command returns `PROCESS_START` |
| W3-AR3 adapter boundary review | challenges W3-A3; independent internal GPT reviewer | read-only prior and novel regression | passed: stable repeated timing, seven post-EOF payload sizes, stdout-close hangs, termination stderr, cause precedence, command shapes, depths 1–4 persistence, immutability, and PID cleanup all pass |
| W3-AG1 reference-adapter convergence | depends on W3-A3, W3-AR3, and G1 | lead acceptance owner | accepted: executable Realization/adapter `0.2.0`, 18-test shared suite, README, canonical record, and repository gate agree; Wave 2 `0.1.0` remains immutable |
| W3-P0S1 bounded proof preflight | informs W3-P0L1; independent internal GPT concern owner | read-only law, local-tool, falsifier, and evidence-boundary analysis | complete: recommends experimental Lean-core universal `pop-empty` probe; found `sorry` exit-zero and admitted-axiom traps; keeps translation/tool trust and non-global authority explicit |
| W3-P0R1 diverse proof skeptic | challenges W3-P0S1; Claude Fable 5 | read-only semantic-model, trust-boundary, and evidence-scope audit | complete REVISE: support only model satisfaction/pipeline evidence, pin the expected theorem statement, treat new Evidence as additional, and disposition the accepted fixture-only hazard; its `--trust=0` concern was directly falsified against Lean 4.30.0 help/execution |
| W3-P0L1 bounded proof boundary | depends on W3-P0S1/P0R1 and W3-LG1; lead integration | exclusive proof design/plan acceptance; no universal foundation authority | accepted experimentally in ADR 0009 with all four bounded review corrections and explicit non-authority/revisit conditions |
| W3-PF1 proof falsifiers | depends on W3-P0L1; independent internal GPT fixture owner | exclusive `fixtures/proofs/v1/**` and `scripts/proof_fixture_check.py` | complete red checkpoint: 25 future groups freeze theorem, warning, axiom, exact-statement, linkage, digest, tool, fixture-Evidence, manifest, and path behavior; only future checker/proof/manifest absence remains red |
| W3-P1 named-law proof implementation | depends on W3-PF1; Claude Sonnet 5 | exclusive `scripts/proof_check.py` and `proofs/stack-pop-empty/**` | implementation checkpoint green: core-only universal theorem, pinned manifest, and standalone checker pass all 25 PF1 groups, direct Lean/checker, compilation, and record/loader gate |
| W3-PR1 proof review | challenges W3-P1; independent internal GPT reviewer | read-only theorem, linkage, provenance, and evidence audit | blocked: 16 coherent manifest/record/theorem/warning/path/Evidence/output mutations falsely pass and Lean execution is unbounded; the theorem itself remains clean and axiom-free |
| W3-PF2 proof boundary successor | depends on W3-PR1; independent fixture owner | exclusive proof fixture/harness scope | complete red checkpoint: 15 successor groups (40 total) pin semantic/tool constants, exact elaborated type, record validity, warnings, containment, Evidence validity, structured output, and bounded tool/version execution; P1 fails only those new controls and both hanging fake-Lean modes are killed within the harness deadline |
| W3-P2 proof checker successor | depends on corrected W3-PF2; internal Codex implementation owner after two stalled Claude Sonnet 5 dispatches | exclusive `scripts/proof_check.py` and proof manifest/source as required | implementation checkpoint green: all 40 groups, direct checker/Lean, compilation, repository gate, and digest audit pass; theorem remains unchanged, universal, core-only, and axiom-free |
| W3-PR2 proof successor review | challenges W3-P2; independent internal Codex plus Claude Fable 5 | read-only prior and novel theorem/linkage/provenance audit | blocked: actual-source output can precede and falsify the axiom audit while `#eval` executes; Evidence accepts arbitrary JSON; unused axiom/modifier-unsafe source passes; fake-only single-type observation reduces assurance; manifest runner is not bound to the executing checker |
| W3-PF3 proof review successor controls | depends on W3-PR2; independent fixture owner | exclusive proof fixture/harness scope | complete red checkpoint: 8 successor groups / 42 cases (48 groups / 104 cases total) freeze source-command/axiom/unsafe rejection, unique dual type and axiom observations, exact proof Evidence semantics/provenance, and executing-runner identity; prior 40 groups remain green and the bounded run is red only on PF3 |
| W3-P3 proof boundary successor | depends on W3-PF3 | exclusive checker/proof manifest/source scope as required | in progress |
| W3-PR3 proof convergence review | challenges W3-P3 | read-only prior and novel theorem/Evidence/provenance audit | pending |
| W3-PG1 named-law evidence gate | depends on accepted W3-P3 successor, W3-PR3, and G1 | lead acceptance owner | pending |
| W3-G1 execution-substrate convergence | depends on W3-LG1, W3-AG1, W3-PG1, and G0 | lead acceptance owner | pending |

W3-S2 used Claude Code 2.1.212 through `agent-dispatch --read-only`, pagu-box
`strict`, the Wave 2 worktree, exact `claude-fable-5`, and explicit high effort. The
current shell profile did not expose `agent-dispatch`, so the lead invoked the immutable
verified Home Manager generation through `nix shell` rather than modifying the host.
Structured output reported auxiliary `claude-haiku-4-5-20251001` usage. The child had
only Read/Grep/Glob tools, performed no execution, writes, delegation, or web research,
and disclosed only the approved public semantic-packages paths and brief. Its import-DAG
dissent remains visible; W3-L0 rejects the speculative constraint for this tracer and
names the elaboration/namespace trigger that would reopen it.

W3-A0 used Claude Code 2.1.212 through `agent-dispatch --read-only`, pagu-box
`strict`, the Wave 3 worktree, exact `claude-sonnet-5`, and explicit high effort.
Structured output reported auxiliary `claude-haiku-4-5-20251001` usage. The child had
only Read/Grep/Glob tools, performed no execution, writes, delegation, or web research,
and disclosed only the approved public semantic-packages paths and brief. W3-A0R1
independently blocked its first packet; W3-A0L1 incorporates the representation,
oracle-independence, lifecycle, error, and performance-scope corrections rather than
treating model provenance as acceptance.

W3-L1 used Claude Code 2.1.212 through `agent-dispatch`, pagu-box `strict`, writable
PWD mode in the isolated Wave 3 worktree, exact `claude-sonnet-5`, explicit high
effort, and exclusive `scripts/record_check.py` ownership. Structured output reported
auxiliary `claude-haiku-4-5-20251001` usage. Git, Python, Nix, and out-of-worktree
probes were denied inside the child, so it returned execution-blocked rather than
claiming runtime success. The lead ran the unchanged red-first harness green, reran
the accepted record/repository gate and compilation, and owns the separate README,
repository-gate, and plan integration. Disclosure was limited to the approved public
Wave 3 worktree and brief; no web research or delegation occurred.

W3-L3 used Claude Code through `agent-dispatch`, pagu-box `strict`, writable PWD mode
in the isolated Wave 3 worktree, exact `claude-sonnet-5`, explicit high effort, no
fallback, and exclusive `scripts/record_check.py` ownership. The child used a Nix
Python environment with jsonschema 4.26.0 to execute the unchanged 18-group and full
repository gates; worktree Git metadata was denied, so the lead separately ran
`git diff --check`. Disclosure was limited to the approved public worktree and brief;
no web research, installs, unrelated data, or delegation occurred.

W3-A1 used Claude Code through `agent-dispatch`, pagu-box `strict`, writable PWD mode
in the isolated Wave 3 worktree, exact `claude-sonnet-5`, explicit high effort, no
fallback, and exclusive `semantic_packages/**` ownership. The child and lead both ran
the unchanged 9-test AF1 suite, compilation, actual adapter EOF, and the full repository
gate green. Disclosure was limited to the approved public worktree and brief; no web,
unrelated data, installs, or delegation occurred.

W3-A2 used Claude Code through `agent-dispatch`, pagu-box `strict`, writable PWD mode
in the isolated Wave 3 worktree, exact `claude-sonnet-5`, explicit high effort, no
fallback, and exclusive `semantic_packages/**` ownership. It ran all 16 AF2 tests,
compilation, and the full record/loader gate green. Its child sandbox could not access
worktree Git metadata; the lead separately ran diff hygiene. Disclosure was limited to
the approved public worktree and brief; no web, unrelated data, installs, or delegation
occurred.

W3-A3 used the same `agent-dispatch`/pagu-box strict writable boundary, exact
`claude-sonnet-5`, explicit high effort, no fallback, and exclusive
`semantic_packages/stack_runner.py` ownership. It ran the 18-test successor repeatedly,
compilation, actual adapter behavior, and record/loader gate green. Worktree Git and
the unrelated Lean executable were unavailable in the child; the lead owns those
separate gates. Disclosure remained limited to the approved public worktree and brief;
no web, unrelated data, or delegation occurred.

W3-P0R1 used Claude Code through `agent-dispatch --read-only`, pagu-box `strict`, exact
`claude-fable-5`, explicit high effort, and no fallback. It could not execute Lean in
its sandbox, so its likely-Lean-3-only objection to `--trust=0` remained an inference;
the lead directly verified the installed Lean 4.30.0 help and a successful
`--stdin --trust=0` invocation. The statement-linkage, evidence-wording, additional-
record, and fixture-hazard corrections were accepted. Disclosure was limited to the
approved public worktree and brief; no writes, web, installs, unrelated data, or
delegation occurred.

W3-P1 used Claude Code through `agent-dispatch`, pagu-box `strict`, writable PWD mode
in the isolated Wave 3 worktree, exact `claude-sonnet-5`, explicit high effort, no
fallback, and exclusive proof/checker ownership. It used the existing Lean 4.30.0
toolchain explicitly, with no store path committed, and ran the unchanged 25-group
oracle, direct checker, compilation, and record/loader gate green. Worktree Git metadata
was unavailable inside the child; the lead owns diff hygiene. Disclosure was limited
to the approved public worktree and brief; no web, unrelated data, or delegation
occurred.

## Specification changes required before implementation

The design audit found prerequisites that the original implementation order omitted:

1. Define provisional identity, version pinning, local declaration IDs, and reference
   integrity without assuming semantic version compatibility.
2. Define Stack's empty-pop behavior and extensional observation/equivalence.
3. Define the conformance adapter protocol, including generated values, observations,
   and adapter-observed effect events.
4. Define persistence as an observable obligation over both the pre- and post-`push`
   logical stacks.
5. Define the execution profile, workload, and cost measure referenced by the
   performance claim, even if acceptable performance evidence remains absent.
6. Define how a consumer policy treats missing, inapplicable, supporting, challenging,
   and assertion-only evidence.

## Proposed implementation order

1. Record the identity/reference invariants and temporary JSON interchange decision.
2. Define strict provisional JSON Schema records for `Specification`, `Realization`,
   `Claim`, `Evidence`, `RealizationProfile`, and `ConsumerPolicy`.
3. Add valid and invalid fixtures, including dangling references, unknown fields, and
   mismatched subject/profile versions; validate them in the repository gate.
4. Encode Stack as linked canonical records and keep `specs/stack.pspec` explicitly
   illustrative until a parser is justified.
5. Extend the existing link checker with a deterministic local file/directory loader,
   stable diagnostics, and no silent dropping of required or unsupported aspects.
6. Define the child-process adapter protocol, implement one independent reference
   Realization behind it, and keep the harness semantic oracle separate.
7. Select one bounded proof integration and machine-check one named Stack law without
   treating that proof assistant as the platform's universal foundation.
8. Add independently authored Rust and TypeScript realizations plus adapters.
9. Run shared property/model checks against both realizations and the resource/effect
   observations; demonstrate rejection of deliberately broken fixtures.
10. Persist the specification, realization, claim, evidence, and profile/policy links
    locally with provenance.
11. Expose a minimal CLI or web browser that makes evidence mechanism, result,
    applicability, assumptions, exclusions, and unknowns visible.
12. Implement an explainable compatibility query with separate semantic and
    directional realization-compatibility conclusions.
13. Record discoveries, revise the core model, and decide whether OrderedMap is the
    next semantic package.

## Quality gates

- Schema validation accepts every valid fixture and rejects every invalid fixture;
  undeclared required data is not silently ignored.
- The loader rejects dangling and version-mismatched references with stable,
  actionable diagnostics.
- Evidence and acceptance records pin their governing input revisions; a relevant
  predecessor change marks downstream acceptance stale until its gates are rerun.
- One named law is checked by a machine-invoked proof checker whose version,
  assumptions, inputs, and result are recorded.
- Both independent realizations satisfy the same reusable conformance suite.
- A law-breaking realization and a persistence-breaking realization are rejected with
  useful counterexamples.
- The effect boundary and its exclusions are shown explicitly; no claim is made about
  effects the adapter cannot observe.
- The browser/CLI distinguishes claim lifecycle from proof, test, benchmark, audit,
  and assertion evidence, and shows challenging, inapplicable, and unknown evidence.
- An unsubstantiated performance claim remains visible and is not reported as proved
  or measured.
- Compatibility output demonstrates semantic substitutability separately from its
  directional boundary mechanism and includes an operationally compatible but
  semantically unacceptable case.
- A fresh clone can run the documented gate commands and reproduce recorded fixture
  results.

## Verification commands

Current repository-structure gate:

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/check_repo.py
```

On a Nix host without the Python dependencies installed globally, the equivalent
invocation used for W2-G1 is:

```sh
nix shell --impure --expr \
  'with import <nixpkgs> {}; python3.withPackages (ps: with ps; [jsonschema rfc3339-validator])' \
  --command python3 scripts/check_repo.py
```

Wave 2 pins `jsonschema[format]==4.26.0` and `rfc3339-validator==0.1.4`; the checker
enables format assertion explicitly. The current Wave 3 gate also runs:

```sh
python3 -m py_compile scripts/check_repo.py scripts/record_check.py
python3 scripts/loader_fixture_check.py
python3 -m unittest discover -s tests/adapter -v
python3 -m py_compile semantic_packages/*.py tests/adapter/test_stack_runner.py fixtures/adapters/v1/fake_stack_adapter.py
python3 scripts/record_check.py fixtures/records/valid/*.json
python3 scripts/record_check.py fixtures/records/invalid/schema/spec/kind-array.json
```

Expected repository observation: `Record fixture checks passed: 9 valid, 20
schema-invalid, 38 link-invalid, 2 link-valid.`, `Loader fixture checks passed: 18
contract groups.`, `Adapter fixture checks passed: 18 tests.`, and `Repository checks
passed.` with exit status 0. The direct positive graph reports `Graph is valid: 0 diagnostics.`
with exit status 0; the negative graph reports `SCHEMA_KIND_TYPE
fixtures/records/invalid/schema/spec/kind-array.json#/kind` with the intended exit
status 1. Each later milestone must add its executable command and expected observation
here before its progress item may be marked complete. Gate the command's exit status,
not a grep or summary proxy.

## Progress

- [x] Repository knowledge scaffold
- [x] Research-to-design handoff audit
- [x] Temporary canonical interchange decision
- [x] Identity and reference invariants
- [x] Stack empty behavior and extensional observation
- [x] Adapter operation/observation/effect boundary
- [x] Persistence witness and falsifier
- [x] Execution profile, workload, and cost measure
- [x] Consumer treatment of evidence states
- [x] Conditional specification/realization claim and evidence scope
- [x] Design-closure ambiguity and counterexample review
- [x] Six core JSON schemas
- [x] Positive and negative schema fixtures
- [x] Spec loader
- [x] Reference model
- [ ] Proof integration
- [ ] Rust realization
- [ ] TypeScript realization
- [x] Shared conformance suite
- [ ] Evidence records
- [ ] Browser/CLI
- [ ] Compatibility explanation
- [ ] Retrospective and next ExecPlan

## Discoveries

- The existing `schemas/spec.schema.json` is a permissive scaffold, not a completed
  milestone: it neither models the six core entities nor closes references.
- The illustrative Stack law uses equality over an abstract carrier without defining
  extensional observation, so it is not yet portable executable semantics.
- Empty-pop behavior, generator bounds, the persistence witness, and the observable
  effect boundary are undefined.
- `amortized_O(1)` lacks a cost measure, workload, and profile. The initial fixture's
  `status: asserted` conflated claim state with evidence; the field was removed, so
  the claim remains visibly unsupported until linked evidence exists.
- The original plan omitted `RealizationProfile` and `ConsumerPolicy` schemas even
  though both are resolver inputs in the architecture.
- Same-spec registration is only a candidate relation. Semantic substitutability
  requires policy-, profile-, claim-, and evidence-relative evaluation.
- Realization compatibility is directional and context-dependent; language/runtime
  metadata alone cannot establish it.
- The repository gate currently checks required project-memory files, Markdown links,
  and JSON syntax. Schema validation, reference integrity, permanent negative
  fixtures, proof checking, conformance, and evidence provenance must become
  executable gates as their milestones land.
- The documented Python command is not available in every host environment. The
  fresh-clone gate needs a small reproducible development environment before it can
  be considered portable.
- `lang-bang` demonstrates a useful project-system ladder: keep durable invariants,
  volatile work, decisions, and derived views in different homes; de-risk with
  refuting probes; and promote repeated prose facts into generated or checked
  artifacts. ExecPlan 0001 adopts those principles without its mature-project
  orchestration overhead.
- A content-free dispatcher probe on 2026-07-18 verified strict read-only Claude
  launches through Claude Code 2.1.210 with explicit high effort. `sonnet` resolved
  to `claude-sonnet-5`.
  Both `fable` and the pinned `claude-fable-5` selector reported runtime usage as
  `claude-opus-4-8`; therefore evidence must retain requested and resolved identities
  rather than treating the friendly selector as provider proof.
- The tested homelab generation was activated on 2026-07-18. The live Claude Code
  2.1.212 profile resolved the pinned selector to runtime `claude-fable-5` through
  `agent-dispatch --read-only` with explicit high effort. The official manifest
  hashes, dedicated dispatcher regression test, Home Manager activation build,
  formatter, full homelab flake checks, and post-activation content-free probe all
  passed.
- Read-only external review prevents repository mutation but still discloses readable
  prompts, files, and tool results. The current approval boundary rejected sending
  repository documents during this probe, so no project content was disclosed. A
  future Claude node must record explicit authorization for its scoped disclosure.
- A content-free Herdr pilot created and supervised an interactive Sonnet 5 pane,
  detected its state, delivered follow-up input, and exposed output to the lead. Herdr
  is therefore the preferred observable PTY/worktree control plane around delegated
  processes, but not a replacement for `agent-dispatch`: it does not enforce sandbox,
  provider, depth, concurrency, or read-only policy.
- The prior dispatcher forwarded Herdr's arbitrary-process-launch socket into strict
  children, creating a confused-deputy escape from pagu-box. The activated generation
  removes that forwarding, adds a regression test, and records the boundary in its
  ADR. Inspection of the live wrapper confirms that neither `HERDR_*` nor Herdr's
  configuration directory is forwarded into delegated children.
- DC1 model-diverse review converged on exact `(kind, id, version)` record addresses,
  flat per-specification-version declaration IDs, top-first repeated-pop Stack
  observation, harness-owned comparison, opaque durable adapter handles, and
  boundary-scoped effect evidence. Sonnet's packet also proposed ID uniqueness across
  all same-kind records, which contradicted its own multi-version rule; the integrated
  invariant instead makes the full address tuple unique and permits one ID at multiple
  exact versions.
- The policy list conflated concern priority with proposition polarity. DC1 separates
  `required | preferred | optional | ignored` from semantic prohibitions. Selected
  challenging evidence blocks a required concern; missing or inapplicable evidence
  does not prove a required negative obligation. The conservative behavior is
  explicit and may later be parameterized without erasing contradictory evidence.
- DC1-R1 rejected the first integrated draft because named cost fields did not yet
  define a falsifiable proposition and evidence appeared to require a realization even
  for a specification-law proof. DC1-L2 now fixes the tracer profile, workload, unit,
  aggregation, bound, and supporting methods, and makes realization/adapter scope
  conditional on claim subject and evidence mechanism. The failed review remains in
  the DAG rather than being rewritten as an initial pass.
- W2-GPT1 found that treating an adapter as a canonical exact reference would silently
  create a seventh record kind. For the tracer, each immutable Realization instead
  embeds one versioned adapter descriptor; realization-executing Evidence repeats its
  `(id, version)` selector and the link checker requires an exact match. Multiple
  independently versioned adapters remain deferred until they justify another local
  namespace or canonical kind.
- W2-D1 proved that eight cleanly isolated link-negative graphs were still an
  insufficient oracle: a checker could ignore wrong-kind and exact-version handling or
  skip several reference-bearing surfaces and pass. W2-F2 therefore expands controls
  before checker implementation and makes each expected diagnostic include a code,
  source path, JSON pointer, and requested target.
- W2-R1 found that free-form Claim lifecycle could smuggle result/assurance language,
  JSON Schema date formats are annotations unless the validator asserts them, and
  policy event patterns could drift from the referenced effect contract. The successor
  uses a provisional lifecycle enum, explicit exact-set Evidence profile scope, asserted
  date validation, and a link rule binding policy patterns to declared events.
- W2-D2 rejected the first expanded oracle because unequal profile sets did not prove
  order-independent equality and typed local-role paths remained skippable. W2-F3 adds
  one zero-diagnostic `[A, B]` versus `[B, A]` graph plus isolated cost-measure,
  carrier, operation-family, Claim, and policy coherence falsifiers. W2-D3 passed the
  successor; the failed checkpoint review remains visible rather than being rewritten.
- The W2-P1 lead control used `jsonschema` 4.26.0 with `rfc3339-validator` 0.1.4
  and an explicit `FormatChecker`: all 7 schemas passed metaschema validation; 8 flat
  valid records and all valid/link-graph records passed shape validation; all 15 schema
  negatives rejected; all 105 JSON files parsed. This temporary lead control supports
  a checkpoint only; W2-C1 must make the same observations durable in the repository
  before W2-G1 can close.
- W2-CR1 rejected a checker that passed every checkpoint fixture: novel records showed
  missing subject-dependent Evidence scope, ambiguous duplicate profile members,
  policy event-role confusion, schema-classifier type crashes, lost reference
  candidates, and CLI tracebacks. W2-F4 converted those observations into red controls
  before W2-C2. The successor now passes 19 schema negatives, 35 link negatives, two
  link-valid graphs, direct missing/invalid-input CLI probes, and both diagnostics for
  a reference with simultaneous wrong-kind and wrong-version candidates. These are
  lead observations; W2-CR2 remains the independent generality gate.
- W2-CR2 then found a non-string `kind` crash, false dependent role errors after valid
  duplicate-ID diagnostics, and truncated multi-kind candidates. W2-F5 made those
  failures permanent controls; W2-C3 indexes roles as sets, type-checks `kind`, and
  reports all candidate kinds and versions. W2-CR3 passed the exact gate and repeated
  280 systematic wrong-type mutations with no exception or false acceptance. Failed
  CR1 and CR2 remain part of the checker assurance trail.
- W2-R2 found no material convergence blocker. It identified three deliberately
  deferred loader/oracle concerns: normalize input paths before identity and duplicate
  handling, define self-import and cyclic-import behavior when the loader exists, and
  promote coarse fallback schema diagnostics into exact oracles only when a new
  counterexample demands it. It also exposed the transitive RFC 3339 validator pin,
  which Wave 2 fixed before closing W2-G1.
- W3-S1, W3-S2, and W3-F1 independently converged on a thin source-set loader and
  phase barriers, but disagreed on symlinks, explicit extensions, and import cycles.
  W3-L0 chooses the smallest deterministic filesystem surface and preserves imports as
  exact visible edges only. The two cycle-rejection proposals are deferred, with
  namespace, elaboration, initialization, or transitive acquisition semantics as the
  reopen trigger; implementation order is not allowed to decide the question silently.
- W3-LF1 made the accepted boundary executable before implementation. The current
  checker reports directories as `INPUT_READ_ERROR`, accepts explicit non-JSON and
  symlink inputs, and cannot load the positive self/cycle/diamond/repeated-import
  graphs. All 16 committed loader JSON records parse, the harness compiles, and the
  accepted 8/20/38/2 record gate remains green. Both explicit and recursively
  discovered lowercase JSON symlinks must fail with `INPUT_SYMLINK`.
- W3-A0R1 rejected normative fresh handles because allocation is not observable, and
  rejected sharing the Realization's Stack code as the harness oracle because it would
  make tests tautological. The successor permits fresh or interned tokens with stable
  denotations, uses an independent trace oracle, ends sessions through EOF, separates
  protocol errors from semantic challenges, and explicitly leaves
  `realization-steps` unsupported. An undetectable perfect shadow adapter is expected
  to pass black-box behavior while retaining adapter-faithfulness and effect-
  completeness assumptions.
- W3-L1 makes lexical source aliases and file/directory overlap idempotent, recursively
  discovers lowercase JSON without following symlinks, preserves normalized source
  labels as provenance, and retains the input/schema phase barrier. Making source
  labels visible on schema diagnostics intentionally changes the earlier direct CLI
  spelling from pointer-only output; the durable loader oracle now freezes
  code/source/pointer/order together. W3-LR1 remains the independent generality gate.
- W3-LR1 then falsified that checkpoint with unhandled directory scan errors, repeated
  diagnostics for failing aliases and overlapping discovery, argv-dependent empty-set
  labels, traversal through intermediate symlink components, and incorrect root-base
  labels. Existing phase, direct-file, import-edge, address, and outside-base probes
  passed. W3-LF2 converts every blocker into a permanent oracle before W3-L2; the
  initial green checkpoint is not rewritten as convergence.
- W3-L2 made all 16 successor groups green, but W3-LR2 still blocked convergence.
  Exactly two leading slashes retain a special spelling under `posixpath.normpath`, and
  per-entry `DirEntry` classification errors still escape as tracebacks. A third probe
  replaced a classified regular file with a symlink before reading. ADR 0007 now states
  the smallest coherent boundary explicitly: this deterministic loader consumes a
  quiescent source tree and is not a secure traversal API for concurrent adversarial
  mutation. W3-LF3 freezes the two in-boundary defects; the race remains a documented
  exclusion and a future descriptor-based loader revisit condition rather than a
  silently partial security mechanism.
- W3-L3 closes both in-boundary defects. W3-LR3 reran the 18-group and full record
  gates, every prior blocker, and six novel probes covering independent `is_dir` and
  `is_file` errors, nested phase barriers, one-to-four leading slashes, reversed overlap
  ordering, and `PathLike` inputs. No in-boundary violation remained, so W3-LG1 closes
  with concurrent mutation and adversarial containment still explicit exclusions.
- W3-AF1 freezes the child boundary without implementing it. Fake adapters exercise
  reference-like, fresh/interned, destructive, wrong-result, nonterminating, event,
  malformed transport, process-failure, catchable-liar, and perfect-shadow behavior.
  A separate control requires the actual `semantic_packages.stack_adapter` command so
  a runner implemented only against test children cannot close W3-A1. The test suite
  compiles but currently fails at the intentionally absent product package.
- W3-A1 supplies an independently implemented immutable linked Stack behind the child
  adapter and a runner-owned expected-trace oracle. All 9 AF1 tests and the repository
  gate pass, including the actual module boundary. W3-AR1 remains the independent
  generality and lifecycle gate; authored green evidence does not close W3-AG1.
- W3-AR1 blocked that checkpoint. Clean request/response behavior followed by nonzero
  EOF exit, EOF hang, or extra EOF output is currently accepted as support; a missing
  command escapes instead of returning an error; stderr is drained rather than retained
  as provenance. A targeted child also showed that a nonempty pushed source can be
  rebound on its next use because the runner retains empty/remainders but not every
  constructed pushed handle. W3-AF2 freezes each observation before W3-A2.
- W3-A2 closes those six controls, but W3-AR2 found three narrower boundary defects.
  A SIGTERM-ignoring EOF hang consumes roughly three configured timeout windows;
  non-newline bytes emitted only after EOF are retained internally but treated as clean
  EOF; and an empty command escapes the `OSError` start boundary as `IndexError`.
  Large binary stderr, semantic/lifecycle cause precedence, depth-three persistence,
  and process cleanup otherwise passed. W3-AF3 freezes only the remaining defects.
- W3-A3 closes those final controls. W3-AR3 repeated the full suite and added deadline,
  large unterminated-output, stdout-close, termination-stderr, cause-precedence,
  command-shape, deep-persistence, immutability, and leak probes without finding an
  in-boundary violation. W3-AG1 adds executable Realization/adapter version `0.2.0`
  rather than mutating published Wave 2 version `0.1.0`, deliberately re-baselines the
  valid-record gate from eight to nine, and integrates all 18 adapter tests into G0.
- W3-P0S1 found a locally available core-only Lean 4.30.0 route for universal
  `pop-empty`, plus decisive `sorry` and admitted-axiom controls. W3-P0R1 challenged
  overbroad evidence wording, name-only theorem linkage, nonexistent supersession
  semantics, and the accepted `fixture-only` Evidence hazard. ADR 0009 accepts a
  corrected experiment: model-satisfaction/pipeline support only, exact statement and
  digest linkage, additional pending Evidence, and no authority over another law or
  proof system. Direct execution resolved Fable's unverified `--trust=0` objection in
  favor of the installed Lean 4.30.0 flag.
- W3-PF1 converts that boundary into 25 contract groups before product code. All
  committed Lean/JSON controls self-check against explicit Lean 4.30.0; the harness is
  red only because `scripts/proof_check.py`, the actual proof source, and its manifest
  do not yet exist. No canonical Evidence or schema changed.
- W3-P1 supplies the core-only universal model theorem, self-digesting manifest, and
  standalone phased checker. All 25 authored controls are green, including wrong-but-
  true statements and axiom dependencies. W3-PR1 remains the independent generality
  gate for coherent record/link drift, manifest authority, warnings, path boundaries,
  tool completion, and exact-statement strength.
- W3-PR1 confirmed the theorem is universal, core-only, and axiom-free, but blocked the
  checker boundary. Sixteen coherent mutations passed: semantic constants and record
  validity were not pinned, expected axioms could be widened, assignability stood in
  for exact theorem type, warnings and manifest/Evidence/path containment were porous,
  malformed structured output could forge success, and Lean execution had no timeout.
  W3-PF2 converts those categories into durable controls before W3-P2. The PR1 handoff
  also printed a conflicting Lean commit hash; repeated direct `lean --version` output,
  the manifest, and PF1 agree on `d024af099ca4bf2c86f649261ebf59565dc8c622`, which
  remains the accepted observed provenance rather than the reviewer transcript typo.
- W3-PF2 freezes the blocking review as 15 permanent successor groups, bringing the
  harness to 40 groups. The P1 checker remains green on all prior controls and red on
  exact-scope, schema/link, axiom-authority, theorem-type, warning, canonical-path,
  Evidence-input, structured-output, and timeout controls. The harness owns a three-
  second outer deadline and verifies that both version-query and proof-execution hangs
  leave no fake-Lean child process; this is a red checkpoint, not product acceptance.
  A read-only implementation consultation then found that the first PF2 draft repeated
  the PF1 Claim-reference and declaration-id mutations while demanding different sole
  diagnostics. The lead removed those duplicate successor witnesses before P2 rather
  than making diagnostic output depend on indistinguishable inputs; the original PF1
  exact-link controls and PF2 coherent-alternate-graph control retain the requirements.
  The same disposition makes the immutable-empty-axioms diagnostic precede proof
  execution when a hostile manifest attempts to authorize a known axiom; PF1 still
  observes both actual axiom-bearing sources under the accepted empty manifest.
- Two W3-P2 Claude Code 2.1.212 attempts used `agent-dispatch`, pagu-box `strict`, the
  isolated Wave 3 worktree, exact `claude-sonnet-5`, explicit high effort, and an
  exclusive checker/proof write boundary. The disclosed scope was the governing docs,
  checker/proof package, and committed proof fixtures. Both produced no handoff or
  filesystem change and were interrupted after prolonged pre-edit silence; a direct
  dispatcher-mediated `--version` health check succeeded. The lead therefore reassigned
  implementation internally while retaining provider diversity at read-only review.
- W3-P2 closes the authored successor harness at 40 groups. The checker now pins the
  ADR boundary and exact tool descriptor, schema-validates the two proof inputs, checks
  bounded semantic linkage, rejects manifest/Evidence/path escape and malformed Lean
  output, observes independently elaborated actual and expected types, requires an
  empty axiom audit, and bounds both Lean subprocess phases with process-group cleanup.
  The manifest's final runner digest is
  `148162e12e495a51b61947cc7f2babbde2e97f2f8d1ed682de714e72fdf19c04`;
  W3-PR2 still owns novel false-acceptance review and Evidence-specific trust concerns.
- W3-PR2 blocks P2 despite the 40 green authored groups. The internal static review
  found that arbitrary JSON can serve as optional Evidence, unused declared axioms and
  modifier-prefixed unsafe declarations are not rejected, a fixture-specific fallback
  accepts only one theorem-type observation, and the manifest runner is not bound to
  the executing checker. Fable 5 then demonstrated with real Lean that source-emitted
  information can put a false no-axiom line before the appended audit, causing an
  axiom-backed theorem to pass, and that source `#eval` can perform a filesystem write
  during checking. These are acceptance-boundary failures, not translation-fidelity or
  binary-attestation non-goals; W3-PF3 freezes them before P3.
- W3-PR2's Fable consultation used Claude Code 2.1.212 through
  `agent-dispatch --read-only`, pagu-box `strict`, exact `claude-fable-5`, explicit high
  effort, and only the listed repository docs/code/fixtures. Runtime model provenance
  was not separately disclosed. It used removed temporary sources, made no repository
  edits, delegation, or web requests. Two broader internal dynamic-review briefs were
  rejected by the safety classifier and produced no evidence; the successful internal
  lane was therefore narrowed to static code/generalization review and normal gates.
- W3-PF3 converts the five blocker categories into 8 groups and 42 cases. It requires
  original proof sources to reject declared axioms, modifier-prefixed unsafe code,
  `#eval`, and `#print` before Lean execution; exactly one independently named actual-
  type, expected-type, and axiom observation; a schema-valid exact Evidence record with
  bounded model wording, ADR assumptions/exclusions, and dynamic manifest/runner/input/
  tool/result provenance; and identity between the executing checker and manifest
  runner. The full 48-group/104-case P2 run completed in about 33 seconds, kept all 40
  prior groups green, and failed only the new controls.

## Decision log

- Start with Stack to validate the pipeline; move to OrderedMap only after the loop closes.
- Keep the storage format replaceable and the surface syntax provisional.
- Use JSON as the tracer bullet's temporary canonical interchange format; see
  [ADR 0003](../../decisions/0003-temporary-json-interchange.md).
- Treat unknown and assertion-only concerns as visible outcomes, not implicit passes.
- Use human-directed, lead-accountable collaboration over a revisioned work-dependency
  DAG; see
  [ADR 0004](../../decisions/0004-human-led-agent-team.md).
- Use model/provider diversity for independent concerns and reviews when useful, but
  derive authority and assurance only from the governing brief, artifacts, and evidence.
- Route routine execution to Sonnet 5 and complex consultation or skepticism to the
  Fable 5 profile, normally at high effort. Keep this choice in the active plan so it
  can change with availability and observed performance; do not encode it as a
  constitutional or architectural guarantee.
- Use Herdr for lead-side pane/worktree observability and interaction while retaining
  `agent-dispatch` as the bounded provider and sandbox boundary. Do not grant the
  Herdr control socket to delegated children.
- Address canonical records and references by exact typed `(kind, id, version)` tuples,
  with flat stable local declaration IDs per specification version; see
  [ADR 0005](../../decisions/0005-exact-typed-references.md).
- Treat prohibition as a required negative semantic obligation rather than an
  evidence-priority rank. Contested required concerns and unproved prohibitions do not
  pass by default; see
  [ADR 0006](../../decisions/0006-separate-priority-from-prohibition.md).
- Treat the multi-provider capability and verification-status matrix and secure dispatch workflow as
  operational project memory, with versioned facts re-probed before reuse; see
  [the multi-provider workflow](../../operations/multi-provider-workflow.md).
- Treat Wave 3 loading as deterministic discovery of one finite local source set and
  imports as exact visible edges only; do not infer filesystem acquisition, namespace,
  ordering, or compatibility semantics. See
  [ADR 0007](../../decisions/0007-local-loader-and-import-edges.md). This experimental
  choice was decided with retained dissent favoring an import DAG.
- Use the tracer-scoped child-process Stack adapter while keeping expected traces in
  the harness and handle identity unobservable. See
  [ADR 0008](../../decisions/0008-tracer-child-process-adapter.md). This does not select
  a universal transport or establish adapter faithfulness.
- Use one core-only Lean 4 probe as replaceable, specification-scoped model-satisfaction
  evidence for `pop-empty`, with exact statement/input/tool provenance and no authority
  over another law or a project-wide proof foundation. See
  [ADR 0009](../../decisions/0009-bounded-pop-empty-proof-probe.md).

## Result

Wave 1 design closure passed DC1-G1 after one rejected integration and a reviewed
successor. Wave 2 passed W2-G1 after four rejected checker/oracle checkpoints and
reviewed successors. The repository now carries seven strict schema files defining six
canonical record kinds, positive and falsifying schema/reference fixtures, and a
deterministic durable record gate. W3-LG1 now closes the provisional loader/import
slice after three implementation/review successors and 18 durable contract groups.
W3-AG1 now closes the executable Python reference Realization and shared adapter suite
after three reviewed successors and 18 durable tests. The bounded proof checker remains
active at its PF2 successor. No independent Rust or TypeScript realization, proof
Evidence gate, or browser has started.

## Stop and escalation conditions

- Stop before schema implementation if identity/reference or Stack observation rules
  are still ambiguous enough to permit incompatible interpretations.
- Stop and revise the design if a schema or resolver would collapse claim lifecycle,
  evidence review, evidence result, and assurance into one field.
- Stop and revise the design if a conformance adapter requires either realization's
  representation to become normative.
- Escalate to the user before changing constitutional intent, weakening an observable
  requirement, or selecting a universal proof/transport foundation.
- Treat a falsifying fixture as a design result; do not weaken it merely to recover a
  green gate.
