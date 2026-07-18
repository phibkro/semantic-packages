# Rust Stack realization

This package independently realizes Stack with an immutable, bottom-first boxed slice.
`src/stack.rs` contains only the Stack operations. `src/main.rs` is the thin
`stack-runner-json-v1` adapter: it assigns session-local opaque handles, translates
bounded valid JSON requests, and reports no adapter-observed events.

The package intentionally has no Cargo manifest or third-party crates. Wave 4 uses a
direct edition-2024 compiler boundary because an exact offline `rustc` and C linker are
available while Cargo and vendored dependencies are not. This is an experimental
tracer choice, not a general Rust packaging recommendation.

## Build and run

From the repository root, select tools through `RUSTC` and `CC` or their portable
defaults:

```sh
"${RUSTC:-rustc}" --edition 2024 -C "linker=${CC:-cc}" \
  implementations/rust/src/main.rs -o /tmp/stack-rust-adapter
/tmp/stack-rust-adapter
```

The repository candidate matrix constructs the same build as a shell-free argument
vector and passes the resulting binary path separately to the conformance runner.

Observed Wave 4 build provenance was `rustc 1.96.1 (31fca3adb 2026-06-26)` with GCC
15.2.0. These versions describe the reviewed run; the portable instructions do not pin
host-specific store paths.

## Scope

The adapter accepts the three exact v1 request shapes, independent of object-member
order and insignificant whitespace, for JSON integers in the selected `-2` through `2`
domain. It emits one LF-terminated response per request, requires monotonically
increasing canonical-decimal nonnegative sequence numbers without a machine-integer
bound, echoes them exactly, and exits successfully when stdin closes.

Malformed client behavior, general JSON interchange, nontrivial Unicode/element-number
domains, concurrency, remote transports, adapter discovery, performance evidence, and
adapter-external effect completeness are outside this package's Wave 4 claim. An empty
`events` list means only that this adapter reported no events.
