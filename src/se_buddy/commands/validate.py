"""`se-buddy validate` - six layers of findings with evidence (spec Sec.7.2, Sec.7.3)."""

from __future__ import annotations

from pathlib import Path

from se_buddy.commands._common import add_model_argument, load_model_or_die
from se_buddy.validate import run_all_layers


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("validate", help="six layers of findings with evidence")
    add_model_argument(parser)
    parser.set_defaults(func=run)


def run(args) -> int:
    model = load_model_or_die(args)
    if model is None:
        return 1

    findings = run_all_layers(Path.cwd(), model)
    for finding in findings:
        print(f"[{finding.severity:7s}] {finding.layer:14s} {finding.message}")

    return 1 if any(f.severity == "ERROR" for f in findings) else 0
