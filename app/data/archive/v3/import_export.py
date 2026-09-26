"""Load an Admin → Exports download into the Google Sheets workbook.

For the one case it was written for: the app ran on the local SQLite store
because the workbook was only half configured, so answers exist in the export
but not in the sheet. Download `reviews.csv`, `responses.csv` and
`edge_responses.csv` from the Admin page *while that app is still running*,
then:

    export GOOGLE_SHEET_ID='<the id>'
    python app/tools/import_export.py ~/Downloads --dry-run
    python app/tools/import_export.py ~/Downloads

Rows are matched on the same deterministic keys the app uses, so a row already
in the sheet is updated in place and a missing one is appended. Running it twice
is safe.
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import sheets  # noqa: E402

#: export file name -> workbook tab
FILES = {
    "reviews.csv": sheets.REVIEWS,
    "responses.csv": sheets.RESPONSES,
    "edge_responses.csv": sheets.EDGE_RESPONSES,
}


def read_csv(path: pathlib.Path, tab: str) -> list[dict[str, str]]:
    """Read an export, tolerating a file written under an older column layout.

    A column added after the export was taken is simply absent from the file. It
    is filled with the empty string rather than treated as corruption — refusing
    the file would strand exactly the answers this tool exists to rescue. The key
    column is different: without it a row cannot be matched to a sheet row at
    all, so a file lacking it is genuinely unusable.
    """
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    header = set(rows[0]) if rows else set(sheets.COLUMNS[tab])

    key_column = sheets.KEY_COLUMN[tab]
    if key_column not in header:
        raise SystemExit(f"{path.name} has no {key_column} column, so its rows "
                         f"cannot be matched to the workbook")

    absent = [name for name in sheets.COLUMNS[tab] if name not in header]
    if absent:
        print(f"  note: {path.name} predates {', '.join(absent)} — left empty")
    unknown = sorted(header - set(sheets.COLUMNS[tab]))
    if unknown:
        print(f"  note: {path.name} has columns the workbook does not: "
              f"{', '.join(unknown)} — ignored")

    return [{name: (row.get(name) or "") for name in sheets.COLUMNS[tab]} for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=pathlib.Path,
                        help="folder holding the three exported CSVs")
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would be written, and write nothing")
    args = parser.parse_args()

    if not sheets.configured():
        raise SystemExit(sheets.configuration_gap() or
                         f"set {sheets.ENV_SHEET_ID} and a service account first")

    book = sheets.GoogleSheetsWorkbook.from_env()
    print(f"workbook {book.sheet_id} as {sheets.describe_account()}\n")
    if not args.dry_run:
        book.ensure_tabs()

    for filename, tab in FILES.items():
        path = args.directory / filename
        if not path.exists():
            print(f"{tab}: no {filename} — skipped")
            continue
        rows = read_csv(path, tab)
        key_column = sheets.KEY_COLUMN[tab]
        index = sheets.row_index(book.read_tab(tab), tab)

        appends = [r for r in rows if r[key_column] not in index]
        updates = [r for r in rows if r[key_column] in index]
        print(f"{tab}: {len(rows)} row(s) in {filename} — "
              f"{len(appends)} to append, {len(updates)} to update")
        if args.dry_run:
            continue
        book.append_rows(tab, appends)
        for row in updates:
            book.update_row(tab, index[row[key_column]], row)

    print("\ndry run — nothing written" if args.dry_run else "\ndone")


if __name__ == "__main__":
    main()
