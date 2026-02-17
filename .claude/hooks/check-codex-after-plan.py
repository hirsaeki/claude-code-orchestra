#!/usr/bin/env python
"""
PostToolUse hook: Suggest Codex review after Plan tasks.

This hook runs after Task tool execution and suggests Codex consultation
for reviewing plans and implementation strategies.
"""

import json
import sys

# Task descriptions that suggest planning/design work
PLAN_INDICATORS = [
    "plan",
    "design",
    "architect",
    "structure",
    "implement",
    "strategy",
    "approach",
    "solution",
    "refactor",
    "migrate",
    "optimize",
]


def should_suggest_codex_review(tool_input: dict, tool_output: str | None = None) -> tuple[bool, str]:
    """Determine if Codex review should be suggested after task completion."""
    subagent_type = tool_input.get("subagent_type", "").lower()
    description = tool_input.get("description", "").lower()
    prompt = tool_input.get("prompt", "").lower()

    # Check if subagent_type indicates planning work
    # Note: No dedicated "plan" agent exists; planning tasks typically use
    # "general-purpose" or "researcher". We match planning-related types broadly.
    if subagent_type in ("plan", "planner"):
        return True, "Planning task completed"

    # Check description/prompt for planning keywords
    combined_text = f"{description} {prompt}"
    for indicator in PLAN_INDICATORS:
        if indicator in combined_text:
            return True, f"Task involves '{indicator}'"

    return False, ""


def main():
    try:
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", "")

        # Only process Task tool
        if tool_name != "Task":
            sys.exit(0)

        tool_input = data.get("tool_input", {})
        tool_output = data.get("tool_output", "")

        should_suggest, reason = should_suggest_codex_review(tool_input, tool_output)

        if should_suggest:
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        f"[Codex Review Suggestion] {reason}. "
                        "Consider having Codex review this plan for potential improvements.\n"
                        "**Recommended**: Use Task tool with subagent_type='general-purpose' "
                        "and prompt Codex for review:\n"
                        "```\n"
                        'codex exec --skip-git-repo-check --sandbox read-only -a never '
                        '"Review this plan: {paste plan summary}" '
                        "2>> .claude/logs/cli-tools.stderr.log\n"
                        "```"
                    )
                }
            }
            print(json.dumps(output))

        sys.exit(0)

    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
