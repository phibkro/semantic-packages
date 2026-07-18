# ADR 0008: Tracer child-process adapter

## Status

Accepted for ExecPlan 0001 only.

## Context

The canonical Stack reference Realization already declares protocol
`stack-runner-json-v1` and “JSON messages over a child process,” while the active plan
described an in-process reference adapter. A conformance harness must eventually run
the same observable boundary against independently authored implementations without
comparing their representations or sharing their operation code as an oracle.

## Decision

Keep the semantic oracle in the harness, implement the reference Realization
independently, and expose it through the tracer-scoped child-process protocol defined in
[the adapter protocol](../design/adapter-protocol.md). Use lockstep NDJSON, session-local
opaque handles, tagged pop results, and per-invocation adapter-reported event classes.
Closing stdin ends the session.

Handle identity, spelling, allocation, freshness, and interning are unobservable.
Protocol failures and adapter errors are execution errors; well-formed results that
violate Stack observations are semantic counterexamples. Passing the boundary does not
prove adapter faithfulness or absence of adapter-external effects.

## Alternatives and review corrections

- A special in-process harness boundary for the reference implementation would not
  exercise the protocol used by later independent Realizations and would contradict
  the canonical record.
- Making every returned handle fresh was rejected during review because it exposes an
  allocation property. Both distinct and interned tokens must pass when denotations are
  stable and extensionally equal.
- Reusing the reference implementation as the harness oracle was rejected as a
  tautological test. Expected traces remain harness-owned.
- A synthetic `shutdown` operation was rejected because process EOF already supplies
  lifecycle without adding a non-Stack operation.
- A universal ABI, Wasm boundary, or transport was not selected; the tracer needs only
  one replaceable executable boundary.

## Consequences

- Rust and TypeScript adapters can later implement the same small protocol without
  sharing representation or operation code.
- The runner can distinguish semantic challenges from protocol and execution errors.
- Effect conclusions remain scoped to adapter-reported events.
- Performance instrumentation remains absent and the performance concern unsupported.

## Revisit conditions

Revisit before adding general element types, concurrency, remote execution, adapter
discovery, cost instrumentation, or another specification family. Selecting a
universal transport or ABI requires separate architectural and operator review.
