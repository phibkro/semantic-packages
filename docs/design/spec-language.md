# Minimum viable specification language

## Design target

The first language is not universal. It is sufficient when it can express one useful abstract data type, its observations, laws, one resource/effect property, and scoped claims that can be connected to external proof and test systems.

## Proposed core forms

```text
specification
import
carrier/type
operation
observation
law
state / transition
resource
 effect
claim
profile
```

## Illustrative syntax

```text
spec Stack[A] {
  type Stack

  op empty : Stack
  op push  : Stack * A -> Stack
  obs pop  : Stack -> Option[A * Stack]

  law pop_push(s: Stack, x: A):
    pop(push(s, x)) == Some((x, s))

  effects {
    forbidden: io.*
    optional: debug.emit
  }

  resources {
    persistence: old_state_remains_valid
  }

  claim push_cost {
    concern: performance
    proposition: amortized_O(1)
    profile: default
  }
}
```

This syntax is provisional. The initial parser may use JSON/YAML internally while this form guides semantics.

## Semantic rules

- A field-like declaration denotes an observation, not a memory slot.
- Effects describe observable or permitted interactions, not specific syscalls.
- Resource properties are user-definable abstractions with declared composition rules.
- Performance claims are profile-relative and require a measurement or proof method.
- Claims are not accepted without an explicit evidence status.
- Unknown or unsupported semantic aspects remain visible rather than being silently ignored.
