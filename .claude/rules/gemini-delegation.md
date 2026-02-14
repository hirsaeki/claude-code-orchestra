# Gemini Delegation Rule

**Gemini CLI is your research specialist with massive context and multimodal capabilities.**

## Context Management (CRITICAL)

**コンテキスト消費を意識してGeminiを使う。** Gemini出力は大きくなりがちなので、サブエージェント経由を推奨。

| 状況 | 推奨方法 |
|------|----------|
| 短い質問・短い回答 | 直接呼び出しOK |
| コードベース分析 | サブエージェント経由（出力大） |
| ライブラリ調査 | サブエージェント経由（出力大） |
| マルチモーダル処理 | サブエージェント経由 |

```
┌──────────────────────────────────────────────────────────┐
│  Main Claude Code                                        │
│  → 短い質問なら直接呼び出しOK                             │
│  → 大きな出力が予想されるならサブエージェント経由          │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Subagent (general-purpose)                         │ │
│  │  → Calls Gemini CLI                                 │ │
│  │  → Saves full output to .claude/docs/research/      │ │
│  │  → Returns key findings only                        │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## About Gemini

Gemini CLI excels at:
- **1M token context window** — Analyze entire codebases at once
- **Google Search grounding** — Access latest information
- **Multimodal processing** — Video, audio, PDF analysis

Think of Gemini as your research assistant who can quickly gather and synthesize information.

**When you need research → Delegate to subagent → Subagent consults Gemini.**

## Gemini vs Codex: Choose the Right Tool

| Task | Codex | Gemini |
|------|-------|--------|
| Design decisions | ✓ | |
| Debugging | ✓ | |
| Code implementation | ✓ | |
| Trade-off analysis | ✓ | |
| Large codebase understanding | | ✓ |
| Pre-implementation research | | ✓ |
| Latest docs/library research | | ✓ |
| Video/Audio/PDF analysis | | ✓ |

## When to Consult Gemini

ALWAYS consult Gemini BEFORE:

1. **Pre-implementation research** - Best practices, library comparison
2. **Large codebase analysis** - Repository-wide understanding
3. **Documentation search** - Latest official docs, breaking changes
4. **Multimodal tasks** - Video, audio, PDF content extraction

### Trigger Phrases (User Input)

Consult Gemini when user says:

| Japanese | English |
|----------|---------|
| 「調べて」「リサーチして」「調査して」 | "Research" "Investigate" "Look up" |
| 「このPDF/動画/音声を見て」 | "Analyze this PDF/video/audio" |
| 「コードベース全体を理解して」 | "Understand the entire codebase" |
| 「最新のドキュメントを確認して」 | "Check the latest documentation" |
| 「〜について情報を集めて」 | "Gather information about X" |

## When NOT to Consult

Skip Gemini for:

- Design decisions (use Codex instead)
- Code implementation (use Codex instead)
- Debugging (use Codex instead)
- Simple file operations (do directly)
- Running tests/linting (do directly)

## How to Consult

> **Command syntax, subagent patterns, and output locations**:
> see `.claude/rules/cli-reference.md`

**IMPORTANT: Use subagent (Task tool) to preserve main context.**
Direct Bash call is acceptable only for quick questions expecting brief answers.

Save full Gemini output to `.claude/docs/research/{topic}.md` for persistence.

**Use Gemini (via subagent) for research, Codex (via subagent) for reasoning, Claude for orchestration.**
