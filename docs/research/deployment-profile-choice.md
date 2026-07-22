# OrderedMap deployment-profile choice probe

## Question and retained result

Can the next consumer tracer choose between genuinely different deployment profiles
without silently treating Evidence from one profile as assurance for another? The
retained probe answers **yes, but only through append-only successor facts and fresh
profile-bound campaigns**. It rejects the tempting shortcut of relabeling the accepted
OrderedMap reports or Realizations.

The two candidate records under
[`fixtures/research/ordered-map-profile-choice/`](../../fixtures/research/ordered-map-profile-choice/)
hold the OrderedMap input domain, workload, scale, concurrency, and cost vocabulary
constant. They differ only where deployment differs:

| Candidate profile | Platform/runtime boundary | Distinguishing host constraint |
|---|---|---|
| `ordered-map-native-process/0.1.0` | x86_64-linux native child process | native runtime |
| `ordered-map-deno-sandbox/0.1.0` | Deno 2.9 x86_64-linux child process | Deno runtime with network denied |

This is a controlled comparison, not a new semantic domain and not a claim that the
two runtime boundaries interoperate. The profile records are research candidates, not
members of an accepted registry manifest.

## Falsifier and consequence

The accepted Rust and TypeScript Realizations support only
`ordered-map-ascii-fold/0.1.0`. All 14 Claims and all 14 linked Evidence records across
law, persistence, and effect concerns have that same exact applicability set. Both
retained campaign reports also bind the exact old profile path and digest. Therefore
every accepted Claim and Evidence item is inapplicable to both candidate profiles,
even when its toolchain happens to resemble a proposed runtime boundary. The probe
freezes that complete census and includes derived relabel/addition controls so a
single broadened record breaks the exact-applicability oracle.

Any implementation that edits those applicability sets, changes the accepted
Realization bytes, or copies the old result behind a new profile address fails the
probe. Environment resemblance is not an Evidence-transfer rule. Introducing such a
rule would be specification/profile refinement work and needs its own concrete
falsifier and design gate.

## Released actor contract

The smallest honest green successor keeps exact profile selection rather than adding
heuristic ranking:

1. append two profile records and two exact ConsumerPolicies;
2. append one successor Rust Realization supporting only the native profile and one
   successor TypeScript Realization supporting only the Deno profile;
3. run profile-specific conformance plans and retain new reports rather than reusing
   the old profile-bound reports;
4. author profile-scoped Claims and Evidence for the policy-required law, persistence,
   and effect concerns; keep performance optional and visibly unsupported until a
   profile-specific measurement or proof exists;
5. expose two exact consumer decisions from one captured append-only graph, each with
   one acceptable matching package and the other profile's valid Evidence listed as
   inapplicable;
6. keep the directional child-process boundary separate from semantic acceptance.

The negative controls are: swapped profile Evidence is inapplicable and blocks its
required concern; an unknown, omitted, range, or implicit-latest profile selector
fails closed; the old accepted graph and its two decisions remain byte-for-byte and
behaviorally unchanged; no performance conclusion is inferred from runtime metadata.

This probe does not authorize generalized profile refinement, Evidence migration,
performance comparison, interoperability compatibility, or changes to Stack.
