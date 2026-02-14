# Codex Delegation Rule

**Codex CLI is your highly capable supporter.**

## Context Management (CRITICAL)

**コンテキスト消費を意識してCodexを使う。** 大きな出力が予想される場合はサブエージェント経由を推奨。

| 状況 | 推奨方法 |
|------|----------|
| 短い質問・短い回答 | 直接呼び出しOK |
| 詳細な設計相談 | サブエージェント経由 |
| デバッグ分析 | サブエージェント経由 |
| 複数の質問がある | サブエージェント経由 |

```
┌──────────────────────────────────────────────────────────┐
│  Main Claude Code                                        │
│  → 短い質問なら直接呼び出しOK                             │
│  → 大きな出力が予想されるならサブエージェント経由          │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Subagent (general-purpose)                         │ │
│  │  → Calls Codex CLI                                  │ │
│  │  → Processes full response                          │ │
│  │  → Returns key insights only                        │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## About Codex

Codex CLI is an AI with exceptional reasoning and task completion abilities.
Think of it as a trusted senior expert you can always consult.

**When facing difficult decisions → Delegate to subagent → Subagent consults Codex.**

## When to Consult Codex

ALWAYS consult Codex BEFORE:

1. **Design decisions** - How to structure code, which pattern to use
2. **Debugging** - If cause isn't obvious or first fix failed
3. **Implementation planning** - Multi-step tasks, multiple approaches
4. **Implementation (code + tests)** - Any code or test authoring
5. **Test failure analysis** - Root cause and fix strategy
6. **Trade-off evaluation** - Choosing between options

### Trigger Phrases (User Input)

Consult Codex when user says:

| Japanese | English |
|----------|---------|
| 「どう設計すべき？」「どう実装する？」 | "How should I design/implement?" |
| 「なぜ動かない？」「原因は？」「エラーが出る」 | "Why doesn't this work?" "Error" |
| 「どちらがいい？」「比較して」「トレードオフは？」 | "Which is better?" "Compare" |
| 「〜を作りたい」「〜を実装して」 | "Build X" "Implement X" |
| 「テストを書いて」「テストを作って」 | "Write tests" "Create tests" |
| 「テストが落ちた」「原因は？」 | "Tests failed" "Root cause?" |
| 「考えて」「分析して」「深く考えて」 | "Think" "Analyze" "Think deeper" |

## When NOT to Consult

Skip Codex for simple, straightforward tasks:

- Simple documentation edits (typo fixes, wording)
- Following explicit user instructions that do not change code/tests
- Standard operations (git commit, running tests)
- Non-code tasks with clear, single solutions
- Reading/searching files

## Quick Check

Ask yourself: "Am I about to make a non-trivial decision?"

- YES → Consult Codex first
- NO → Proceed with execution

## How to Consult

> **Command syntax, sandbox modes, patch application, and subagent patterns**:
> see `.claude/rules/cli-reference.md`

**IMPORTANT: Use subagent (Task tool) to preserve main context.**
Direct Bash call is acceptable only for quick questions expecting < 1 paragraph.

**Don't hesitate to delegate. Subagents + Codex = efficient collaboration.**
