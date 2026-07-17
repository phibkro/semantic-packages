# ADR 0004: Human-led work-dependency DAG

## Status

Accepted.

## Context

The project should be managed at the level of intent, product direction, semantic
boundaries, and evidence rather than turning the main conversation into a stream of
implementation details. Specialist agents can explore and execute more effectively,
but their concerns must influence decisions without obscuring accountability or the
protected long-term vision.

## Decision

Use human-directed, lead-accountable collaboration over a revisioned work-dependency
DAG. The DAG describes readiness and artifact flow, not an organizational hierarchy or
the full deliberation network. Roles annotate nodes; they do not form a command tree.
Corrections create successor nodes so prior evidence and dissent remain visible:

- the user owns mission, protected intent, and product priorities;
- the lead agent owns graph framing, dependency and gate criteria, bounded delegation,
  concern disposition, shared-surface integration assignment, and acceptance of
  integrated results without becoming the relay for every interaction or local check;
- specialists own delegated nodes, may influence any affected node laterally through
  evidence or objections, and are expected to challenge assumptions;
- an independent reviewer or skeptic attempts to falsify consequential work;
- different models/providers may occupy independent nodes to reduce correlated blind
  spots, but model identity conveys neither rank nor assurance;
- evidence and governing constraints decide technical disputes, not agent count;
- every material concern receives an explicit disposition, and protected-boundary or
  hard-to-reverse disputes escalate to the user.

The main conversation stays at the managerial and product level. Implementation detail
returns as evidence packets, decisions, risks, counterexamples, and requests for
direction rather than raw activity logs.

## Alternatives and dissent

- **One generalist agent performs all work:** simpler coordination, but weaker
  independent challenge and too much implementation detail in the management thread.
- **Autonomous agent swarm:** more parallelism, but diffuse authority, conflicting
  writes, and greater risk of local optimization drifting from the constitution.
- **Majority vote or forced consensus:** appears collaborative but gives agent count
  false epistemic weight and can erase minority evidence.
- **Human approves every implementation choice:** preserves authority but makes the
  feedback loop unnecessarily slow; reversible choices within an accepted contract
  remain delegated.

No dissent overrides the constitutional protected boundary. Minority reports remain
attached when their objection is unresolved or its predicted failure remains testable.

## Consequences

- Delegated work needs explicit scope, ownership, evidence, review, and stop conditions.
- The lead remains accountable for synthesis and independently verifies returned artifacts.
- Parallel work is read-only, path-exclusive, or isolated; shared surfaces have one integrator.
- Each node has one accountable owner; contributors and reviewers may be plural.
- Independent nodes proceed when their named predecessors close; nominal waves are not global barriers.
- Relevant predecessor or gate changes invalidate downstream acceptance until evidence is rerun.
- External provider use follows explicit data-sharing authority; local review remains available without it.
- Decisions may close with documented dissent rather than artificial unanimity.
- More deliberation is spent on consequential or irreversible choices; routine
  reversible implementation decisions remain fast.

## Revisit conditions

Revisit this model if it repeatedly adds delay without exposing hidden assumptions, if
lead-owned convergence becomes a queue rather than an accountability boundary, if
evidence packets fail to let the lead verify delegated work, or if project scale
requires a different integration topology. Any replacement must preserve human
authority over mission and the constitutional protected boundary.
