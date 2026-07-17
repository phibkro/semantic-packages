# Execution plans

An ExecPlan is a living design and implementation document that lets an agent complete substantial work using only the repository and the plan.

Each ExecPlan must contain:

1. **Purpose and observable outcome**
2. **Context and repository map**
3. **Non-goals and constraints**
4. **Specification changes**
5. **Implementation steps in dependency order**
6. **Quality gates and evidence required**
7. **Progress checklist**
8. **Discoveries and changed assumptions**
9. **Decision log**
10. **Result and remaining work**
11. **Stop and escalation conditions**

Plans must describe commands and expected observations. Update the plan whenever implementation reveals that the original design is wrong or incomplete. Completed plans move from `docs/exec-plans/active/` to `docs/exec-plans/completed/`.

De-risk each consequential step with the smallest probe or negative fixture that can
falsify its premise. Record rejected routes and the evidence that rejected them when
future agents might otherwise repeat the work.

For delegated work, the plan must also record a revisioned work-dependency DAG: each
package's accountable owner, hard predecessors, downstream convergence gate, exclusive
write ownership, integration points, reviewer, evidence packet, and escalation owner.
One integrator owns each shared file or surface. Failed gates create successor nodes
and retain their observations rather than mutating accepted history. Evidence packets
record tool and model/provider provenance when it affects reproducibility. For
cross-provider nodes, record requested and runtime-resolved model IDs, explicit effort,
dispatcher/tool versions, sandbox and PWD mode, worktree and exclusive write scope,
network and externally disclosed data scope, prompt/brief revision, outputs, checks,
fallbacks, failures, and reviewer provenance. A model consultation is normally a
`supports` or `challenges` edge, not a hard predecessor.

Material decision-log entries record the question and options, governing concerns,
evidence or falsifying probe, decision and rationale, dissent and its disposition, and
the observation that would reopen the decision. Consequential accepted choices still
graduate to ADRs.
