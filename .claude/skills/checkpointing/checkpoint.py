#!/usr/bin/env python3
"""
Checkpoint script: Read CLI logs and update agent context files.

Usage:
    python checkpoint.py [--since YYYY-MM-DD]

Updates:
    - CLAUDE.md
    - .codex/AGENTS.md
    - .gemini/GEMINI.md
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
LOG_FILE = PROJECT_ROOT / ".claude" / "logs" / "cli-tools.jsonl"

CONTEXT_FILES = {
    "claude": PROJECT_ROOT / "CLAUDE.md",
    "codex": PROJECT_ROOT / ".codex" / "AGENTS.md",
    "gemini": PROJECT_ROOT / ".gemini" / "GEMINI.md",
}

SESSION_HISTORY_HEADER = "## Session History"


def parse_logs(since: str | None = None) -> list[dict]:
    """Parse JSONL log file and return entries."""
    if not LOG_FILE.exists():
        return []

    entries = []
    since_dt = None
    if since:
        since_dt = datetime.fromisoformat(since).replace(tzinfo=timezone.utc)

    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if since_dt:
                    entry_dt = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                    if entry_dt < since_dt:
                        continue
                entries.append(entry)
            except (json.JSONDecodeError, KeyError):
                continue

    return entries


def summarize_entries(entries: list[dict]) -> dict[str, list[dict]]:
    """Group and summarize entries by tool and date."""
    by_date: dict[str, dict[str, list]] = {}

    for entry in entries:
        ts = entry.get("timestamp", "")
        date = ts[:10] if ts else "unknown"
        tool = entry.get("tool", "unknown")

        if date not in by_date:
            by_date[date] = {"codex": [], "gemini": []}

        if tool in by_date[date]:
            by_date[date][tool].append({
                "prompt": entry.get("prompt", "")[:200],
                "response_preview": entry.get("response", "")[:300],
                "success": entry.get("success", False),
            })

    return by_date


def generate_session_history(by_date: dict) -> str:
    """Generate markdown session history section."""
    if not by_date:
        return ""

    lines = [SESSION_HISTORY_HEADER, ""]

    for date in sorted(by_date.keys(), reverse=True):
        lines.append(f"### {date}")
        lines.append("")

        data = by_date[date]

        if data.get("codex"):
            lines.append("**Codex相談:**")
            for item in data["codex"][:5]:  # Limit to 5 per day
                prompt_summary = item["prompt"][:100].replace("\n", " ")
                status = "✓" if item["success"] else "✗"
                lines.append(f"- {status} {prompt_summary}...")
            lines.append("")

        if data.get("gemini"):
            lines.append("**Gemini調査:**")
            for item in data["gemini"][:5]:  # Limit to 5 per day
                prompt_summary = item["prompt"][:100].replace("\n", " ")
                status = "✓" if item["success"] else "✗"
                lines.append(f"- {status} {prompt_summary}...")
            lines.append("")

    return "\n".join(lines)


def update_context_file(file_path: Path, session_history: str) -> bool:
    """Update context file with session history."""
    if not file_path.exists():
        print(f"Warning: {file_path} does not exist, skipping")
        return False

    content = file_path.read_text(encoding="utf-8")

    # Remove existing session history section
    pattern = rf"{re.escape(SESSION_HISTORY_HEADER)}.*"
    content = re.sub(pattern, "", content, flags=re.DOTALL)
    content = content.rstrip() + "\n\n"

    # Append new session history
    content += session_history

    file_path.write_text(content, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="Checkpoint session context")
    parser.add_argument("--since", help="Only include logs since this date (YYYY-MM-DD)")
    args = parser.parse_args()

    # Parse logs
    entries = parse_logs(args.since)
    if not entries:
        print("No log entries found.")
        print(f"Log file: {LOG_FILE}")
        return

    print(f"Found {len(entries)} log entries")

    # Summarize
    by_date = summarize_entries(entries)

    # Generate session history
    session_history = generate_session_history(by_date)
    if not session_history:
        print("No session history to write")
        return

    # Update each context file
    for name, file_path in CONTEXT_FILES.items():
        if update_context_file(file_path, session_history):
            print(f"Updated: {file_path}")
        else:
            print(f"Skipped: {file_path}")

    print("\nSession history has been written to all context files.")
    print("All agents (Claude, Codex, Gemini) can now see the session history.")


if __name__ == "__main__":
    main()
