#!/usr/bin/env python
"""
PreToolUse hook: Remind to use Git Bash syntax on Windows.

Blocks Bash commands that use PowerShell syntax, since Claude Code
on Windows requires Git Bash.
"""

import json
import platform
import sys

# PowerShell-specific patterns to detect
POWERSHELL_PATTERNS = [
    # Redirection
    "2>$null",
    ">$null",
    # Cmdlets
    "Remove-Item",
    "Copy-Item",
    "Move-Item",
    "New-Item",
    "Get-Item",
    "Set-Item",
    "Get-Content",
    "Set-Content",
    "Get-ChildItem",
    "Get-Location",
    "Set-Location",
    "Test-Path",
    "Invoke-",
    "Write-Host",
    "Write-Output",
    # Common PowerShell parameters
    "-Recurse",
    "-Force",
    "-ErrorAction",
    "-Path",
    "-ItemType",
]


def detect_powershell_syntax(command: str) -> str | None:
    """Detect PowerShell patterns in command. Returns matched pattern or None."""
    for pattern in POWERSHELL_PATTERNS:
        if pattern in command:
            return pattern
    return None


def main():
    # Only check on Windows
    if platform.system() != "Windows":
        sys.exit(0)

    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input", {})
        command = tool_input.get("command", "")

        if not command:
            sys.exit(0)

        pattern = detect_powershell_syntax(command)

        if pattern:
            output = {
                "decision": "block",
                "reason": (
                    f"PowerShell syntax detected: `{pattern}`. "
                    "Claude Code on Windows requires Git Bash (POSIX syntax). "
                    "Use: `2>/dev/null` not `2>$null`, "
                    "`cp -r` not `Copy-Item`, "
                    "`rm -rf` not `Remove-Item`, "
                    "`/` path separators not `\\`."
                ),
            }
            print(json.dumps(output))

        sys.exit(0)

    except Exception as e:
        # Don't block on hook errors
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
