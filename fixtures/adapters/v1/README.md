# Stack runner adapter controls

`fake_stack_adapter.py` is executable test data for `stack-runner-json-v1`, not a
registered Realization or a semantic oracle. Its modes give the runner portable child
processes for positive behavior, semantic counterexamples, protocol/execution errors,
reported-event classification, and the known black-box trust limit.

The test harness owns its expected traces. The fixture's list-backed state is private
to the child and must never be imported by runner code or tests.

The red-first suite freezes one small future API:
`semantic_packages.stack_runner.run_stack_conformance(command, *, values,
max_depth, max_history, observation_limit, timeout_seconds)`. Its report exposes
`result`, stable `causes`, ordered `(event, disposition)` pairs, `assumptions`, and
`exclusions`. It deliberately does not prescribe the runner's internal model,
subprocess machinery, or a Realization representation.

The positive fixture modes validate the runner independently. A separate test invokes
`python -m semantic_packages.stack_adapter` so the Wave 3 checkpoint also requires an
actual independently implemented reference Realization behind the accepted protocol.
