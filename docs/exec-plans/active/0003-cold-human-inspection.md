# ExecPlan 0003: Cold-human semantic inspection journey

## Purpose and observable outcome

Move from an architecture proven once to a product that an uninvolved human can inspect.
Starting from the repository's documented entrypoint, the participant can select the
exact Stack graph snapshot and answer, without implementation archaeology:

1. what meaning is specified;
2. what is proved, tested, assumed, challenged, unsupported, or unknown;
3. which Realizations are semantically acceptable under the named policy/profile;
4. which directional deployment boundary each acceptable candidate requires; and
5. why the failed exact successor does not inherit predecessor Evidence and how the
   predecessor remains recoverable.

The first node reconciles durable project memory so the participant and future agents
do not begin from status claims contradicted by the accepted repository. The journey
is not accepted by documentation review or by the lead successfully running commands;
it requires a retained observation from a human who did not build the tracer.

## Context and repository map

ExecPlans 0001 and 0002 completed the bounded Stack architecture and actor-complete
local product loop. Their retained failures and evidence live under
`docs/exec-plans/completed/`. Current semantic authority remains in the constitution,
`ARCHITECTURE.md`, and concern documents. `docs/design/system-map.md` is the derived
current-state orientation, `docs/design/user-journeys.md` owns the four accepted actor
contracts, and this plan owns the next live edge.

The accepted predecessor includes six exact record kinds, deterministic finite loading,
one bounded Lean proof, Rust and TypeScript Realizations, declaration-scoped Evidence,
an honest 24-record graph, resolver and theory projections, a 31-record failed-successor
snapshot, exact predecessor recovery, and protected squash release. It does not include
human-facing `.pspec` elaboration, general assurance derivation, semantic refinement,
a second semantic domain, hosted acquisition, signatures, production search, or a web
browser.

## Non-goals and constraints

- Do not change canonical records, schemas, resolver semantics, Evidence meaning, or
  compatibility relations merely to improve prose.
- Do not count the project lead, a prior implementation agent, or a green repository
  gate as the cold-human observation.
- Do not collapse Evidence mechanisms/results/applicability into a badge or summary.
- Keep semantic acceptability separate from directional realization compatibility.
- Keep local finite registry semantics distinct from hosted acquisition and security.
- Do not build a general CLI framework, web UI, `.pspec` elaborator, or second semantic
  package before the baseline journey identifies an actor-visible deficit.
- Preserve Stack as the regression substrate; a future OrderedMap tracer joins it and
  never replaces it silently.

## Specification and documentation changes

M0 changes descriptive project memory only: archive completed plans; correct README,
system-map, user-journey, and backlog status; and name this plan as the current edge.
Any normative semantic change discovered by the human journey must enter a successor
design node or ADR rather than being disguised as usability documentation.

The cold-human protocol will freeze the participant brief, starting revision, allowed
documentation, commands, questions, expected observable facts, timing/assistance
limits, raw response retention, privacy boundary, and falsifier before product changes.
If the current surface fails, the smallest actor-visible successor may be documentation,
a thin graph-derived command, or a projection correction; its class follows the
observed failure rather than a preferred interface.

## Implementation steps and revisioned DAG

```text
M0 stale-memory baseline
  -> M1 descriptive reconciliation
  -> M-R independent truth/link review
  -> M-G memory gate
  -> H0 current-surface command inventory
  -> H1 cold-human protocol and falsifier
  -> H2 uninvolved-human observation
       -> PASS: H-G journey acceptance
       -> BLOCK: H-S smallest observed-deficit successor -> H2 replay
```

