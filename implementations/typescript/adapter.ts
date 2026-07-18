/** Dependency-free Deno adapter for stack-runner-json-v1. */

import { empty, pop, push, type Stack } from "./stack.ts";

type JsonObject = Record<string, unknown>;
type JsonParseWithSource = (
  text: string,
  reviver: (
    this: unknown,
    key: string,
    value: unknown,
    context: { readonly source: string },
  ) => unknown,
) => unknown;

interface Request {
  readonly seq: bigint;
  readonly seqJson: string;
  readonly op: "empty" | "push" | "pop";
  readonly args: JsonObject;
}

const encoder = new TextEncoder();
const decoder = new TextDecoder("utf-8", { fatal: true });
const stacks = new Map<string, Stack<number>>();
let nextHandle = 0;
let lastSequence: bigint | undefined;

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(object: JsonObject, expected: readonly string[]): boolean {
  const actual = Object.keys(object).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length &&
    actual.every((key, index) => key === wanted[index]);
}

function requireHandle(value: unknown): Stack<number> {
  if (typeof value !== "string" || value.length === 0) {
    throw new Error("stack handle must be a nonempty string");
  }

  const stack = stacks.get(value);
  if (stack === undefined) {
    throw new Error("stack handle does not belong to this session");
  }
  return stack;
}

function store(stack: Stack<number>): string {
  const handle = `ts-stack-${nextHandle}`;
  nextHandle += 1;
  stacks.set(handle, stack);
  return handle;
}

function parseRequest(line: string): Request {
  let seqJson: string | undefined;
  const parseWithSource = JSON.parse as JsonParseWithSource;
  const parsed = parseWithSource(line, (key, value, context) => {
    if (key === "seq" && typeof value === "number") {
      seqJson = context.source;
    }
    return value;
  });
  if (!isObject(parsed) || !hasExactKeys(parsed, ["seq", "op", "args"])) {
    throw new Error("request must contain exactly seq, op, and args");
  }

  const { op, args } = parsed;
  if (seqJson === undefined || !/^(?:0|[1-9][0-9]*)$/.test(seqJson)) {
    throw new Error("seq must be a nonnegative JSON integer");
  }
  const seq = BigInt(seqJson);
  if (lastSequence !== undefined && seq <= lastSequence) {
    throw new Error("seq must increase monotonically");
  }
  if (op !== "empty" && op !== "push" && op !== "pop") {
    throw new Error("unknown operation");
  }
  if (!isObject(args)) {
    throw new Error("args must be an object");
  }

  if (op === "empty" && !hasExactKeys(args, [])) {
    throw new Error("empty args must contain no members");
  }
  if (op === "push") {
    if (!hasExactKeys(args, ["stack", "value"])) {
      throw new Error("push args must contain exactly stack and value");
    }
    if (
      !Number.isSafeInteger(args.value) ||
      (args.value as number) < -2 ||
      (args.value as number) > 2
    ) {
      throw new Error("push value must be a profile integer from -2 through 2");
    }
    requireHandle(args.stack);
  }
  if (op === "pop") {
    if (!hasExactKeys(args, ["stack"])) {
      throw new Error("pop args must contain exactly stack");
    }
    requireHandle(args.stack);
  }

  lastSequence = seq;
  return { seq, seqJson, op, args };
}

function execute(request: Request): string {
  let result: JsonObject;

  if (request.op === "empty") {
    result = { stack: store(empty<number>()) };
  } else if (request.op === "push") {
    const source = requireHandle(request.args.stack);
    const value = request.args.value as number;
    result = { stack: store(push(source, value)) };
  } else {
    const observed = pop(requireHandle(request.args.stack));
    result = observed.tag === "none"
      ? { tag: "none" }
      : {
        tag: "some",
        value: observed.value,
        remainder: store(observed.remainder),
      };
  }

  return `{"seq":${request.seqJson},"status":"ok","result":${JSON.stringify(result)},"events":[]}`;
}

async function writeResponse(response: string): Promise<void> {
  const bytes = encoder.encode(`${response}\n`);
  let offset = 0;
  while (offset < bytes.length) {
    offset += await Deno.stdout.write(bytes.subarray(offset));
  }
}

async function processLine(line: string): Promise<void> {
  if (line.endsWith("\r")) {
    line = line.slice(0, -1);
  }
  await writeResponse(execute(parseRequest(line)));
}

async function main(): Promise<void> {
  let pending = "";
  for await (const chunk of Deno.stdin.readable) {
    pending += decoder.decode(chunk, { stream: true });
    let newline = pending.indexOf("\n");
    while (newline !== -1) {
      const line = pending.slice(0, newline);
      pending = pending.slice(newline + 1);
      await processLine(line);
      newline = pending.indexOf("\n");
    }
  }

  pending += decoder.decode();
  if (pending.length !== 0) {
    throw new Error("final request must be LF-terminated");
  }
}

await main();
