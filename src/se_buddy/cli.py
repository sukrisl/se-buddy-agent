"""Command dispatch for `se-buddy` (spec Sec.7.3).

Phase 0 wires up only `doctor`. Every other verb in Sec.7.3's surface
arrives with the phase that gives it something real to do.
"""

from __future__ import annotations

import argparse

from se_buddy import doctor as doctor_module


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="se-buddy")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="is this installation sound? (spec Sec.5.3)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "doctor":
        return doctor_module.run()
    parser.error(f"unknown command: {args.command}")
    return 2
