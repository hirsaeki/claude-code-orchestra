#!/usr/bin/env python
"""
Checkpoint script: Read CLI logs and update agent context files.

Usage:
    python checkpoint.py [--since YYYY-MM-DD]           # Session history mode
    python checkpoint.py --full [--since YYYY-MM-DD]    # Full checkpoint mode
    python checkpoint.py --full --analyze               # Full checkpoint + skill analysis
    python checkpoint.py --handoff [--goal TEXT]        # Handoff package for next session

Session History Mode (default):
    Updates CLAUDE.md, .codex/AGENTS.md, .gemini/GEMINI.md with CLI consultation history.

Full Checkpoint Mode (--full):
    Creates comprehensive checkpoint file in .claude/checkpoints/ including:
    - Git commits and file changes
    - CLI tool consultations (Codex/Gemini)
    - Design decisions changes
    - Session summary

Analyze Mode (--full --analyze):
    After creating checkpoint, outputs a prompt for AI analysis to extract
    reusable skill patterns. Use with subagent to analyze and suggest new skills.

Handoff Mode (--handoff):
    Creates a session handoff package in .claude/handoffs/ including:
    - Handoff summary (progress, open work, next actions)
    - Resume prompt template for a new session
"""

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
LOG_FILE = PROJECT_ROOT / ".claude" / "logs" / "cli-tools.jsonl"
CHECKPOINTS_DIR = PROJECT_ROOT / ".claude" / "checkpoints"
HANDOFFS_DIR = PROJECT_ROOT / ".claude" / "handoffs"
DESIGN_FILE = PROJECT_ROOT / ".claude" / "docs" / "DESIGN.md"

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


