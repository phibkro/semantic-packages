# Agent instructions

## Mission

Build the smallest end-to-end system that demonstrates semantic specifications can be authored, checked, implemented independently, evaluated with explicit evidence, and browsed as the primary software artifact.

## Source of truth

Read these before substantial work:

1. `docs/vision/constitution.md`
2. `ARCHITECTURE.md`
3. `docs/design/core-model.md`
4. `docs/design/spec-language.md`
5. `docs/design/tracer-bullet.md`
6. the relevant file in `docs/exec-plans/active/`

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

## Completion standard

A change is complete only when:

1. its observable goal is stated;
2. relevant docs and schemas agree;
3. executable checks pass;
4. evidence and known exclusions are recorded;
5. the active ExecPlan reflects the resulting state.

## ExecPlans

For cross-cutting features or work expected to span multiple files, use an ExecPlan as defined in `.agent/PLANS.md`. Continue updating it while implementing; it is a living handoff artifact.
