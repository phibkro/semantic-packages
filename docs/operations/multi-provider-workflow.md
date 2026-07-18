# Multi-provider agent workflow

## Purpose and authority

This runbook tells future leads how to use multiple agent models without widening
authority, hiding data disclosure, or turning model identity into assurance. It is an
operational snapshot, not architecture or constitutional intent. Repository
`AGENTS.md`, the active ExecPlan, inherited sandbox policy, and the user's current data
sharing authority take precedence.

The capability observations below were verified on 2026-07-18. Re-probe versioned or
environment-dependent facts before relying on them, and record changed observations in
the active ExecPlan.

## Capability and verification-status matrix

| Route | Current use | Boundary and status |
|---|---|---|
| Lead Codex and product collaboration agents | integration, bounded implementation, independent GPT-family concern/review nodes | Available through the agent product's collaboration controls and inherited sandbox. This is not permission to invoke a raw `codex` process. |
| Claude Sonnet 5 | routine implementation, structured analysis, bounded execution | Route verified using `agent-dispatch claude`; request exact `claude-sonnet-5` and high effort. Claude Code 2.1.212 was observed in Wave 3, while Wave 4 preflight reported 2.1.210; two Wave 3 write attempts and the bounded Wave 4 W4-H1C0 attempt stalled without edits, so re-probe version/model resolution, bound retries, and retain an internal fallback. |
| Claude Fable 5 | complex reasoning, skepticism, convergence review | Route/version and one decisive Wave 3 review verified through Claude Code 2.1.212 using `agent-dispatch claude`; request exact `claude-fable-5` and high effort. Several later Wave 3/4 consultations exhausted turns or produced no verdict, so do not make availability a silent hard dependency. |
| Delegated external Codex | possible cross-provider child work | The `agent-dispatch codex` entrypoint is advertised; execution is unverified. Probe the model, version, and task behavior before making it a plan dependency. Never invoke delegated `codex` directly. |
| Herdr | lead-side panes, pane output, status, interaction, and worktree organization | Optional observable control plane. It is neither the sandbox nor provider boundary. The Herdr control socket and `HERDR_*` control environment never enter delegated children. |
| OpenCode / Kimi | potential future diversity route | Not supported by the current dispatcher contract. Do not invoke directly; first add and review a bounded dispatcher/provider adapter. |
| Local Gemma or another local model | potential low-cost, low-sensitivity probe | No route or task capability is verified. Do not substitute it for a required node without a fit-for-task probe and recorded reassignment. |

Availability is not authority. A model may support or challenge a node, but only the
governing brief, artifacts, executable evidence, concern dispositions, and convergence
gate can accept work.

## Routing policy

Use the smallest capable team:

- Sonnet 5 at high effort for straightforward execution and bounded synthesis.
- Fable 5 at high effort for complex ambiguity, system-level skepticism, or a
  consequential convergence review.
- An internal GPT-family collaboration agent when available, or a separately probed
  external Codex child through `agent-dispatch`, for an independently framed concern,
  implementation, or review when diversity can reduce correlated blind spots.
- For consequential work on the same issue, prefer at least two independently prompted
  model families when available. Give them the same governing question before either
  sees the other's preferred answer.

Do not vote or average confidence. Fuse propositions, counterexamples, artifacts, and
observations. The lead records each material concern as incorporated, falsified,
accepted risk, deferred with an owner and trigger, or escalated. A failed review creates
a successor node; it is not rewritten into an initial pass.

Model choice is a revisable execution annotation. Provider quota, latency, or
unavailability must not block unrelated DAG nodes, and fallback is recorded rather
than hidden.

## Delegation sequence

1. Read the governing documents and active ExecPlan.
2. Define the node ID and revision, observable outcome, hard predecessors, downstream
   gate, accountable owner, integration owner, scope, non-goals, falsifier, required
   evidence, disclosure scope, and stop conditions.
3. Decide whether consultation is read-only or execution needs writes.
4. For external writes, create an isolated worktree and grant one exclusive path set.
   Parallel writers otherwise need provably non-overlapping paths.
5. Dispatch through `agent-dispatch`; never invoke raw `claude` or delegated `codex`.
6. Independently verify returned artifacts and resolved model provenance.
7. Attach the packet through `supports`, `challenges`, or the declared hard dependency;
   dispose concerns and run the convergence gate.

Consultation normally is not a hard predecessor. Make it one only when the brief says
the gate cannot safely close without that observation.

### Delegation brief template

Use this structure for every bounded node; omit no field silently:

```text
Node/revision and accountable owner:
Observable outcome:
Upstream dependencies and governing documents:
Downstream convergence gate and integration owner:
Read/write mode, worktree, and exclusive path scope:
Authorized external data and network scope:
Required artifacts, evidence, and independent review:
Non-goals:
Falsifier and stop/escalation conditions:
Requested provider/model, effort, and fallback policy:
```

## Secure command patterns

The installed CLI is authoritative; check `agent-dispatch --help` and the delegated
tool's version before using these templates. Create the brief in an owner-only file or
private temporary directory, set `node_brief_path` to that path, and remove the file
after use. Do not put secrets in a prompt, argument, transcript, or tool result.

