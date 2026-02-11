#!/usr/bin/env python
"""
SessionEnd hook: Remind user to update PLAN.md and create handoff package at session end.

This hook is intentionally non-blocking. It only adds contextual reminder
when the ending session appears to involve planning/implementation work.
"""

import json
import re
import subprocess
import sys
from pathlib import Path


PLAN_SIGNALS = [
    r"/plan",
    r"implementation plan",
    r"実装計画",
    r"計画",
    r"タスクリスト",
]

HANDOFF_SIGNALS = [
    r"/handoff",
    r"handoff",
    r"引き継ぎ",
    r"引継ぎ",
    r"再開",
    r"resume",
    r"checkpoint",
    r"実装",
    r"テスト",
    r"修正",
]


def serialize_payload_for_match(payload: dict) -> str:
    """Serialize hook payload into searchable lowercase text."""
    try:
        return json.dumps(payload, ensure_ascii=False).lower()
    except Exception:
        return ""


def matches_any_signal(text: str, patterns: list[str]) -> bool:
    """Return True if any regex pattern matches the text."""
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def session_mentions_plan(payload: dict) -> bool:
    """Best-effort detection of planning-related session content."""
    text = serialize_payload_for_match(payload)
    if not text:
        return False

    return matches_any_signal(text, PLAN_SIGNALS)


def session_mentions_handoff(payload: dict) -> bool:
    """Best-effort detection of handoff-related session content."""
    text = serialize_payload_for_match(payload)
    if not text:
        return False

    return matches_any_signal(text, HANDOFF_SIGNALS)


def resolve_repo_root() -> Path:
    """Resolve repository root from hook location."""
    return Path(__file__).resolve().parents[2]


def count_working_tree_changes(repo_root: Path) -> int:
    """Get current git working tree change count."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode != 0:
            return 0
        return len([line for line in result.stdout.splitlines() if line.strip()])
    except Exception:
        return 0


def plan_md_exists(repo_root: Path) -> bool:
    """Check whether PLAN.md exists at repository root."""
    return (repo_root / "PLAN.md").exists()


def find_latest_handoff_file(repo_root: Path) -> Path | None:
    """Get the latest generated handoff markdown file."""
    handoffs_dir = repo_root / ".claude" / "handoffs"
    if not handoffs_dir.exists():
        return None

    candidates = [
        path
        for path in handoffs_dir.glob("*.md")
        if not path.name.endswith(".prompt.md")
    ]
    if not candidates:
        return None

    return max(candidates, key=lambda path: path.stat().st_mtime)


def should_emit_session_end_reminder(
    *,
    plan_related: bool,
    handoff_related: bool,
    change_count: int,
) -> bool:
    """Determine whether reminder should be emitted."""
    return plan_related or handoff_related or change_count > 0


def build_plan_reminder(repo_root: Path) -> str:
    """Build PLAN.md reminder text."""
    plan_status = "更新済み" if plan_md_exists(repo_root) else "未作成"
    return (
        "[PLAN.md Reminder] このセッションは plan 関連の内容を含んでいます。"
        "終了前に、確定した実装計画をローカルの PLAN.md にコピーしてください。"
        f"(現在: PLAN.md は {plan_status})"
    )


def build_handoff_reminder(repo_root: Path, change_count: int) -> str:
    """Build handoff reminder text."""
    handoff_file = find_latest_handoff_file(repo_root)
    handoff_status = handoff_file.name if handoff_file else "未作成"
    dirty_suffix = f"作業ツリー変更: {change_count}件。" if change_count > 0 else ""
    return (
        "[Handoff Reminder] セッション終了前に `/handoff --goal \"次セッションの最優先目標\"` "
        "を実行して引き継ぎパックを作成してください。"
        "もし既に終了している場合は、新しいセッションの最初に同じコマンドを実行してください（/resume は不要）。"
        f"(最新 handoff: {handoff_status})"
        f" {dirty_suffix}".rstrip()
    )


def build_reminder_parts(
    *,
    repo_root: Path,
    plan_related: bool,
    handoff_related: bool,
    change_count: int,
) -> list[str]:
    """Build reminder parts based on session signals."""
    parts: list[str] = []

    if plan_related:
        parts.append(build_plan_reminder(repo_root))

    if handoff_related or plan_related or change_count > 0:
        parts.append(build_handoff_reminder(repo_root, change_count))

    return parts


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        repo_root = resolve_repo_root()

        plan_related = session_mentions_plan(payload)
        handoff_related = session_mentions_handoff(payload)
        change_count = count_working_tree_changes(repo_root)

        if not should_emit_session_end_reminder(
            plan_related=plan_related,
            handoff_related=handoff_related,
            change_count=change_count,
        ):
            sys.exit(0)

        reminder_parts = build_reminder_parts(
            repo_root=repo_root,
            plan_related=plan_related,
            handoff_related=handoff_related,
            change_count=change_count,
        )

        if not reminder_parts:
            sys.exit(0)

        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionEnd",
                "additionalContext": " ".join(reminder_parts),
            }
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(0)

    except Exception:
        # Never block session end on hook failures
        sys.exit(0)


if __name__ == "__main__":
    main()
