# ADR 0007: Local loader and import edges

## Status

Accepted for ExecPlan 0001 only.

## Context

Wave 2 validates records supplied as explicit file paths, but path spelling can make
one physical source appear twice and directories are not a defined input. The Stack
tracer also carries exact Specification import references without defining namespace,
visibility, elaboration order, recursive acquisition, or registry behavior. Letting
filesystem traversal or an implementation's recursion strategy decide those semantics
would turn incidental mechanism into product meaning.

## Decision

Define the Wave 3 loader as a deterministic local source-set front end to the existing
schema and link checker. It normalizes lexical path aliases relative to one captured
base directory, deduplicates one normalized source reached more than once, recursively
discovers lowercase `.json` regular files under explicit directories, rejects explicit
non-JSON and symbolic-link inputs, and preserves normalized source paths only as
provenance. Canonical record identity remains `(kind, id, version)`.

Input and schema failures form a phase barrier: the checker reports those failures
without manufacturing downstream dangling-reference diagnostics from a partial graph.
An empty discovered source set is an input failure. Diagnostic code, normalized source
label, JSON pointer, ordering, and exit status are stable; operating-system prose is
not.

For ExecPlan 0001, a Specification import is only an exact visible edge to another
loaded Specification record. Imports do not locate files, merge namespaces, re-export
declarations, impose initialization order, or infer compatibility. Self-imports,
cycles, diamonds, and repeated exact edges are therefore structurally valid when every
target is present. A target outside the supplied local source set remains dangling even
if a matching file exists elsewhere.

## Alternatives and dissent

- Rejecting self-imports and strongly connected components would preserve a possible
  future package DAG. Two independent Wave 3 reviewers preferred that route. It is not
  adopted because current imports have no elaboration or visibility semantics, module
  systems do not universally require acyclicity, and the restriction would select a
  speculative future model before the tracer demonstrates the need.
- Following file symlinks and deduplicating by resolved inode-like identity would make
  some aliases convenient, but adds platform and containment behavior unrelated to
  canonical record identity. Rejecting symlinks is the smaller deterministic slice.
- Loading an explicitly named non-`.json` file based only on its contents is possible,
  but conflicts with the tracer's declared temporary interchange boundary and makes
  accidental `.pspec` treatment plausible.
- Immediate-only directory discovery is smaller locally but does not load a nested
  finite registry tree. Recursive discovery remains bounded and deterministic when
  symlinks are excluded.

## Consequences

- Filesystem paths are reproducible provenance, never semantic addresses.
- Repeated argv, lexical aliases, and file/directory overlap are idempotent.
- Distinct files carrying one canonical address still produce a duplicate-address
  diagnostic.
- Import cycles cannot cause loader recursion because imports never acquire files.
- Registry acquisition, authoring elaboration, namespace composition, refinement, and
  compatibility remain separate future concerns.

## Revisit conditions

Revisit before imports gain namespace, declaration visibility, refinement,
initialization, or transitive acquisition semantics, or before symlinks and portable
filesystem identity become supported inputs. Add new falsifying fixtures and migrate
affected records rather than silently changing the meaning of this provisional loader.
