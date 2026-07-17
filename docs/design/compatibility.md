# Compatibility and resolution

## Semantic graph

Edges express relations such as:

- implements;
- refines;
- observationally equivalent;
- translates to;
- satisfies under profile;
- conflicts with.

Semantic compatibility is always relative to a specification version, required claim
set, consumer policy, and applicable profile. `implements` is a declared candidate
edge; acceptable evidence is required before the resolver reports satisfaction.

## Realization graph

Edges express practical composition mechanisms and costs:

- direct same-language linking;
- shared managed runtime;
- native FFI;
- Wasm component/canonical ABI;
- RPC/process/message boundary;
- incompatible.

Realization compatibility is directional and context-dependent. It is derived from
both endpoints, available adapters/bindings, deployment constraints, and policy; it
is not an equivalence relation inferred from language names. Stored edges are
explainable observations or declared mechanisms that the resolver may re-evaluate.

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

The execution profile describes the requested environment and workload. Realization
metadata describes what an implementation offers. A match between the two is a
resolver result, not something implied by sharing a profile label.

## Resolver output

A resolution is an explainable result, not merely a chosen package:

- selected realization(s);
- semantic relation used;
- evidence supporting each required claim;
- boundary mechanism and estimated integration cost;
- unmet preferences and unknowns.

The resolver must be able to demonstrate the distinction with at least two cases:

1. semantically acceptable realizations that require a non-direct boundary; and
2. operationally composable realizations that fail the consumer's semantic or
   evidence policy.
