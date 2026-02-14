# CLI Reference — Codex & Gemini Commands

Canonical reference for all CLI invocation patterns.
Other files should link here instead of duplicating command examples.

## General Rules

- **Always run from project root** — never `cd` to a subdirectory first.
  Specify target directory in the prompt if needed.
- **Subagent recommended** for outputs > 10 lines (preserves main context).
- **stderr**: redirect to file, never discard.
  Use `2>> .claude/logs/cli-tools.stderr.log` (not `2>/dev/null` or `2>$null`).

## Codex CLI

### Analysis (read-only)

```bash
codex exec --skip-git-repo-check --sandbox read-only --full-auto "{question}" 2>> .claude/logs/cli-tools.stderr.log
```

### Implementation (write)

```bash
codex exec --skip-git-repo-check --sandbox workspace-write --full-auto "Work on files in {target/dir/}. {task}" 2>> .claude/logs/cli-tools.stderr.log
```

### Sandbox Modes

| Mode | Flag | Use Case |
|------|------|----------|
| Analysis | `read-only` | Design review, debugging, trade-offs |
| Work | `workspace-write` | Implementation, refactoring, fixes |

### Patch Application (Windows)

Codex patch application is the **only** case where PowerShell is used.
All other commands must use Git Bash (POSIX) syntax.

```powershell
# patch.diff must be UTF-8 (no BOM)
$patch = [System.IO.File]::ReadAllText((Join-Path (Get-Location) 'patch.diff'))
codex.exe --codex-run-as-apply-patch "$patch"
```

Do **not** use `apply_patch.bat` — it has argument parsing issues on Windows.

## Gemini CLI

### Research

```bash
gemini -p "{research question}" 2>> .claude/logs/cli-tools.stderr.log
```

### Codebase Analysis

```bash
gemini -p "{question}" --include-directories . 2>> .claude/logs/cli-tools.stderr.log
```

### Subdirectory Analysis

```bash
gemini -p "Analyze src/auth/" --include-directories src/auth 2>> .claude/logs/cli-tools.stderr.log
```

### Multimodal (PDF/video/audio)

```bash
gemini -p "{prompt}" --file "path/to/file" 2>> .claude/logs/cli-tools.stderr.log
```

### JSON Output

```bash
gemini -p "{question}" --output-format json 2>> .claude/logs/cli-tools.stderr.log
```

## Subagent Invocation Pattern

```
Task tool parameters:
- subagent_type: "general-purpose"
- run_in_background: true (optional)
- prompt: |
    {Task description}
    
    # Run from project root, never cd first
    codex exec --skip-git-repo-check --sandbox read-only --full-auto "{question}" 2>> .claude/logs/cli-tools.stderr.log
    
    Return CONCISE summary.
```

## Language Protocol

1. Ask Codex/Gemini in **English**
2. Receive response in **English**
3. Report to user in **Japanese**

## Output Locations

| Agent | Output |
|-------|--------|
| Codex | Summary returned to orchestrator |
| Gemini | Full output saved to `.claude/docs/research/{topic}.md` |
| Both | I/O logged to `.claude/logs/cli-tools.jsonl` |
