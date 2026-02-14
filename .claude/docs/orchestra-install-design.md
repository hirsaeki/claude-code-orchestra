# Orchestra Installer Design (Windows / Interactive)

> **Status: Design Draft — Not yet implemented.**
> This document describes a planned installer. No code exists yet.

## Purpose

Provide a safe, repeatable way to install the Claude Code Orchestra template into an **existing** project on Windows.
The installer must preserve existing configuration while merging the template’s hooks, skills, and agent setup.

## Scope

- **OS**: Windows (PowerShell)
- **Mode**: Interactive
- **Precondition**: Existing `CLAUDE.md` and possibly existing `.claude/`, `.codex/`, `.gemini/`.

## Design Principles

- **Safety first**: never overwrite without explicit user consent.
- **Idempotent**: re-running should be safe and converge to the same result.
- **Minimal intrusion**: only add what is needed; preserve existing settings.
- **Transparent**: show what will change; report what was changed or skipped.

---

## User Experience (Interactive Flow)

1. **Detect existing assets**
   - `.claude/`, `.codex/`, `.gemini/`, `CLAUDE.md`
2. **Backup**
   - Create timestamped backups for any touched path (file or folder).
3. **Select policy**
   - `A` Safe: skip conflicts by default
   - `B` Recommended: merge when possible, ask on conflicts
   - `C` Force: replace on conflicts (still backups)
4. **Resolve conflicts**
   - For each conflicting file, ask:
     - `[M]erge / [S]kip / [R]eplace`
5. **Apply changes**
6. **Summary report**
   - Applied / Skipped / Needs manual review

---

## Files Added to Template (Installer Side)

```
scripts/
  orchestra-install.ps1
  orchestra-manifest.json
  orchestra-merge-rules.json
```

- **manifest**: list of template paths to install
- **merge rules**: per-path merge strategy (append/merge/replace)

---

## Installation Targets

- `.claude/`
- `.codex/`
- `.gemini/`
- `CLAUDE.md` (append/replace section only)

---

## Merge Strategy

### 1) `CLAUDE.md`

- Append a dedicated section (e.g. `## Orchestra Template`)
- If the section already exists, replace only that section
- Do **not** overwrite unrelated content

### 2) `.claude/settings.json`

- **Deep merge** with existing settings
- Merge strategy:
  - `hooks`: merge arrays by `matcher` + `hooks[].command` identity
  - `permissions.allow`: union (dedupe)
  - `permissions.deny`: union (dedupe)
  - `env`: keep existing keys, add missing keys only
- Preserve unknown keys to remain forward compatible

### 3) `.codex/config.toml`

- Do not override `model`, `approval_policy`, or existing skill configuration
- Only add a missing `skills.config` entry that points to the template’s context-loader

### 4) Other files

- Default behavior: **copy**
- If conflict: follow interactive decision (merge/skip/replace)

---

## Backup Strategy

- For each path that will be modified, create:
  - `.<name>.bak-YYYYMMDD-HHMM`
- Backup includes full directory (for `.claude`, `.codex`, `.gemini`) or file
- Backups are created **before** any write

---

## Idempotency Rules

- Re-running the script should not duplicate hook entries
- `CLAUDE.md` should maintain a **single** Orchestra section
- JSON merges should be stable across runs

---

## Conflict Resolution Rules

Interactive choices:
- **Merge**: use merge strategy for file type
- **Skip**: leave existing file unchanged
- **Replace**: overwrite with template version (backup exists)

Policy shortcuts:
- **Safe**: default to Skip
- **Recommended**: default to Merge where supported, otherwise Ask
- **Force**: default to Replace

---

## PowerShell Functions (Planned)

- `Get-ProjectRoot()`
- `Load-Manifest()` / `Load-MergeRules()`
- `Backup-Path()`
- `Merge-JsonDeep()`
- `Merge-ClaudeMd()`
- `Copy-With-Decision()`
- `Show-Report()`

---

## Open Questions

- Final location for `scripts/` in the target repository?
- Should the installer support non-interactive mode later (CI)?
- Should hooks use `python` or `python` on Windows (auto-detect)?

---

## Next Step

Implement `scripts/orchestra-install.ps1` and the manifest/merge-rule files.
