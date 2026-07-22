export type ClassToken = "a" | "b" | "c";

export interface Entry {
  readonly class: ClassToken;
  readonly value: number;
}

export class OrderedMap {
  private readonly values: ReadonlyMap<ClassToken, number>;
  private readonly order: readonly ClassToken[];

  private constructor(
    values: ReadonlyMap<ClassToken, number>,
    order: readonly ClassToken[],
  ) {
    this.values = values;
    this.order = order;
    Object.freeze(this);
  }

  static empty(): OrderedMap {
    return new OrderedMap(new Map(), Object.freeze([]));
  }

  put(key: string, value: number): OrderedMap {
    const token = classify(key);
    const values = new Map(this.values);
    values.set(token, value);
    const order = this.values.has(token)
      ? this.order
      : Object.freeze([...this.order, token]);
    return new OrderedMap(values, order);
  }

  lookup(key: string): number | undefined {
    return this.values.get(classify(key));
  }

  entries(): readonly Entry[] {
    return Object.freeze(this.order.map((token) =>
      Object.freeze({ class: token, value: this.values.get(token)! })
    ));
  }
}

function classify(key: string): ClassToken {
  const token = key.toLowerCase();
  if (token !== "a" && token !== "b" && token !== "c") {
    throw new Error("key is outside the selected profile domain");
  }
  return token;
}
