---
name: handoff
description: |
  Generate an Amp-style handoff package for the next session.
  Creates both summary and resume prompt files from git + CLI logs.
  Use when user says: "引き継ぎ", "ハンドオフ", "セッション終了",
  "handoff", "wrap up", "end session".
---

# Handoff Package

**次セッションに引き継ぐための handoff を作成する。**

## Purpose

セッション終盤で、以下を1回で生成する:

- `.claude/handoffs/YYYY-MM-DD-HHMMSS.md`（作業サマリー）
- `.claude/handoffs/YYYY-MM-DD-HHMMSS.prompt.md`（再開用プロンプト）

## Usage

### 書き込み（セッション終了時）

```bash
# 基本
python .claude/skills/checkpointing/checkpoint.py --handoff

# 目標つき（推奨）
python .claude/skills/checkpointing/checkpoint.py --handoff --goal "次セッションの目標"

# 期間を絞る
python .claude/skills/checkpointing/checkpoint.py --handoff --since "2026-02-10" --goal "残タスク整理"
```

### 読み込み（セッション開始時）

```bash
# 最新のハンドオフを読み込み
python .claude/skills/checkpointing/checkpoint.py --handoff --resume

# 一覧表示
python .claude/skills/checkpointing/checkpoint.py --handoff --list

# 特定のハンドオフを読み込み（0=最新, 1=1つ前, ...）
python .claude/skills/checkpointing/checkpoint.py --handoff --resume --index 1
```

## Workflow

### 書き込み（/handoff）

1. `--goal` が未指定なら、ユーザーに「次セッションの最優先目標」を1文で確認する
2. `checkpoint.py --handoff` を実行する
3. 生成された `*.md` と `*.prompt.md` のパスを報告する

### 読み込み（/handoff --resume）

1. セッション開始時に SessionStart hook が自動通知する
2. `/handoff --resume` でハンドオフ内容を読み込む
3. Snapshot / Open Work / Suggested Next Actions を要約する
4. 最初の1手を提案し、承認後に実行する

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

