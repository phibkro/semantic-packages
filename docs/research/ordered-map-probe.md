# OrderedMap second-domain paper probe

## Status and question

This is O1b research input for ExecPlan 0004, not an accepted Specification or a
canonical registry source. It asks whether a structurally different domain can state
honest observable meaning in the current record model and identifies the first product
surface that blocks its actor journey.

The decisive question is not “can a JSON Schema accept another ID?” It is: can a theory
author state one observation, law, visible unknown, and targeted breaker without
prescribing representation, and how far can that exact record travel through the
current product path before Stack-specific authority stops it?

## Candidate observable contract

`OrderedMap[Key,Value]` is an abstract finite mapping whose live key-equivalence
classes have stable first-insertion order. The concrete key representative retained or
returned for a class is deliberately unobserved. The minimal surface is:

| Kind | Declaration | Observable meaning |
|---|---|---|
| carrier | `Key` | abstract key domain governed by `key-equivalence`; no host equality commitment |
| carrier | `Value` | abstract value domain governed by `value-equivalence`; no host equality commitment |
| carrier | `OrderedMap` | finite mapping from key-equivalence classes to values; no tree, hash table, array, mutation, or ownership commitment |
| operation | `empty` | produces a map with no entries |
| operation | `put` | adds a new key/value or replaces the value at an equivalent existing key |
| observation | `lookup` | returns the value associated with an equivalent key, or `None` |
| observation | `entries` | returns the finite live sequence of key-equivalence classes and associated values in first-insertion order; concrete key representatives are not observed |
| equivalence | `key-equivalence` | declared equivalence relation over `Key` used to identify one live key class |
| equivalence | `value-equivalence` | declared equivalence relation over `Value` used for lookup and entry comparison |
| equivalence | `ordered-map-equivalence` | pointwise equality of the `entries` class/value sequence under the two declared equivalences |
| law | `lookup-empty` | `lookup(empty, k) == None` |
| law | `lookup-put-same` | looking up the inserted key returns the inserted value |
| law | `lookup-put-other` | inserting a non-equivalent key does not change another key's lookup |
| law | `put-existing-position` | putting an equivalent key preserves the existing key class position and replaces its associated value; retention or replacement of a concrete key representative is unobserved |
| law | `put-new-appends` | a genuinely new key appends exactly one entry |
| effect | `ordered-map-effects` | `io.*` forbidden inside the declared observation boundary; `debug.emit` optional; unlisted events unspecified |
| resource | `persistence` | retained map handles remain usable and observationally unchanged after `put` on them or derived handles |

`key-equivalence` and `value-equivalence` are required to be equivalence relations and
are semantic input, not host equality. The selected finite campaign may instantiate
JSON integers with ordinary integer equality, but that scopes Evidence and does not
narrow the normative laws to integers. `entries` observes the order of key-equivalence
classes and associated values, never which concrete representative an implementation
stores or returns.

Deletion is excluded from the first probe. Without deletion, “first insertion order of
live keys” and overwrite position have one small falsifiable meaning. Add deletion only
when an actor journey demonstrates whether reinsertion restores an old position or
appends a new one; guessing now would create semantics unrelated to the generality
question.

## Breaker and finite observation

Two candidate Realizations can use private representations such as an ordered sequence
of pairs and a key-index plus separate order sequence. These are examples for
independence review, not normative choices.

The cheapest targeted breaker moves an existing key class to the end on overwrite. Its
non-vacuous witness uses inequivalent keys `k1` and `k2`: construct
`m0 = put(put(empty, k1, v1), k2, v2)`, then observe
`put(m0, k1, v3)`. Correct class/value order is `[(class(k1), v3),
(class(k2), v2)]`; the breaker returns the reversed class order. It should continue to
satisfy `lookup-put-same`, `lookup-put-other`, and new-key append behavior while
challenging only `put-existing-position` and cases that observe the changed `entries`
sequence. A finite campaign over a declared small key/value domain and bounded
operation histories can falsify the law; passing remains bounded test Evidence, not a
universal proof.

