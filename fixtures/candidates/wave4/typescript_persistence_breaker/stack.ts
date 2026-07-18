/**
 * Independently authored Stack fixture for Wave 4 candidate controls.
 *
 * The representation is fixture-local.  Consumers may observe it only through the
 * adapter's opaque handles and repeated pop operations.
 */

export type StackValue = {
  values: number[];
};

export type PopResult =
  | { tag: "none" }
  | { tag: "some"; value: number; remainder: StackValue };

export class PersistenceBreakerStack {
  #caseNumber = 0;
  #pushNumber = 0;

  empty(): StackValue {
    this.#caseNumber += 1;
    this.#pushNumber = 0;
    return { values: [] };
  }

  push(source: StackValue, value: number): StackValue {
    this.#pushNumber += 1;

    // Compute the extension correctly before applying the fixture's one deliberate
    // fault to the retained source value.
    const extended = { values: [value, ...source.values] };

    // The canonical Wave 4 campaign's fourth logical case is the retained-source
    // push case.  Its second push extends a nonempty source.  This test-only counter
    // makes only that retained source observably change; the returned Stack remains
    // correct and all other canonical cases retain normal Stack behavior.
    if (
      this.#caseNumber === 4 &&
      this.#pushNumber === 2 &&
      source.values.length > 0
    ) {
      source.values[0] = source.values[0] === 1 ? -1 : 1;
    }

    return extended;
  }

  pop(source: StackValue): PopResult {
    if (source.values.length === 0) {
      return { tag: "none" };
    }

    return {
      tag: "some",
      value: source.values[0],
      remainder: { values: source.values.slice(1) },
    };
  }
}
