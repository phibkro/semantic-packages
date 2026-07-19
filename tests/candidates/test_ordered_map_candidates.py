"""Red-first package and independence controls for the O6c candidates."""

from __future__ import annotations

import hashlib
import json
import os
import re
import select
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from semantic_packages import ordered_map_contract, ordered_map_runner


ROOT = Path(__file__).resolve().parents[2]
RUST = ROOT / "implementations" / "ordered-map" / "rust"
TYPESCRIPT = ROOT / "implementations" / "ordered-map" / "typescript"
RUST_FILES = {"README.md", "src/main.rs", "src/ordered_map.rs"}
TYPESCRIPT_FILES = {"README.md", "adapter.ts", "ordered_map.ts"}
DECLARATIONS = {
    "lookup-empty",
    "lookup-put-same",
    "lookup-put-other",
    "put-existing-position",
    "put-new-appends",
    "persistence",
    "ordered-map-effects",
}
CASE_IDS = {
    "lookup-empty",
    "same-class-replacement",
    "other-class-preservation",
    "nonlast-overwrite-order",
    "new-class-append-three",
    "retained-new-class-source",
    "retained-existing-class-source",
}


def _required_tool(environment: str, executable: str) -> str:
    requested = os.environ.get(environment, executable)
    resolved = shutil.which(requested)
    if resolved is None:
        raise AssertionError(f"{environment}={requested!r} is not executable")
    return resolved


def _source_files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }


def _assert_packet_files(root: Path, expected: set[str]) -> None:
    if root.is_symlink():
        raise AssertionError(f"candidate root must not be a symlink: {root}")
    allowed_directories = {
        parent.as_posix()
        for relative in expected
        for parent in Path(relative).parents
        if parent.as_posix() != "."
    }
    observed_files: set[str] = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise AssertionError(f"candidate entry must not be a symlink: {path}")
        if path.is_dir():
            if relative not in allowed_directories:
                raise AssertionError(f"unexpected candidate directory: {path}")
            continue
        if not path.is_file() or relative not in expected:
            raise AssertionError(f"unexpected candidate entry: {path}")
        if not path.resolve().is_relative_to(root.resolve()):
            raise AssertionError(f"candidate file escapes packet root: {path}")
        observed_files.add(relative)
    if observed_files != expected:
        raise AssertionError((root, observed_files, expected))


def _without_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", text)