| Node | Owner, dependencies, and write boundary | Required evidence and downstream gate |
|---|---|---|
| M0 stale-memory baseline | continuity owner; read-only; depends on merged ExecPlans 0001/0002 and PR 6 | exact contradictory paths/claims, completed-plan census, and current product exclusions; releases M1 |
| M1 descriptive reconciliation | continuity owner; exclusive README, system map, user journeys, backlog, plan locations, and this plan | no semantic/product behavior change; completed history remains byte-identical except path; releases M-R |
| M-R1 memory truth review | independent read-only reviewer; depends on M1 | BLOCK: archived bytes, links, hosted/cold-human status, Evidence boundaries, compatibility separation, and route ordering pass; structural checker still required old active paths and Result text still called completed M1 remaining |
| M-S1 structural/status successor | continuity owner; depends on M-R1; exclusive checker inventory and this plan | complete: checker requires completed 0001/0002 plus active 0003, the failed full-gate observation is retained, and Result state follows the DAG |
| M-R2 memory truth successor review | same independent read-only reviewer; depends on M-S1 | BLOCK: both original functional blockers close and all prior boundaries hold, but M1 was retroactively given checker ownership discovered only by M-R1, misattributing M-S1 work and weakening retained history |
| M-S2 ownership-history successor | continuity owner; depends on M-R2; exclusive this plan | complete candidate: M1 keeps its original descriptive scope; the failed gate exposes an omitted structural dependency and M-S1 owns the checker correction |
| M-R3 final memory truth review | same independent read-only reviewer; depends on M-S2 | PASS: M1 retains its original scope, M-R1/S1 and M-R2/S2 history is truthful, both functional blockers stay closed, archive bytes/links/status/exclusions/Evidence/compatibility/route boundaries remain intact, and no self-ratification residue remains |
| M-G memory gate | lead acceptance; depends on M-R3 and repository gate | accepted: only active 0003 remains, completed 0001/0002 are byte-identical moves, stale live references are absent, M-R1/R2 failures and successors remain visible, M-R3 passes, diff hygiene passes, and the locked gate passes 24/20/38/3 records, 18 loader groups, 36 adapter tests, 18 candidates, 127 actor journeys, 20 governance tests, two reports/eight Evidence records, and 49 proof groups; releases H0 |
| H0 current-surface inventory | continuity owner; read-only; depends on M-G | exact current commands/APIs and their outputs mapped to the five participant questions; no proposed UI yet |
| H1 protocol freeze | continuity owner with independent review; exclusive journey protocol/tests/docs | participant eligibility, starting context, questions, assistance limits, success rubric, privacy, falsifier, and retained raw-observation form |
| H2 cold-human observation | operator-coordinated uninvolved human; depends on H1 | exact revision, environment, commands, answers, hesitation/failure points, assistance, duration, and exclusions; no repository write authority |
| H-S observed-deficit successor | continuity owner; depends on H2 BLOCK | smallest change tied to an observed actor deficit, with red-first scenario and independent review; returns to H2 |
| H-G journey gate | lead acceptance; depends on H2 PASS and locked local/hosted gates | all five questions answered accurately without hidden implementation knowledge; releases the OrderedMap plan |

## Quality gates and evidence required

### Memory reconciliation

- `docs/exec-plans/active/` contains only this live plan.
- completed plans remain available under `docs/exec-plans/completed/` with their
  rejected reviews and exact evidence history intact.
- README, system map, user journeys, backlog, and plan links agree that J1–J5, JG,
  checkout maintenance, and the Herdr workflow experiment are complete.
- hosted release is complete; the uninvolved-human inspection journey is explicitly
  unobserved.
- general assurance derivation, `.pspec` elaboration, second-domain generality,
  refinement, hosted acquisition/security, and browser UI remain absent.
- `git diff --check` and `python3 scripts/check_repo.py` pass.

### Cold-human journey

- the protocol begins from a public exact revision and a documented entrypoint;
- participant questions are answerable from graph-derived output rather than source
  code or private lead explanation;
- unsupported performance, assumptions, exclusions, and contradictory/non-supporting
  Evidence remain visible;
- semantic selection and directional deployment mechanism are answered separately;
- the successor cannot inherit predecessor Evidence, and predecessor recovery remains
  explainable without implicit `latest`, migration, or semantic-version inference;
- a wrong answer, required undocumented assistance, hidden source-code archaeology, or
  collapsed evidence state is a BLOCK and creates H-S.

## Progress

