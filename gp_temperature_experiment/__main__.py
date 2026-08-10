from __future__ import annotations

import argparse
import sys
import traceback

from .config import load_config
from .runner import run_experiment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gp_temperature_experiment",
        description="Run the replicated-curve GP temperature experiment.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="Run an experiment configuration.")
    run_parser.add_argument("--config", required=True, help="Path to JSON-compatible YAML.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        try:
            result = run_experiment(load_config(args.config))
            print(f"Experiment result: {result}", flush=True)
            return 0
        except Exception:
            traceback.print_exc()
            return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())

