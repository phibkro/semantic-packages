# ADR 0015: Operator-led Herdr consultation boundary

## Status

Accepted by MP-H1 after explicit operator authorization on 2026-07-19, the retained
MP-H1R1/R2 blockers, MP-H1R3/R4 successor PASS reviews, and the full locked repository
gate. It does not replace dispatcher enforcement for children or writable work.

## Context

The multi-provider workflow previously required every provider launch to pass through
`agent-dispatch`. During north-star route mapping, two read-only Fable 5 dispatches
failed before launch because the dispatcher's two worker locks reported occupied even
though no corresponding dispatcher process was observable. The operator explicitly
asked the lead to test consultation through Herdr instead and update the workflow if
effective.

Reusing an older advisor pane was not effective: its checkout-scoped view could not see
the target merged-state worktree. A new pane created with the intended checkout as its
PWD successfully started Claude Code 2.1.210, resolved Fable 5 at high effort, entered
plan mode, read the authorized public strategic documents, and remained observable
through pane status and transcript. The checkout stayed unchanged. Provider API retry
latency remains ordinary failure evidence, not proof that the route completed.

Unlike a dispatcher child, a provider started in a Herdr pane is a host process. Its
read-only instruction is procedural; it may inherit credentials and Herdr control
capability; it has no pagu-box `strict` guarantee or dispatcher depth limit. Calling it
a child or sandboxed review would conceal the material security difference.

## Decision

Retain `agent-dispatch` as the only route for cross-provider children, writable work,
unattended execution, untrusted input, and consultation requiring enforced isolation.
Never invoke a raw provider from an ordinary agent shell.

Permit a separate operator-led Herdr route only when all of these conditions hold:

- the operator explicitly authorizes the broader trusted boundary for this
  consultation; that authority expires when the consultation ends;
- the lead is already inside Herdr and resumes or starts one named advisor session in a
  dedicated tab whose pane has the exact intended clean checkout as its PWD; split
  panes require explicit operator direction;
- the task is bounded, interactive, read-only advice with no edits, delegation, or
  external actions;
- model, effort, plan mode, PWD, authorized public disclosure, pane identity, and lack
  of OS-enforced isolation are verified and recorded;
- the checkout is checked for mutations before and after; and
- the result contributes only support or challenge evidence and cannot ratify a gate.

A live pane whose PWD or visible filesystem is another worktree is invalid. Exit and
resume the same named/session-ID advisor in the correctly scoped tab rather than
spawning another advisor. Any write, unexpected disclosure, lost observability, or need
for unattended continuation stops the experiment and returns the node to the dispatcher
or the lead.

## Consequences

- Provider diversity can remain available when dispatcher worker slots are wedged,
  without falsely claiming the same containment.
- Named session continuity preserves advisor context without multiplying provider
  sessions, while dedicated tabs avoid consuming the operator's shared mobile view.
- Herdr becomes an explicitly modeled trusted consultation route as well as a lead-side
  control plane; it still does not become a delegated-child sandbox.
- Every writable provider task keeps the existing isolated-worktree and dispatcher
  requirements.
- The dispatcher lock observation remains a separate operational defect. This ADR does
  not weaken its limits or claim to repair it.
- Consultation success is judged by a usable bounded report plus unchanged checkout,
  not merely by launching the provider or seeing it read files.

## Rejected alternatives

- Treating the Herdr pane as equivalent to `agent-dispatch --read-only` was rejected
  because the enforcement and inherited capabilities differ materially.
- Broadly replacing `agent-dispatch` with Herdr was rejected because writes and child
  delegation still require bounded authority and OS enforcement.
- Continuing a persistent advisor in a pane scoped to another worktree was rejected
  after its target view proved stale. Resuming that session at the correct PWD is the
  preferred successor, not creating another advisor.
- Waiting indefinitely for a wedged dispatcher or provider retry was rejected because
  consultation is normally a support/challenge edge, not a global blocker.

## Revisit conditions

Revisit if Herdr gains an enforced child sandbox, the provider can be launched with a
verified stripped control environment and filesystem policy, dispatcher lock handling
is repaired, a consultation mutates state, or the route exposes credentials or control
capability beyond the explicitly accepted boundary.
