# Contributing

## Lifecycle

```text
intent/classify → baseline/falsifier → design/risk → realize
                → evidence → converge/release → observe/maintain
```

This is a reversible evidence-bearing spine, not a mandatory waterfall. Select the
proportional change profile in
[`docs/design/lifecycle.md`](docs/design/lifecycle.md): feature, defect, improvement,
refactor, optimization, dependency/toolchain, migration/deprecation, incident,
experiment, documentation/specification, release/configuration, or governance.
Inherited research or design is named rather than silently skipped. Failed gates create
successor nodes and retain the failed result.

| Concern | Minimum retained observation | Gate |
|---|---|---|
| Intent | outcome, class, actor, authority, non-goals | protected semantics and reversibility are explicit |
| Baseline | current observation and cheapest useful falsifier | failure or deficit is observed for the intended reason |
| Design/risk | contract, inherited decisions, alternatives, recovery | affected semantic, compatibility, evidence, security, and operational concerns are disposed |
| Realization | smallest bounded change | acceptance criteria were not weakened |
| Evidence | positive, negative, regression, and relevant integration observations | claims match evidence scope and contradictory results remain visible |
| Convergence | review disposition, documentation, reproducibility, rollout | required gates pass and rollback/recovery is adequate |
| Learning | actual outcome and reopen triggers | plans, ADRs, backlog, ownership, and stale Evidence are updated |

## Change workflow

1. State the observable outcome.
2. Identify the governing specification and affected claims.
3. Create or update an ExecPlan for cross-cutting work.
4. Record and run the smallest observation that can falsify the intended result.
5. Implement the smallest vertical slice; use red–green–refactor where meaningful.
6. Reconcile/refactor only while preserving the now-green observable behavior.
7. Record evidence, assumptions, exclusions, recovery, and reopen triggers.
8. Run `python3 scripts/check_repo.py` and the relevant narrower gates.
9. Update the plan, backlog, ADRs, and design docs when learning changes the graph.

## Conventional commits

Every prospective commit and pull-request title uses this form:

```text
<type>[optional scope][!]: <description>
```

The allowed types are `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `build`,
`ci`, `chore`, `revert`, and `style`. Use a short lowercase scope when it helps a
reviewer locate the concern, and use `!` only when the change breaks an observable
contract. The description must contain non-whitespace text, and the whole subject or
title must be at most 72 Unicode characters. Merge commits and `fixup!`/`squash!`
subjects are rejected in a pull request's prospective `base..head` range.

Good subjects name the externally useful change rather than the editing activity:

```text
feat(registry): inspect the curated Stack theory publication
fix(governance): reject placeholder-only PR evidence
docs(lifecycle): record maintenance reopen triggers
```

For a breaking change, pair the marker with an explanation in the commit body and the
pull request's risks and recovery sections:

```text
feat(schema)!: require evidence input digests
```

The range rule is intentionally prospective: history before the pull request base is
not re-linted. A failing diagnostic names the commit and links back here so an author
can amend the local commit before publication. Do not weaken a title or split one
coherent change merely to satisfy the grammar; choose the type and scope that best
describe the actual lifecycle node.

Pull requests use [the repository template](.github/pull_request_template.md). Complete
every section with concrete outcome, lifecycle, governing scope, design, falsifier and
verification evidence, risks/exclusions, recovery/reopen triggers, and review
dispositions. `TBD`, `TODO`, comments, or headings without substantive content do not
close a section. The title follows the same Conventional Commit grammar so a squash
merge produces a useful durable history entry.

## Governance

Agents may change implementations, tests, plans, and nonconstitutional design documents. Changes to the constitution or project intent require explicit human review.
