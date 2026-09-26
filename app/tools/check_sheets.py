"""Verify the Google Sheets credentials, step by step.

Each step reports on its own so a failure names the thing to fix rather than
producing one opaque traceback.

    python app/tools/check_sheets.py            # check only
    python app/tools/check_sheets.py --write    # also round-trip a test row
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import sheets  # noqa: E402

OK, BAD = "  ok  ", "  FAIL"


def report(passed: bool, message: str) -> bool:
    print(f"{OK if passed else BAD}  {message}")
    return passed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true",
                        help="write and remove a temporary tab to prove write access")
    args = parser.parse_args()

    print("Google Sheets configuration\n")

    # 1. libraries
    try:
        import gspread                                     # noqa: F401
        from google.oauth2.service_account import Credentials  # noqa: F401
        report(True, "gspread and google-auth are installed")
    except ImportError:
        report(False, "gspread / google-auth missing — pip install -r requirements.txt")
        sys.exit(1)

    # 2. environment
    identifier = sheets.sheet_id()
    if not report(bool(identifier),
                  f"{sheets.ENV_SHEET_ID} is set" if identifier
                  else f"{sheets.ENV_SHEET_ID} is not set"):
        sys.exit(1)
    print(f"        sheet id: {identifier}")

    raw = sheets.credentials_setting()
    if not report(bool(raw),
                  f"{sheets.ENV_CREDENTIALS} is set" if raw
                  else f"{sheets.ENV_CREDENTIALS} is not set"):
        sys.exit(1)

    # 3. credentials parse
    path = pathlib.Path(raw)
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() \
            else json.loads(raw)
    except Exception as error:
        report(False, f"credentials are neither a readable JSON file nor inline JSON: {error}")
        sys.exit(1)
    report(True, f"credentials parsed ({'file' if path.exists() else 'inline JSON'})")

    account = payload.get("client_email", "")
    if not report(payload.get("type") == "service_account" and bool(account),
                  "credentials are a service account"):
        print("        expected a service-account key, not an OAuth client id")
        sys.exit(1)
    print(f"        service account: {account}")
    print(f"        project: {payload.get('project_id', '?')}")

    # 4. open the workbook
    workbook = sheets.GoogleSheetsWorkbook(identifier)
    try:
        book = workbook._open()
        report(True, f"opened the workbook: {book.title!r}")
    except Exception as error:
        report(False, f"could not open the workbook: {error}")
        print(f"\n        Share the sheet with {account} as an Editor,")
        print("        and confirm the id is the part of the URL between /d/ and /edit.")
        sys.exit(1)

    # 5. what the workbook holds
    try:
        existing = workbook.tab_titles()
    except Exception as error:
        report(False, f"could not list the tabs: {error}")
        sys.exit(1)
    print(f"        worksheets: {', '.join(existing)}")
    ours = [tab for tab in sheets.ALL_TABS if tab in existing]
    if not ours:
        report(True, "the workbook holds no round yet — ready for "
                     "`python app/tools/bootstrap_round.py`")
    else:
        import store

        store.use_workbook(workbook)
        try:
            store.check_ready()
            meta = store.round_metadata()
            report(True, f"round {meta.get('round_id')} · instrument "
                         f"{meta.get('eval_spec_version')} · definitions "
                         f"{meta.get('definitions_id')}")
        except Exception as error:
            report(False, f"the round tabs are incomplete or wrongly shaped: {error}")
            sys.exit(1)

    # 6. optional write round-trip, on a temporary tab — never on a round tab
    if args.write:
        probe = "_connection_test"
        try:
            if probe in existing:
                workbook.delete_tab(probe)
            workbook.create_tab(probe)
            sheet = book.worksheet(probe)
            sheet.update("A1", [["written by check_sheets.py"]])
            report(sheet.acell("A1").value == "written by check_sheets.py",
                   "wrote and read back a cell on a temporary tab")
            workbook.delete_tab(probe)
            report(True, "removed the temporary tab")
        except Exception as error:
            report(False, f"write round-trip failed: {error}")
            sys.exit(1)

    print("\nGoogle Sheets access is configured.")
    if not args.write:
        print("Re-run with --write to prove write access before the evaluators start.")


if __name__ == "__main__":
    main()
