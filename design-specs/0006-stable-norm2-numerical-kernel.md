# Design spec 0006: stable approximate `norm2` numerical kernel

## Contract status

Pre-implementation contract for semantic domain four and one stacked pull request.
Revision 1 freezes the user need, observable approximation relation, campaign,
falsifiers, Definition of Done, and exclusions on 2026-07-23 before production code.
Any semantic change requires a numbered revision with the triggering observation and
reopens affected controls. Algorithms, internal precision, branching, modules, and
languages remain implementation choices. This feature starts from the opened
interaction-protocol PR at exact head `9407be2` and has its own branch and PR.

## User need

A package consumer implementing geometry, scaling, or distance calculations needs a
2D Euclidean-norm kernel that does not overflow or underflow merely because an
intermediate square is outside the binary64 range when the mathematical result is
representable. The consumer must be able to select a realization under an explicit
binary64 profile, see the exact approximation relation and finite inputs checked, and
keep numerical acceptance separate from the process boundary needed to call it.

A numerical theory author needs to state `sqrt(x²+y²)` over mathematical reals without
requiring a naïve square-and-add algorithm, a particular scaling method, internal
precision, instruction set, or source language. A package author needs an exact input
encoding and observable error rule. A theory consumer needs to see the mathematical
proposition and its limitations without package source or a selection decision.

## Felt user journey

```text
nix develop --command python3 -m semantic_packages numerical inspect \
  registry/stable-norm2/manifest.json \
  --output /tmp/stable-norm2-inspection.json
```

Expected summary:

```text
inspected stable-norm2 0.1.0: 2 registered realizations accepted, 1 overflow breaker challenged across 36 cases; tolerance=2-ulp; satisfaction=policy-relative -> /tmp/stable-norm2-inspection.json
```

The command authenticates one finite local graph and campaign plan, executes two
registered independent kernels and one naïve breaker in isolated child processes,
computes a high-precision campaign oracle outside every candidate, evaluates every
output under the frozen relation, resolves exact Claims/Evidence under one profile and
policy, reports directional boundaries separately, and atomically writes a closed
`numerical-package-inspection-v1` report. Its conclusion is only
`bounded-approximate-kernel-observed`.

## Observable numerical contract

The operation is the mathematical real function

```text
norm2(x, y) = sqrt(x*x + y*y)
```

for the finite non-NaN binary64 inputs in the retained campaign whose mathematical
result is representable as a finite binary64 value. Inputs and outputs cross the child
boundary as canonical `float.hex()` strings, preserving the exact tested binary64
values without making source-language decimal parsing authoritative.

For each input pair, the runner constructs an independent 100-decimal-digit oracle from
the exact binary64 values, takes the nonnegative square root, and rounds that oracle to
binary64. A candidate supports the case exactly when:

1. it returns one syntactically valid finite binary64 value;
2. the value is nonnegative; and
3. its ordered binary64 distance from the rounded oracle is at most **2 ULPs**.

The ULP metric orders finite binary64 bit patterns monotonically, treating `-0.0` and
`+0.0` as distance zero. It is an observation relation under profile
`stable-norm2-binary64`, not equality of source representation or a universal real
number metric.

The fixed twelve-case campaign covers:

- `(0,0)`, unit axes, and `(3,4)`;
- sign invariance and swapped operands;
- adjacent and ordinary inexact magnitudes;
- large equal values whose naïve squares overflow but result is finite;
- highly unbalanced large/small values;
- small equal normal values whose naïve squares underflow; and
- subnormal/normal-boundary inputs.

Passing all twelve cases is finite Evidence. It does not prove the bound for every
binary64 pair or establish correctly rounded output.

## Values and constraints

1. **Approximation is explicit.** No ambient language epsilon, decimal digit count,
   approximate-equality helper, or candidate-selected tolerance has authority.
2. **Oracle independence.** Expected values and ULP ordering live in the runner and
   frozen tests, never in candidate source or candidate output.
3. **Meaning over algorithm.** Scaling, ratio reduction, fused operations, extended
   precision, standard-library calls, or another implementation are permitted.
4. **Profile-relative semantics.** Binary64 encoding, finite-domain restriction,
   100-digit oracle precision, 2-ULP threshold, and campaign inputs are exact profile
   and Evidence scope, not universal Specification defaults.
5. **Finite Evidence over universal error claims.** Accepted campaign Evidence supports
   only the twelve retained inputs per realization.
6. **Claims separate from Evidence.** The real-valued proposition remains in the
   Specification; realization Claims and campaign Evidence carry profile and limits.
7. **Semantic acceptance separate from deployment.** A child-process boundary neither
   supports the numerical Claim nor follows from numerical acceptance.
8. **Plural mathematics.** This approximate metric coexists with exact algebra,
   protocols, effects, resources, and proofs without redefining their equality.

## Required actor outcomes

### Theory author

The author publishes an operation proposition, an observation relation naming the exact
profile-local metric, and explicit finite-evidence limits without selecting an
algorithm. Existing Specifications without numerical kernels remain valid. Invalid or
duplicate numerical declaration IDs, unknown operation references, nonpositive oracle
precision, negative ULP bounds, and an empty campaign fail with stable diagnostics.

