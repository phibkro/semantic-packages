# TypeScript OrderedMap candidate

This dependency-free packet implements `ordered-map-runner-json-v1` with an immutable
class-to-value table plus a separate insertion-order sequence. The representation is a
private packet choice, not Specification meaning. The adapter translates valid bounded
requests into operations and session-local opaque handles.

```sh
${DENO:-deno} check --no-config --no-lock --no-npm --no-remote \
  adapter.ts ordered_map.ts
${DENO:-deno} run --no-config --no-lock --no-npm --no-remote --no-prompt \
  adapter.ts
```

Observed provenance is deno 2.9.2 and TypeScript 6.0.3. The packet has no network
imports and requests no runtime permissions.

adapter faithfulness and event completeness remain assumptions. external effects,
performance instrumentation, concurrency, malformed clients, registry-driven execution,
and cross-language interoperation are excluded. A runner report is an ephemeral fact,
not Evidence, review, registration, or acceptance authority.
