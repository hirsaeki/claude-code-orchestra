#!/usr/bin/env python
"""
UserPromptSubmit hook: Route to appropriate agent based on user intent.

Analyzes user prompts and suggests the most appropriate agent
(Codex for design/debug, Gemini for research/multimodal).
"""

import json
import sys

# Triggers for Codex (design, debugging, deep reasoning)
CODEX_TRIGGERS = {
    "ja": [
        "設計", "どう設計", "アーキテクチャ",
        "なぜ動かない", "エラー", "バグ", "デバッグ",
        "どちらがいい", "比較して", "トレードオフ",
        "実装方法", "どう実装", "実装して", "コードを書", "コードを作",
        "テスト", "テストを書く", "テスト作成", "テスト追加", "テストが落ちた",
        "リファクタリング", "リファクタ",
        "レビュー", "見て",
        "考えて", "分析して", "深く",
    ],
    "en": [
        "design", "architecture", "architect",
        "debug", "error", "bug", "not working", "fails",
        "compare", "trade-off", "tradeoff", "which is better",
        "how to implement", "implementation", "implement",
        "test", "tests", "write tests", "test writing", "testing",
        "refactor", "simplify",
        "review", "check this",
        "think", "analyze", "deeply",
    ],
}

# Triggers for Gemini (research, multimodal, large context)
GEMINI_TRIGGERS = {
    "ja": [
        "調べて", "リサーチ", "調査",
        "PDF", "動画", "音声", "画像",
        "コードベース全体", "リポジトリ全体",
        "最新", "ドキュメント",
        "ライブラリ", "パッケージ",
    ],
    "en": [
        "research", "investigate", "look up", "find out",
        "pdf", "video", "audio", "image",
        "entire codebase", "whole repository",
        "latest", "documentation", "docs",
        "library", "package", "framework",
    ],
}


def validate_trigger_configuration() -> None:
    """Validate trigger tables to prevent accidental string concatenation regressions."""
    japanese_codex_triggers = CODEX_TRIGGERS.get("ja", [])
    if "実装して" not in japanese_codex_triggers:
        raise ValueError("Missing required Codex trigger: 実装して")
    if "テスト" not in japanese_codex_triggers:
        raise ValueError("Missing required Codex trigger: テスト")
    if "実装してテスト" in japanese_codex_triggers:
        raise ValueError("Invalid merged trigger found: 実装してテスト")


def detect_agent(prompt: str) -> tuple[str | None, str]:
    """Detect which agent should handle this prompt."""
    prompt_lower = prompt.lower()

    # Check Codex triggers
    for triggers in CODEX_TRIGGERS.values():
        for trigger in triggers:
            if trigger in prompt_lower:
                return "codex", trigger

    # Check Gemini triggers
    for triggers in GEMINI_TRIGGERS.values():
        for trigger in triggers:
            if trigger in prompt_lower:
                return "gemini", trigger

    return None, ""


def run_self_test() -> int:
    """Run lightweight regression checks for trigger routing."""
    validate_trigger_configuration()

    codex_agent_1, codex_trigger_1 = detect_agent("実装して")
    if codex_agent_1 != "codex" or codex_trigger_1 != "実装して":
        print("Self-test failed: '実装して' should route to codex", file=sys.stderr)
        return 1

    codex_agent_2, codex_trigger_2 = detect_agent("テスト")
    if codex_agent_2 != "codex" or codex_trigger_2 != "テスト":
        print("Self-test failed: 'テスト' should route to codex", file=sys.stderr)
        return 1

    codex_agent_3, _ = detect_agent("実装してテストを書いて")
    if codex_agent_3 != "codex":
        print("Self-test failed: combined Japanese trigger should route to codex", file=sys.stderr)
        return 1

    return 0


def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
            sys.exit(run_self_test())

        validate_trigger_configuration()

        data = json.load(sys.stdin)
        prompt = data.get("prompt", "")

        # Skip short prompts
        if len(prompt) < 10:
            sys.exit(0)

        agent, trigger = detect_agent(prompt)

        if agent == "codex":
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": (
                        f"[Agent Routing] Detected '{trigger}' - this task may benefit from "
                        "Codex CLI's deep reasoning capabilities. "
                        "**Run from project root (never cd first)**: "
                        "`codex exec --skip-git-repo-check --sandbox read-only --full-auto "
                        '"{task description}"` for design decisions, debugging, or complex analysis. '
                        "For implementation or test authoring, prefer: "
                        "`codex exec --skip-git-repo-check --sandbox workspace-write --full-auto "
                        '"{task description}"`.'
                    )
                }
            }
            print(json.dumps(output))

        elif agent == "gemini":
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": (
                        f"[Agent Routing] Detected '{trigger}' - this task may benefit from "
                        "Gemini CLI's research capabilities. "
                        "**Run from project root (never cd first)**: "
                        '`gemini -p "Research: {topic}"` '
                        "for documentation, library research, or multimodal content."
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