All declarations with no Claims or selected Evidence remain visibly unclaimed/unknown.
The actor-complete design will add one optional performance proposition so the package
resolver also retains an explicit unsupported, non-blocking concern; its exact workload
and measure belong to O2 rather than this theory-only probe.

## Categorical and higher-order disposition

The observation-first contract is compatible with the coalgebraic reading already
present in Stack: consumers distinguish states by observations, not constructors or
representation. That validates the design direction without requiring a coalgebra
framework.

Map/fold identity or fusion laws are attractive category-shaped candidates, but the
current executable boundary cannot generate, serialize, or compare arbitrary functions.
The record schema could store such a law as prose while the campaign could not falsify
it, producing ornamental generality. The minimal tracer therefore defers higher-order
map/fold laws. Reopen them only with a bounded named transformation vocabulary or a
separately justified function-observation protocol.

No import translates meaning and no version asserts refinement in this slice, so
institution morphisms, satisfaction-preserving translations, simulation, and
bisimulation are not yet triggered. Propositions-as-types remains internal to any
future proof mechanism; this tracer does not make its Specification a type.

## Executed probes

The retained research fixture uses the exact declarations above at address
`(specification, ordered-map, 0.1.0)`. It is deliberately outside the canonical
registry: [`fixtures/research/ordered-map`](../../fixtures/research/ordered-map/) and
[`tests/research/test_ordered_map_probe.py`](../../tests/research/test_ordered_map_probe.py)
make every observation below replayable.

1. Current canonical record and link validation:

   ```sh
   python3 scripts/record_check.py fixtures/research/ordered-map/records/spec.json
   ```

   Observation: `Graph is valid: 0 diagnostics.`

2. Current manifest graph plus theory projection over the retained one-member manifest:

   ```sh
   python3 -m unittest tests.research.test_ordered_map_probe
   ```

   The existing `inspect_stack_graph` name is Stack-specific, but its supplied-manifest
   mechanics accepted the exact record without default discovery or execution.
   `project_theory` required no domain-specific change and exposes all 17 declarations
   as unknown.

3. Current theory-publication actor view over the same record:

   The same replayable test requires exactly four
   `PUBLICATION_MISSING_ADDRESS` diagnostics and one
   `PUBLICATION_UNEXPECTED_ADDRESS` diagnostic.

   Four diagnostics require the frozen Stack theory addresses and one rejects the
   OrderedMap address. This is the first real product blocker: publication authority is
   derived from the Stack manifest at module import, not from an explicit supplied
   manifest/contract.

## Design consequence and falsifier result

The current declaration model, exact linker, manifest-governed graph mechanics, and
theory projection are sufficient for this paper contract. Do not extend their semantic
forms or fork an OrderedMap projection merely to create visible work.

The first extraction candidate is a manifest-driven theory publication observation with
Stack retained as a compatibility wrapper. That choice is not yet authorized for code:
O-R1 blocked the first candidate, O-S1 made the required corrections, and O-R1b must
verify them before the domain-contract gate. Registration and resolver design remain
downstream because the theory author cannot yet publish the new domain.

## Sources and interpretation boundary

- Goguen and Burstall's
  [institution framework](https://publish.lfcs.inf.ed.ac.uk/reports/90/ECS-LFCS-90-106)
  motivates delaying cross-logic composition until satisfaction must survive a change
  of notation or logic.
- Lambek and Scott's *Introduction to Higher-Order Categorical Logic* motivates the
  typed-calculus/category/proof-lane connection discussed in the research synthesis.
- The [HoTT Book](https://homotopytypetheory.org/book/) is one source for distinguishing
  structured types from mere propositions; this project uses proof relevance only as a
  Claim/Evidence analogy and adopts none of HoTT as a universal foundation.

This probe establishes expressibility and the first observed blocker only. It does not
establish publication, Realization conformance, Evidence, resolution, maintenance,
human usability, or generality.
