/** An independently authored persistent Stack realization.
 *
 * The linked-node representation is private to this package.  Callers can only
 * construct stacks with `empty` and `push`, or observe them with `pop`.
 */

interface EmptyNode {
  readonly kind: "empty";
}

interface LinkNode<T> {
  readonly kind: "link";
  readonly value: T;
  readonly rest: Stack<T>;
}

export type Stack<T> = EmptyNode | LinkNode<T>;

export type PopResult<T> =
  | { readonly tag: "none" }
  | { readonly tag: "some"; readonly value: T; readonly remainder: Stack<T> };

const EMPTY_NODE: EmptyNode = Object.freeze({ kind: "empty" });
const NONE = Object.freeze({ tag: "none" } as const);

export function empty<T>(): Stack<T> {
  return EMPTY_NODE;
}

export function push<T>(stack: Stack<T>, value: T): Stack<T> {
  return Object.freeze({ kind: "link", value, rest: stack });
}

export function pop<T>(stack: Stack<T>): PopResult<T> {
  if (stack.kind === "empty") {
    return NONE;
  }

  return Object.freeze({
    tag: "some",
    value: stack.value,
    remainder: stack.rest,
  });
}