def _without_comments_or_strings(text: str) -> str:
    text = _without_comments(text)
    return re.sub(
        r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`',
        '""',
        text,
        flags=re.DOTALL,
    )


def _tool_output(command: tuple[str, ...]) -> str:
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout


def _locked_tools() -> tuple[str, str, str]:
    rustc = _required_tool("RUSTC", "rustc")
    deno = _required_tool("DENO", "deno")
    gcc = _required_tool("GCC", "gcc")
    rust_version = _tool_output((rustc, "--version", "--verbose"))
    deno_version = _tool_output((deno, "--version"))
    gcc_version = _tool_output((gcc, "--version"))
    if not all(
        token in rust_version
        for token in (
            "release: 1.96.1",
            "commit-hash: 31fca3adb283cc9dfd56b49cdee9a96eb9c96ffd",
            "host: x86_64-unknown-linux-gnu",
            "LLVM version: 21.1.8",
        )
    ):
        raise AssertionError(rust_version)
    if deno_version.splitlines() != [
        "deno 2.9.2 (stable, release, x86_64-unknown-linux-gnu)",
        "v8 14.9.207.2-rusty",
        "typescript 6.0.3",
    ]:
        raise AssertionError(deno_version)
    if not gcc_version.startswith("gcc (GCC) 15.2.0\n"):
        raise AssertionError(gcc_version)
    return rustc, deno, gcc


def _rust_build(output: Path) -> tuple[str, ...]:
    rustc, _deno, gcc = _locked_tools()
    return (
        rustc,
        "--edition=2024",
        "-C",
        "opt-level=2",
        "-C",
        f"linker={gcc}",
        "-o",
        os.fspath(output),
        os.fspath(RUST / "src" / "main.rs"),
    )


def _rust_unit_build(output: Path) -> tuple[str, ...]:
    rustc, _deno, gcc = _locked_tools()
    return (
        rustc,
        "--edition=2024",
        "--test",
        "-C",
        f"linker={gcc}",
        "-o",
        os.fspath(output),
        os.fspath(RUST / "src" / "ordered_map.rs"),
    )


def _typescript_command() -> tuple[str, ...]:
    _rustc, deno, _gcc = _locked_tools()
    return (
        deno,
        "run",
        "--no-config",
        "--no-lock",
        "--no-npm",
        "--no-remote",
        "--no-prompt",
        os.fspath(TYPESCRIPT / "adapter.ts"),
    )


def _read_response(process: subprocess.Popen[bytes]) -> dict:
    assert process.stdout is not None
    ready, _, _ = select.select([process.stdout.fileno()], [], [], 3.0)
    if not ready:
        raise AssertionError("candidate did not produce a bounded response")
    line = process.stdout.readline()
    if not line.endswith(b"\n"):
        raise AssertionError(f"candidate response is not LF framed: {line!r}")
    return json.loads(line)


def _exercise_valid_framing(command: tuple[str, ...]) -> None:
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    try:
        process.stdin.write(b'{ "args" : { }, "op" : "empty", "seq" : 0 }\n')
        process.stdin.flush()
        empty = _read_response(process)
        if set(empty) != {"seq", "status", "result", "events"}:
            raise AssertionError(empty)
        if (empty["seq"], empty["status"], empty["events"]) != (0, "ok", []):
            raise AssertionError(empty)
        if set(empty["result"]) != {"map"}:
            raise AssertionError(empty)
        handle = empty["result"]["map"]

        put = json.dumps(
            {"op": "put", "args": {"value": 1, "key": "A", "map": handle}, "seq": 1},
            separators=(",", ":"),
        )
        process.stdin.write((put + "\n").encode("utf-8"))
        process.stdin.flush()
        put_response = _read_response(process)
        if set(put_response) != {"seq", "status", "result", "events"}:
            raise AssertionError(put_response)
        if (put_response["seq"], put_response["status"], put_response["events"]) != (
            1,
            "ok",
            [],
        ) or set(put_response["result"]) != {"map"}:
            raise AssertionError(put_response)
        updated = put_response["result"]["map"]

        combined = (
            json.dumps(
                {"args": {"key": "a", "map": updated}, "seq": 2, "op": "lookup"},
                separators=(",", ":"),
            )
            + "\n"
            + json.dumps(
                {"seq": 3, "args": {"map": updated}, "op": "entries"},
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        midpoint = len(combined) - 7
        process.stdin.write(combined[:midpoint])
        process.stdin.flush()
        process.stdin.write(combined[midpoint:])
        process.stdin.flush()
        self_lookup = _read_response(process)
        entries = _read_response(process)
        if self_lookup != {
            "seq": 2,
            "status": "ok",
            "result": {"tag": "some", "value": 1},
            "events": [],
        }:
            raise AssertionError(self_lookup)
        if entries != {
            "seq": 3,
            "status": "ok",
            "result": {"entries": [{"class": "a", "value": 1}]},
            "events": [],
        }:
            raise AssertionError(entries)
        process.stdin.close()
        returncode = process.wait(timeout=3)
        if returncode != 0:
            assert process.stderr is not None
            raise AssertionError(process.stderr.read())
        assert process.stdout is not None and process.stderr is not None
        if process.stdout.read() != b"" or process.stderr.read() != b"":
            raise AssertionError("candidate emitted output after the valid framing exchange")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


PACKETS_EXIST = RUST.is_dir() and TYPESCRIPT.is_dir()


class OrderedMapCandidatePreconditionTest(unittest.TestCase):
    def test_reviewed_runner_and_locked_toolchains_precede_candidate_packets(self) -> None:
        plan = ordered_map_contract.inspect_conformance_plan()
        self.assertTrue(plan.ok, plan.diagnostics)
        self.assertEqual(
            "2cf7b481946ce1c0130e70b0d0ffcc1ec5a58bb10e7963b3f5058253bb63447a",
            plan.canonical_sha256,
        )
        self.assertEqual(
            ("command",),
            tuple(
                __import__("inspect")
                .signature(ordered_map_runner.run_ordered_map_conformance)
                .parameters
            ),
        )
        rustc, deno, gcc = _locked_tools()
        self.assertTrue(rustc)
        self.assertTrue(deno)
        self.assertTrue(gcc)

    def test_two_candidate_packets_are_the_only_red_predecessor(self) -> None:
        self.assertTrue(
            PACKETS_EXIST,
            "O6c-P intentionally precedes both implementations/ordered-map packets",
        )


@unittest.skipUnless(PACKETS_EXIST, "O6c-P freezes package controls before implementation")
class OrderedMapCandidateContractTest(unittest.TestCase):
    def test_packets_have_exact_small_documented_source_boundaries(self) -> None:
        _assert_packet_files(RUST, RUST_FILES)
        _assert_packet_files(TYPESCRIPT, TYPESCRIPT_FILES)
        for readme in (RUST / "README.md", TYPESCRIPT / "README.md"):
            text = readme.read_text(encoding="utf-8")
            for phrase in (
                "ordered-map-runner-json-v1",
                "adapter faithfulness",
                "event completeness",
                "external effects",
                "performance",
                "registry-driven execution",
                "not Evidence",
            ):
                self.assertIn(phrase, text)
        rust_readme = (RUST / "README.md").read_text(encoding="utf-8")
        for command_part in (
            'candidate_dir=$(mktemp -d)',
            "${RUSTC:-rustc} --edition=2024 -C opt-level=2",
            "-C linker=${GCC:-gcc}",
            '-o "$candidate_dir/ordered-map-rust"',
            "src/main.rs",
            '"$candidate_dir/ordered-map-rust"',
            "${RUSTC:-rustc} --edition=2024 --test",
            '-o "$candidate_dir/ordered-map-unit"',
            "src/ordered_map.rs",
            '"$candidate_dir/ordered-map-unit"',
            "rustc 1.96.1",
            "31fca3adb283cc9dfd56b49cdee9a96eb9c96ffd",
            "gcc (GCC) 15.2.0",
        ):
            self.assertIn(command_part, rust_readme)
        typescript_readme = (TYPESCRIPT / "README.md").read_text(encoding="utf-8")
        for command_part in (
            "${DENO:-deno} check --no-config --no-lock --no-npm --no-remote",
            "adapter.ts ordered_map.ts",
            "${DENO:-deno} run --no-config --no-lock --no-npm --no-remote --no-prompt",
            "adapter.ts",
            "deno 2.9.2",
            "TypeScript 6.0.3",
        ):
            self.assertIn(command_part, typescript_readme)

    def test_private_representations_are_deliberately_different(self) -> None:
        rust = _without_comments_or_strings(
            (RUST / "src" / "ordered_map.rs").read_text(encoding="utf-8")
        )
        typescript = _without_comments_or_strings(
            (TYPESCRIPT / "ordered_map.ts").read_text(encoding="utf-8")
        )
        self.assertRegex(
            rust,
            r"(?:pub\s+)?struct\s+OrderedMap\s*\{\s*"
            r"entries:\s*Vec<\(ClassToken,\s*i64\)>,?",
        )
        self.assertNotIn("HashMap", rust)
        self.assertRegex(
            typescript,
            r"(?:export\s+)?class\s+OrderedMap\s*\{\s*"
            r"private readonly values:\s*ReadonlyMap<ClassToken,\s*number>;\s*"
            r"private readonly order:\s*readonly ClassToken\[\];",
        )
        self.assertNotEqual(rust.encode(), typescript.encode())

    def test_sources_do_not_import_candidates_runner_or_campaign_oracle(self) -> None:
        _assert_packet_files(RUST, RUST_FILES)
        _assert_packet_files(TYPESCRIPT, TYPESCRIPT_FILES)
        packet_text = {
            path: path.read_text(encoding="utf-8")
            for root in (RUST, TYPESCRIPT)
            for path in root.rglob("*")
            if path.is_file()
        }
        forbidden = (
            "semantic_packages",
            "ordered_map_runner",
            "ordered_map_contract",
            "contracts/ordered-map",
            "implementations/ordered-map/rust",
            "implementations/ordered-map/typescript",
            *CASE_IDS,
            *DECLARATIONS,
        )
        for path, text in packet_text.items():
            with self.subTest(path=path):
                self.assertFalse([token for token in forbidden if token in text])
                self.assertNotIn("http://", text)
                self.assertNotIn("https://", text)
        rust_main = (RUST / "src" / "main.rs").read_text(encoding="utf-8")
        rust_map = (RUST / "src" / "ordered_map.rs").read_text(encoding="utf-8")
        for text in (rust_main, rust_map):
            self.assertNotRegex(text, r"include(?:_str|_bytes)?!\s*\(")
            self.assertNotIn("#[path", text)
            for runtime_escape in (
                "std::fs",
                "File::open",
                "read_to_string",
                "Command::new",
                "env!",
                "option_env!",
            ):
                self.assertNotIn(runtime_escape, text)
        self.assertIn("mod ordered_map;", rust_main)
        typescript_adapter = _without_comments(
            (TYPESCRIPT / "adapter.ts").read_text(encoding="utf-8")
        )
        typescript_map = _without_comments(
            (TYPESCRIPT / "ordered_map.ts").read_text(encoding="utf-8")
        )
        imports = re.findall(r'from\s+["\']([^"\']+)["\']', typescript_adapter)
        self.assertEqual(["./ordered_map.ts"], imports)
        self.assertEqual(1, len(re.findall(r"\bimport\b", typescript_adapter)))
        self.assertNotRegex(typescript_adapter, r"\bimport\s*\(")
        self.assertNotRegex(typescript_map, r"\bimport\b|\bexport\b.*\bfrom\s+[\"\']")
        for text in (typescript_adapter, typescript_map):
            for runtime_escape in (
                "import(",
                "Deno.read",
                "Deno.open",
                "Deno.Command",
                "fetch(",
            ):
                self.assertNotIn(runtime_escape, text)

    def test_rust_build_and_unit_boundary_are_reproducible(self) -> None:
        before = _source_files(RUST)
        with tempfile.TemporaryDirectory(prefix="ordered-map-rust-") as raw:
            first = Path(raw) / "candidate-a"
            second = Path(raw) / "candidate-b"
            for output in (first, second):
                subprocess.run(_rust_build(output), check=True, timeout=20)
            self.assertEqual(
                hashlib.sha256(first.read_bytes()).digest(),
                hashlib.sha256(second.read_bytes()).digest(),
            )
            unit = Path(raw) / "ordered-map-unit"
            subprocess.run(
                _rust_unit_build(unit),
                check=True,
                timeout=20,
            )
            subprocess.run((os.fspath(unit),), check=True, timeout=10)
        self.assertEqual(before, _source_files(RUST))

    def test_typescript_checks_offline_without_emitting_build_artifacts(self) -> None:
        before = _source_files(TYPESCRIPT)
        subprocess.run(
            (
                _locked_tools()[1],
                "check",
                "--no-config",
                "--no-lock",
                "--no-npm",
                "--no-remote",
                os.fspath(TYPESCRIPT / "adapter.ts"),
                os.fspath(TYPESCRIPT / "ordered_map.ts"),
            ),
            check=True,
            timeout=20,
        )
        self.assertEqual(before, _source_files(TYPESCRIPT))

    def test_rust_candidate_supports_the_exact_campaign(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ordered-map-rust-run-") as raw:
            binary = Path(raw) / "candidate"
            subprocess.run(_rust_build(binary), check=True, timeout=20)
            report = ordered_map_runner.run_ordered_map_conformance((os.fspath(binary),))
        self.assertEqual("supports", report.result, report)
        self.assertEqual(DECLARATIONS, {item.declaration_id for item in report.declarations})

    def test_typescript_candidate_supports_the_exact_campaign(self) -> None:
        report = ordered_map_runner.run_ordered_map_conformance(_typescript_command())
        self.assertEqual("supports", report.result, report)
        self.assertEqual(DECLARATIONS, {item.declaration_id for item in report.declarations})

    def test_both_candidates_are_persistent_under_arbitrary_opaque_handles(self) -> None:
        commands: list[tuple[str, ...]] = []
        temporary = tempfile.TemporaryDirectory(prefix="ordered-map-both-")
        self.addCleanup(temporary.cleanup)
        binary = Path(temporary.name) / "rust-candidate"
        subprocess.run(_rust_build(binary), check=True, timeout=20)
        commands.append((os.fspath(binary),))
        commands.append(_typescript_command())
        for command in commands:
            with self.subTest(command=command[0]):
                report = ordered_map_runner.run_ordered_map_conformance(command)
                persistence = next(
                    item for item in report.declarations if item.declaration_id == "persistence"
                )
                self.assertEqual(("supports", 2), (persistence.result, persistence.observation_count))

    def test_both_adapters_accept_valid_reordered_split_and_combined_frames(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ordered-map-framing-") as raw:
            binary = Path(raw) / "rust-candidate"
            subprocess.run(_rust_build(binary), check=True, timeout=20)
            for command in ((os.fspath(binary),), _typescript_command()):
                with self.subTest(command=command[0]):
                    _exercise_valid_framing(command)

    def test_packet_commands_exit_cleanly_and_leave_repository_unchanged(self) -> None:
        before = {
            path.relative_to(ROOT): path.read_bytes()
            for root in (RUST, TYPESCRIPT)
            for path in root.rglob("*")
            if path.is_file()
        }
        with tempfile.TemporaryDirectory(prefix="ordered-map-exit-") as raw:
            binary = Path(raw) / "candidate"
            subprocess.run(_rust_build(binary), check=True, timeout=20)
            for command in ((os.fspath(binary),), _typescript_command()):
                process = subprocess.run(command, input=b"", capture_output=True, timeout=3)
                self.assertEqual(0, process.returncode, process.stderr)
                self.assertEqual(b"", process.stdout)
        after = {
            path.relative_to(ROOT): path.read_bytes()
            for root in (RUST, TYPESCRIPT)
            for path in root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
