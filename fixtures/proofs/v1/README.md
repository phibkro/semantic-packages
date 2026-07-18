# Bounded `pop-empty` proof controls

This packet is test data for `scripts/proof_fixture_check.py`.  It freezes the
experimental ADR 0009 boundary without providing the future product proof under
`proofs/` or the future checker `scripts/proof_check.py`.

`positive.lean` models the Specification's finite top-first observation space as
`List A` and checks `pop(empty) = Option.none` for every `A : Type u`.  The list is
only a mathematical observation model; no Realization or adapter imports this file.
The other Lean files are falsifiers for elaboration, warning, admitted-axiom,
statement-linkage, and quantification mistakes.

`manifest.template.json` is a valid JSON template.  The fixture harness materializes
its `$...` digest placeholders in a disposable repository and invokes the future
checker through this small CLI:

```text
python3 scripts/proof_check.py --manifest PATH --lean EXECUTABLE [--evidence PATH]
```

The Lean executable is always explicit and injectable.  Neither this packet nor the
future checker may hardcode a Nix store path.  A clean invocation prints exactly
`Proof is valid: 0 diagnostics.` and exits zero.  A failing invocation exits one and
prints stable signatures of the form `CODE source#/pointer`; explanatory prose after
`: ` is not frozen.

The checker verifies the theorem statement mechanically by checking the named theorem
against `expectedStatement` in generated Lean source, then requires the structured
positive observation from `#print axioms`.  Merely finding the theorem name or grepping
the committed source is not sufficient.

Proof/provenance failures are checker errors, never semantic `challenges` Evidence.
Finite instantiations are deliberately rejected as statement mismatches rather than
accepted as proof of the universal law.
