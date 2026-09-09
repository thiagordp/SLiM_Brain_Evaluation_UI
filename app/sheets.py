"""The shared Google Sheets workbook — the live store for a deployed run.

Streamlit Community Cloud does not guarantee that runtime-generated local files
survive, so a SQLite file there is not a safe database. One shared Sheets
workbook is, and it is also inspectable and trivially exportable.

Two rules from the design shape this module:

* **Narrow writes only.** Never download a tab, edit a frame and write it back:
  a concurrent evaluator's newer answer would be silently overwritten. Rows are
  preallocated, each evaluator owns their own rows, and a save updates exactly
  one row range.
* **Deterministic keys.** Every row carries the key its caller computes, so a
  save is always "find my row, update its cells".

``LocalWorkbook`` writes the same tabs as CSV. It exists for dry runs and tests
— it is not a live store for a running evaluation.

Seven tabs, in two groups. CONFIG / EVALUATORS / ASSIGNMENTS say what the
experiment *is*: who evaluates what, and which switches are on. REVIEWS /
RESPONSES / EDGE_RESPONSES hold what the evaluators *decided*. The first group
changes rarely and is read on almost every page; the second changes constantly
and is read one review at a time. They are cached accordingly.
"""
from __future__ import annotations

import csv
import json
import os
import pathlib
from typing import Any, Protocol

# The Splitter writes this workbook before the evaluation app reads it, so the
# canonical names are the ones that project already uses. The HE_-prefixed
# aliases are accepted too, so a single export serves both applications.
ENV_SHEET_ID = "GOOGLE_SHEET_ID"
ENV_CREDENTIALS = "GOOGLE_SERVICE_ACCOUNT_JSON"
ENV_SHEET_ID_ALIASES = (ENV_SHEET_ID, "HE_GOOGLE_SHEET_ID")
ENV_CREDENTIALS_ALIASES = (ENV_CREDENTIALS, "HE_GOOGLE_CREDENTIALS", "GOOGLE_CREDENTIALS")


#: Streamlit's idiomatic place for a service-account key, as a TOML table.
SECRETS_SERVICE_ACCOUNT = "gcp_service_account"


def _secrets():
    """Streamlit secrets when running under Streamlit, otherwise nothing.

    Streamlit Community Cloud provides no environment variables — secrets arrive
    only through st.secrets — so every lookup has to consult both.
    """
    try:
        import streamlit as st

        return st.secrets
    except Exception:
        return {}


def _first_env(names: tuple[str, ...]) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    secrets = _secrets()
    for name in names:
        try:
            if name in secrets:
                return str(secrets[name])
        except Exception:
            continue
    return ""


def sheet_id() -> str:
    return _first_env(ENV_SHEET_ID_ALIASES)


def credentials_setting() -> str:
    return _first_env(ENV_CREDENTIALS_ALIASES)


def service_account_info() -> dict | None:
    """The key as a mapping, from whichever form it was supplied in."""
    secrets = _secrets()
    try:
        if SECRETS_SERVICE_ACCOUNT in secrets:
            return dict(secrets[SECRETS_SERVICE_ACCOUNT])
    except Exception:
        pass
    raw = credentials_setting()
    if not raw:
        return None
    candidate = pathlib.Path(raw)
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))
    return json.loads(raw)


def configured() -> bool:
    return bool(sheet_id()) and service_account_info() is not None


def configuration_gap() -> str:
    """Name the missing half of a partial configuration, or "" when there is none.

    The live store needs both the workbook id and the key. Supplying one without
    the other is never a deliberate request for the local store: it is a
    deployment that runs on SQLite while everyone assumes the workbook is being
    filled, and the answers are only found missing after the fact. The caller
    stops on this rather than falling back.
    """
    has_id = bool(sheet_id())
    try:
        has_account = service_account_info() is not None
    except Exception:
        has_account = True      # present but unreadable — a different problem
    if has_id == has_account:
        return ""
    if has_id:
        return (
            f"`{ENV_SHEET_ID}` is set but no service account is. Add the key as a "
            f"`[{SECRETS_SERVICE_ACCOUNT}]` table in Streamlit secrets, or as "
            f"`{ENV_CREDENTIALS}`."
        )
    return (
        f"A service account is set but `{ENV_SHEET_ID}` is not, so the app has no "
        f"workbook to write to. Add `{ENV_SHEET_ID}` — the segment of the sheet's URL "
        f"between `/d/` and `/edit` — to the same secrets."
    )


