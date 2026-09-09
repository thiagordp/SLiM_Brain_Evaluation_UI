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
                        help="append and delete a test row to prove write access")
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

    # 5. tabs
    try:
        workbook.ensure_tabs()
        existing = [w.title for w in book.worksheets()]
        report(all(tab in existing for tab in sheets.ALL_TABS),
               f"tabs present: {', '.join(sheets.ALL_TABS)}")
        print(f"        worksheets: {', '.join(existing)}")
    except Exception as error:
        report(False, f"could not create/verify tabs (write access?): {error}")
        sys.exit(1)

    # 6. read
    try:
        counts = {tab: len(workbook.read_tab(tab)) for tab in sheets.ALL_TABS}
        report(True, "read every tab")
        for tab, count in counts.items():
            print(f"        {tab}: {count} data rows")
    except Exception as error:
        report(False, f"could not read a tab: {error}")
        sys.exit(1)

    # 7. optional write round-trip
    if args.write:
        probe = "__connection_test__"
        try:
            workbook.append_rows(sheets.RESPONSES, [{
                "response_key": probe, "review_id": probe, "answer": "Yes",
                "comment_evidence": "written by check_sheets.py",
            }])
            rows = workbook.read_tab(sheets.RESPONSES)
            index = sheets.row_index(rows, sheets.RESPONSES)
            found = probe in index
            report(found, "appended a test row")
            if found:
                workbook.update_row(sheets.RESPONSES, index[probe], {
                    "response_key": probe, "review_id": probe, "answer": "No",
                    "comment_evidence": "updated",
                })
                after = {r["response_key"]: r["answer"]
                         for r in workbook.read_tab(sheets.RESPONSES)}
                report(after.get(probe) == "No", "updated that row in place")
                book.worksheet(sheets.RESPONSES).delete_rows(index[probe])
                remaining = sheets.row_index(
                    workbook.read_tab(sheets.RESPONSES), sheets.RESPONSES)
                report(probe not in remaining, "removed the test row")
        except Exception as error:
            report(False, f"write round-trip failed: {error}")
            sys.exit(1)

    print("\nGoogle Sheets is configured. The app will use it automatically:")
    print("  streamlit run app/streamlit_app.py")
    if not args.write:
        print("\nRe-run with --write to prove write access before the evaluators start.")


if __name__ == "__main__":
    main()
