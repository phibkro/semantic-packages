# Cold-human Stack inspection protocol

## Purpose

Observe whether an uninvolved human can inspect the accepted Stack tracer from one
documented command without source-code archaeology or private explanation. This is a
product observation, not a test of the participant and not evidence that the model is
general beyond Stack.

## Frozen starting context

The operator records an exact public commit before recruiting the participant. The
participant receives only:

1. a fresh checkout of that commit;
2. the repository `README.md` as the entrypoint; and
3. the statement: “Use the documented Stack inspection command and its output to
   answer the five questions below. Do not inspect Python source, tests, or registry
   JSON.”

The environment must provide Python 3 and the dependencies documented by README. No
Lean, Rust, Deno, network access, artifact execution, or prior green repository gate is
required for this observation.

An eligible participant has not implemented, reviewed, or been briefed on the Stack
tracer internals. The project lead, implementation agent, inspection-surface reviewer,
and anyone who has read the resolver, projection, maintenance, journey-test, or record
implementation are ineligible.

## Exact task

The README command must name both manifest paths and every address selector explicitly:

- profile `realizationProfile/stack-default/0.1.0`;
- predecessor Specification `specification/stack/0.1.0`;
- successor Specification `specification/stack/0.2.0`;
- predecessor policy `consumerPolicy/stack-bounded-policy/0.1.0`; and
- successor policy `consumerPolicy/stack-bounded-policy/0.2.0`.

From that command's output alone, the participant answers in their own words:

1. What observable meaning does Stack 0.1.0 specify?
2. What does the output classify as supported, contested, unsupported, unknown,
   assumed, or excluded? Name the Evidence mechanism, result, and review state where
   Evidence is shown.
3. Which 0.1.0 Realizations are semantically acceptable under the exact policy and
   profile? Is unsupported performance blocking or non-blocking?
4. For each acceptable candidate, what is the directional deployment boundary? Keep
   this answer separate from semantic acceptability.
5. Why does the failed 0.2.0 successor inherit no 0.1.0 Evidence, and which exact
   predecessor candidates remain recoverable? Does the tool select one automatically?

The operator may clarify ordinary vocabulary in this protocol but may not interpret
output, point to source/tests/records, suggest an answer, alter selectors, or run an
undocumented command. Any such help is recorded and makes the observation a BLOCK.
The observation ends after 30 minutes or when the participant submits answers.

## Success rubric and falsifier

PASS requires all five answers to be materially accurate from the documented output:

- meaning includes the relevant operations, observations, laws, effect/prohibition,
  persistence resource, and performance proposition rather than only the package name;
- Evidence result, review state, applicability/selection, assumptions, exclusions,
  contradiction, unsupported state, and unknown/unclaimed state remain distinguishable;
- both Rust and TypeScript 0.1.0 are semantically acceptable, required concerns are
  satisfied, and optional performance is unsupported but non-blocking;
- both candidates require the separate `consumer-to-realization` /
  `child-process-ndjson` / non-direct boundary;
- the 0.2.0 Rust candidate is unacceptable because required declarations have no
  exact-version support, nine predecessor Evidence records are stale for reason
  `exact-specification-version`, and both exact 0.1.0 candidates are recovery options
  without automatic selection.

A wrong or missing material answer, source/test/record archaeology, required
undocumented assistance, implicit `latest` reasoning, or a collapsed Evidence or
compatibility axis is a BLOCK.

Before involving a participant, run the journey controls. If README lacks the exact
command, the command cannot run, selectors are implicit, output omits a rubric fact,
or the command executes an artifact, H1 is BLOCK and creates the H-S1 minimal-surface
successor. A preflight PASS does not substitute for H2.

## Retained observation form

Store a privacy-reviewed observation under `docs/evidence/human-inspection/` containing:

```text
protocol revision:
repository commit:
participant eligibility attestation:
environment and Python version:
start/end time and duration:
documented command and exit status:
answers 1–5 (participant's words):
hesitations and navigation path:
operator assistance (including none):
unexpected output or failures:
rubric disposition per question:
overall PASS or BLOCK:
known exclusions:
```

Use a participant-chosen pseudonym or opaque identifier. Do not retain names, contact
details, terminal history outside the task, audio/video, or unrelated environment
data. The participant reviews the retained text before it is committed. A missing
privacy review or eligibility attestation blocks H-G.

## Interpretation boundary

This observation can support only inspectability of the exact local Stack snapshots
at the recorded revision. It does not establish authoring usability, accessibility,
generality, security, hosted acquisition, proof correctness, Realization conformance,
or production readiness. A green automated preflight proves only that the frozen
surface contract is present; it is not human-journey Evidence.
