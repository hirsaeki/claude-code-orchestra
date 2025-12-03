# LLM/Agent Development Template for Claude Code

## 🚀 使い方

### 方法1: 新規プロジェクトを作成

GitHubの "Use this template" ボタンを使用：

1. このリポジトリページで **"Use this template"** → **"Create a new repository"**
2. 新しいリポジトリ名を入力して作成
3. クローンして開発開始

```bash
git clone https://github.com/YOUR_USERNAME/your-new-project.git
cd your-new-project

# CLAUDE.md を編集してプロジェクト情報を記入
```

**または CLI で：**
```bash
gh repo create my-new-project --template YOUR_USERNAME/llm-dev-template --clone
cd my-new-project
```

### 方法2: 既存プロジェクトに追加

既存のコードベースにClaude Code設定を追加：

```bash
cd your-existing-project

# テンプレートから必要なファイルを取得
git clone --depth 1 https://github.com/YOUR_USERNAME/llm-dev-template.git /tmp/cc-template
cp -r /tmp/cc-template/.claude .
cp -r /tmp/cc-template/docs .
cp /tmp/cc-template/CLAUDE.md .
cp /tmp/cc-template/.gitignore .gitignore.claude  # 必要な行を既存の.gitignoreにマージ
rm -rf /tmp/cc-template

# コミット
git add .claude docs CLAUDE.md
git commit -m "Add Claude Code configuration from llm-dev-template"
```

### セットアップ後にやること

1. `CLAUDE.md` を編集してプロジェクト情報を記入
2. 必要に応じて `.claude/settings.json` の権限を調整
3. 使用するライブラリを `/research-lib` で文書化

## 📁 構成

```
.claude/
├── settings.json              # 最大権限（機密ファイルのみ保護）
├── agents/
│   ├── lib-researcher.md      # ライブラリ調査・文書化
│   ├── refactorer.md          # シンプル化リファクタリング
│   ├── debugger.md            # デバッグ
│   └── code-reviewer.md       # コードレビュー
├── commands/
│   ├── research-lib.md        # /research-lib langchain
│   ├── simplify.md            # /simplify src/agents/
│   ├── update-design.md       # /update-design（明示的な設計記録）
│   └── update-lib-docs.md     # /update-lib-docs
└── skills/
    └── design-tracker/        # 設計追跡スキル（自動発動）
        └── SKILL.md

docs/
├── DESIGN.md                  # 設計ドキュメント（自動更新）
└── libraries/                 # ライブラリごとのドキュメント
    └── _TEMPLATE.md           # テンプレート

CLAUDE.md                      # プロジェクトメモリ
```

## 🤖 サブエージェント

### lib-researcher
新しいライブラリを導入する時や，既存ライブラリの仕様を確認する時：

```
> lib-researcherでlangchainを調査して
```

### refactorer
コードをシンプルにしたい時（ライブラリ機能は維持）：

```
> refactorerで src/agents/chat.py をシンプルにして
```

### debugger
エラーが発生した時：

```
> debuggerでこのエラーを調査して
```

### code-reviewer
コード変更後のレビュー：

```
> code-reviewerでレビューして
```

## ⚡ スラッシュコマンド

| コマンド | 説明 | 使用例 |
|----------|------|--------|
| `/research-lib` | ライブラリを調査して文書化 | `/research-lib openai` |
| `/simplify` | コードをシンプルにリファクタリング | `/simplify src/llm/client.py` |
| `/update-lib-docs` | ライブラリドキュメントを最新化 | `/update-lib-docs` |
| `/update-design` | 設計ドキュメントを明示的に更新 | `/update-design` |

## 🎯 スキル（自動発動）

### design-tracker

会話の中で設計に関する決定が行われると，自動的に `docs/DESIGN.md` に記録します．

**自動発動するタイミング：**
- アーキテクチャや設計パターンの議論
- 「ReActパターンで実装しよう」などの決定
- 「これを記録して」「設計に追加」という発言
- 「今の設計どうなってる？」という質問

**使用例：**
```
> エージェントはReActパターンで実装して，LangGraphを使おう
（自動的にdocs/DESIGN.mdに記録される）

> 今の設計を見せて
（docs/DESIGN.mdの内容を表示）
```

## 📚 ライブラリドキュメントの運用

### 新しいライブラリを導入する時

1. `/research-lib {library}` で調査・文書化
2. `docs/libraries/{library}.md` が作成される
3. 実装時はこのドキュメントを参照

### リファクタリングする時

1. `docs/libraries/` の該当ドキュメントを確認
2. ライブラリの制約を把握した上でリファクタリング
3. テストで動作確認

### 定期メンテナンス

1. `/update-lib-docs` で最新情報を確認
2. 破壊的変更があればコードを修正

## ⚙️ 権限設定

最大権限を与えつつ，機密ファイルのみ保護：

```json
{
  "permissions": {
    "allow": ["Bash(*)", "Read(*)", "Edit(*)", "Write(*)", "WebFetch(*)"],
    "deny": [
      "Read(./.env)", "Read(./.env.*)",
      "Read(./**/*.pem)", "Read(./**/*.key)",
      "Read(~/.ssh/**)", "Read(~/.aws/**)"
    ]
  }
}
```

これで他のユーザー（自分含む）が "Use this template" ボタンで新規プロジェクトを作成できます．
