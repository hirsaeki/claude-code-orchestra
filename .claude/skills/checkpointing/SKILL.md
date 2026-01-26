---
name: checkpointing
description: |
  Save session context to agent configuration files. Reads CLI logs and
  updates CLAUDE.md, .codex/AGENTS.md, .gemini/GEMINI.md with session history.
  Use this to persist important decisions and context across sessions.
metadata:
  short-description: Checkpoint session context to all agent configs
---

# Checkpointing — セッションコンテキストの永続化

**セッション中のCodex/Gemini相談履歴を各エージェントの設定ファイルに保存します。**

## 目的

```
┌─────────────────────────────────────────────────────────────┐
│  .claude/logs/cli-tools.jsonl                               │
│  (Codex/Geminiへの入出力ログ)                                │
│                      ↓                                      │
│  /checkpointing                                             │
│                      ↓                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │  CLAUDE.md   │ │ AGENTS.md    │ │ GEMINI.md            │ │
│  │  (Claude)    │ │ (Codex)      │ │ (Gemini)             │ │
│  │              │ │              │ │                      │ │
│  │ ## Session   │ │ ## Session   │ │ ## Session           │ │
│  │ History      │ │ History      │ │ History              │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 使い方

```
/checkpointing
```

または

```
/checkpointing --since "2026-01-26"
```

## 処理内容

1. **サブエージェントがログを読み込み**
   - `.claude/logs/cli-tools.jsonl` を解析
   - Codex/Geminiへの相談内容を抽出

2. **重要な情報を要約**
   - 設計決定
   - 調査結果
   - デバッグで判明したこと

3. **各コンテキストファイルに追記**
   - `CLAUDE.md` の `## Session History` セクション
   - `.codex/AGENTS.md` の `## Session History` セクション
   - `.gemini/GEMINI.md` の `## Session History` セクション

## Session History フォーマット

```markdown
## Session History

### 2026-01-26

**Codex相談:**
- 設計: サブエージェントパターンでCodex/Gemini呼び出しを推奨
- 理由: メインオーケストレーターのコンテキスト節約

**Gemini調査:**
- MCP vs CLI比較: 現時点ではCLI維持を推奨
- 詳細: `.claude/docs/research/cli-vs-mcp-comparison.md`
```

## 実行タイミング

以下のタイミングで `/checkpointing` を実行することを推奨:

- セッション終了前
- 重要な設計決定後
- 大きな機能実装完了後
- 長時間作業の区切り

## 注意事項

- ログが空の場合は何も追記されません
- 既存の `## Session History` セクションは上書きされます
- ログファイル自体は変更されません（読み取りのみ）
