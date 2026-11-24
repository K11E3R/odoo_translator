#!/usr/bin/env python3
"""Run non-destructive release checks for Odoo PO Translator.

This script never removes files, edits Git history, creates commits, tags,
pushes branches, or publishes releases. Those operations remain explicit
maintainer decisions.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_tests() -> int:
    command = [sys.executable, "-m", "pytest", "-q"]
    print("+", " ".join(command))
    return subprocess.call(command, cwd=ROOT)


def check_required_files() -> list[str]:
    required = [
        "README.md",
        "README.fr.md",
        "SECURITY.md",
        "CHANGELOG.md",
        "LICENSE",
        "pyproject.toml",
        "requirements.txt",
        "src/po_translator/translator.py",
        "src/po_translator/cli.py",
        "docs/brand/mark.svg",
        "docs/brand/logo.svg",
        "docs/social-preview.svg",
    ]
    return [name for name in required if not (ROOT / name).is_file()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-tests", action="store_true", help="Check files and metadata without running pytest.")
    args = parser.parse_args(argv)

    print("Odoo PO Translator — release readiness checks")
    missing = check_required_files()
    if missing:
        print("Missing required files:")
        for item in missing:
            print(f"  - {item}")
        return 1

    try:
        with (ROOT / "pyproject.toml").open("rb") as handle:
            project = tomllib.load(handle)["project"]
    except (OSError, KeyError, tomllib.TOMLDecodeError) as exc:
        print(f"Unable to read pyproject.toml: {exc}", file=sys.stderr)
        return 1

    print(f"Package: {project.get('name', 'unknown')}")
    print(f"Version: {project.get('version', 'unknown')}")
    print(f"Python requirement: {project.get('requires-python', 'unspecified')}")
    print(f"License: {project.get('license', 'unspecified')}")

    if not args.skip_tests:
        return run_tests()

    print("File and metadata checks passed. Tests were explicitly skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
