# Explicit PSpec uninvolved-author observation

## Purpose and boundary

This protocol supplies ExecPlan 0006 A5-H. It observes whether one eligible uninvolved
theory author can complete the two tasks promised by
[design-spec 0001](../../design-specs/0001-explicit-pspec-author-journey.md) from public
repository instructions. It is product-usability observation, not semantic Evidence,
proof that hosted laws are true, or arbitrary-domain generality.

The operator coordinates the participant. The implementing agent must not impersonate
the participant, fill in successful results, or coach around a blocking ambiguity.

## Participant eligibility and privacy

The participant:

- had no prior involvement in semantic-packages research, design, implementation, or
  review;
- receives only the exact public revision and the task text below;
- may ask questions, but every answer and other assistance is retained by category;
- reviews the retained observation for factual accuracy;
- need not provide a name, demographic data, terminal transcript, source contents from
  outside the repository, or any credential.

Record only task result, integer duration in seconds, assistance categories, blocking
ambiguities, exact revision, and participant review. Stop immediately if a command
would disclose a credential or leave the repository and `/tmp`.

## Environment

Use a clean public checkout at the exact candidate revision. Confirm:

```sh
git status --short
git rev-parse HEAD
```

The first command must print nothing. Retain the second command as `revision` in the
observation. Do not use an implementing agent's dirty worktree.

## Task 1 — Stack success, failure, and recovery

1. Follow README “Author an exact semantic Specification” to author Stack into
   `/tmp/stack-spec.json`.
2. Read `specs/stack.pspec` and identify where root identity, the `pop-empty` law, and
   the exact profile reference are authored.
3. Follow the README failure exercise. Use the diagnostic to find the blank law, restore
   any nonempty statement in the disposable source, and rerun successfully.
4. State whether the output is presented as a canonical Specification, semantic proof,
   or Evidence. The accepted answer is canonical Specification only.

## Task 2 — OrderedMap through the same contract

1. Follow the README command to author OrderedMap into `/tmp/ordered-map-spec.json`.
2. Read `specs/ordered-map.pspec` and identify the `put-new-appends` law and the exact
   `ordered-map-ascii-fold` profile reference.
3. In a disposable `/tmp` copy, change only the nonempty `put-new-appends` statement,
   rerun the same command shape, and confirm the changed hosted text is preserved in the
   output without being described as checked or proved.
4. State whether either command searched for a profile that was not named. The accepted
   answer is no.

## Observation result

Both tasks pass only if the participant reaches their expected observations from the
README and source files without undisclosed assistance. A blocking ambiguity, wrong
authority claim, command failure, or unrecorded assistance makes A5-H fail and creates
the smallest explicit design-spec or implementation successor.

Retain the participant-reviewed result at
`reports/authoring/uninvolved-author-observation.json` with exactly this public shape:

```json
{
  "kind": "human-author-observation-v1",
  "revision": "40 lowercase hexadecimal characters",
  "participant": {
    "eligible": true,
    "priorProjectInvolvement": "none",
    "reviewedObservation": true
  },
  "tasks": [
    {
      "domain": "stack",
      "result": "pass",
      "durationSeconds": 1,
      "assistance": []
    },
    {
      "domain": "ordered-map",
      "result": "pass",
      "durationSeconds": 1,
      "assistance": []
    }
  ],
  "blockingAmbiguities": []
}
```

Durations above are shape examples, not observations to copy. Failed or assisted
outcomes retain their truthful values and are never edited into a pass. The participant
reviews the final record before it becomes gate input.
