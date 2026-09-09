"""Freeze the live configuration so a finished round stays reproducible.

Every review records the ``config_version`` it was performed under. That is a
digest, not the data: this writes the data beside it, so months later the exact
assignment set behind a number can still be reconstructed.

    python app/tools/snapshot_config.py                 # snapshot what is live
    python app/tools/snapshot_config.py --list          # what has been kept

Run it whenever the configuration is formally accepted or changed. Commit the
result: a snapshot that exists only on the machine that made it is not a record.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import manifest  # noqa: E402
import sheets  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "config_snapshots"


def rows_for(tab: str) -> list[dict]:
    if tab == sheets.CONFIG:
        return [{"key": k, "value": str(v)} for k, v in sorted(manifest.config().items())]
    if tab == sheets.EVALUATORS:
        return manifest.evaluators()
    return manifest.assignments()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=pathlib.Path, default=OUT)
    parser.add_argument("--list", action="store_true",
                        help="list the snapshots already kept and exit")
    args = parser.parse_args()

    if args.list:
        if not args.out.exists():
            print("no snapshots yet")
            return
        for directory in sorted(args.out.iterdir()):
            counts = ", ".join(
                f"{p.stem} {sum(1 for _ in p.open(encoding='utf-8')) - 1}"
                for p in sorted(directory.glob("*.csv")))
            print(f"  {directory.name}   {counts}")
        return

    version = manifest.config_version()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = args.out / f"{stamp}_{version}"
    directory.mkdir(parents=True, exist_ok=True)

    print(f"source: {manifest.source_name()}")
    print(f"config_version: {version}\n")
    for tab in sheets.CONFIG_TABS:
        rows = rows_for(tab)
        columns = list(sheets.COLUMNS[tab])
        path = directory / f"{tab}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({name: row.get(name, "") for name in columns})
        print(f"  {tab:12s} {len(rows):4d} rows -> {path.name}")

    print(f"\nwrote {directory}")
    print("Commit it: a snapshot only on this machine is not a record.")


if __name__ == "__main__":
    main()