def describe_account() -> str:
    """Identify the service account without ever revealing the key.

    `service_account_info()` returns the private key. Never print or log it;
    print this instead.
    """
    try:
        info = service_account_info()
    except Exception:
        return "unreadable service account"
    if info is None:
        return "no service account"
    return f"{info.get('client_email', '?')} (project {info.get('project_id', '?')})"

# --- configuration: what the experiment is
CONFIG, EVALUATORS, ASSIGNMENTS = "CONFIG", "EVALUATORS", "ASSIGNMENTS"
# --- evaluation: what the evaluators decided
REVIEWS, RESPONSES, EDGE_RESPONSES = "REVIEWS", "RESPONSES", "EDGE_RESPONSES"
#: A phase is finally submitted for an evaluator only when a row exists here.
#: Sheets has no transaction across the many review-row updates a submission
#: makes, so the marker is written last: a submission interrupted halfway leaves
#: reviews submitted and no marker, and retrying is safe because submitting an
#: already-submitted review changes nothing.
PHASE_SUBMISSIONS = "PHASE_SUBMISSIONS"

CONFIG_TABS = (CONFIG, EVALUATORS, ASSIGNMENTS)
EVALUATION_TABS = (REVIEWS, RESPONSES, EDGE_RESPONSES, PHASE_SUBMISSIONS)
ALL_TABS = CONFIG_TABS + EVALUATION_TABS

COLUMNS: dict[str, tuple[str, ...]] = {
    # A key/value tab rather than one row of many columns: the settings are read
    # and written one at a time, and a new setting must not mean a new column.
    CONFIG: ("key", "value"),
    EVALUATORS: (
        "evaluator_id", "name", "is_admin", "pair_id",
        "agreement_split", "individual_split",
    ),
    ASSIGNMENTS: (
        "assignment_key", "evaluator_id", "phase_id", "split_id",
        "source_id", "work_id", "assignment_order", "assignment_state",
    ),
    REVIEWS: (
        "review_id", "phase_id", "evaluator_id", "evaluator_name", "pair_id",
        "source_id", "work_id", "assignment_key", "split_id",
        # Provenance, stamped when work begins rather than when the row is made:
        # a preallocated row may sit for weeks under a configuration that is not
        # the one its evaluation is eventually performed under.
        "brain_snapshot_id", "eval_spec_version", "config_version",
        "assignment_state",
        # Where this review's preallocated rows sit, so opening one paper is a
        # narrow range read rather than a whole-tab download.
        "responses_first_row", "responses_last_row",
        "edges_first_row", "edges_last_row",
        "pdf_read_confirmed", "status", "started_at", "last_saved_at",
        "submitted_at",
    ),
    RESPONSES: (
        "response_key", "review_id", "source_id", "object_type", "object_id",
        "question_key", "criterion_id", "field_subitem", "answer",
        "comment_evidence", "unclear", "applicability", "updated_at",
    ),
    EDGE_RESPONSES: (
        "edge_response_key", "review_id", "source_id", "host_claim_id", "edge_key",
        "edge_from", "edge_to", "other_claim_id", "edge_type", "label_correct",
        "comment_correct_label", "updated_at",
    ),
    PHASE_SUBMISSIONS: (
        "submission_key", "evaluator_id", "phase_id", "config_version",
        "status", "submitted_at",
    ),
}

KEY_COLUMN = {
    CONFIG: "key",
    EVALUATORS: "evaluator_id",
    ASSIGNMENTS: "assignment_key",
    REVIEWS: "review_id",
    RESPONSES: "response_key",
    EDGE_RESPONSES: "edge_response_key",
    PHASE_SUBMISSIONS: "submission_key",
}

#: Rows per write request, so a large preallocation stays inside payload limits.
WRITE_CHUNK = 2000


class StorageError(RuntimeError):
    """A storage operation failed in a way the caller must not paper over."""


class QuotaExceeded(StorageError):
    """Google refused the request for now. Nothing is wrong with the workbook.

    Google allows 60 read requests per minute per user. A burst — several
    evaluators arriving at once, or a page that reads more than it needs —
    exhausts it, and the right response is to wait, not to change anything.
    """


def _status_of(error) -> int | None:
    response = getattr(error, "response", None)
    return getattr(response, "status_code", None)


def _is_missing_range(error) -> bool:
    """Sheets answers a range naming a tab it does not have with a 400."""
    return _status_of(error) == 400 and "Unable to parse range" in str(error)


