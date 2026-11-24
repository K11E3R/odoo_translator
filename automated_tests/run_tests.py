"""Compatibility entry point for the supported pytest suite."""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    return subprocess.call([sys.executable, "-m", "pytest", "-q"])


if __name__ == "__main__":
    raise SystemExit(main())
