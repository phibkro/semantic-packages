# ADR 0003: Temporary JSON interchange

## Status

Accepted for ExecPlan 0001 only.

## Context

The tracer bullet needs one canonical representation that schemas, fixtures, the
loader, link checks, and the browser can share. The illustrative `.pspec` syntax does
not yet have defined parsing or elaboration semantics. Implementing it first would
mix surface-language design with validation of the end-to-end lifecycle.

## Decision

Use JSON as the temporary canonical interchange format for the six core records in
ExecPlan 0001, validated with JSON Schema draft 2020-12. Keep `.pspec` as a
noncanonical authoring sketch until the tracer bullet demonstrates what its parser
must preserve.

This decision does not make JSON the semantic model or the final authoring language.
Record identity, references, observable meaning, and evidence rules remain format
independent.

## Consequences

- The first schema, fixture, loader, graph, and browsing work shares one unambiguous
  interchange representation.
- Surface-syntax questions cannot block the lifecycle tracer bullet.
- A later parser must elaborate to the canonical records and preserve stable IDs and
  diagnostics.
- Replacing JSON requires migration fixtures and an updated ADR, not changes to the
  semantic contract merely for serialization convenience.
