# Agent instructions

## Mission

Build the smallest end-to-end system that demonstrates semantic specifications can be authored, checked, implemented independently, evaluated with explicit evidence, and browsed as the primary software artifact.

## Source of truth

Read these before substantial work:

1. `docs/vision/constitution.md`
2. `ARCHITECTURE.md`
3. `docs/design/core-model.md`
4. `docs/design/system-map.md` for end-to-end plane, layer, trust-boundary, and
   implementation-status orientation;
5. `docs/design/user-journeys.md` when framing or accepting actor-visible work;
6. the relevant concern document under `docs/design/`:
   - authoring and observation: `spec-language.md`;
   - adapter execution: `adapter-protocol.md`;
   - claims and assurance: `evidence-model.md`;
   - resolution: `compatibility.md`;
   - work and gates: `lifecycle.md`;
   - current vertical slice: `tracer-bullet.md`;
7. the relevant file in `docs/exec-plans/active/`
6. before delegating across models or providers,
   `docs/operations/multi-provider-workflow.md`

Treat repository documentation as durable project memory. Do not rely on prior chat context.

## Working rules

- Preserve observable semantics; do not prescribe representation without a demonstrated need.
- Keep semantic compatibility separate from realization/interoperability compatibility.
- Separate claims from evidence supporting those claims.
- Never weaken a requirement merely to make an implementation pass.
- Prefer the smallest vertical slice that exercises the full lifecycle.
- Avoid selecting a universal proof assistant, implementation language, or transport before the tracer bullet demonstrates the requirement.
- Record consequential design changes as ADRs under `docs/decisions/`.
- Keep active plans updated as discoveries invalidate assumptions.
- Run `python3 scripts/check_repo.py` before declaring a task complete.

## Team model

The user owns mission, protected intent, and product priorities. Work under an active
ExecPlan is organized as a revisioned DAG of governing decisions, bounded work
packages, concern/evidence outputs, and convergence gates; roles attach to nodes rather
than forming a command hierarchy. The lead owns graph framing, bounded delegation,
shared-surface integration assignment, material-concern disposition, and acceptance
against the active ExecPlan. Crew agents own assigned nodes and are expected to
challenge affected nodes directly with evidence or counterexamples.

Delegated briefs must name the observable outcome, upstream dependencies, downstream
convergence gate, accountable owner, scope and exclusive write boundary, governing
documents, required evidence and review, non-goals, and stop/escalation conditions.
Parallel work must be read-only or have non-overlapping ownership; one integrator owns
each shared surface. Package-local reversible work may close through predeclared checks
without lead relay. Crew reports retain unresolved concerns and failed or contradictory
evidence. Model/provider diversity may reduce correlated blind spots, but model identity
never grants authority or assurance. See `docs/design/lifecycle.md` for the full protocol.

Cross-provider children must be launched through `agent-dispatch`; agents never invoke
`claude` or delegated `codex` directly. Read-only consultation uses
`agent-dispatch --read-only`, while delegated writes require an isolated worktree and
exclusive scope. The current dispatcher permits two delegated workers and depth two
(lead -> worker -> reviewer), then fails loudly; every child enters pagu-box `strict`,
and inherited authority may only narrow. Record requested and runtime-resolved model
provenance, explicit
effort, sandbox/write mode, and the externally disclosed data scope in the handoff.
Herdr may provide lead-side panes, status, interaction, and worktree organization, but
it does not replace `agent-dispatch` or become a child capability. Never expose its
control socket or `HERDR_*` control environment inside a delegated sandbox.
Follow the capability and verification-status matrix, routing, command patterns,
provenance packet, and failure handling in
`docs/operations/multi-provider-workflow.md`; re-probe versioned capabilities rather
than treating that operational snapshot as timeless.

## Completion standard

A change is complete only when:

1. its observable goal is stated;
2. relevant docs and schemas agree;
3. executable checks pass;
4. evidence and known exclusions are recorded;
5. the active ExecPlan reflects the resulting state.

## ExecPlans

For cross-cutting features or work expected to span multiple files, use an ExecPlan as defined in `.agent/PLANS.md`. Continue updating it while implementing; it is a living handoff artifact.
