# AGENTS.md — Subagent Execution Contract

## Scope

- Applies to all tasks and files under `repo/`.
- Target agents are **Codex CLI** and **Gemini CLI**.

## Agent Dispatch

- If a task is executed via `codex exec`, apply **Codex Rules** below.
- If a task is executed via `gemini -p`, apply **Gemini Rules** below.
- If delegation crosses agents, pass applicable rules unchanged.

## Global Hard Rules (Fail-Closed)

1. If any rule cannot be followed, **STOP** and report the reason.
2. Do not silently switch to alternative behavior.
3. When stopping, return the exact failed command and concise stderr/stdout.

## Patch Application on Windows (Mandatory)

### Codex Rules

- **MUST NOT** use `apply_patch` command alias or `apply_patch.bat`.
- **MUST** invoke Codex directly:
  `codex.exe --codex-run-as-apply-patch "<UTF-8 patch string>"`
- Patch text must be passed as one argument with preserved newlines.
- Patch text must contain exact markers:
  `*** Begin Patch` and `*** End Patch`.
- On patch parse failure: regenerate patch text and retry once.
- If still failing: **STOP** and report details.

### Gemini Rules

- **MUST** read `repo/.gemini/GEMINI.md` before first Gemini call in a task.
- **MUST NOT** discard stderr (`2>/dev/null`, `2>$null`).
- **MUST** redirect stderr to `.claude/logs/cli-tools.stderr.log`.
- **MUST** save substantial findings to `.claude/docs/research/{topic}.md`.
- On non-zero exit: **STOP** and report exact command and stderr.

## Execution Defaults

- Run commands from `repo/` root unless the task explicitly requires otherwise.
- Keep changes minimal and task-scoped.
- Do not run destructive git operations unless explicitly requested.

## Required Hand-Off Format

- Files changed
- What was implemented
- Validation run (or why skipped)
- Risks / follow-ups
