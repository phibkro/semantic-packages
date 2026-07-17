# Evidence model

## Assurance is multidimensional

A single “verified” badge is insufficient. Evidence is indexed by concern and mechanism.

| Concern | Example mechanisms |
|---|---|
| algebraic correctness | proof, property tests |
| protocol safety | model checking, trace tests |
| memory safety | language guarantee, proof, sanitizer evidence |
| performance | complexity proof, benchmark |
| security | formal model, fuzzing, audit |
| interoperability | conformance and differential tests |

## Status lifecycle

Evidence review may use workflow states:

```text
unverified → pending → accepted
                    ↘ rejected
accepted → superseded/revoked
```

This workflow is distinct from assurance strength.

## Required metadata

Every evidence record must expose:

- claim identifier;
- specification and realization versions;
- method and toolchain;
- assumptions;
- environment or generated domain;
- result and timestamp;
- exclusions;
- provenance/signature where available.

## Formal verification qualification

“Formally verified” means a proposition was proved relative to a model, assumptions, logic, and trusted kernel. It does not mean the specification captures every intended real-world property.