def _api_error(context: str, error) -> StorageError:
    """One Google failure, told apart from another.

    A quota rejection is temporary and means wait; anything else may not be, and
    the two must not read alike to whoever is looking at the screen.
    """
    if _status_of(error) == 429:
        return QuotaExceeded(
            f"{context}: Google's read quota for this minute is used up "
            f"(60 requests per minute per user). Nothing is wrong with the "
            f"workbook and nothing was changed — wait a moment and reload."
        )
    return StorageError(f"{context}: {error}. Nothing was created or changed.")


class Workbook(Protocol):
    def ensure_tabs(self) -> None: ...
    def check_ready(self) -> None: ...
    def read_tab(self, tab: str) -> list[dict[str, str]]: ...
    def read_range(self, tab: str, first: int, last: int) -> list[dict[str, str]]: ...
    def append_rows(self, tab: str, rows: list[dict[str, Any]]) -> int: ...
    def update_row(self, tab: str, row_number: int, values: dict[str, Any]) -> None: ...
    def update_rows(self, tab: str, updates: list[tuple[int, dict[str, Any]]]) -> None: ...
    def row_count(self, tab: str) -> int: ...


def _column_letter(index: int) -> str:
    """1-based column index to an A1 column letter."""
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def row_index(rows: list[dict[str, str]], tab: str) -> dict[str, int]:
    """key -> sheet row number (header is row 1, so data starts at row 2)."""
    key_column = KEY_COLUMN[tab]
    return {row[key_column]: number
            for number, row in enumerate(rows, start=2) if row.get(key_column)}


def _ordered(tab: str, values: dict[str, Any]) -> list[Any]:
    return ["" if values.get(name) is None else values.get(name)
            for name in COLUMNS[tab]]


def _as_row(tab: str, raw: list) -> dict[str, str]:
    """A row of raw cell values as a record. Trailing empty cells are omitted."""
    padded = list(raw) + [""] * (len(COLUMNS[tab]) - len(raw))
    return {name: str(value) for name, value in zip(COLUMNS[tab], padded)}


# --------------------------------------------------------------- Google Sheets
def _credentials() -> dict:
    try:
        info = service_account_info()
    except json.JSONDecodeError as error:
        raise StorageError(
            f"{ENV_CREDENTIALS} is neither a readable JSON file path nor inline JSON"
        ) from error
    if info is None:
        raise StorageError(
            f"no service account: set {ENV_CREDENTIALS}, or a [{SECRETS_SERVICE_ACCOUNT}] "
            f"table in Streamlit secrets"
        )
    return info