### Package author

Two independently authored kernels expose the same one-request/one-response hex-float
adapter. One uses the host robust hypot primitive; one uses explicit max/min scaling and
ratio reduction. Neither imports the other or the runner. A retained naïve
`sqrt(x*x+y*y)` candidate is challenged on the first large finite-result case.

### Theory consumer

The theory projection shows the real-valued proposition, exact observation relation,
profile, assumptions, exclusions, and unknown universal coverage. It excludes candidate
source, package Evidence, campaign internals, and consumer selection.

### Package consumer

The exact query shows both registered realizations accepted, the breaker challenged and
ineligible, every per-case error distance, applicable Evidence axes, finite limitation,
and each accepted candidate's directional child-process boundary. Missing, stale,
challenging, inconclusive, error, assertion-only, or inapplicable Evidence fails closed
for the required numerical concern.

## Frozen falsifiers

The feature is false if:

1. Any accepted predecessor byte or behavior is changed to admit numerical kernels.
2. A Specification without numerical declarations becomes invalid or receives implicit
   approximation semantics.
3. The tolerance, oracle precision, input encoding, finite-domain restriction, or case
   set is absent, candidate-controlled, silently defaulted, or reported only in prose.
4. Decimal text round-tripping changes a tested binary64 input or output unnoticed.
5. NaN, infinity, a negative norm, malformed output, extra output, timeout, or candidate
   error contributes support.
6. A final pass/fail without exact input, output, rounded oracle, ULP distance, and
   threshold is accepted as a complete observation.
7. The large finite-result overflow case accepts the naïve breaker, or a passing kernel
   is judged by an oracle copied from candidate code.
8. Swapped/sign-equivalent cases expose representation identity as semantic authority.
9. A candidate chooses or widens the 2-ULP threshold, or report mutation can turn a
   challenge into support.
10. Claims, Evidence, profile, policy, plan, source, adapter, report, or manifest scope
    is stale, mismatched, incomplete, forged, or inapplicable yet contributes acceptance.
11. Numerical acceptance is inferred from process compatibility, or a deployment
    boundary is inferred from numerical acceptance.
12. The command discovers inputs, scans source trees, accesses the network, executes an
    unmanifested candidate, aliases output to a governed input, mutates input, reuses
    mutable candidate state, or changes prior output after failure.
13. Documentation or output claims every-input coverage, correct rounding, real-arithmetic
    proof, reproducibility across arbitrary hardware/runtime rounding modes, interval
    containment, NaN/infinity semantics, performance, or arbitrary numerical generality.
14. The exact command, focused controls, independent review, full repository gate, or
    one-spec/one-PR mapping does not pass from a clean exact head.

## Definition of Done

- The felt command executes 36 isolated cases, accepts two registered realizations,
  challenges the naïve breaker at the first exact overflow counterexample, and writes
  the closed report atomically.
- Every retained case exposes exact hex inputs/output, rounded-oracle hex, ULP distance,
  threshold, and result; the report cannot hide malformed or nonfinite outputs.
- Exact Claims and fresh Evidence satisfy the required concern only for both registered
  realizations under the exact profile/policy.
- Theory/package projections and semantic/directional compatibility remain separate.
- Focused negative controls attack encoding, oracle independence, overflow/underflow,
  tolerance authority, Evidence scope, acquisition, isolation, aliases, atomicity, and
  overclaim; all material concerns are retained and disposed in ExecPlan 0011.
- Durable docs state what is real, excluded, recoverable, and sufficient to reopen.
- One PR maps 1:1 to this design spec and opens only after complete local convergence.
  Its report starts with the exact command and one sentence saying what is real.

## Known exclusions

- The campaign is twelve exact finite input pairs, not exhaustive binary64 verification.
- It does not define NaN, infinity, unrepresentable real results, alternate rounding
  modes, non-binary64 types, vector dimensions other than two, complex values, interval
  outputs, derivatives, conditioning, performance, SIMD, or reproducibility across all
  libm/hardware implementations.
- A 2-ULP campaign bound is not correct rounding or a real-analysis proof.
- High-precision Decimal arithmetic and conversion into the mathematical proposition are
  part of the campaign oracle TCB and remain review assumptions.
- Adapter faithfulness and complete child-boundary observation remain assumptions.
- Local exact records are not hosted acquisition or production deployment authority.

## Recovery and reopen triggers

Revert the eventual squash commit to remove the stable-norm2 declaration, candidates,
records, command, and docs while retaining the interaction-protocol and all predecessor
packages. Failed inspection preserves governed inputs and prior output.

Reopen for exhaustive proofs, correctly rounded requirements, interval/error-budget
composition, configurable tolerances, NaN/infinity behavior, alternative formats or
rounding modes, higher-dimensional norms, hardware reproducibility, SIMD/performance,
conditioning analysis, or hosted acquisition.

## Revision history

- **2026-07-23, revision 1 (user need and falsifiers frozen):** Selects stable 2D norm
  as the operator-approved approximate numerical kernel. Freezes exact binary64 hex
  observations, a 100-digit independent oracle, 2-ULP relation, twelve finite cases,
  two independent kernels, one naïve overflow breaker, fourteen falsifiers, and all
  exclusions before production code.
