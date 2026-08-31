"""`se-buddy baseline [<name>]` - read a recorded baseline (spec Sec.6.4, Sec.7.3)."""

from __future__ import annotations

from pathlib import Path

from se_buddy.baseline import baselines_dir, load_baseline


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("baseline", help="read a recorded baseline (spec Sec.6.4)")
    parser.add_argument("name", nargs="?", default=None, help="baseline name; omit to list all")
    parser.set_defaults(func=run)


def run(args) -> int:
    root = Path.cwd()

    if args.name is None:
        directory = baselines_dir(root)
        if not directory.exists():
            print("no baselines recorded yet")
            return 0
        names = sorted(p.stem for p in directory.glob("*.yaml"))
        if not names:
            print("no baselines recorded yet")
            return 0
        for name in names:
            print(name)
        return 0

    manifest = load_baseline(root, args.name)
    if manifest is None:
        print(f"se-buddy: no baseline named {args.name!r}")
        return 1

    print(f"baseline {args.name}")
    print(f"  date        {manifest.get('date')}")
    print(f"  model hash  {manifest.get('model_hash')}")
    for register, rows in (manifest.get("registers") or {}).items():
        print(f"  {register}: {len(rows)} row(s)")
    open_ids = manifest.get("open_ask_ids") or []
    print(f"  open asks   {len(open_ids)}")
    return 0
