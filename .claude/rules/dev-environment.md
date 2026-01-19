# 開発環境ルール

プロジェクトの開発環境とツールチェーン．

## パッケージ管理: uv

**pip は使用禁止．すべて uv 経由で実行する．**

```bash
# パッケージ追加
uv add <package>
uv add --dev <package>    # 開発依存

# 依存関係の同期
uv sync

# スクリプト実行
uv run <command>
uv run python script.py
uv run pytest
```

### pyproject.toml

依存関係は `pyproject.toml` で管理:

```toml
[project]
dependencies = [
    "httpx>=0.27",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "ruff>=0.8",
]
```

## リント・フォーマット: ruff

```bash
# チェック
uv run ruff check .

# 自動修正
uv run ruff check --fix .

# フォーマット
uv run ruff format .
```

### ruff 設定（pyproject.toml）

```toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "UP",     # pyupgrade
]
ignore = ["E501"]  # line too long (formatter handles)

[tool.ruff.format]
quote-style = "double"
```

## 型チェック: ty

```bash
# 型チェック実行
uv run ty check src/
```

### ty の特徴

- Rust 製の高速型チェッカー（Astral 製）
- ruff / uv と同じエコシステム
- mypy 互換の型アノテーション

## ノートブック: marimo

インタラクティブな Python ノートブック環境．

```bash
# ノートブック作成・編集
uv run marimo edit notebook.py

# ノートブック実行（CLI）
uv run marimo run notebook.py

# アプリとしてデプロイ
uv run marimo run notebook.py --host 0.0.0.0 --port 8080
```

### marimo の特徴

- **純粋な Python ファイル**（.py）: Git との相性が良い
- **リアクティブ**: セル間の依存を自動追跡
- **再現性**: セルの実行順序に依存しない

### marimo 使用時の注意

```python
# ❌ Bad: グローバル状態の変更
data = []
def add_item(item):
    data.append(item)  # 副作用

# ✅ Good: 純粋関数
def add_item(data: list, item) -> list:
    return [*data, item]
```

## タスクランナー

複数ツールの実行は `pyproject.toml` の scripts か poe で管理:

```toml
[tool.poe.tasks]
lint = "ruff check . && ruff format --check ."
format = "ruff check --fix . && ruff format ."
typecheck = "ty check src/"
test = "pytest -v"
all = ["lint", "typecheck", "test"]
```

## よく使うコマンド

```bash
# 初期化
uv init
uv venv
source .venv/bin/activate

# 開発依存インストール
uv sync --all-extras

# 品質チェック（全部）
uv run ruff check . && uv run ruff format --check . && uv run ty check src/ && uv run pytest

# または poe 経由
poe all
```

## チェックリスト

コード提出前に確認:

- [ ] `uv run ruff check .` がパス
- [ ] `uv run ruff format --check .` がパス
- [ ] `uv run ty check src/` がパス
- [ ] `uv run pytest` がパス
