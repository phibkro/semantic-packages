import { OrderedMap } from "./ordered_map.ts";

type JsonObject = Record<string, unknown>;
const decoder = new TextDecoder("utf-8", { fatal: true });
const encoder = new TextEncoder();
const maps = new Map<string, OrderedMap>();
let nextHandle = 0;
let nextSequence = 0;

function object(value: unknown): JsonObject {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("expected object");
  }
  return value as JsonObject;
}

function exact(value: JsonObject, keys: readonly string[]): void {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  if (actual.length !== expected.length ||
    actual.some((key, index) => key !== expected[index])) {
    throw new Error("unexpected members");
  }
}

function string(value: unknown): string {
  if (typeof value !== "string" || value.length === 0) throw new Error("expected string");
  return value;
}

function integer(value: unknown): number {
  if (!Number.isInteger(value) || (value as number) < -2 || (value as number) > 2) {
    throw new Error("value outside profile");
  }
  return value as number;
}

function retained(handle: unknown): OrderedMap {
  const value = maps.get(string(handle));
  if (value === undefined) throw new Error("unknown map handle");
  return value;
}

function store(value: OrderedMap): string {
  const handle = `ts-map-${nextHandle}`;
  nextHandle += 1;
  maps.set(handle, value);
  return handle;
}

function response(seq: number, result: JsonObject): string {
  return JSON.stringify({ seq, status: "ok", result, events: [] });
}

function execute(line: string): string {
  const request = object(JSON.parse(line));
  exact(request, ["seq", "op", "args"]);
  if (!Number.isInteger(request.seq) || request.seq !== nextSequence) {
    throw new Error("invalid sequence");
  }
  const seq = request.seq as number;
  nextSequence += 1;
  const op = string(request.op);
  const args = object(request.args);

  if (op === "empty") {
    exact(args, []);
    return response(seq, { map: store(OrderedMap.empty()) });
  }
  if (op === "put") {
    exact(args, ["map", "key", "value"]);
    const updated = retained(args.map).put(string(args.key), integer(args.value));
    return response(seq, { map: store(updated) });
  }
  if (op === "lookup") {
    exact(args, ["map", "key"]);
    const value = retained(args.map).lookup(string(args.key));
    return response(seq, value === undefined ? { tag: "none" } : { tag: "some", value });
  }
  if (op === "entries") {
    exact(args, ["map"]);
    return response(seq, { entries: retained(args.map).entries() });
  }
  throw new Error("unknown operation");
}

async function write(line: string): Promise<void> {
  const bytes = encoder.encode(`${line}\n`);
  let offset = 0;
  while (offset < bytes.length) offset += await Deno.stdout.write(bytes.subarray(offset));
}

let pending = "";
for await (const chunk of Deno.stdin.readable) {
  pending += decoder.decode(chunk, { stream: true });
  let newline = pending.indexOf("\n");
  while (newline !== -1) {
    const line = pending.slice(0, newline);
    pending = pending.slice(newline + 1);
    await write(execute(line));
    newline = pending.indexOf("\n");
  }
}
pending += decoder.decode();
if (pending.length !== 0) throw new Error("final request must be LF terminated");
