#!/usr/bin/env python
"""
SessionStart hook: Notify if unread handoff packages exist.

Checks .claude/handoffs/ for the latest .prompt.md file and suggests
loading it via `/handoff --resume`.
"""

import json
import sys
from pathlib import Path

HANDOFFS_DIR = Path(__file__).parent.parent / "handoffs"


def find_latest_prompt() -> Path | None:
    """Find the most recent .prompt.md file in the handoffs directory."""
    if not HANDOFFS_DIR.is_dir():
        return None
    prompts = sorted(HANDOFFS_DIR.glob("*.prompt.md"), reverse=True)
    return prompts[0] if prompts else None


def main() -> None:
    try:
        json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        pass

    latest = find_latest_prompt()
    if not latest:
        sys.exit(0)

    handoff_name = latest.stem.replace(".prompt", "")
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                f"[Handoff] 前セッションのハンドオフがあります: "
                f"`.claude/handoffs/{latest.name}`\n"
                f"読み込むには `/handoff --resume` を実行してください。\n"
                f"一覧を見るには `/handoff --list` を実行してください。"
            ),
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
