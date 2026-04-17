"""CLI entry point for release assembly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from release_tooling.release_package.assembler import assemble_release
from release_tooling.release_package.request import ReleaseRequest


def main() -> None:
    args = parse_args()
    request = build_request(args)
    result = assemble_release(request)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="assemble-release")
    parser.add_argument("--package-name", required=True)
    parser.add_argument("--baseline-tag", required=True)
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--input-root", action="append", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    return parser.parse_args()


def build_request(args: argparse.Namespace) -> ReleaseRequest:
    return ReleaseRequest(
        package_name=args.package_name,
        baseline_tag=args.baseline_tag,
        baseline_commit=args.baseline_commit,
        input_roots=tuple(path.resolve() for path in args.input_root),
        output_root=args.output_root.resolve(),
    )


if __name__ == "__main__":
    main()
