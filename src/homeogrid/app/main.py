"""CLI entrypoint."""

from __future__ import annotations

import argparse
import json

from homeogrid.app.replay import replay_file
from homeogrid.app.run import run_runtime


def main() -> None:
    parser = argparse.ArgumentParser(prog="homeogrid")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--config", required=True)
    ablate_parser = subparsers.add_parser("ablate")
    ablate_parser.add_argument("--config", required=True)
    replay_parser = subparsers.add_parser("replay")
    replay_parser.add_argument("--file", required=True)
    args = parser.parse_args()
    if args.command == "replay":
        print(json.dumps(replay_file(args.file), ensure_ascii=False, indent=2))
        return
    run_runtime(args.config, args.command)


if __name__ == "__main__":
    main()
