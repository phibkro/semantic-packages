"""Red-first build, protocol, and semantic controls for Wave 4 candidates.

The fixture packages are external negative controls.  This module treats every child
as opaque: it checks process framing directly and delegates Stack meaning to the
canonical shared campaign in ``semantic_packages.stack_runner``.
"""

from __future__ import annotations

import json
import os
import selectors
import shlex
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from typing import BinaryIO, Sequence

from semantic_packages.stack_runner import (
    ConformanceReport,
    default_stack_conformance_plan,
    run_stack_conformance,
)


ROOT = Path(__file__).resolve().parents[2]
RUST_BREAKER = ROOT / "fixtures" / "candidates" / "wave4" / "rust_law_breaker"
TYPESCRIPT_BREAKER = (
    ROOT / "fixtures" / "candidates" / "wave4" / "typescript_persistence_breaker"
)
RUST_CANDIDATE = ROOT / "implementations" / "rust"
TYPESCRIPT_CANDIDATE = ROOT / "implementations" / "typescript"

PLAN_SHA256 = "e055eab406683a01a32e8b563ef2e299169ddb2745685b5ad3ffae3297d93f6c"
DECLARATIONS = ("pop-empty", "pop-push", "persistence", "stack-effects")
PROCESS_TIMEOUT_SECONDS = 3.0


def _required_tool(environment_name: str, executable_name: str) -> str:
    configured = os.environ.get(environment_name)
    if configured:
        resolved = shutil.which(configured)
        if resolved is None:
            raise AssertionError(
                f"{environment_name}={configured!r} is not executable; "
                "an explicit tool selection is never replaced by PATH"
            )
        return resolved

    resolved = shutil.which(executable_name)
    if resolved is None:
        raise AssertionError(
            f"required tool {environment_name}/{executable_name} is unavailable; "
            f"set {environment_name} or add {executable_name} to PATH"
        )
    return resolved


def _format_process(process: subprocess.CompletedProcess[bytes]) -> str:
    return (
        f"command: {shlex.join(process.args)}\n"
        f"exit: {process.returncode}\n"
        f"stdout: {process.stdout!r}\n"
        f"stderr: {process.stderr!r}"
    )


class CrossLanguageCandidateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rustc = _required_tool("RUSTC", "rustc")
        cls.cc = _required_tool("CC", "cc")
        cls.deno = _required_tool("DENO", "deno")
        cls.tool_versions = "\n".join(
            (
                cls._tool_version((cls.rustc, "--version", "--verbose")),
                cls._tool_version((cls.cc, "--version")),
                cls._tool_version((cls.deno, "--version")),
            )
        )

    @staticmethod
    def _tool_version(argv: Sequence[str]) -> str:
        process = subprocess.run(
            tuple(argv),
            cwd=ROOT,
            shell=False,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if process.returncode != 0:
            raise AssertionError(_format_process(process))
        return f"{shlex.join(process.args)}:\n{process.stdout.decode('utf-8', 'replace').strip()}"

    def _run_checked(self, argv: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
        process = subprocess.run(
            tuple(argv),
            cwd=ROOT,
            shell=False,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=PROCESS_TIMEOUT_SECONDS,
        )
        self.assertEqual(
            0,
            process.returncode,
            f"{_format_process(process)}\nversions:\n{self.tool_versions}",
        )
        return process

    def _assert_sources(self, paths: Sequence[Path], owner: str) -> None:
        for path in paths:
            self.assertTrue(
                path.is_file(),
                f"missing {owner} candidate source: {path.relative_to(ROOT)}",
            )

    def _rust_build_argv(self, main: Path, output: Path) -> tuple[str, ...]:
        return (
            self.rustc,
            "--edition",
            "2024",
            "-C",
            f"linker={self.cc}",
            str(main),
            "-o",
            str(output),
        )

    def _build_rust(self, package: Path, output: Path) -> tuple[str, ...]:
        main = package / "src" / "main.rs"
        stack = package / "src" / "stack.rs"
        self._assert_sources((main, stack), "Rust")
        build_argv = self._rust_build_argv(main, output)
        self._run_checked(build_argv)
        self.assertTrue(output.is_file(), f"rustc emitted no child: {shlex.join(build_argv)}")
        return (str(output),)

    def _deno_check_argv(self, package: Path) -> tuple[str, ...]:
        return (
            self.deno,
            "check",
            "--no-config",
            "--no-lock",
            "--no-npm",
            "--no-remote",
            str(package / "adapter.ts"),
            str(package / "stack.ts"),
        )

    def _deno_child_argv(self, package: Path) -> tuple[str, ...]:
        return (
            self.deno,
            "run",
            "--no-config",
            "--no-lock",
            "--no-npm",
            "--no-remote",
            "--no-prompt",
            str(package / "adapter.ts"),
        )

    def _check_typescript(self, package: Path) -> tuple[str, ...]:
        self._assert_sources(
            (package / "adapter.ts", package / "stack.ts"), "TypeScript"
        )
        check_argv = self._deno_check_argv(package)
        self._run_checked(check_argv)
        return self._deno_child_argv(package)

    def _read_response(
        self,
        process: subprocess.Popen[bytes],
        stream: BinaryIO,
        buffered: bytearray,
    ) -> bytes:
        deadline = time.monotonic() + PROCESS_TIMEOUT_SECONDS
        selector = selectors.DefaultSelector()
        selector.register(stream, selectors.EVENT_READ)
        try:
            while b"\n" not in buffered:
                remaining = deadline - time.monotonic()
                self.assertGreater(remaining, 0.0, "adapter response timed out")
                ready = selector.select(remaining)
                self.assertTrue(ready, "adapter response timed out")
                chunk = os.read(stream.fileno(), 4096)
                self.assertNotEqual(b"", chunk, f"adapter exited early: {process.poll()}")
                buffered.extend(chunk)
        finally:
            selector.close()

        line, separator, remainder = buffered.partition(b"\n")
        self.assertEqual(b"\n", separator)
        self.assertEqual(b"", remainder, "adapter emitted extra stdout before a request")
        buffered.clear()
        self.assertFalse(line.endswith(b"\r"), "response must use LF, not CRLF")
        return line

    def _request(
        self,
        process: subprocess.Popen[bytes],
        buffered: bytearray,
        request: bytes,
        *,
        seq: int,
        op: str,
    ) -> dict[str, object]:
        assert process.stdin is not None and process.stdout is not None
        self.assertTrue(request.endswith(b"\n"))
        process.stdin.write(request)
        process.stdin.flush()
        line = self._read_response(process, process.stdout, buffered)
        try:
            response = json.loads(line.decode("utf-8", "strict"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            self.fail(f"response is not one UTF-8 LF JSON object: {line!r}: {error}")

        self.assertIsInstance(response, dict)
        self.assertEqual({"seq", "status", "result", "events"}, set(response))
        self.assertIs(type(response["seq"]), int)
        self.assertEqual(seq, response["seq"])
        self.assertEqual("ok", response["status"])
        self.assertIsInstance(response["events"], list)
        self.assertTrue(
            all(isinstance(event, str) and event for event in response["events"])
        )

        result = response["result"]
        self.assertIsInstance(result, dict)
        if op in ("empty", "push"):
            self.assertEqual({"stack"}, set(result))
            self.assertIsInstance(result["stack"], str)
            self.assertTrue(result["stack"])
        elif op == "pop":
            self.assertEqual("some", result.get("tag"))
            self.assertEqual({"tag", "value", "remainder"}, set(result))
            self.assertIs(type(result["value"]), int)
            self.assertIsInstance(result["remainder"], str)
            self.assertTrue(result["remainder"])
        else:  # pragma: no cover - helper misuse, not an adapter outcome
            raise AssertionError(f"unsupported raw-probe operation: {op}")
        return response

    def _assert_codec_and_clean_eof(self, child_argv: Sequence[str]) -> None:
        process = subprocess.Popen(
            tuple(child_argv),
            cwd=ROOT,
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdin is not None and process.stdout is not None
        buffered = bytearray()
        try:
            empty = self._request(
                process,
                buffered,
                b' { "op" : "empty", "args" : { }, "seq" : 0 }\n',
                seq=0,
                op="empty",
            )
            empty_handle = empty["result"]["stack"]
            push_request = (
                '{ "args" : { "value" : 2, "stack" : '
                + json.dumps(empty_handle)
                + ' }, "seq" : 1, "op" : "push" }\n'
            ).encode("utf-8")
            pushed = self._request(
                process, buffered, push_request, seq=1, op="push"
            )
            pushed_handle = pushed["result"]["stack"]
            pop_request = (
                '{ "seq" : 2, "args" : { "stack" : '
                + json.dumps(pushed_handle)
                + ' }, "op" : "pop" }\n'
            ).encode("utf-8")
            self._request(process, buffered, pop_request, seq=2, op="pop")

            process.stdin.close()
            process.stdin = None
            try:
                tail, stderr = process.communicate(timeout=PROCESS_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                process.kill()
                tail, stderr = process.communicate()
                self.fail(
                    f"adapter did not exit after EOF: {shlex.join(child_argv)}; "
                    f"stdout={tail!r}; stderr={stderr!r}"
                )
            self.assertEqual(
                0,
                process.returncode,
                f"adapter EOF exit: {process.returncode}; stderr={stderr!r}; "
                f"command={shlex.join(child_argv)}",
            )
            self.assertEqual(b"", tail, "adapter emitted stdout after the final response")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    def _assert_outcomes(
        self,
        report: ConformanceReport,
        expected: dict[str, tuple[str, tuple[str, ...]]],
        *,
        overall: str,
        causes: tuple[str, ...],
    ) -> None:
        actual = {
            outcome.declaration_id: (outcome.result, outcome.causes)
            for outcome in report.declaration_outcomes
        }
        self.assertEqual(PLAN_SHA256, report.plan_sha256, report)
        self.assertEqual(overall, report.result, report)
        self.assertEqual(causes, report.causes, report)
        self.assertEqual(set(DECLARATIONS), set(actual), report)
        self.assertEqual(expected, actual, report)

    # Fixture/toolchain controls: these must be green before candidate work starts.

    def test_rust_breaker_builds_with_explicit_stdlib_boundary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="wave4-rust-breaker-build-") as directory:
            self._build_rust(RUST_BREAKER, Path(directory) / "rust-law-breaker")

    def test_typescript_breaker_typechecks_offline(self) -> None:
        self._check_typescript(TYPESCRIPT_BREAKER)

    def test_rust_breaker_codec_and_eof_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory(prefix="wave4-rust-breaker-codec-") as directory:
            child_argv = self._build_rust(
                RUST_BREAKER, Path(directory) / "rust-law-breaker"
            )
            self._assert_codec_and_clean_eof(child_argv)

    def test_typescript_breaker_codec_and_eof_lifecycle(self) -> None:
        self._assert_codec_and_clean_eof(self._deno_child_argv(TYPESCRIPT_BREAKER))

    def test_rust_breaker_challenges_only_pop_push(self) -> None:
        with tempfile.TemporaryDirectory(prefix="wave4-rust-breaker-semantic-") as directory:
            child_argv = self._build_rust(
                RUST_BREAKER, Path(directory) / "rust-law-breaker"
            )
            report = run_stack_conformance(
                child_argv, plan=default_stack_conformance_plan()
            )
        expected = {declaration: ("supports", ()) for declaration in DECLARATIONS}
        expected["pop-push"] = ("challenges", ("POP_PUSH_VALUE",))
        self._assert_outcomes(
            report,
            expected,
            overall="challenges",
            causes=("POP_PUSH_VALUE",),
        )

    def test_typescript_breaker_challenges_only_persistence(self) -> None:
        report = run_stack_conformance(
            self._deno_child_argv(TYPESCRIPT_BREAKER),
            plan=default_stack_conformance_plan(),
        )
        expected = {declaration: ("supports", ()) for declaration in DECLARATIONS}
        expected["persistence"] = (
            "challenges",
            ("RETAINED_HANDLE_CHANGED",),
        )
        self._assert_outcomes(
            report,
            expected,
            overall="challenges",
            causes=("RETAINED_HANDLE_CHANGED",),
        )

    # Correct candidate controls: red only while the named package sources are absent.

    def test_rust_correct_candidate_builds_with_explicit_stdlib_boundary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="wave4-rust-candidate-build-") as directory:
            self._build_rust(RUST_CANDIDATE, Path(directory) / "stack-rust-adapter")

    def test_typescript_correct_candidate_typechecks_offline(self) -> None:
        self._check_typescript(TYPESCRIPT_CANDIDATE)

    def test_rust_correct_candidate_codec_and_eof_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory(prefix="wave4-rust-candidate-codec-") as directory:
            child_argv = self._build_rust(
                RUST_CANDIDATE, Path(directory) / "stack-rust-adapter"
            )
            self._assert_codec_and_clean_eof(child_argv)

    def test_typescript_correct_candidate_codec_and_eof_lifecycle(self) -> None:
        self._assert_sources(
            (
                TYPESCRIPT_CANDIDATE / "adapter.ts",
                TYPESCRIPT_CANDIDATE / "stack.ts",
            ),
            "TypeScript",
        )
        self._assert_codec_and_clean_eof(
            self._deno_child_argv(TYPESCRIPT_CANDIDATE)
        )

    def test_rust_correct_candidate_supports_exact_default_campaign(self) -> None:
        with tempfile.TemporaryDirectory(prefix="wave4-rust-candidate-semantic-") as directory:
            child_argv = self._build_rust(
                RUST_CANDIDATE, Path(directory) / "stack-rust-adapter"
            )
            report = run_stack_conformance(
                child_argv, plan=default_stack_conformance_plan()
            )
        self._assert_outcomes(
            report,
            {declaration: ("supports", ()) for declaration in DECLARATIONS},
            overall="supports",
            causes=(),
        )

    def test_typescript_correct_candidate_supports_exact_default_campaign(self) -> None:
        child_argv = self._check_typescript(TYPESCRIPT_CANDIDATE)
        report = run_stack_conformance(
            child_argv, plan=default_stack_conformance_plan()
        )
        self._assert_outcomes(
            report,
            {declaration: ("supports", ()) for declaration in DECLARATIONS},
            overall="supports",
            causes=(),
        )


if __name__ == "__main__":
    unittest.main()
