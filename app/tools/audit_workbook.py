"""Audit the round workbook: is what it stores consistent? Read-only.

    python app/tools/audit_workbook.py            # errors and warnings
    python app/tools/audit_workbook.py --all      # also information lines

Uses the configured workbook (GOOGLE_SHEET_ID and the service account) and the
Brain snapshot. Two read requests; nothing is written or repaired. Exits 1 when
any error is found. The checks are described in `app/integrity.py`.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import sys

APP = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

import integrity  # noqa: E402
import manifest  # noqa: E402
import sheets  # noqa: E402
import store  # noqa: E402
from brain import load_brain  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--all", action="store_true", help="also print information lines")
    args = parser.parse_args()
    try:
        problems = integrity.run(load_brain(), store.workbook(), manifest.round_id())
    except sheets.StorageError as error:
        print(f"Cannot read the workbook: {error}")
        return 1
    counts = collections.Counter(p.level for p in problems)
    for problem in problems:
        if args.all or problem.level != integrity.INFO:
            print(problem)
    print(f"\n{counts[integrity.ERROR]} error(s), {counts[integrity.WARNING]} warning(s)"
          f" — workbook {sheets.sheet_id() or '(configured)'}, round {manifest.round_id()}")
    return 1 if counts[integrity.ERROR] else 0


if __name__ == "__main__":
    raise SystemExit(main())
