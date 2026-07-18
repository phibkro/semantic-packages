# TypeScript persistence-breaker fixture

This fixture is an external negative control for Wave 4. It implements the Stack
operations and `stack-runner-json-v1` envelope independently, then deliberately
changes one retained nonempty source in the canonical campaign's retained-source push
case. The returned extension is computed before that change. The fixture must
therefore challenge only `persistence` with `RETAINED_HANDLE_CHANGED` while
`pop-empty`, `pop-push`, and `stack-effects` remain supported.

The trigger is deliberately test-only: within the one adapter session, the fourth
`empty` begins the canonical retained-source push case and its second `push` changes
that case's retained nonempty source. This package is never a mode of an accepted
Realization, and a later TypeScript candidate must not reuse it.

The adapter accepts only the exact valid request shapes and profile integers selected
by protocol v1. Its only import is the fixture-local Stack module; it has no external
dependencies. JSON object order and insignificant whitespace are ignored. It emits
only LF-terminated JSON responses on stdout, reports no events, and exits zero after
clean EOF. Malformed client requests, general JSON values, networking, browser use,
performance, concurrency, and adapter faithfulness are outside this fixture's scope.

Set `DENO` to a reviewed offline Deno executable. The Wave 4 evidence run used Deno
2.9.2 with TypeScript 6.0.3; its host-specific store path is provenance, not a portable
repository instruction:

```sh
"${DENO:-deno}" check \
  --no-config --no-lock --no-npm --no-remote \
  fixtures/candidates/wave4/typescript_persistence_breaker/adapter.ts \
  fixtures/candidates/wave4/typescript_persistence_breaker/stack.ts
```

A reordered and whitespace-varied valid request followed by EOF must produce one
clean response and exit zero:

```sh
printf ' { "op" : "empty", "args" : { }, "seq" : 0 }\n' | \
  "${DENO:-deno}" run \
    --no-config --no-lock --no-npm --no-remote --no-prompt \
    fixtures/candidates/wave4/typescript_persistence_breaker/adapter.ts
```

The shared default campaign is the semantic oracle. Run it from the repository root;
the printed tuple must be
`('challenges', ('RETAINED_HANDLE_CHANGED',), [('persistence', 'challenges', ('RETAINED_HANDLE_CHANGED',)), ('pop-empty', 'supports', ()), ('pop-push', 'supports', ()), ('stack-effects', 'supports', ())])`:

```sh
/nix/store/wjw50ljy6vyvv61d3pnqmhfzfpvsjnbj-python3-3.14.6-env/bin/python3 -c \
  'import sys; from semantic_packages.stack_runner import default_stack_conformance_plan, run_stack_conformance; report = run_stack_conformance(tuple(sys.argv[1:]), plan=default_stack_conformance_plan()); print((report.result, report.causes, sorted((item.declaration_id, item.result, item.causes) for item in report.declaration_outcomes)))' \
  "${DENO:-deno}" run \
  --no-config --no-lock --no-npm --no-remote --no-prompt \
  fixtures/candidates/wave4/typescript_persistence_breaker/adapter.ts
```
