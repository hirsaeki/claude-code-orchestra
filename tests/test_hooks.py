#!/usr/bin/env python
"""Unit tests for Claude Code Orchestra hooks."""

import json
import py_compile
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "hooks"
ALL_HOOKS = sorted(HOOKS_DIR.glob("*.py"))


def run_hook(
    hook_path: Path, payload: dict, timeout: int = 10
) -> tuple[str, str, int]:
    """Run a hook as a subprocess, passing payload as JSON via stdin."""
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(hook_path.parent.parent.parent),
    )
    return result.stdout, result.stderr, result.returncode


BASH_PAYLOAD = {
    "tool_name": "Bash",
    "tool_input": {"command": "echo hello"},
    "tool_response": {"stdout": "hello", "stderr": "", "exit_code": 0},
}

EMPTY_PAYLOAD: dict = {}


class TestHookCompilation:
    @pytest.mark.parametrize("hook", ALL_HOOKS, ids=[h.name for h in ALL_HOOKS])
    def test_hook_compiles(self, hook: Path) -> None:
        py_compile.compile(str(hook), doraise=True)


class TestAllHooksBasic:
    @pytest.mark.parametrize("hook", ALL_HOOKS, ids=[h.name for h in ALL_HOOKS])
    def test_hook_does_not_crash_on_bash_payload(self, hook: Path) -> None:
        stdout, stderr, code = run_hook(hook, BASH_PAYLOAD)
        assert code == 0, f"{hook.name} crashed: {stderr}"

    @pytest.mark.parametrize("hook", ALL_HOOKS, ids=[h.name for h in ALL_HOOKS])
    def test_hook_does_not_crash_on_empty_payload(self, hook: Path) -> None:
        stdout, stderr, code = run_hook(hook, EMPTY_PAYLOAD)
        assert code == 0, f"{hook.name} crashed on empty: {stderr}"


class TestLogCliTools:
    HOOK = HOOKS_DIR / "log-cli-tools.py"

    @pytest.fixture()
    def log_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        monkeypatch.setenv("_ORCHESTRA_LOG_DIR_OVERRIDE", str(log_dir))

        hook_src = self.HOOK.read_text(encoding="utf-8")
        patched = hook_src.replace(
            'LOG_DIR = Path(__file__).parent.parent / "logs"',
            f'LOG_DIR = Path(r"{log_dir}")',
        )
        patched_hook = tmp_path / "log-cli-tools.py"
        patched_hook.write_text(patched, encoding="utf-8")
        return patched_hook

    def _read_last_log_entry(self, log_env: Path) -> dict | None:
        log_file = log_env.parent / "logs" / "cli-tools.jsonl"
        if not log_file.exists():
            return None
        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            return None
        return json.loads(lines[-1])

    def test_codex_command_gets_logged(self, log_env: Path) -> None:
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": 'codex exec --skip-git-repo-check --sandbox read-only --full-auto "test question"'
            },
            "tool_response": {
                "stdout": "codex says hello",
                "stderr": "some warning",
                "exit_code": 0,
            },
        }
        run_hook(log_env, payload)
        entry = self._read_last_log_entry(log_env)
        assert entry is not None, "No log entry created"
        assert entry["tool"] == "codex"
        assert entry["success"] is True
        assert "codex says hello" in entry["stdout"]
        assert "some warning" in entry["stderr"]

    def test_gemini_command_gets_logged(self, log_env: Path) -> None:
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": 'gemini -p "research topic"'},
            "tool_response": {
                "stdout": "gemini output",
                "stderr": "",
                "exit_code": 0,
            },
        }
        run_hook(log_env, payload)
        entry = self._read_last_log_entry(log_env)
        assert entry is not None
        assert entry["tool"] == "gemini"

    def test_non_cli_command_not_logged(self, log_env: Path) -> None:
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo hello"},
            "tool_response": {"stdout": "hello", "stderr": "", "exit_code": 0},
        }
        run_hook(log_env, payload)
        entry = self._read_last_log_entry(log_env)
        assert entry is None

    def test_exit_code_zero_means_success(self, log_env: Path) -> None:
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": 'codex exec --skip-git-repo-check --sandbox read-only --full-auto "q"'
            },
            "tool_response": {"stdout": "ok", "stderr": "", "exit_code": 0},
        }
        run_hook(log_env, payload)
        entry = self._read_last_log_entry(log_env)
        assert entry is not None
        assert entry["success"] is True

    def test_exit_code_nonzero_means_failure(self, log_env: Path) -> None:
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": 'codex exec --skip-git-repo-check --sandbox read-only --full-auto "q"'
            },
            "tool_response": {"stdout": "", "stderr": "error", "exit_code": 1},
        }
        run_hook(log_env, payload)
        entry = self._read_last_log_entry(log_env)
        assert entry is not None
        assert entry["success"] is False
        assert entry["exit_code"] == 1

    def test_stderr_captured_in_log(self, log_env: Path) -> None:
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": 'codex exec --skip-git-repo-check --sandbox read-only --full-auto "q"'
            },
            "tool_response": {
                "stdout": "",
                "stderr": "important stderr info",
                "exit_code": 0,
            },
        }
        run_hook(log_env, payload)
        entry = self._read_last_log_entry(log_env)
        assert entry is not None
        assert "important stderr info" in entry["stderr"]


