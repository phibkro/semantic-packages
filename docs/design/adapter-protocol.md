# Tracer adapter protocol

## Scope

`stack-runner-json-v1` is the executable adapter boundary for the Stack tracer in
ExecPlan 0001. It is not a universal ABI, transport, semantic model, or registry
protocol. The harness launches an explicitly supplied child command; resolving or
building a Realization from registry metadata remains outside this version.

The semantic oracle and the adapter have different ownership:

- the harness derives expected top-first traces from generated operation histories and
  compares observed values;
- a reference Realization implements Stack independently behind the adapter;
- the adapter translates protocol requests and results but never defines equality,
  expected traces, or assurance.

Reusing the Realization's Stack operation code as the harness oracle would make the
test tautological and is not permitted.

## Process and framing

One child process is one session. The harness sends UTF-8, LF-terminated JSON objects
on stdin and receives exactly one UTF-8, LF-terminated JSON object on stdout for every
request. Requests are lockstep and never pipelined. Stdout contains no banners, logs,
blank lines, or other values. Stderr is retained as diagnostic provenance but has no
semantic meaning.

The harness ends a session by closing stdin. The adapter then exits successfully.
Unexpected EOF, timeout, malformed UTF-8 or JSON, an invalid response shape, extra
stdout, a sequence mismatch, or nonzero process exit is a protocol/execution error,
not evidence challenging a Stack law. Bounds, seeds, and timeouts scope an evidence
run; they do not narrow the normative laws.

## Messages

Every request has exactly `seq`, `op`, and `args`. `seq` is a nonnegative integer,
increases monotonically within the session, and is echoed exactly. The tracer accepts
only these request shapes:

```json
{"seq": 0, "op": "empty", "args": {}}
{"seq": 1, "op": "push", "args": {"stack": "h0", "value": 1}}
{"seq": 2, "op": "pop", "args": {"stack": "h1"}}
```

Harness-generated elements are JSON integers in the selected profile's `-2` through
`2` domain. General element serialization is not selected by this protocol.

A successful response has exactly `seq`, `status`, `result`, and `events`:

```json
{"seq": 0, "status": "ok", "result": {"stack": "h0"}, "events": []}
{"seq": 2, "status": "ok", "result": {"tag": "none"}, "events": []}
{"seq": 2, "status": "ok", "result": {"tag": "some", "value": 1, "remainder": "h0"}, "events": []}
```

`empty` and `push` return a `stack`. `pop` returns a tagged `none` or `some`; absence
is not overloaded with an element value. An error response to a valid request has
exactly `seq`, `status`, `error`, and `events`:

```json
{"seq": 2, "status": "error", "error": {"code": "adapter-error", "message": "diagnostic"}, "events": []}
```

`result` and `error` are mutually exclusive. An adapter error on a valid request is an
execution error or inconclusive attempt, not a semantic counterexample. Behavior for
malformed client requests is outside v1; the runner instead falsifies malformed
adapter responses.

JSON object member order and insignificant whitespace carry no meaning. The `error`
object has exactly nonempty string fields `code` and `message`; its vocabulary is
adapter diagnostic data rather than a second semantic-result taxonomy.

## Handles and observation

A handle is a nonempty opaque string valid only in its originating live session. Every
returned handle remains usable with a stable observable denotation until session end.
An adapter may intern one token for extensionally equal values or return distinct
tokens. Token equality, allocation, spelling, and freshness have no Stack meaning, and
a token may not be rebound while a retained handle exists.

The harness observes a handle by repeatedly issuing `pop`, appending each `some.value`
and continuing with `some.remainder` until `none`. The resulting sequence is top-first.
Two handles are Stack-equivalent exactly when these finite sequences are pointwise
equal under the selected element equality. The harness retains source and ancestor
handles and repeats their observations after operations on them or derived handles to
falsify destructive `push` or `pop` behavior.

## Effect trace

`events` is the ordered list of nonempty adapter-reported event-class strings for that
single invocation. It contains no expected trace or equality result. For the tracer,
an exact pattern matches the same string; a pattern ending in `.*` matches a nonempty
suffix after that dotted prefix. Thus `io.*` matches `io.read` but not `io` or `io.`.

An observed forbidden match is a semantic counterexample within this reported
boundary. `debug.emit` is optional and retained when observed. An event unmatched by
an explicit pattern is retained with the Specification's `default: unspecified`
disposition; it is not silently allowed. An empty list means only that the adapter
reported no events. Adapter completeness, adapter-external effects, stdout/stderr
effects, and Realization faithfulness remain explicit assumptions or exclusions.

## Runner classifications

The runner keeps fine causes separate from Evidence's coarse result:

| Cause | Evidence result contribution |
|---|---|
| wrong value, tag, order, remainder, or retained-handle observation | `challenges` |
| adapter-reported forbidden event | `challenges` |
| malformed response, sequence/framing failure, timeout, or process failure | `error` |
| adapter error response to a valid request | `error` or `inconclusive` |
| clean bounded run | candidate `supports`, still subject to review and policy |

The initial controls include empty-pop, depth-two top-first observation, `pop_push`,
fresh-token and interned-token extensionally equal remainders, retained ancestors after
push and pop, wrong-result and destructive variants, bounded nontermination, optional,
forbidden, and unspecified events, malformed transport variants, a catchable shallow
liar, and an undetectable perfect shadow implementation. The last must pass black-box
behavior while demonstrating that conformance cannot prove the adapter faithfully
exposes some separately claimed implementation.

## Explicit exclusions

This version does not report the profile's `realization-steps` cost measure and creates
no performance evidence. The visible performance claim remains unsupported. It also
does not define general element encoding, concurrent requests, remote transports,
adapter discovery, build execution, registry resolution, or evidence persistence.
