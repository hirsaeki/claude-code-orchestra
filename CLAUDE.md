# Claude Code Orchestra

**マルチエージェント協調フレームワーク**

Claude Code が Codex CLI（深い推論）と Gemini CLI（大規模リサーチ）を統合し、各エージェントの強みを活かして開発を加速する。

---

## Policy Source (CRITICAL)

サブエージェント実行ポリシーの**唯一の正本**は `repo/AGENTS.md`。

- Codex/Gemini への委譲時は `repo/AGENTS.md` のルールを最優先で適用する
- 個別ガイド（`.codex/AGENTS.md`, `.gemini/GEMINI.md`）と衝突する場合は `repo/AGENTS.md` を優先する

---

## Why This Exists

| Agent | Strength | Use For |
|-------|----------|---------|
| **Claude Code** | オーケストレーション、ユーザー対話 | 全体統括、タスク管理、テスト実行 |
| **Codex CLI** | 深い推論、設計判断、デバッグ | 設計相談、実装、テストコード作成、失敗解析 |
| **Gemini CLI** | 1Mトークン、マルチモーダル、Web検索 | コードベース全体分析、ライブラリ調査、PDF/動画処理 |

**IMPORTANT**: 単体では難しいタスクも、3エージェントの協調で解決できる。

---

## Context Management (CRITICAL)

Claude Code のコンテキストは **200k トークン** だが、ツール定義等で **実質 70-100k** に縮小する。

**YOU MUST** サブエージェント経由で Codex/Gemini を呼び出す（出力が10行以上の場合）。

| 出力サイズ | 方法 | 理由 |
|-----------|------|------|
| 1-2文 | 直接呼び出しOK | オーバーヘッド不要 |
| 10行以上 | **サブエージェント経由** | メインコンテキスト保護 |
| 分析レポート | サブエージェント → ファイル保存 | 詳細は `.claude/docs/` に永続化 |

```
# MUST: サブエージェント経由（大きな出力）
Task(subagent_type="general-purpose", prompt="Codexに設計を相談し、要約を返して")

# OK: 直接呼び出し（小さな出力のみ）
Bash("codex exec --skip-git-repo-check ... '1文で答えて'")  # Always run from project root (never cd first)
```

---

## Quick Reference

### Codex を使う時

- 設計判断（「どう実装？」「どのパターン？」）
- 実装（プロダクションコード/テストコード）
- テスト失敗の原因分析
- デバッグ（「なぜ動かない？」「エラーの原因は？」）
- 比較検討（「AとBどちらがいい？」）

### Codex 呼び出しテンプレ（実装/テスト作成）

大きな出力が見込まれるため **サブエージェント経由** を使う。

```
Task(subagent_type="general-purpose", prompt="
実装とテスト作成をCodexに依頼する。

# IMPORTANT: Run from project root, never cd to subdirectory first
# Specify target directory in the prompt if needed
codex exec --skip-git-repo-check --sandbox workspace-write --full-auto \"
Work on files in {target/directory/}. {Implement task in English. Include files to modify and tests to add.}
\"

Return CONCISE summary:
- Files changed
- Tests added/updated
- Risks or follow-ups
")
```

短い質問・小さな修正のみ、直接呼び出しも可。

→ 詳細: `.claude/rules/codex-delegation.md`

### Gemini を使う時

- リサーチ（「調べて」「最新の情報は？」）
- 大規模分析（「コードベース全体を理解して」）
- マルチモーダル（「このPDF/動画を見て」）

→ 詳細: `.claude/rules/gemini-delegation.md`

---

## Workflow

```
/startproject <機能名>
```

1. Gemini がリポジトリ分析（サブエージェント経由）
2. Claude が要件ヒアリング・計画作成
3. Codex が計画レビュー（サブエージェント経由）
4. Claude がタスクリスト作成
5. Codex が実装とテストコード作成
6. Claude がテスト整理・実行
7. Codex がテスト結果を分析して修正方針を提示
8. 必要に応じて 5-7 を反復

→ 詳細: `/startproject`, `/plan`, `/tdd` skills

### Session Handoff Rule

セッション終了前に `/handoff --goal "次セッションの目標"` を実行し、
`.claude/handoffs/` に引き継ぎパック（summary + resume prompt）を保存する。

- `checkpointing --full`: 履歴保存・分析向け
- `handoff`: 次セッション再開速度の最適化向け

### Planning Tagging Rule

`/startproject` と `/plan` のタスクは、各ステップに担当を明記する。

- (Codex): 実装・テストコード作成・失敗分析
- (Claude): テスト整理・実行・調整

---

## Shell Environment (Windows)

**You MUST use Git Bash (POSIX) syntax for all shell commands.**

Claude Code on Windows requires Git Bash. Never use PowerShell syntax.

| Use (Git Bash) | NOT (PowerShell) |
|----------------|------------------|
| `2>> .claude/logs/cli-tools.stderr.log` | `2>$null` |
| `cp -r` | `Copy-Item -Recurse` |
| `rm -rf` | `Remove-Item -Recurse -Force` |
| `mkdir -p` | `New-Item -ItemType Directory` |
| `/path/to/file` | `\path\to\file` |

---

## Tech Stack

- **Python** / **uv** (pip禁止)
- **ruff** (lint/format) / **ty** (type check) / **pytest**
- `poe lint` / `poe test` / `poe all`

→ 詳細: `.claude/rules/dev-environment.md`

---

## Timeout Configuration

Codex/Gemini CLI calls may take several minutes for complex reasoning tasks.

| Setting | Value | Purpose |
|---------|-------|---------|
| `BASH_DEFAULT_TIMEOUT_MS` | 600000 (10 min) | Default timeout for Bash commands |
| `BASH_MAX_TIMEOUT_MS` | 3600000 (1 hour) | Maximum allowed timeout |

Configured in `.claude/settings.json` → `env` section.

---

## Documentation

| Location | Content |
|----------|---------|
| `.claude/rules/` | コーディング・セキュリティ・言語ルール |
| `.claude/docs/DESIGN.md` | 設計決定の記録 |
| `.claude/docs/research/` | Gemini調査結果 |
| `.claude/logs/cli-tools.jsonl` | Codex/Gemini入出力ログ |

---

## Language Protocol

- **思考・コード**: 英語
- **ユーザー対話**: 日本語
