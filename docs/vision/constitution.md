# Project constitution

## Mission

Make semantic contracts reusable and distributable independently of executable implementations, while allowing independently authored realizations and explicit evidence to compete under consumer-defined policies.

## North-star outcome

A user can select a specification based on meaning, select or provide a realization based on deployment needs and trust policy, and inspect exactly what is proved, tested, measured, assumed, or unknown.

## Principles

1. **Meaning over mechanism** — specify observable guarantees; leave representations and algorithms open where possible.
2. **Contracts before implementations** — executable reuse is optional and subordinate to semantic reuse.
3. **Plural mathematics** — algebra, coalgebra, effects, resources, protocols, cost models, and domain logics may coexist rather than being forced into one universal logic.
4. **Explicit evidence** — proof, testing, benchmarking, audit, and assertion are distinct mechanisms with distinct scopes.
5. **Competing realizations** — multiple implementations of one specification are expected.
6. **Consumer authority** — users decide which concerns and assurance levels matter for a deployment.
7. **Compositionality** — specifications, realizations, evidence, refinements, and policies should compose where their semantics permit it.
8. **Tracer bullets** — establish the complete feedback loop before optimizing individual layers.

## Non-goals for the first prototype

- synthesizing arbitrary implementations;
- replacing general-purpose programming languages;
- proving all claims formally;
- defining a universal logic for every software domain;
- eliminating executable dependency reuse in all cases;
- optimizing cross-language execution before measuring it.

## Protected boundary

An implementation or agent may propose changes to project intent, but may not silently weaken requirements, redefine success, or erase contradictory evidence.