class GoogleSheetsWorkbook:
    def __init__(self, sheet_id: str) -> None:
        self.sheet_id = sheet_id
        self._sheet = None
        #: tab -> worksheet handle. Looking one up costs a metadata request, and
        #: the set of tabs does not change while the app is running.
        self._tabs: dict[str, Any] = {}

    @classmethod
    def from_env(cls) -> "GoogleSheetsWorkbook":
        identifier = sheet_id()
        if not identifier:
            raise StorageError(f"{ENV_SHEET_ID} is not set")
        return cls(identifier)

    def _open(self):
        if self._sheet is not None:
            return self._sheet
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError as error:                      # pragma: no cover
            raise StorageError(
                "google sheets support needs `gspread` and `google-auth`"
            ) from error
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(_credentials(), scopes=scopes)
        account = _credentials().get("client_email", "the service account")
        try:
            self._sheet = gspread.authorize(creds).open_by_key(self.sheet_id)
        except Exception as error:                        # pragma: no cover
            raise StorageError(self.explain(error, account)) from error
        return self._sheet

    def explain(self, error: Exception, account: str) -> str:
        """Turn Google's error into the specific thing to go and fix.

        403 and 404 mean different things and have different fixes, so they must
        not collapse into one "check your configuration" message.
        """
        text = str(error)
        status = getattr(getattr(error, "response", None), "status_code", None)
        forbidden = status == 403 or "PermissionError" in type(error).__name__ or \
            "does not have permission" in text
        missing = status == 404 or "SpreadsheetNotFound" in type(error).__name__

        if forbidden:
            return (
                f"The workbook exists, but {account} cannot open it.\n\n"
                f"Share the sheet with that address as an **Editor**:\n"
                f"open https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit "
                f"→ Share → paste the address → set the role to Editor → Share.\n\n"
                f"Your own access to the sheet does not grant the service account "
                f"anything; it has to be shared explicitly."
            )
        if missing:
            return (
                f"No workbook with id `{self.sheet_id}` exists.\n\n"
                f"{ENV_SHEET_ID} should be only the segment between `/d/` and `/edit` "
                f"in the sheet's URL — not the whole URL, and not the `#gid=` part."
            )
        return (
            f"Could not open sheet `{self.sheet_id}` as {account}: {text}\n\n"
            f"Check {ENV_SHEET_ID}, that the Google Sheets API is enabled for the "
            f"project, and that the sheet is shared with that address as an Editor."
        )

    def _worksheet(self, tab: str):
        """The tab, created only if Google says it genuinely is not there.

        The handle is kept. ``sheet.worksheet(tab)`` fetches the whole workbook's
        metadata every time it is called, so looking a tab up cost a request of
        its own before every read and every write — seven of them just to check
        the headers at startup.

        This used to catch every exception and respond by creating the tab. A
        read-quota rejection reads as an exception too, so a burst of traffic
        made the app conclude the tab was missing and try to create one that
        already existed — recovering from a transient failure by attempting a
        structural change to the workbook. Only ``WorksheetNotFound`` means
        absent; anything else is raised, because a failure to read must never
        become a decision to write.
        """
        import gspread                                   # already a dependency

        cached = self._tabs.get(tab)
        if cached is not None:
            return cached
        sheet = self._open()
        try:
            worksheet = sheet.worksheet(tab)
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=tab, rows=1000,
                                            cols=len(COLUMNS[tab]))
            worksheet.update("A1", [list(COLUMNS[tab])])
        except gspread.exceptions.APIError as error:
            raise _api_error(f"Could not reach tab {tab}", error) from error
        self._tabs[tab] = worksheet
        return worksheet

    def ensure_tabs(self) -> None:
        """Create the tabs and fix their headers. A bootstrap step, not a startup one.

        Fifteen requests: a metadata fetch per tab and a header read per tab.
        `bootstrap_sheets.py` calls it once when a workbook is prepared. The
        running app calls `check_ready` instead.
        """
        for tab in ALL_TABS:
            worksheet = self._worksheet(tab)
            header = worksheet.row_values(1)
            if header != list(COLUMNS[tab]):
                worksheet.update("A1", [list(COLUMNS[tab])])

    def check_ready(self) -> None:
        """Is the workbook reachable and shaped as expected — in two requests.

        Three requests, once per process: one to open it, which proves it exists
        and is shared with this account; one listing of its tabs, which both
        answers "are they all there" and yields the handles every later read
        would otherwise fetch one at a time; and one `values.batchGet` carrying
        all seven header rows together. It never creates or changes anything,
        because a running app is not the thing that prepares a workbook.
        """
        import gspread                                   # already a dependency

        sheet = self._open()                             # 1 request, then cached
        try:
            # One listing gives both the answer to "are the tabs there" and the
            # handles every later read would otherwise fetch one at a time.
            present = {w.title: w for w in sheet.worksheets()}
        except gspread.exceptions.APIError as error:
            raise _api_error("Could not list the workbook's tabs", error) from error
        missing = [tab for tab in ALL_TABS if tab not in present]
        if missing:
            raise StorageError(
                f"The workbook is missing {', '.join(missing)}. Run "
                f"`bootstrap_sheets.py` against it before starting the app. "
                f"Nothing was created or changed."
            )
        self._tabs.update({tab: present[tab] for tab in ALL_TABS})

        ranges = [f"'{tab}'!1:1" for tab in ALL_TABS]
        try:
            answer = sheet.values_batch_get(ranges)      # 1 request for all seven
        except gspread.exceptions.APIError as error:
            raise _api_error("Could not read the workbook's headers", error) from error

        found = {}
        for tab, block in zip(ALL_TABS, answer.get("valueRanges", [])):
            rows = block.get("values") or [[]]
            found[tab] = [str(cell) for cell in rows[0]]
        wrong = [tab for tab in ALL_TABS if found.get(tab) != list(COLUMNS[tab])]
        if wrong:
            raise StorageError(
                f"These tabs do not have the headers this version expects: "
                f"{', '.join(wrong)}. Run `bootstrap_sheets.py` against the "
                f"workbook. Nothing was changed."
            )

    def read_tab(self, tab: str) -> list[dict[str, str]]:
        records = self._worksheet(tab).get_all_records(expected_headers=list(COLUMNS[tab]))
        return [{name: str(row.get(name, "")) for name in COLUMNS[tab]} for row in records]

    def read_range(self, tab: str, first: int, last: int) -> list[dict[str, str]]:
        """One contiguous block of rows, by sheet row number.

        The whole point of preallocating a review's rows together: reading one
        paper costs a few hundred cells instead of the whole tab.
        """
        if last < first:
            return []
        columns = COLUMNS[tab]
        end = _column_letter(len(columns))
        values = self._worksheet(tab).get(f"A{first}:{end}{last}")
        return [_as_row(tab, raw) for raw in values]

    def row_count(self, tab: str) -> int:
        """Data rows present, excluding the header."""
        return max(len(self._worksheet(tab).col_values(1)) - 1, 0)

    def append_rows(self, tab: str, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        worksheet = self._worksheet(tab)
        payload = [_ordered(tab, row) for row in rows]
        for start in range(0, len(payload), WRITE_CHUNK):
            worksheet.append_rows(payload[start:start + WRITE_CHUNK],
                                  value_input_option="RAW")
        return len(payload)

    def update_row(self, tab: str, row_number: int, values: dict[str, Any]) -> None:
        """One row, one request — never a whole-tab rewrite."""
        self.update_rows(tab, [(row_number, values)])

    def update_rows(self, tab: str, updates) -> None:
        """Several rows in one request, each still a targeted range.

        A whole-tab rewrite would silently overwrite a concurrent evaluator's
        newer answer; this only ever names the rows it owns.
        """
        updates = list(updates)
        if not updates:
            return
        worksheet = self._worksheet(tab)
        last = _column_letter(len(COLUMNS[tab]))
        payload = [{"range": f"A{number}:{last}{number}",
                    "values": [_ordered(tab, values)]}
                   for number, values in updates]
        if len(payload) == 1:
            worksheet.update(payload[0]["range"], payload[0]["values"],
                             value_input_option="RAW")
            return
        worksheet.batch_update(payload, value_input_option="RAW")


# ------------------------------------------------------------- local dry runs
class LocalWorkbook:
    """The same tabs as CSV files. For dry runs and tests, not for live use."""

    def __init__(self, directory: pathlib.Path) -> None:
        self.directory = pathlib.Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, tab: str) -> pathlib.Path:
        return self.directory / f"{tab}.csv"

    def ensure_tabs(self) -> None:
        for tab in ALL_TABS:
            path = self._path(tab)
            if not path.exists():
                with path.open("w", newline="", encoding="utf-8") as handle:
                    csv.writer(handle).writerow(COLUMNS[tab])

    def check_ready(self) -> None:
        """Local files cost nothing to create, so readiness is just having them."""
        self.ensure_tabs()

    def read_tab(self, tab: str) -> list[dict[str, str]]:
        self.ensure_tabs()
        with self._path(tab).open(encoding="utf-8") as handle:
            return [{name: row.get(name, "") or "" for name in COLUMNS[tab]}
                    for row in csv.DictReader(handle)]

    def read_range(self, tab: str, first: int, last: int) -> list[dict[str, str]]:
        if last < first:
            return []
        rows = self.read_tab(tab)
        return rows[first - 2:last - 1]        # sheet row 2 is the first record

    def row_count(self, tab: str) -> int:
        return len(self.read_tab(tab))

    def append_rows(self, tab: str, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        self.ensure_tabs()
        with self._path(tab).open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            for row in rows:
                writer.writerow(_ordered(tab, row))
        return len(rows)

    def update_row(self, tab: str, row_number: int, values: dict[str, Any]) -> None:
        self.update_rows(tab, [(row_number, values)])

    def update_rows(self, tab: str, updates) -> None:
        updates = list(updates)
        if not updates:
            return
        self.ensure_tabs()
        path = self._path(tab)
        with path.open(encoding="utf-8") as handle:
            lines = list(csv.reader(handle))
        for row_number, values in updates:
            index = row_number - 1
            if not 0 < index < len(lines):
                raise StorageError(f"{tab} has no row {row_number}")
            lines[index] = [str(v) for v in _ordered(tab, values)]
        with path.open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerows(lines)


def workbook_from_env(dry_run_dir: pathlib.Path | None = None) -> Workbook | None:
    """The live workbook when configured, a local one when a directory is given.

    Returns None when neither is configured, so the caller can fall back to the
    local SQLite store used for development.
    """
    if configured():
        return GoogleSheetsWorkbook.from_env()
    if dry_run_dir is not None:
        return LocalWorkbook(dry_run_dir)
    return None
