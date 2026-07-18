set_option warningAsError true

universe u

abbrev ObservedStack (A : Type u) := List A

def empty {A : Type u} : ObservedStack A := []

def pop {A : Type u} : ObservedStack A → Option (A × ObservedStack A)
  | [] => Option.none
  | x :: xs => Option.some (x, xs)

theorem stack_pop_empty (A : Type u) (extra : Nat := by exact 0) :
    (let _witness := extra
     pop (empty : ObservedStack A) = Option.none) := rfl
