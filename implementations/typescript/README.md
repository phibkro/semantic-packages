# TypeScript Stack realization

This package independently realizes the Stack 0.1.0 operations behind the
tracer-scoped `stack-runner-json-v1` child-process boundary. `stack.ts` uses immutable
linked nodes; that representation is package-private and is not part of Stack meaning.
`adapter.ts` owns only session-local opaque handles and NDJSON translation.

The package has no third-party dependencies, package manifest, network import, or
runtime permission request. Check and run it offline with Deno:

```sh
${DENO:-deno} check --no-config --no-lock --no-npm --no-remote \
  implementations/typescript/adapter.ts implementations/typescript/stack.ts
${DENO:-deno} run --no-config --no-lock --no-npm --no-remote --no-prompt \
  implementations/typescript/adapter.ts
```

The Wave 4 implementation run observed Deno 2.9.2 and TypeScript 6.0.3. Those are
provenance, not a requirement to use one machine-specific executable path.

The adapter assumes valid v1 requests, one lockstep session, element integers in the
selected `-2` through `2` profile domain, and a harness that treats returned handles
as opaque. Canonical-decimal nonnegative sequence numbers are compared without a
JavaScript safe-integer bound and echoed exactly; alternate integral JSON spellings
such as `1.0`, `1e3`, and `-0` are not selected by this boundary. Malformed-client
behavior, adapter faithfulness, event completeness,
external effects, performance instrumentation, concurrency, remote transport,
browser use, registry-driven execution, and cross-language interoperation remain
outside this package's claim.