- [x] M0 stale-memory baseline
- [x] M1 descriptive reconciliation
- [x] M-R1 independent memory truth review rejected with two blockers
- [x] M-S1 structural/status successor
- [x] M-R2 independent memory truth successor review rejected with one history blocker
- [x] M-S2 ownership-history successor
- [x] M-R3 final memory truth review passed
- [x] M-G memory gate
- [ ] H0 current-surface command inventory
- [ ] H1 cold-human protocol freeze
- [ ] H2 uninvolved-human observation
- [ ] H-G cold-human journey gate

## Discoveries and changed assumptions

- Both completed ExecPlans remained under `active/`; README and system-map links taught
  future agents that accepted work was still live.
- The system map still called hosted release open and conditional on tool provisioning,
  even though protected PR 4 and maintenance PR 5 passed the locked hosted gate.
- The user-journey purpose still assigned release convergence to JG after JG acceptance.
- Every `Now` backlog item was already complete. The backlog also said to integrate one
  proof assistant and replace Stack with OrderedMap; the bounded Lean integration exists,
  and replacing Stack would destroy the required regression comparison.
- The first full-gate replay rejected the archive because `scripts/check_repo.py`
  required both completed plans at their former active paths. This exposed an omitted
  structural dependency outside M1's declared descriptive scope. M-R1 retained the
  failure, and M-S1 updates the inventory to require both completed histories and the
  sole active ExecPlan 0003 rather than weakening the required-memory check.
- Independent route consultations converged on a second-domain generality probe but
  differed on the immediate predecessor. The Fable review identified the cheaper
  unobserved cold-human inspection first; this plan accepts that ordering because it can
  reveal actor deficits before new semantic scope is added. OrderedMap record
  expressibility may be paper-probed during H0, but no implementation depends on it.

## Decision log

| Question and options | Evidence and concerns | Decision and reopen observation |
|---|---|---|
| archive completed plans or keep them active as context | `.agent/PLANS.md` requires completed plans to move; two active completed plans caused current-state contradictions | move both byte-identically to `completed/` and link them as history; reopen if an accepted predecessor is substantively reopened rather than merely referenced |
| next route: cold-human inspection, OrderedMap, refinement, `.pspec`, adapter Evidence, or hosted registry | current architecture is complete for Stack but its human inspectability is explicitly unobserved; second-domain work before observing current output may compound usability deficits | run cold-human inspection first, then OrderedMap; refinement and `.pspec` wait for two semantic domains, adapter Evidence waits for a non-circular mechanism, hosted infrastructure waits for an actor need |
| replace or retain Stack when adding OrderedMap | replacement would remove the only accepted regression substrate and turn generality into a rewrite | retain Stack and add OrderedMap as a structurally different peer; reopen only if maintaining both creates measured unsustainable duplication |

## Result and remaining work

M0 identified contradictory durable status and established the accepted product
plateau: one complete local Stack loop, not a general semantic-package ecosystem. M1
completed the descriptive reconciliation. M-R1 retained two exact blockers: the
required-file checker still named old active paths, and this Result paragraph lagged
the Progress state. M-S1 closes both in the candidate. M-R2 then retained one
history-attribution blocker after M1 was retroactively assigned checker ownership;
M-S2 restores the original boundary and attributes the omitted dependency to its true
successor. M-R3 and the final locked gate pass, so M-G accepts the reconciled memory
and releases H0 current-surface inventory.

After H-G, the intended route is OrderedMap generality, then deployment-profile choice,
explicit refinement/evolution, cross-domain `.pspec` elaboration, and non-circular
adapter-faithfulness Evidence. Hosted acquisition, signatures, indexing, and richer UI
remain later actor-driven routes rather than infrastructure goals.

## Stop and escalation conditions

- stop if reconciliation changes normative semantics or erases a retained failure;
- stop if a completed plan is rewritten rather than moved byte-identically;
- stop if the cold-human protocol uses a participant already familiar with tracer internals;
- stop if success requires interpreting implementation representation or private source;
- stop before claiming generality from Stack alone or compatibility from version syntax;
- escalate protected-intent changes, standing external-provider authority, participant
  privacy decisions beyond the recorded protocol, or a request to weaken the five
  terminal questions.