def run_git_command(args: list[str]) -> str | None:
    """Run a git command and return output, or None if failed."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def get_git_commits(since: str | None = None) -> list[dict]:
    """Get git commits since the specified date."""
    args = ["log", "--pretty=format:%H|%ai|%s", "-n", "100"]
    if since:
        args.extend(["--since", since])

    output = run_git_command(args)
    if not output:
        return []

    commits = []
    for line in output.split("\n"):
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({
                "hash": parts[0][:7],
                "date": parts[1],
                "message": parts[2],
            })
    return commits


def get_file_changes(since: str | None = None) -> dict[str, list[str]]:
    """Get file changes (created, modified, deleted) since the specified date."""
    changes: dict[str, list[str]] = {"created": [], "modified": [], "deleted": []}

    if since:
        args = ["log", "--since", since, "--name-status", "--pretty=format:"]
    else:
        args = ["diff", "--name-status", "HEAD~10", "HEAD"]

    output = run_git_command(args)
    if not output:
        return changes

    seen: set[str] = set()
    for line in output.split("\n"):
        line = line.strip()
        if not line or "\t" not in line:
            continue

        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue

        status, filepath = parts[0], parts[1]
        if filepath in seen:
            continue
        seen.add(filepath)

        if status.startswith("A"):
            changes["created"].append(filepath)
        elif status.startswith("M"):
            changes["modified"].append(filepath)
        elif status.startswith("D"):
            changes["deleted"].append(filepath)

    return changes


def get_file_stats(since: str | None = None) -> dict[str, tuple[int, int]]:
    """Get line additions/deletions per file."""
    if since:
        args = ["log", "--since", since, "--numstat", "--pretty=format:"]
    else:
        args = ["diff", "--numstat", "HEAD~10", "HEAD"]

    output = run_git_command(args)
    if not output:
        return {}

    stats: dict[str, tuple[int, int]] = {}
    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue

        parts = line.split("\t")
        if len(parts) != 3:
            continue

        added, deleted, filepath = parts
        try:
            add_count = int(added) if added != "-" else 0
            del_count = int(deleted) if deleted != "-" else 0
            if filepath in stats:
                prev = stats[filepath]
                stats[filepath] = (prev[0] + add_count, prev[1] + del_count)
            else:
                stats[filepath] = (add_count, del_count)
        except ValueError:
            continue

    return stats


def get_working_tree_changes() -> list[str]:
    """Get git working tree changes in short format."""
    output = run_git_command(["status", "--short"])
    if not output:
        return []
    return [line for line in output.split("\n") if line.strip()]


def summarize_recent_entries(
    entries: list[dict],
    *,
    success: bool | None,
    limit: int = 5,
) -> list[str]:
    """Create compact summaries of recent CLI entries."""
    filtered: list[dict] = []
    for entry in entries:
        if success is not None and entry.get("success", False) != success:
            continue
        filtered.append(entry)

    recent = sorted(filtered, key=lambda e: e.get("timestamp", ""), reverse=True)

    summaries: list[str] = []
    for entry in recent[:limit]:
        tool = entry.get("tool", "unknown")
        prompt = entry.get("prompt", "")
        prompt_summary = prompt.replace("\n", " ").strip()
        if len(prompt_summary) > 90:
            prompt_summary = prompt_summary[:87] + "..."
        if not prompt_summary:
            prompt_summary = "(no prompt captured)"
        summaries.append(f"[{tool}] {prompt_summary}")

    return summaries


def generate_handoff_package(since: str | None = None, goal: str | None = None) -> tuple[Path, Path]:
    """Generate handoff summary + resume prompt for the next session."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    HANDOFFS_DIR.mkdir(parents=True, exist_ok=True)

    handoff_file = HANDOFFS_DIR / f"{timestamp}.md"
    prompt_file = HANDOFFS_DIR / f"{timestamp}.prompt.md"

    entries = parse_logs(since)
    commits = get_git_commits(since)
    file_changes = get_file_changes(since)
    working_tree = get_working_tree_changes()
    branch = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"

    codex_entries = [e for e in entries if e.get("tool") == "codex"]
    gemini_entries = [e for e in entries if e.get("tool") == "gemini"]

    codex_success = sum(1 for e in codex_entries if e.get("success", False))
    gemini_success = sum(1 for e in gemini_entries if e.get("success", False))

    recent_successes = summarize_recent_entries(entries, success=True, limit=5)
    recent_failures = summarize_recent_entries(entries, success=False, limit=5)

    total_files = (
        len(file_changes["created"])
        + len(file_changes["modified"])
        + len(file_changes["deleted"])
    )

    next_actions: list[str] = []
    if goal:
        next_actions.append(f"Break the goal into the next smallest deliverable: {goal}")
    if working_tree:
        next_actions.append(
            f"Review {len(working_tree)} working tree change(s) and choose the first file to continue."
        )
    if recent_failures:
        next_actions.append("Retry the latest failed CLI task with a narrower prompt and explicit output format.")
    next_actions.append("Run focused verification for touched files before additional edits.")
    next_actions.append("Create a fresh `/handoff` snapshot before ending the next session.")

    deduped_actions: list[str] = []
    seen_actions: set[str] = set()
    for action in next_actions:
        if action in seen_actions:
            continue
        deduped_actions.append(action)
        seen_actions.add(action)

    handoff_lines: list[str] = []
    handoff_lines.append(f"# Handoff: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    handoff_lines.append("")
    handoff_lines.append("## Goal")
    handoff_lines.append("")
    handoff_lines.append(f"- {goal if goal else '(No explicit goal provided)'}")
    handoff_lines.append("")

    handoff_lines.append("## Snapshot")
    handoff_lines.append("")
    handoff_lines.append(f"- **Branch**: `{branch}`")
    handoff_lines.append(f"- **Commits captured**: {len(commits)}")
    handoff_lines.append(
        f"- **Files changed (git history window)**: {total_files} "
        f"({len(file_changes['modified'])} modified, "
        f"{len(file_changes['created'])} created, "
        f"{len(file_changes['deleted'])} deleted)"
    )
    handoff_lines.append(f"- **Working tree changes**: {len(working_tree)}")
    handoff_lines.append(
        f"- **Codex consultations**: {len(codex_entries)} "
        f"({codex_success} success, {len(codex_entries) - codex_success} failed)"
    )
    handoff_lines.append(
        f"- **Gemini researches**: {len(gemini_entries)} "
        f"({gemini_success} success, {len(gemini_entries) - gemini_success} failed)"
    )
    if since:
        handoff_lines.append(f"- **Since**: {since}")
    handoff_lines.append("")

    handoff_lines.append("## Completed Signals")
    handoff_lines.append("")
    if recent_successes:
        for item in recent_successes:
            handoff_lines.append(f"- {item}")
    else:
        handoff_lines.append("- No successful CLI consultations recorded in the selected range.")
    handoff_lines.append("")

    handoff_lines.append("## Open Work")
    handoff_lines.append("")
    handoff_lines.append("### Working Tree Changes")
    handoff_lines.append("")
    if working_tree:
        for line in working_tree[:20]:
            handoff_lines.append(f"- `{line}`")
        if len(working_tree) > 20:
            handoff_lines.append(f"- ... and {len(working_tree) - 20} more")
    else:
        handoff_lines.append("- Working tree is clean.")
    handoff_lines.append("")

    handoff_lines.append("### Recent Failed CLI Calls")
    handoff_lines.append("")
    if recent_failures:
        for item in recent_failures:
            handoff_lines.append(f"- {item}")
    else:
        handoff_lines.append("- No failed CLI calls recorded in the selected range.")
    handoff_lines.append("")

    handoff_lines.append("## Suggested Next Actions")
    handoff_lines.append("")
    for index, action in enumerate(deduped_actions[:4], start=1):
        handoff_lines.append(f"{index}. {action}")
    handoff_lines.append("")

    handoff_lines.append("## Verification Checklist")
    handoff_lines.append("")
    handoff_lines.append("- `git status --short`")
    handoff_lines.append("- `poe lint` (or project-specific lint command)")
    handoff_lines.append("- `poe test` (or focused test command)")
    handoff_lines.append("")

    handoff_lines.append("## Resume Prompt")
    handoff_lines.append("")
    handoff_lines.append(f"Use `{prompt_file.name}` in the next session.")
    handoff_lines.append("")
    handoff_lines.append("---")
    handoff_lines.append(f"*Generated by checkpointing skill at {timestamp}*")

    handoff_file.write_text("\n".join(handoff_lines), encoding="utf-8")

    resume_prompt_lines: list[str] = []
    resume_prompt_lines.append("# Resume Prompt")
    resume_prompt_lines.append("")
    resume_prompt_lines.append("Copy the following block into the first message of your next session:")
    resume_prompt_lines.append("")
    resume_prompt_lines.append("```text")
    resume_prompt_lines.append("このプロジェクトの作業を再開します。まず handoff を読んで状況整理してください。")
    resume_prompt_lines.append(f"- Handoff file: `.claude/handoffs/{handoff_file.name}`")
    resume_prompt_lines.append(f"- Goal: {goal if goal else '(No explicit goal provided)'}")
    resume_prompt_lines.append("")
    resume_prompt_lines.append("進め方:")
    resume_prompt_lines.append("1. Snapshot / Open Work / Suggested Next Actions を要約")
    resume_prompt_lines.append("2. 最初の1手を提案し、承認後に実行")
    resume_prompt_lines.append("3. 変更後に Verification Checklist のコマンドを実行")
    resume_prompt_lines.append("4. 終了前に `/handoff` を更新")
    resume_prompt_lines.append("```")

    prompt_file.write_text("\n".join(resume_prompt_lines), encoding="utf-8")

    return handoff_file, prompt_file


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


def generate_full_checkpoint(since: str | None = None) -> Path | None:
    """Generate a comprehensive checkpoint file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    checkpoint_file = CHECKPOINTS_DIR / f"{timestamp}.md"

    # Ensure checkpoints directory exists
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

    # Gather data
    entries = parse_logs(since)
    commits = get_git_commits(since)
    file_changes = get_file_changes(since)
    file_stats = get_file_stats(since)

    # Count CLI consultations
    codex_count = sum(1 for e in entries if e.get("tool") == "codex")
    gemini_count = sum(1 for e in entries if e.get("tool") == "gemini")

    # Build checkpoint content
    lines: list[str] = []

    # Header
    lines.append(f"# Checkpoint: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    total_files = (
        len(file_changes["created"])
        + len(file_changes["modified"])
        + len(file_changes["deleted"])
    )
    lines.append(f"- **Commits**: {len(commits)}")
    lines.append(
        f"- **Files changed**: {total_files} "
        f"({len(file_changes['modified'])} modified, "
        f"{len(file_changes['created'])} created, "
        f"{len(file_changes['deleted'])} deleted)"
    )
    lines.append(f"- **Codex consultations**: {codex_count}")
    lines.append(f"- **Gemini researches**: {gemini_count}")
    if since:
        lines.append(f"- **Since**: {since}")
    lines.append("")

    # Git History
    lines.append("## Git History")
    lines.append("")

    if commits:
        lines.append("### Commits")
        lines.append("")
        for commit in commits[:20]:  # Limit to 20 commits
            lines.append(f"- `{commit['hash']}` {commit['message']}")
        if len(commits) > 20:
            lines.append(f"- ... and {len(commits) - 20} more commits")
        lines.append("")

    # File Changes
    lines.append("### File Changes")
    lines.append("")

    if file_changes["created"]:
        lines.append("**Created:**")
        for f in file_changes["created"][:15]:
            stat = file_stats.get(f, (0, 0))
            lines.append(f"- `{f}` (+{stat[0]})")
        if len(file_changes["created"]) > 15:
            lines.append(f"- ... and {len(file_changes['created']) - 15} more files")
        lines.append("")

    if file_changes["modified"]:
        lines.append("**Modified:**")
        for f in file_changes["modified"][:15]:
            stat = file_stats.get(f, (0, 0))
            lines.append(f"- `{f}` (+{stat[0]}, -{stat[1]})")
        if len(file_changes["modified"]) > 15:
            lines.append(f"- ... and {len(file_changes['modified']) - 15} more files")
        lines.append("")

    if file_changes["deleted"]:
        lines.append("**Deleted:**")
        for f in file_changes["deleted"][:15]:
            lines.append(f"- `{f}`")
        if len(file_changes["deleted"]) > 15:
            lines.append(f"- ... and {len(file_changes['deleted']) - 15} more files")
        lines.append("")

    if not any(file_changes.values()):
        lines.append("No file changes detected.")
        lines.append("")

    # CLI Tool Consultations
    lines.append("## CLI Tool Consultations")
    lines.append("")

    codex_entries = [e for e in entries if e.get("tool") == "codex"]
    gemini_entries = [e for e in entries if e.get("tool") == "gemini"]

    if codex_entries:
        lines.append(f"### Codex ({len(codex_entries)} consultations)")
        lines.append("")
        for entry in codex_entries[:10]:
            status = "✓" if entry.get("success", False) else "✗"
            prompt = entry.get("prompt", "")[:80].replace("\n", " ")
            lines.append(f"- {status} {prompt}...")
        if len(codex_entries) > 10:
            lines.append(f"- ... and {len(codex_entries) - 10} more consultations")
        lines.append("")

    if gemini_entries:
        lines.append(f"### Gemini ({len(gemini_entries)} researches)")
        lines.append("")
        for entry in gemini_entries[:10]:
            status = "✓" if entry.get("success", False) else "✗"
            prompt = entry.get("prompt", "")[:80].replace("\n", " ")
            lines.append(f"- {status} {prompt}...")
        if len(gemini_entries) > 10:
            lines.append(f"- ... and {len(gemini_entries) - 10} more researches")
        lines.append("")

    if not entries:
        lines.append("No CLI tool consultations recorded.")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Generated by checkpointing skill at {timestamp}*")

    # Write checkpoint file
    checkpoint_file.write_text("\n".join(lines), encoding="utf-8")

    return checkpoint_file


def generate_skill_analysis_prompt(checkpoint_content: str) -> str:
    """Generate a prompt for AI to analyze checkpoint and suggest skills."""
    return f'''Analyze the following checkpoint and identify reusable work patterns that could become skills.

A "skill" is a repeatable workflow pattern that can be triggered by specific phrases and executed consistently.

## Checkpoint Content

{checkpoint_content}

## Analysis Instructions

1. **Identify Patterns**: Look for regularities in:
   - Sequences of commits that form a logical workflow
   - File change patterns (e.g., test + implementation together)
   - CLI consultation patterns (design → implementation → review)
   - Multi-step operations that could be templated

2. **For each potential skill, provide**:
   - **Name**: Short, descriptive name (e.g., "tdd-feature", "research-implement")
   - **Description**: What this skill accomplishes
   - **Trigger phrases**: When should this skill be invoked (Japanese + English)
   - **Workflow steps**: Ordered list of actions
   - **Files typically involved**: Patterns like `tests/**/*.py`, `src/**/*.py`
   - **Confidence**: How confident are you this is a reusable pattern (0.0-1.0)
   - **Evidence**: What in the checkpoint suggests this pattern

3. **Output format**:

```markdown
## Skill Suggestions

### Skill 1: {{name}}
**Confidence:** {{0.0-1.0}}
**Description:** {{description}}

**Trigger phrases:**
- "{{Japanese phrase}}"
- "{{English phrase}}"

**Workflow:**
1. {{step 1}}
2. {{step 2}}
3. {{step 3}}

**Files involved:**
- `{{pattern 1}}`
- `{{pattern 2}}`

**Evidence:**
- {{evidence from checkpoint}}
```

4. **Quality criteria**:
   - Only suggest skills with confidence >= 0.6
   - Skip trivial patterns (single file edits, simple commits)
   - Focus on multi-step workflows that save time when repeated
   - Consider what would be valuable to automate in future sessions

Provide your analysis:'''


def save_skill_suggestions(checkpoint_file: Path, suggestions: str) -> Path:
    """Save skill suggestions to a file next to the checkpoint."""
    suggestions_file = checkpoint_file.with_suffix(".skills.md")
    suggestions_file.write_text(suggestions, encoding="utf-8")
    return suggestions_file


def main():
    parser = argparse.ArgumentParser(
        description="Checkpoint session context",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python checkpoint.py                    # Update session history in agent configs
  python checkpoint.py --full             # Create full checkpoint file
  python checkpoint.py --full --since 2026-01-26  # Full checkpoint since date
  python checkpoint.py --full --analyze   # Full checkpoint + skill analysis prompt
  python checkpoint.py --handoff --goal "Continue API auth refactor"  # Handoff pack
        """,
    )
    parser.add_argument(
        "--since",
        help="Only include data since this date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Create full checkpoint file with git history and file changes",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Output skill analysis prompt (use with --full)",
    )
    parser.add_argument(
        "--handoff",
        action="store_true",
        help="Create handoff summary + resume prompt for the next session",
    )
    parser.add_argument(
        "--goal",
        help="Optional goal statement for handoff mode",
    )
    args = parser.parse_args()

    if args.handoff and args.full:
        print("Error: --handoff cannot be combined with --full")
        return

    if args.handoff and args.analyze:
        print("Error: --handoff cannot be combined with --analyze")
        return

    if args.handoff:
        print("Creating handoff package...")
        handoff_file, prompt_file = generate_handoff_package(args.since, args.goal)

        print(f"\nHandoff created: {handoff_file}")
        print(f"Resume prompt created: {prompt_file}")
        print("\nUse the resume prompt in the first message of your next session.")
        return

    if args.full:
        # Full checkpoint mode
        print("Creating full checkpoint...")
        checkpoint_file = generate_full_checkpoint(args.since)
        if checkpoint_file:
            print(f"\nCheckpoint created: {checkpoint_file}")
            print("\nCheckpoint includes:")
            print("  - Git commits and file changes")
            print("  - CLI tool consultations (Codex/Gemini)")
            print("  - Session summary")

            if args.analyze:
                # Generate skill analysis prompt
                checkpoint_content = checkpoint_file.read_text(encoding="utf-8")
                prompt = generate_skill_analysis_prompt(checkpoint_content)

                # Save prompt to file
                prompt_file = checkpoint_file.with_suffix(".analyze-prompt.md")
                prompt_file.write_text(prompt, encoding="utf-8")

                print(f"\n{'='*60}")
                print("SKILL ANALYSIS MODE")
                print(f"{'='*60}")
                print(f"\nAnalysis prompt saved to: {prompt_file}")
                print("\nNext step: Use a subagent to analyze and suggest skills:")
                print(f'  Read the prompt file and pass it to a subagent for analysis.')
                print(f"\nThe subagent will identify reusable patterns and suggest new skills.")
        else:
            print("Failed to create checkpoint.")
        return

    # Session history mode (default)
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
