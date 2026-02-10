# トラブルシューティング

## Codex CLI が見つからない

```bash
# 確認
which codex
codex --version

# インストール
npm install -g @openai/codex
```

## 認証エラー

```bash
# 再認証
codex login

# ステータス確認
codex login status
```

## タイムアウト

| reasoning_effort | 推奨タイムアウト |
|-----------------|-----------------|
| low             | 60s             |
| medium          | 180s            |
| high            | 600s            |
| xhigh           | 900s            |

config.toml で設定:
```toml
[mcp_servers.codex]
tool_timeout_sec = 600
```

## Git リポジトリエラー

```bash
# Git 管理外で実行する場合
codex exec --skip-git-repo-check ...
```

## reasoning 出力が多すぎる

```bash
# stderr をファイルへ退避
codex exec --skip-git-repo-check ... 2>> .claude/logs/cli-tools.stderr.log

# または config.toml で
hide_agent_reasoning = true
```

## `apply_patch` が Windows で不安定

`apply_patch.bat` 経由で引数が崩れる場合、`codex.exe` を直接呼び出す。

```powershell
# patch.diff は UTF-8 (no BOM) で作成
$patch = [System.IO.File]::ReadAllText((Join-Path (Get-Location) 'patch.diff'))
codex.exe --codex-run-as-apply-patch "$patch"
```

## セッション継続できない

```bash
# 最近のセッション一覧
codex sessions list

# 特定セッションの詳細
codex sessions show {SESSION_ID}
```

## sandbox 権限エラー

| エラー | 原因 | 解決策 |
|--------|------|--------|
| Permission denied | read-only で書き込み | workspace-write に変更 |
| Network blocked | sandbox 制限 | danger-full-access（慎重に） |

## メモリ不足

大きなコードベースを分析する場合:
1. 対象ファイルを絞る
2. 段階的に分析
3. `--config context_limit=...` で調整
