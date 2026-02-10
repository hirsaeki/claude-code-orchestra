# CLI Tool Logging Best Practices

Research on logging Codex/Gemini CLI input/output in multi-agent system.

**Date**: 2026-02-10

## Problem Statement

Users cannot easily see:
- What prompts were sent to Codex/Gemini
- What responses were received
- Timeline of AI agent interactions

Both tools are called via Bash tool, so output is visible in Claude Code UI, but:
- Hard to track across multiple conversations
- No persistent history
- Difficult to debug multi-agent workflows

## Recommended Approach: PostToolUse Hook + JSONL Logging

### Why This Approach?

1. **Leverage Existing Infrastructure**: PostToolUse hook already exists for Bash tool
2. **Non-Intrusive**: No need to modify CLI tools or create wrapper scripts
3. **Simple**: File-based append-only logging
4. **Queryable**: JSONL format is both human-readable and machine-parseable
5. **Low Overhead**: Async append operation, minimal performance impact

### Architecture

```text
Claude Code calls Bash tool
  -> codex exec --skip-git-repo-check ... "prompt"
  -> gemini -p "prompt"
  (optional, if stderr noise reduction is needed)
  -> ... 2>> .claude/logs/cli-tools.stderr.log

PostToolUse Hook (Bash matcher)
  -> Receives: tool_input + tool_response (or tool_output)
  -> Detects: codex/gemini command segments
  -> Extracts: prompt, stdout, stderr, response fallback
  -> Logs: .claude/logs/cli-tools.jsonl
```

## Implementation Details

### 1. Input Schema Compatibility

`log-cli-tools.py` supports both payload variants to avoid confusion:

- Preferred schema: `tool_response` (dict with `stdout`, `stderr`, `exit_code`, `content`)
- Backward-compatible schema: `tool_output` (string or dict)

Resolution rules:
1. If `tool_response` is dict, use it first
2. Else if `tool_response` is string, map it to `stdout`
3. Else if `tool_output` is dict/string, use that fallback

Command detection rule:
- Match `codex`/`gemini` at command-segment boundaries (`^`, `;`, `|`, `&&`, `||`) to reduce false positives from prompt text.

### 2. Log Format: JSON Lines (JSONL)

Each line is a complete JSON object:

```json
{"timestamp":"2026-02-10T10:30:45+00:00","tool":"codex","model":"gpt-5.3-codex","prompt":"How should I design...","stdout":"I recommend...","stderr":"","response":"I recommend...","success":true,"has_output":true,"exit_code":0}
{"timestamp":"2026-02-10T10:32:12+00:00","tool":"gemini","model":"gemini-3-pro-preview","prompt":"Research best practices...","stdout":"","stderr":"Progress...","response":"Progress...","success":true,"has_output":true,"exit_code":0}
```

**Fields**:
- `timestamp`: ISO 8601 format with timezone
- `tool`: `"codex"` or `"gemini"`
- `model`: Model name used
- `prompt`: Input prompt (truncated to 2000 chars if longer)
- `stdout`: Captured standard output
- `stderr`: Captured standard error
- `response`: Backward-compatible aggregate (`stdout` first, else `stderr`, else empty)
- `success`: Whether call succeeded (`exit_code == 0`)
- `has_output`: Whether either stream has content
- `exit_code`: Exit code from CLI command

**Benefits**:
- One log entry per line = easy to append
- Valid JSON = easy to parse with `jq`, Python, etc.
- Human-readable with proper formatting
- Keeps compatibility for consumers reading only `response`

### 3. Hook Behavior Notes

- Logging is append-only to `.claude/logs/cli-tools.jsonl`
- Notification spam is reduced by default:
  - No success notification unless `CLAUDE_ORCHESTRA_LOG_NOTIFY=1`
  - Failed commands (`exit_code != 0`) emit a hook message by default

### 4. Configuration: `.claude/settings.json`

Add to `PostToolUse` hooks:

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/log-cli-tools.py\"",
      "timeout": 5
    }
  ]
}
```

**Note**: Multiple hooks can match the same tool, so this can coexist with `post-test-analysis.py`.

### 5. Log Storage Location

```text
.claude/
  logs/
    cli-tools.jsonl         # Main structured log
    cli-tools.stderr.log    # Optional stderr sink for noisy commands
  hooks/
    log-cli-tools.py
  settings.json
```

**Why `.claude/logs/`?**
- Consistent with `.claude/` convention
- Easy to add to `.gitignore` (logs are local-only)
- Separate from documentation/rules

### 6. Querying Logs

**View recent calls:**
```bash
tail -20 .claude/logs/cli-tools.jsonl | jq '.'
```

**Filter by tool:**
```bash
jq 'select(.tool == "codex")' .claude/logs/cli-tools.jsonl
```

**Count calls per tool:**
```bash
jq -r '.tool' .claude/logs/cli-tools.jsonl | sort | uniq -c
```

**Failed calls only:**
```bash
jq 'select(.success == false)' .claude/logs/cli-tools.jsonl
```

**Calls with no output:**
```bash
jq 'select(.success == true and .has_output == false)' .claude/logs/cli-tools.jsonl
```

## Security Considerations

### 1. Sensitive Data in Prompts/Outputs

Prompts and streams may contain:
- API keys (if user accidentally includes)
- User data
- Proprietary code

Current hook includes lightweight masking for common token patterns (e.g. `sk-...`, `AIza...`, `ghp_...`).

### 2. Retention Guidance

- Keep `.claude/logs/` out of version control
- Periodically rotate/remove logs in long-running projects
- Avoid putting secrets into CLI prompts when possible

## Implementation Checklist

- [x] Create `.claude/logs/` directory
- [x] Add `.claude/logs/` to `.gitignore`
- [x] Create `log-cli-tools.py` hook
- [x] Update `.claude/settings.json` (PostToolUse -> Bash)
- [x] Test with sample codex/gemini call
- [x] Verify JSONL format with `jq`
- [x] Document for team (add to DESIGN.md or README)

## Testing Plan

### Unit Checks

```python
def test_success_is_exit_code_based():
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": 'codex exec --full-auto "q"'},
        "tool_response": {"stdout": "", "stderr": "", "exit_code": 0}
    }
    # expected: success == True, has_output == False
