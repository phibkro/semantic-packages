# Compatibility and resolution

## Semantic graph

Edges express relations such as:

- implements;
- refines;
- observationally equivalent;
- translates to;
- satisfies under profile;
- conflicts with.

## Realization graph

Edges express practical composition mechanisms and costs:

- direct same-language linking;
- shared managed runtime;
- native FFI;
- Wasm component/canonical ABI;
- RPC/process/message boundary;
- incompatible.

## Realization metadata

```yaml
language: rust
language_version: "..."
target: wasm32-wasip2
runtime: wasmtime
interface: wasm-component-model
abi: canonical-abi
memory_model: linear-memory
build_system: cargo
```

Language is meaningful because it predicts ecosystem reuse, runtime sharing, FFI requirements, and optimization opportunities. It is not itself evidence of semantic conformance.

## Resolver input

```text
required specification
consumer concern policy
minimum evidence policy
execution/deployment profile
acceptable interoperability cost
```

## Resolver output

A resolution is an explainable result, not merely a chosen package:

- selected realization(s);
- semantic relation used;
- evidence supporting each required claim;
- boundary mechanism and estimated integration cost;
- unmet preferences and unknowns.
