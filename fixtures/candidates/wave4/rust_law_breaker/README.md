# Rust pop-push negative-control fixture

This fixture is test data for Wave 4's candidate controls. It is not an accepted
Realization and must not be used as an implementation template.

`src/stack.rs` contains an independently implemented persistent Stack. `src/main.rs`
exposes it through the tracer-only `stack-runner-json-v1` NDJSON process boundary. The
adapter deliberately changes the value returned by the first nonempty `pop` in a
session while preserving the correct remainder; every later operation uses the Stack
result unchanged. This is intended to challenge only the `pop-push` declaration in the
canonical campaign.

Build directly with an edition-2024 Rust compiler; Cargo and external crates are not
used:

```sh
"${RUSTC:-rustc}" --edition 2024 -C linker="${CC:-cc}" \
  src/main.rs -o /tmp/semantic-packages-rust-law-breaker
```

The Wave 4 evidence run used rustc 1.96.1 and GCC 15.2.0. Their host-specific store
paths are provenance, not portable repository instructions.

Run the resulting executable as a lockstep child process:

```sh
/tmp/semantic-packages-rust-law-breaker
```

The request codec is deliberately bounded to the valid v1 request shapes and JSON
integers. It accepts JSON object members in any order with insignificant whitespace.
Malformed clients, a reusable JSON library, general element encoding, performance,
concurrency, and adapter-external event observation are outside this fixture.
