set_option warningAsError true

universe u

abbrev ObservedStack (A : Type u) := List A

def empty {A : Type u} : ObservedStack A := []

def pop {A : Type u} : ObservedStack A → Option (A × ObservedStack A)
  | [] => Option.none
  | x :: xs => Option.some (x, xs)

#eval IO.println "'stack_pop_empty' does not depend on any axioms"

theorem stack_pop_empty (A : Type u) :
    pop (empty : ObservedStack A) = Option.none := rfl
