"""Check that the Brain snapshot can be evaluated with instrument 4.0.

    python app/tools/preflight.py            # errors and warnings; exit 1 on error
    python app/tools/preflight.py --quiet    # errors only

The same check runs inside `bootstrap_round.py` and at app startup.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import preflight  # noqa: E402
from brain import load_brain  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    report = preflight.check(load_brain())
    for key, value in report.summary.items():
        print(f"{key:>20}: {value}")
    if not args.quiet:
        for warning in report.warnings:
            print(f"warning  {warning}")
    for error in report.errors:
        print(f"ERROR    {error}")
    print(f"\n{len(report.errors)} error(s), {len(report.warnings)} warning(s) — "
          + ("the snapshot is evaluable" if report.ok else "the snapshot is NOT evaluable"))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
