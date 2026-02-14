#!/usr/bin/env python
"""
PostToolUse hook: Log Codex/Gemini CLI input/output to JSONL file.

Triggers after Bash tool calls containing 'codex' or 'gemini' commands.
Logs are stored in .claude/logs/cli-tools.jsonl

All agents (Claude Code, subagents, Codex, Gemini) can read this log.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "cli-tools.jsonl"
SENSITIVE_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[bpras]-[A-Za-z0-9\-]+\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]{20,}"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
]


def redact_sensitive(text: str) -> str:
    """Mask known sensitive token patterns in logs."""
    redacted = text
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def extract_quoted_string(command: str, prefix_pattern: str) -> str | None:
    """Extract a quoted string following a prefix pattern.

    Handles double quotes, single quotes, and $'...' syntax.
    Tolerates trailing redirects like 2>> file.
    """
    patterns = [
        prefix_pattern + r'''\s+"((?:[^"\\]|\\.)*)"''',
        prefix_pattern + r"""\s+'((?:[^'\\]|\\.)*)'""",
        prefix_pattern + r"""\s+\$'((?:[^'\\]|\\.)*)'""",
    ]
    for pat in patterns:
        match = re.search(pat, command, re.DOTALL)
        if match:
            return match.group(1).strip()
    return None


def extract_codex_prompt(command: str) -> str | None:
    """Extract prompt from codex exec command."""
    result = extract_quoted_string(command, r"codex\s+exec\s+.*?--full-auto")
    if result:
        return result
    return extract_quoted_string(command, r"codex\s+exec\s+\S+")


def extract_gemini_prompt(command: str) -> str | None:
    """Extract prompt from gemini command."""
    return extract_quoted_string(command, r"gemini\b.*?-p")


def extract_model(command: str) -> str | None:
    """Extract model name from command."""
    match = re.search(r"--model\s+(\S+)", command)
    return match.group(1) if match else None


COMMAND_SEGMENT_TOOL_PATTERN = re.compile(
    r"(?:^|[;&|]\s*|\&\&\s*|\|\|\s*)(codex|gemini)\b",
    re.IGNORECASE,
)


def detect_invoked_tool(command: str) -> str | None:
    """Detect invoked CLI tool from command segments."""
    detected_tools = [
        match.group(1).lower() for match in COMMAND_SEGMENT_TOOL_PATTERN.finditer(command)
    ]
    if "codex" in detected_tools:
        return "codex"
    if "gemini" in detected_tools:
        return "gemini"
    return None


def truncate_text(text: str, max_length: int = 2000) -> str:
    """Truncate text if too long."""
    text = redact_sensitive(text)
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"... [truncated, {len(text)} total chars]"


MAX_LOG_SIZE = 5 * 1024 * 1024


def rotate_log_if_needed() -> None:
    """Rotate log file if it exceeds MAX_LOG_SIZE (5 MB)."""
    if not LOG_FILE.exists():
        return
    try:
        if LOG_FILE.stat().st_size < MAX_LOG_SIZE:
            return
    except OSError:
        return
    rotated = LOG_FILE.with_suffix(".jsonl.1")
    if rotated.exists():
        rotated.unlink()
    LOG_FILE.rename(rotated)


def log_entry(entry: dict) -> None:
    """Append entry to JSONL log file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    rotate_log_if_needed()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def parse_tool_response(hook_input: dict) -> tuple[str, str, int]:
    """Extract stdout/stderr/exit_code from hook payload (supports multiple schemas)."""
    tool_response = hook_input.get("tool_response")
    tool_output = hook_input.get("tool_output")

    if isinstance(tool_response, dict) and any(
        key in tool_response for key in ("stdout", "stderr", "content", "exit_code")
    ):
        stdout = str(tool_response.get("stdout", "") or tool_response.get("content", "") or "")
        stderr = str(tool_response.get("stderr", "") or "")
        exit_code = tool_response.get("exit_code", 0)
        if not isinstance(exit_code, int):
            exit_code = 0
        return stdout, stderr, exit_code

    if isinstance(tool_response, str):
        return tool_response, "", 0

    if isinstance(tool_output, dict):
        stdout = str(tool_output.get("stdout", "") or tool_output.get("content", "") or "")
        stderr = str(tool_output.get("stderr", "") or "")
        exit_code = tool_output.get("exit_code", 0)
        if not isinstance(exit_code, int):
            exit_code = 0
        return stdout, stderr, exit_code

    if isinstance(tool_output, str):
        return tool_output, "", 0

    return "", "", 0


def maybe_emit_notification(tool: str, exit_code: int) -> None:
    """Emit optional hook notification.

    Default behavior is silent unless command fails.
    Set CLAUDE_ORCHESTRA_LOG_NOTIFY=1 to always notify.
    """
    notify_all = os.getenv("CLAUDE_ORCHESTRA_LOG_NOTIFY", "").strip() == "1"
    if not notify_all and exit_code == 0:
        return

    if exit_code == 0:
        message = f"[LOG] {tool.capitalize()} call logged to .claude/logs/cli-tools.jsonl"
    else:
        message = (
            f"[LOG] {tool.capitalize()} call failed (exit_code={exit_code}) - "
            "logged to .claude/logs/cli-tools.jsonl"
        )

    print(json.dumps({"result": "continue", "message": message}))


def main() -> None:
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    # Only process Bash tool calls
    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Bash":
        return

    # Get command and output
    tool_input = hook_input.get("tool_input", {})
    command = str(tool_input.get("command", "") or "")
    stdout, stderr, exit_code = parse_tool_response(hook_input)

    invoked_tool = detect_invoked_tool(command)
    if not invoked_tool:
        return

    # Extract prompt based on tool type
    if invoked_tool == "codex":
        tool = "codex"
        prompt = extract_codex_prompt(command)
        model = extract_model(command) or "gpt-5.3-codex"
    else:
        tool = "gemini"
        prompt = extract_gemini_prompt(command)
        model = "gemini-3-pro-preview"

    # Determine success
    success = exit_code == 0
    has_output = bool(stdout or stderr)
    response = stdout if stdout else stderr if stderr else ""

    # Create log entry
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "model": model,
        "prompt": truncate_text(prompt) if prompt else None,
        "stdout": truncate_text(stdout) if stdout else "",
        "stderr": truncate_text(stderr) if stderr else "",
        "response": truncate_text(response) if response else "",
        "success": success,
        "has_output": has_output,
        "exit_code": exit_code,
    }

    log_entry(entry)
    maybe_emit_notification(tool, exit_code)


if __name__ == "__main__":
    main()