class TestNotifyHandoff:
    HOOK = HOOKS_DIR / "notify-handoff.py"

    def test_no_handoffs_no_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        patched_src = self.HOOK.read_text(encoding="utf-8").replace(
            'HANDOFFS_DIR = Path(__file__).parent.parent / "handoffs"',
            f'HANDOFFS_DIR = Path(r"{tmp_path / "handoffs"}")',
        )
        patched_hook = tmp_path / "notify-handoff.py"
        patched_hook.write_text(patched_src, encoding="utf-8")
        stdout, stderr, code = run_hook(patched_hook, {})
        assert code == 0
        assert stdout.strip() == ""

    def test_with_handoff_shows_notification(self, tmp_path: Path) -> None:
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir()
        (handoffs_dir / "2026-02-15-120000.prompt.md").write_text("resume", encoding="utf-8")

        patched_src = self.HOOK.read_text(encoding="utf-8").replace(
            'HANDOFFS_DIR = Path(__file__).parent.parent / "handoffs"',
            f'HANDOFFS_DIR = Path(r"{handoffs_dir}")',
        )
        patched_hook = tmp_path / "notify-handoff.py"
        patched_hook.write_text(patched_src, encoding="utf-8")
        stdout, stderr, code = run_hook(patched_hook, {})
        assert code == 0
        output = json.loads(stdout)
        ctx = output["hookSpecificOutput"]["additionalContext"]
        assert "/handoff --resume" in ctx

    def test_hook_does_not_crash_on_empty_payload(self) -> None:
        stdout, stderr, code = run_hook(self.HOOK, {})
        assert code == 0


class TestAgentRouter:
    HOOK = HOOKS_DIR / "agent-router.py"

    def test_self_test_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(self.HOOK), "--self-test"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Self-test failed: {result.stderr}"

    def test_japanese_codex_trigger(self) -> None:
        payload = {"prompt": "この関数を実装して"}
        stdout, stderr, code = run_hook(self.HOOK, payload)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            ctx = output.get("hookSpecificOutput", {}).get("additionalContext", "")
            assert "Codex" in ctx

    def test_japanese_gemini_trigger(self) -> None:
        payload = {"prompt": "最新のライブラリを調べて"}
        stdout, stderr, code = run_hook(self.HOOK, payload)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            ctx = output.get("hookSpecificOutput", {}).get("additionalContext", "")
            assert "Gemini" in ctx

    def test_no_trigger_no_output(self) -> None:
        payload = {"prompt": "hello"}
        stdout, stderr, code = run_hook(self.HOOK, payload)
        assert code == 0
        assert stdout.strip() == ""
