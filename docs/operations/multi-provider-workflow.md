# Multi-provider agent workflow

## Purpose and authority

This runbook tells future leads how to use multiple agent models without widening
authority, hiding data disclosure, or turning model identity into assurance. It is an
operational snapshot, not architecture or constitutional intent. Repository
`AGENTS.md`, the active ExecPlan, inherited sandbox policy, and the user's current data
sharing authority take precedence.

Unless a row states otherwise, the capability observations below were verified on
2026-07-18. Re-probe versioned or environment-dependent facts before relying on them,
and record changed observations in the active ExecPlan.

## Capability and verification-status matrix

| Route | Current use | Boundary and status |
|---|---|---|
| Lead Codex and product collaboration agents | integration, bounded implementation, independent GPT-family concern/review nodes | Available through the agent product's collaboration controls and inherited sandbox. This is not permission to invoke a raw `codex` process. |
| `agent-dispatch` boundary | enforced cross-provider children, read-only isolation, and every writable provider task | The strict boundary remains governing. Two read-only consultations on 2026-07-19 failed before provider launch because both hard-coded worker slots reported occupied. On 2026-07-22 a Sonnet 5 child launched from a linked `/tmp` worktree but the strict sandbox omitted its parent `/srv/.../.git` directory, so Git provenance checks failed and the review correctly STOPPED. A later Fable review established provenance from a self-contained clone. The installed wrapper also conditionally forwards Herdr control variables when its parent has `HERDR_ENV=1`, contrary to this repository's stricter child boundary; until that wrapper is corrected, explicitly unset every `HERDR_*` control variable before dispatch and reject any launch evidence that still contains them. These are tooling/provenance defects, not reasons to weaken child or write isolation. |
| Claude Sonnet 5 | routine implementation, structured analysis, bounded execution | Route verified using `agent-dispatch claude`; request exact `claude-sonnet-5` and high effort. Claude Code 2.1.212 was observed in Wave 3, while Wave 4 preflight reported 2.1.210; two Wave 3 write attempts and the bounded Wave 4 W4-H1C0 attempt stalled without edits, so re-probe version/model resolution, bound retries, and retain an internal fallback. |
| Claude Fable 5 | complex reasoning, skepticism, convergence review | Route/version and one decisive Wave 3 review verified through Claude Code 2.1.212 using `agent-dispatch claude`; request exact `claude-fable-5` and high effort. On 2026-07-22 Claude Code 2.1.210 resolved exact `claude-fable-5` plus Haiku 4.5 auxiliary use and completed a 38-turn static implementation review from a self-contained read-only clone. Plan mode first stopped because no `ExitPlanMode` tool was exposed; an execution-mode retry inside the same OS read-only boundary completed. Python/Nix probes were denied, so the PASS remained conditional on lead-run executable gates. Several other Wave 3/4 consultations exhausted turns or produced no verdict, so do not make availability a silent hard dependency. |
| Delegated external Codex | possible cross-provider child work | The `agent-dispatch codex` entrypoint is advertised; execution is unverified. Probe the model, version, and task behavior before making it a plan dependency. Never invoke delegated `codex` directly. |
| Herdr | lead-side panes, pane output, status, interaction, worktree organization, and explicitly authorized interactive consultation | Operator-led Fable 5 consultation was observed through Herdr on 2026-07-19 with Claude Code 2.1.210, high effort, plan mode, and an exact checkout PWD. This route is trusted and procedural, not sandboxed or OS-enforced read-only; it is not a delegated child. The Herdr control socket and `HERDR_*` environment never enter dispatcher children. |
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
3. Decide whether consultation is read-only or execution needs writes. If explicit
   operator authority permits a Herdr advisor, also decide whether its broader trusted
   host boundary is acceptable; otherwise use dispatcher-enforced read-only mode.
4. For external writes, create an isolated worktree and grant one exclusive path set.
   Parallel writers otherwise need provably non-overlapping paths.
5. Dispatch every child and every writer through `agent-dispatch`. A lead already in
   Herdr may use the separately governed operator-led consultation sequence below.
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