Read-only Sonnet consultation from the repository PWD:

```sh
agent-dispatch --read-only claude -- \
  --model claude-sonnet-5 --effort high \
  --permission-mode plan --tools Read,Grep,Glob \
  --no-session-persistence --output-format json -p < "${node_brief_path}"
```

For complex review, replace the model with `claude-fable-5`. A writable execution uses
`agent-dispatch claude` without `--read-only`, runs with the isolated worktree as its
PWD, and grants only the tools needed by the brief, for example:

```sh
agent-dispatch claude -- \
  --model claude-sonnet-5 --effort high \
  --permission-mode acceptEdits --tools Read,Grep,Glob,Edit,Write,Bash \
  --no-session-persistence --output-format json -p < "${node_brief_path}"
```

The dispatcher currently permits two delegated workers and depth two
(lead -> worker -> reviewer), then fails loudly. Every child enters pagu-box `strict`;
sandbox access may narrow but never widen. A read-only parent remains read-only, and a
network-denied parent cannot launch a cloud child.

Herdr may start or display the lead-side dispatcher process in a managed pane. The
child remains observable through its PTY, but it must not receive the Herdr socket,
configuration directory, or control environment. The lead-side pane may have
`HERDR_ENV=1`; a delegated child must not. If a child sees any `HERDR_*` control
variable, Herdr socket, or Herdr configuration path, stop the node and escalate it as
a boundary regression. Do not widen access to test or recover control.

## Data and secret boundary

Read-only prevents mutation, not disclosure. Before an external launch, name exactly
which repository paths, prompts, tool results, and network sources the provider may
receive. Prior approval in another repository or task is not blanket authorization.

Never disclose credentials, loopback API keys, authentication files, environment
dumps, or secret-bearing command output. If a secret appears in any transcript or tool
result, rotate it, verify the old value is rejected, and record only the remediation
and non-secret evidence.

## Required evidence packet

When provider or model choice matters, retain:

- node ID/revision, role, accountable owner, and integration/review owner;
- requested provider/model and runtime-reported primary and auxiliary model IDs;
- explicit effort, dispatcher version, delegated tool version, and prompt/brief revision;
- read-only or writable mode, sandbox profile, PWD mode, worktree, and exclusive paths;
- authorized external disclosure and network scope;
- artifacts changed, commands and exit results, positive and negative observations;
- assumptions, exclusions, permission denials, retries, fallback or reassignment;
- unresolved concerns, failure evidence, reviewer provenance, and gate disposition.

Friendly aliases are not provenance. Inspect structured runtime output such as
`modelUsage`; if the resolved primary model differs from the requested exact model,
record the mismatch and do not cite the requested name as proof of execution.

Use the following disposition footer so a successful-looking handoff does not erase
failed or contradictory evidence:

```text
Node/revision:
Requested -> runtime-resolved model; auxiliary models:
Route, versions, effort, sandbox/PWD, worktree/write scope:
Externally disclosed data and network scope:
Artifacts and commands with exit observations:
Assumptions, exclusions, denials, retries, and substitutions:
Material concerns: incorporated | falsified | accepted risk | deferred(owner/trigger) | escalated
Reviewer provenance and convergence-gate result:
```

## Failure handling and anti-patterns

- **Alias drift:** an alias resolves to another model. Pin the exact selector, inspect
  runtime usage, update the tool if appropriate, and retain the failed observation.
- **Raw provider launch:** never bypass `agent-dispatch` for convenience.
- **Writable consultation:** default skeptical or advisory nodes to read-only.
- **Shared dirty worktree:** do not give an external writer a broad dirty checkout;
  use an isolated worktree and exclusive scope.
- **Socket confused deputy:** never forward the Herdr control plane into a strict child.
- **Standing model authority:** do not accept work because it came from Fable, Sonnet,
  GPT, a local model, or a majority of agents.
- **Anchored diversity:** do not show every reviewer the lead's preferred answer before
  independent framing when correlated error is the risk being tested.
- **Silent fallback:** record provider/model substitution, changed effort, or reduced
  tools; re-run any evidence whose provenance matters.
- **Permission denial misread as semantics:** distinguish sandbox/tool failure from a
  product counterexample, and retain both accurately.
- **Unbounded output as evidence:** keep concise rationale, artifacts, falsifiers, and
  observations; hidden reasoning or long transcripts are not assurance.
- **Provider outage as global blocker:** release unrelated nodes and create a recorded
  reassignment or retry only for affected dependencies.
- **Stale capability claims:** recheck CLI versions, exact model resolution, dispatcher
  limits, and installed Herdr behavior after environment changes.

## Revisit triggers

Update this guide and the active ExecPlan when a provider adapter is added, a model
selector changes resolution, dispatcher depth/concurrency/sandbox behavior changes,
Herdr's security boundary changes, a local model becomes a verified route, or repeated
multi-model review fails to expose useful independent concerns. Consequential boundary
changes belong in an ADR rather than only this runbook.