```

```python
def test_response_fallback_to_stderr():
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": 'gemini -p "q"'},
        "tool_response": {"stdout": "", "stderr": "progress", "exit_code": 0}
    }
    # expected: response == "progress"
```

```python
def test_tool_output_backward_compatibility():
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": 'gemini -p "q"'},
        "tool_output": "legacy-output"
    }
    # expected: stdout == "legacy-output"
```

### Integration Checks

1. Make one successful codex/gemini call with stdout
2. Make one call where only stderr has content
3. Make one call with non-zero exit code
4. Verify JSONL entries include `stdout`, `stderr`, `response`, `success`, `has_output`

### Reusable Payload Examples (PowerShell)

```powershell
$payloads = @(
  @{ tool_name='Bash'; tool_input=@{ command='codex exec --skip-git-repo-check --sandbox read-only --full-auto "stdout-case"' }; tool_response=@{ stdout='stdout-ok'; stderr=''; exit_code=0 } },
  @{ tool_name='Bash'; tool_input=@{ command='gemini -p "stderr-case"' }; tool_response=@{ stdout=''; stderr='stderr-progress'; exit_code=0 } },
  @{ tool_name='Bash'; tool_input=@{ command='gemini -p "fail-case"' }; tool_response=@{ stdout=''; stderr='stderr-fail'; exit_code=2 } },
  @{ tool_name='Bash'; tool_input=@{ command='gemini -p "legacy-case"' }; tool_output='legacy-output-only' }
)

foreach ($payload in $payloads) {
  ($payload | ConvertTo-Json -Depth 10 -Compress) |
    python repo/.claude/hooks/log-cli-tools.py
}
```

Expected outcomes:
- `stdout-case`: `success=true`, `response=stdout-ok`
- `stderr-case`: `success=true`, `response=stderr-progress`
- `fail-case`: `success=false`, `exit_code=2`
- `legacy-case`: `success=true`, `response=legacy-output-only`

### Reusable Payload Examples (bash)

```bash
payloads=(
  '{"tool_name":"Bash","tool_input":{"command":"codex exec --skip-git-repo-check --sandbox read-only --full-auto \"stdout-case\""},"tool_response":{"stdout":"stdout-ok","stderr":"","exit_code":0}}'
  '{"tool_name":"Bash","tool_input":{"command":"gemini -p \"stderr-case\""},"tool_response":{"stdout":"","stderr":"stderr-progress","exit_code":0}}'
  '{"tool_name":"Bash","tool_input":{"command":"gemini -p \"fail-case\""},"tool_response":{"stdout":"","stderr":"stderr-fail","exit_code":2}}'
  '{"tool_name":"Bash","tool_input":{"command":"gemini -p \"legacy-case\""},"tool_output":"legacy-output-only"}'
)

for payload in "${payloads[@]}"; do
  printf '%s\n' "$payload" | python repo/.claude/hooks/log-cli-tools.py
done
```

Expected outcomes are the same as the PowerShell example above.

### Reusable Payload Examples (JSON file)

If you prefer file-based testing, create one JSON payload per file and pipe it.

```bash
mkdir -p .claude/tmp

cat > .claude/tmp/payload-stdout.json <<'EOF'
{"tool_name":"Bash","tool_input":{"command":"codex exec --skip-git-repo-check --sandbox read-only --full-auto \"stdout-case\""},"tool_response":{"stdout":"stdout-ok","stderr":"","exit_code":0}}
EOF

cat > .claude/tmp/payload-stderr.json <<'EOF'
{"tool_name":"Bash","tool_input":{"command":"gemini -p \"stderr-case\""},"tool_response":{"stdout":"","stderr":"stderr-progress","exit_code":0}}
EOF

cat > .claude/tmp/payload-fail.json <<'EOF'
{"tool_name":"Bash","tool_input":{"command":"gemini -p \"fail-case\""},"tool_response":{"stdout":"","stderr":"stderr-fail","exit_code":2}}
EOF

cat > .claude/tmp/payload-legacy.json <<'EOF'
{"tool_name":"Bash","tool_input":{"command":"gemini -p \"legacy-case\""},"tool_output":"legacy-output-only"}
EOF

for file in .claude/tmp/payload-*.json; do
  cat "$file" | python repo/.claude/hooks/log-cli-tools.py
done
```

Expected outcomes are the same as the PowerShell and bash examples above.

## Conclusion

**Recommended implementation**: PostToolUse hook with JSONL logging and dual-schema input support

**Key benefits**:
- ✅ Zero code changes to call sites
- ✅ Transparent to agents
- ✅ stderr preserved for troubleshooting
- ✅ success based on exit code (robust for empty-output success)
- ✅ Reduced hook notification noise by default
- ✅ Lightweight sensitive-data masking