Before dispatching from a linked worktree, run `git rev-parse --git-common-dir`. If its
result is outside the directory the strict child will receive, prepare a self-contained
disposable checkout at the exact revision and verify its clean state instead. A child
that can read files but cannot independently establish the requested Git revision must
STOP; file access alone is not provenance.

The dispatcher currently permits two delegated workers and depth two
(lead -> worker -> reviewer), then fails loudly. Every child enters pagu-box `strict`;
sandbox access may narrow but never widen. A read-only parent remains read-only, and a
network-denied parent cannot launch a cloud child.

Herdr may start or display the lead-side dispatcher process in a managed pane. The
child remains observable through its PTY, but it must not receive the Herdr socket,
configuration directory, or control environment. The lead-side pane may have
`HERDR_ENV=1`; a delegated child must not. The installed dispatcher observed on
2026-07-22 violates this stricter rule by forwarding the control plane conditionally.
Until fixed, invoke it through `env -u HERDR_ENV -u HERDR_WORKSPACE_ID -u
HERDR_TAB_ID -u HERDR_PANE_ID -u HERDR_SOCKET_PATH -u HERDR_CLIENT_SOCKET_PATH -u
HERDR_SESSION agent-dispatch ...`, then inspect launch evidence. If any control variable,
socket, or configuration bind remains, terminate the child and discard its result as
review evidence. Do not widen access to test or recover control.

### Operator-led Herdr consultation

This is a narrow exception for interactive read-only advice, not an alternative child
runtime. Each consultation requires new explicit operator authorization; authority
expires when that consultation ends and does not carry to another task. Use the route
only from a lead already inside Herdr (`HERDR_ENV=1`):

1. Confirm the target checkout is clean and contains exactly the revision to review.
2. Prefer one named, resumable advisor session per role in a dedicated Herdr tab. Exit
   to retain its session ID or name, then resume it in a pane whose PWD is the exact
   target checkout. Do not continue a live pane whose PWD or filesystem view belongs to
   another worktree. Use split panes only when the operator explicitly requests them.
3. Start or resume the provider through that Herdr tab, select the exact model, set high
   effort and plan/read-only mode, then inspect the pane to verify the resolved settings.
4. Give a bounded consultation brief that forbids edits, delegation, and external
   actions; name the public paths authorized for disclosure and the falsifier sought.
5. Observe status and retrieve the report through Herdr. Do not leave the session
   unattended or treat a provider retry as completed evidence.
6. Recheck the target checkout for changes. Any mutation fails the experiment and must
   be retained and escalated; do not use the result as read-only evidence.

The pane may inherit host credentials and Herdr control capability. Prompt-level plan
mode is not pagu-box `strict`, a dispatcher depth limit, or a filesystem guarantee.
Therefore use `agent-dispatch --read-only` instead for untrusted inputs, enforced
isolation, security-sensitive review, or unattended work. Use the dispatcher plus an
isolated worktree for every writable task.

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

For an operator-led Herdr consultation, additionally retain workspace/tab/pane and
provider session IDs or names, the pane PWD, verified interactive model/effort/mode,
explicit operator authorization, the absence of an OS-enforced sandbox, and before/after
checkout status. Never describe that packet as a dispatched child or strict read-only
assurance.

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
- **Raw provider launch:** never invoke a provider from an ordinary agent shell or use
  Herdr to evade dispatcher boundaries. The only direct route is the explicitly
  authorized, read-only, operator-led Herdr consultation above.
- **Writable consultation:** default skeptical or advisory nodes to read-only.
- **Pane proliferation:** do not equate target-checkout freshness with a new provider
  session or split pane. Resume the named advisor in a dedicated tab at the correct PWD.
- **Shared dirty worktree:** do not give an external writer a broad dirty checkout;
  use an isolated worktree and exclusive scope.
- **Detached worktree metadata:** a linked worktree may point to parent Git metadata
  outside the strict child's mounted paths. Use a self-contained exact checkout for
  provenance-sensitive review; never ask the child to trust a claimed revision or
  repair the mount.
- **Socket confused deputy:** never forward the Herdr control plane into a strict
  child, and never mislabel a Herdr advisor that inherits it as sandboxed.
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
