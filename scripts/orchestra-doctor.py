#!/usr/bin/env python
"""Self-diagnosis script for Claude Code Orchestra template."""

import argparse
import json
import py_compile
import shutil
import sys
from pathlib import Path


def find_project_root(start: Path) -> Path | None:
    """Walk up from *start* looking for CLAUDE.md."""
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / "CLAUDE.md").exists():
            return parent
    return None


def check_tool(name: str, verbose: bool) -> bool:
    path = shutil.which(name)
    if path:
        if verbose:
            print(f"  found: {path}")
        return True
    return False


def check_directory(root: Path, rel: str) -> bool:
    return (root / rel).is_dir()


def check_settings_json(root: Path, verbose: bool) -> bool:
    settings = root / ".claude" / "settings.json"
    if not settings.exists():
        if verbose:
            print("  settings.json not found (optional)")
        return True
    try:
        json.loads(settings.read_text(encoding="utf-8"))
        return True
    except (json.JSONDecodeError, OSError) as e:
        if verbose:
            print(f"  error: {e}")
        return False


def check_hooks_compile(root: Path, verbose: bool) -> list[str]:
    hooks_dir = root / ".claude" / "hooks"
    failures: list[str] = []
    if not hooks_dir.is_dir():
        return failures
    for py_file in sorted(hooks_dir.glob("*.py")):
        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            failures.append(f"{py_file.name}: {e}")
            if verbose:
                print(f"  FAIL: {py_file.name}: {e}")
    return failures


def check_symlink(root: Path, rel: str, verbose: bool) -> bool | None:
    target = root / rel
    if not target.exists() and not target.is_symlink():
        return None
    if target.is_symlink():
        resolved = target.resolve()
        ok = resolved.exists()
        if verbose:
            status = "valid" if ok else "BROKEN"
            print(f"  {rel} -> {resolved} ({status})")
        return ok
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Orchestra template health check")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    root = find_project_root(Path(__file__).parent)
    if root is None:
        print("✗ Could not find project root (no CLAUDE.md found)")
        return 1

    if args.verbose:
        print(f"Project root: {root}\n")

    all_ok = True

    tools = ["python", "uv", "ruff", "ty", "codex", "gemini"]
    print("=== Tool Availability ===")
    for tool in tools:
        ok = check_tool(tool, args.verbose)
        mark = "✓" if ok else "✗"
        print(f"  {mark} {tool}")
        if not ok:
            all_ok = False

    print("\n=== Directory Structure ===")
    dirs = [
        ".claude",
        ".codex",
        ".gemini",
        ".claude/hooks",
        ".claude/skills",
        ".claude/rules",
        ".claude/docs",
        ".claude/docs/research",
    ]
    for d in dirs:
        ok = check_directory(root, d)
        mark = "✓" if ok else "✗"
        print(f"  {mark} {d}/")
        if not ok:
            all_ok = False

    print("\n=== Settings Validation ===")
    ok = check_settings_json(root, args.verbose)
    mark = "✓" if ok else "✗"
    print(f"  {mark} .claude/settings.json")
    if not ok:
        all_ok = False

    print("\n=== Hook Compilation ===")
    failures = check_hooks_compile(root, args.verbose)
    if failures:
        for f in failures:
            print(f"  ✗ {f}")
        all_ok = False
    else:
        print("  ✓ All hooks compile successfully")

    print("\n=== Symlinks ===")
    sym_result = check_symlink(
        root, ".codex/skills/design-tracker", args.verbose
    )
    if sym_result is None:
        print("  - .codex/skills/design-tracker (not present)")
    elif sym_result:
        print("  ✓ .codex/skills/design-tracker")
    else:
        print("  ✗ .codex/skills/design-tracker (broken symlink)")
        all_ok = False

    print()
    if all_ok:
        print("✓ All checks passed")
    else:
        print("✗ Some checks failed")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
