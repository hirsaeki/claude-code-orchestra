#!/usr/bin/env python
"""
Stop hook: Remind user to copy finalized plan into local PLAN.md.

This hook is intentionally non-blocking. It only adds contextual reminder
when the current session appears to involve planning work.
"""

import json
import re
import sys
from pathlib import Path


PLAN_SIGNALS = [
    r"/plan",
    r"implementation plan",
    r"実装計画",
    r"計画",
    r"タスクリスト",
]


def has_plan_signal(payload: dict) -> bool:
    """Best-effort detection of planning-related session content."""
    try:
        text = json.dumps(payload, ensure_ascii=False).lower()
    except Exception:
        return False

    return any(re.search(pattern, text, re.IGNORECASE) for pattern in PLAN_SIGNALS)


def plan_md_exists() -> bool:
    """Check whether PLAN.md exists at repository root."""
    repo_root = Path(__file__).resolve().parents[2]
    return (repo_root / "PLAN.md").exists()


def main() -> None:
    try:
        data = json.load(sys.stdin)

        if not has_plan_signal(data):
            sys.exit(0)

        suffix = "更新済み" if plan_md_exists() else "未作成"
        output = {
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "additionalContext": (
                    "[PLAN.md Reminder] このセッションは plan 関連の内容を含んでいます。"
                    "終了前に、確定した実装計画をローカルの PLAN.md にコピーしてください。"
                    f"(現在: PLAN.md は {suffix})"
                ),
            }
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(0)

    except Exception:
        # Never block session stop on hook failures
        sys.exit(0)


if __name__ == "__main__":
    main()
