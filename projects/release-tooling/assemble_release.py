"""Run release assembly without editable install."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    from release_tooling.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
