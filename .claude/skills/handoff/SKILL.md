---
name: handoff
description: |
  Generate an Amp-style handoff package for the next session.
  Creates both summary and resume prompt files from git + CLI logs.
---

# Handoff Package

**次セッションに引き継ぐための handoff を作成する。**

## Purpose

セッション終盤で、以下を1回で生成する:

- `.claude/handoffs/YYYY-MM-DD-HHMMSS.md`（作業サマリー）
- `.claude/handoffs/YYYY-MM-DD-HHMMSS.prompt.md`（再開用プロンプト）

## Usage

```bash
# 基本
python .claude/skills/checkpointing/checkpoint.py --handoff

# 目標つき（推奨）
python .claude/skills/checkpointing/checkpoint.py --handoff --goal "次セッションの目標"

# 期間を絞る
python .claude/skills/checkpointing/checkpoint.py --handoff --since "2026-02-10" --goal "残タスク整理"
```

## Workflow

1. `--goal` が未指定なら、ユーザーに「次セッションの最優先目標」を1文で確認する
2. `checkpoint.py --handoff` を実行する
3. 生成された `*.md` と `*.prompt.md` のパスを報告する
4. `*.prompt.md` の内容を次セッション先頭に貼るよう案内する

## Output Contract

handoff 本体には次を含める:

- Goal
- Snapshot（branch / commits / file changes / CLI結果）
- Open Work（working tree / failed CLI calls）
- Suggested Next Actions（すぐ着手できる順）
- Verification Checklist（`git status`, lint, test）

## Notes

- `/checkpointing --full` は履歴保存向け、`/handoff` は再開効率向け
- セッション終了前に毎回実行する運用を推奨

