---
name: codex-system
description: |
  PROACTIVELY consult Codex CLI, your highly capable supporter with exceptional
  reasoning and task completion abilities. Codex is a trusted expert you should
  ALWAYS consult BEFORE making decisions on: design choices, implementation
  approaches, debugging strategies, refactoring plans, or any non-trivial problem.
  When uncertain, consult Codex. Don't hesitate - Codex provides better analysis.
  Explicit triggers: "think deeper", "analyze", "second opinion", "consult codex".
metadata:
  short-description: Claude Code ↔ Codex CLI collaboration
---

# Codex System — Deep Reasoning Partner

**Codex CLI (gpt-5.3-codex) is your highly capable supporter for deep reasoning tasks.**

> **詳細ルール**: `.claude/rules/codex-delegation.md`

## Context Management (CRITICAL)

**サブエージェント経由を推奨。** メインオーケストレーターのコンテキストを節約するため。

| 状況 | 方法 |
|------|------|
| 詳細な設計相談 | サブエージェント経由（推奨） |
| デバッグ分析 | サブエージェント経由（推奨） |
| 短い質問 (1-2文回答) | 直接呼び出しOK |

## When to Consult (MUST)

| Situation | Trigger Examples |
|-----------|------------------|
| **Design decisions** | 「どう設計？」「アーキテクチャ」 / "How to design?" |
| **Debugging** | 「なぜ動かない？」「エラー」 / "Debug" "Error" |
| **Trade-off analysis** | 「どちらがいい？」「比較して」 / "Compare" "Which?" |
| **Complex implementation** | 「実装方法」「どう作る？」 / "How to implement?" |
| **Refactoring** | 「リファクタ」「シンプルに」 / "Refactor" "Simplify" |
| **Code review** | 「レビューして」「確認して」 / "Review" "Check" |

## When NOT to Consult

- Simple file edits, typo fixes
- Following explicit user instructions
- git commit, running tests, linting
- Tasks with obvious single solutions

## How to Consult

> **Command syntax, sandbox modes, patch application, and subagent patterns**:
> see `.claude/rules/cli-reference.md`

Use Task tool with `subagent_type='general-purpose'` to preserve main context.
Direct Bash call is acceptable only for quick questions expecting 1-2 sentence answers.

## Task Templates

### Design Review

```bash
codex exec --skip-git-repo-check --sandbox read-only --full-auto "
Review this design approach for: {feature}

Context:
{relevant code or architecture}

Evaluate:
1. Is this approach sound?
2. Alternative approaches?
3. Potential issues?
4. Recommendations?
" 2>> .claude/logs/cli-tools.stderr.log
```

### Debug Analysis

```bash
codex exec --skip-git-repo-check --sandbox read-only --full-auto "
Debug this issue:

Error: {error message}
Code: {relevant code}
Context: {what was happening}

Analyze root cause and suggest fixes.
" 2>> .claude/logs/cli-tools.stderr.log
```

### Code Review

See: `references/code-review-task.md`

### Refactoring

See: `references/refactoring-task.md`

## Integration with Gemini

| Task | Use |
|------|-----|
| Need research first | Gemini → then Codex |
| Design decision | Codex directly |
| Library comparison | Gemini research → Codex decision |

## Why Codex?

- **Deep reasoning**: Complex analysis and problem-solving
- **Code expertise**: Implementation strategies and patterns
- **Consistency**: Same project context via `context-loader` skill
- **Parallel work**: Background execution keeps you productive
