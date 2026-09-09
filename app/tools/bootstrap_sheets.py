"""Create the shared workbook and its structure, or verify an existing one.

The app needs six tabs with exact headers: CONFIG, EVALUATORS and ASSIGNMENTS
say what the experiment is; REVIEWS, RESPONSES and EDGE_RESPONSES hold what the
evaluators decided. This creates them, and can create the spreadsheet itself.

`--seed` copies the configuration out of data/manifest.yaml into the three
configuration tabs, which is how a workbook is populated the first time. It
refuses to overwrite configuration that is already there unless `--force` is
given, because the workbook is the live copy once evaluation has started.

    # use a sheet you already made and shared with the service account
    python app/tools/bootstrap_sheets.py

    # let the service account create one and share it with you
    python app/tools/bootstrap_sheets.py --create "SLiM Brain HE Evaluation" \\
        --share you@example.com

Creating a spreadsheet needs the Drive API enabled as well as Sheets. Using an
existing sheet needs only the Sheets API, which is the simpler path.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import sheets  # noqa: E402

OK, BAD = "  ok  ", "  FAIL"


def report(passed: bool, message: str) -> bool:
    print(f"{OK if passed else BAD}  {message}")
    return passed


def _client():
    import gspread
    from google.oauth2.service_account import Credentials

    info = sheets.service_account_info()
    if info is None:
        raise SystemExit(
            f"No service account. Set {sheets.ENV_CREDENTIALS} to the key file path "
            f"or its contents, or add a [{sheets.SECRETS_SERVICE_ACCOUNT}] table to "
            f"Streamlit secrets."
        )
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    return gspread.authorize(Credentials.from_service_account_info(info, scopes=scopes)), info


def _seed(spreadsheet, *, force: bool) -> None:
    """Copy the file configuration into the workbook's configuration tabs."""
    import manifest

    print()
    plans = {
        sheets.CONFIG: [{"key": k, "value": str(v)}
                        for k, v in sorted(manifest.manifest().get("config", {}).items())],
        sheets.EVALUATORS: [
            {name: entry.get(name, "") for name in sheets.COLUMNS[sheets.EVALUATORS]}
            for entry in manifest.manifest().get("evaluators", [])
        ],
        sheets.ASSIGNMENTS: [
            {name: row.get(name, "") for name in sheets.COLUMNS[sheets.ASSIGNMENTS]}
            for row in manifest.manifest().get("assignments", [])
        ],
    }
    for tab, rows in plans.items():
        worksheet = spreadsheet.worksheet(tab)
        existing = len(worksheet.get_all_values()) - 1     # minus the header
        if existing > 0 and not force:
            report(False, f"{tab} already holds {existing} rows — left alone "
                          f"(pass --force to replace)")
            continue
        if existing > 0:
            worksheet.batch_clear([f"A2:{_column_letter(len(sheets.COLUMNS[tab]))}"])
        worksheet.append_rows(
            [[row.get(name, "") for name in sheets.COLUMNS[tab]] for row in rows],
            value_input_option="RAW")
        report(True, f"seeded {tab} with {len(rows)} rows")


def _column_letter(index: int) -> str:
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", metavar="TITLE",
                        help="create a new spreadsheet with this title")
    parser.add_argument("--share", metavar="EMAIL", action="append", default=[],
                        help="give this address editor access (repeatable)")
    parser.add_argument("--seed", action="store_true",
                        help="copy data/manifest.yaml into the configuration tabs")
    parser.add_argument("--force", action="store_true",
                        help="with --seed, replace configuration already present")
    args = parser.parse_args()

    client, info = _client()
    account = info.get("client_email", "?")
    print(f"service account: {account}\n")

    if args.create:
        spreadsheet = client.create(args.create)
        report(True, f"created spreadsheet {args.create!r}")
        print(f"        id:  {spreadsheet.id}")
        print(f"        url: https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit")
        for email in args.share:
            spreadsheet.share(email, perm_type="user", role="writer",
                              notify=False, email_message=None)
            report(True, f"shared with {email} as editor")
        if not args.share:
            print("\n        WARNING: the sheet lives in the service account's Drive and")
            print("        nobody else can open it. Re-run with --share your@email to fix.")
        identifier = spreadsheet.id
    else:
        identifier = sheets.sheet_id()
        if not identifier:
            raise SystemExit(
                f"{sheets.ENV_SHEET_ID} is not set. Either export it, or run with "
                f"--create TITLE --share you@example.com to make a new sheet."
            )
        try:
            spreadsheet = client.open_by_key(identifier)
        except Exception as error:
            raise SystemExit(
                f"could not open sheet {identifier}: {error}\n"
                f"Share it with {account} as an Editor, and check the id is the part "
                f"of the URL between /d/ and /edit."
            )
        report(True, f"opened {spreadsheet.title!r}")

    # --- structure ------------------------------------------------------
    existing = {w.title: w for w in spreadsheet.worksheets()}
    for tab in sheets.ALL_TABS:
        columns = list(sheets.COLUMNS[tab])
        if tab not in existing:
            worksheet = spreadsheet.add_worksheet(title=tab, rows=2000, cols=len(columns))
            worksheet.update(values=[columns], range_name="A1")
            report(True, f"created tab {tab} ({len(columns)} columns)")
        else:
            worksheet = existing[tab]
            header = worksheet.row_values(1)
            if header == columns:
                report(True, f"tab {tab} already correct")
            else:
                worksheet.update(values=[columns], range_name="A1")
                report(True, f"tab {tab} headers rewritten "
                             f"(was {len(header)} columns, now {len(columns)})")
                if header and header != columns:
                    print("        NOTE: headers changed. Rows written under the old "
                          "layout should be re-preallocated, not migrated in place.")

    # Google always makes a default first sheet; remove it if it is unused.
    for title in ("Sheet1", "Foglio1", "Hoja 1", "Página1"):
        if title in {w.title for w in spreadsheet.worksheets()} and len(spreadsheet.worksheets()) > len(sheets.ALL_TABS):
            try:
                spreadsheet.del_worksheet(spreadsheet.worksheet(title))
                report(True, f"removed the empty default tab {title!r}")
            except Exception:
                pass

    if args.seed:
        _seed(spreadsheet, force=args.force)

    print(f"\nWorkbook ready: https://docs.google.com/spreadsheets/d/{identifier}/edit")
    print("\nSet this for the app:")
    print(f"  GOOGLE_SHEET_ID = {identifier}")
    print("\nThen verify end to end:")
    print("  python app/tools/check_sheets.py --write")


if __name__ == "__main__":
    main()
