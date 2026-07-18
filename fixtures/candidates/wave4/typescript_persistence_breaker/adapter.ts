import { PersistenceBreakerStack, type StackValue } from "./stack.ts";

type JsonObject = Record<string, unknown>;

type Request =
  | { seq: number; op: "empty"; args: Record<string, never> }
  | { seq: number; op: "push"; args: { stack: string; value: number } }
  | { seq: number; op: "pop"; args: { stack: string } };

const implementation = new PersistenceBreakerStack();
const handles = new Map<string, StackValue>();
const decoder = new TextDecoder("utf-8", { fatal: true });
const encoder = new TextEncoder();
let nextHandle = 0;
let expectedSequence = 0;

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(value: JsonObject, expected: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length &&
    actual.every((key, index) => key === wanted[index]);
}

function requireHandle(value: unknown): string {
  if (typeof value !== "string" || value.length === 0 || !handles.has(value)) {
    throw new Error("stack must name a nonempty live session handle");
  }
  return value;
}

function parseRequest(line: string): Request {
  let raw: unknown;
  try {
    raw = JSON.parse(line);
  } catch (error) {
    throw new Error(`request is not valid JSON: ${String(error)}`);
  }

  if (!isObject(raw) || !hasExactKeys(raw, ["seq", "op", "args"])) {
    throw new Error("request must have exactly seq, op, and args");
  }
  if (
    typeof raw.seq !== "number" ||
    !Number.isSafeInteger(raw.seq) ||
    raw.seq < 0 ||
    raw.seq !== expectedSequence
  ) {
    throw new Error("seq must be the next nonnegative safe integer");
  }
  if (!isObject(raw.args)) {
    throw new Error("args must be an object");
  }

  if (raw.op === "empty") {
    if (!hasExactKeys(raw.args, [])) {
      throw new Error("empty args must be empty");
    }
    return { seq: raw.seq, op: "empty", args: {} };
  }

  if (raw.op === "push") {
    if (!hasExactKeys(raw.args, ["stack", "value"])) {
      throw new Error("push args must have exactly stack and value");
    }
    const stack = requireHandle(raw.args.stack);
    const value = raw.args.value;
    if (
      typeof value !== "number" ||
      !Number.isSafeInteger(value) ||
      value < -2 ||
      value > 2
    ) {
      throw new Error("push value must be a profile integer from -2 through 2");
    }
    return { seq: raw.seq, op: "push", args: { stack, value } };
  }

  if (raw.op === "pop") {
    if (!hasExactKeys(raw.args, ["stack"])) {
      throw new Error("pop args must have exactly stack");
    }
    return {
      seq: raw.seq,
      op: "pop",
      args: { stack: requireHandle(raw.args.stack) },
    };
  }

  throw new Error("op must be empty, push, or pop");
}

function store(stack: StackValue): string {
  const handle = `h${nextHandle}`;
  nextHandle += 1;
  handles.set(handle, stack);
  return handle;
}

function execute(request: Request): JsonObject {
  if (request.op === "empty") {
    return { stack: store(implementation.empty()) };
  }
  if (request.op === "push") {
    const source = handles.get(request.args.stack)!;
    return { stack: store(implementation.push(source, request.args.value)) };
  }

  const source = handles.get(request.args.stack)!;
  const popped = implementation.pop(source);
  if (popped.tag === "none") {
    return { tag: "none" };
  }
  return {
    tag: "some",
    value: popped.value,
    remainder: store(popped.remainder),
  };
}

async function respond(line: string): Promise<void> {
  const request = parseRequest(line);
  const response = {
    seq: request.seq,
    status: "ok",
    result: execute(request),
    events: [],
  };
  expectedSequence += 1;
  await Deno.stdout.write(encoder.encode(`${JSON.stringify(response)}\n`));
}

async function main(): Promise<void> {
  const reader = Deno.stdin.readable.getReader();
  let pending = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    pending += decoder.decode(value, { stream: true });

    while (true) {
      const newline = pending.indexOf("\n");
      if (newline < 0) {
        break;
      }
      const line = pending.slice(0, newline);
      pending = pending.slice(newline + 1);
      if (line.length === 0) {
        throw new Error("blank request lines are not valid");
      }
      await respond(line);
    }
  }

  pending += decoder.decode();
  if (pending.length !== 0) {
    throw new Error("request must end with LF");
  }
}

try {
  await main();
} catch (error) {
  console.error(`typescript_persistence_breaker: ${String(error)}`);
  Deno.exitCode = 1;
}
