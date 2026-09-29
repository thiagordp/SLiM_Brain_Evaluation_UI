"""The round workbook: the one persistent store of an evaluation round.

One evaluation round is one fresh Google Sheets workbook, created empty and
initialised by `tools/bootstrap_round.py`. There is no other store and no
fallback: if the workbook is missing, unreachable or wrongly shaped, the app
refuses to start rather than keep answers anywhere else.

Two rules shape this module:

* **Narrow writes only.** A tab is never downloaded, edited and written back — a
  concurrent evaluator's newer answer would be silently overwritten. Every save
  names the rows it owns.
* **Deterministic keys.** Every row carries the key its caller computes, so a
  save is always "find my row, update its cells".

Tabs, in three groups:

    round metadata   ROUND, DEFINITIONS            written once by bootstrap
    configuration    CONFIG, EVALUATORS, ASSIGNMENTS
    evaluation       REVIEWS, RESPONSES, CONCEPT_RESPONSES, RELATION_RESPONSES,
                     MISSING_CONCEPTS, PROPOSED_CONCEPTS, RESTATEMENTS,
                     SUBMISSIONS

REVIEWS, RESPONSES, CONCEPT_RESPONSES and RELATION_RESPONSES are preallocated
by bootstrap, one contiguous block per review. MISSING_CONCEPTS,
PROPOSED_CONCEPTS and RESTATEMENTS hold a variable number of rows and grow by
idempotent upserts.
"""
from __future__ import annotations

import json
import os
import pathlib
from typing import Any, Protocol

ENV_SHEET_ID = "GOOGLE_SHEET_ID"
ENV_CREDENTIALS = "GOOGLE_SERVICE_ACCOUNT_JSON"
ENV_SHEET_ID_ALIASES = (ENV_SHEET_ID, "HE_GOOGLE_SHEET_ID")
ENV_CREDENTIALS_ALIASES = (ENV_CREDENTIALS, "HE_GOOGLE_CREDENTIALS", "GOOGLE_CREDENTIALS")

#: Streamlit's idiomatic place for a service-account key, as a TOML table.
SECRETS_SERVICE_ACCOUNT = "gcp_service_account"


def _secrets():
    """Streamlit secrets when running under Streamlit, otherwise nothing."""
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
    try:
        return bool(sheet_id()) and service_account_info() is not None
    except Exception:
        return bool(sheet_id())


def configuration_gap() -> str:
    """What is missing from the workbook configuration, or "" when nothing is."""
    has_id = bool(sheet_id())
    try:
        has_account = service_account_info() is not None
    except Exception:
        has_account = True      # present but unreadable — reported when opened
    if has_id and has_account:
        return ""
    if has_id:
        return (f"`{ENV_SHEET_ID}` is set but no service account is. Add the key as a "
                f"`[{SECRETS_SERVICE_ACCOUNT}]` table in Streamlit secrets, or as "
                f"`{ENV_CREDENTIALS}`.")
    if has_account:
        return (f"A service account is set but `{ENV_SHEET_ID}` is not, so there is "
                f"no round workbook. Add `{ENV_SHEET_ID}` — the segment of the "
                f"sheet's URL between `/d/` and `/edit`.")
    return (f"Neither `{ENV_SHEET_ID}` nor a service account is set. Google Sheets "
            f"is the only evaluation store, so the application cannot start without "
            f"a round workbook.")


def describe_account() -> str:
    """Identify the service account without ever revealing the key."""
    try:
        info = service_account_info()
    except Exception:
        return "unreadable service account"
    if info is None:
        return "no service account"
    return f"{info.get('client_email', '?')} (project {info.get('project_id', '?')})"


# ------------------------------------------------------------------- tabs
ROUND, DEFINITIONS = "ROUND", "DEFINITIONS"
CONFIG, EVALUATORS, ASSIGNMENTS = "CONFIG", "EVALUATORS", "ASSIGNMENTS"
REVIEWS = "REVIEWS"
RESPONSES = "RESPONSES"
CONCEPT_RESPONSES = "CONCEPT_RESPONSES"
RELATION_RESPONSES = "RELATION_RESPONSES"
MISSING_CONCEPTS = "MISSING_CONCEPTS"
PROPOSED_CONCEPTS = "PROPOSED_CONCEPTS"
#: One row per Claim membership in a restatement group of one review.
RESTATEMENTS = "RESTATEMENTS"
#: A phase is finally submitted for an evaluator only when a row exists here.
#: Sheets has no transaction across the review rows a submission touches, so the
#: marker is written last and retrying a half-finished submission is safe.
SUBMISSIONS = "SUBMISSIONS"

METADATA_TABS = (ROUND, DEFINITIONS)
CONFIG_TABS = (CONFIG, EVALUATORS, ASSIGNMENTS)
BLOCK_TABS = (RESPONSES, CONCEPT_RESPONSES, RELATION_RESPONSES)
SELECTION_TABS = (MISSING_CONCEPTS, PROPOSED_CONCEPTS, RESTATEMENTS)
EVALUATION_TABS = (REVIEWS, *BLOCK_TABS, *SELECTION_TABS, SUBMISSIONS)
ALL_TABS = METADATA_TABS + CONFIG_TABS + EVALUATION_TABS

#: The REVIEWS columns that record where each block tab's rows for a review sit.
BLOCK_PREFIX = {RESPONSES: "responses", CONCEPT_RESPONSES: "concepts",
                RELATION_RESPONSES: "relations"}

COLUMNS: dict[str, tuple[str, ...]] = {
    ROUND: ("key", "value"),
    DEFINITIONS: ("key", "label", "source_file", "text", "items_json"),
    CONFIG: ("key", "value"),
    EVALUATORS: ("evaluator_id", "name", "is_admin", "pair_id",
                 "agreement_split", "individual_split"),
    ASSIGNMENTS: ("assignment_key", "evaluator_id", "phase_id", "split_id",
                  "source_id", "pdf_file", "assignment_order", "assignment_state"),
    REVIEWS: (
        "review_id", "round_id", "phase_id", "evaluator_id", "evaluator_name",
        "pair_id", "source_id", "assignment_key", "split_id",
        # Provenance, stamped when work begins rather than when the row is made.
        "brain_snapshot_id", "eval_spec_version", "definitions_id",
        "config_version", "assignment_state",
        "responses_first_row", "responses_last_row",
        "concepts_first_row", "concepts_last_row",
        "relations_first_row", "relations_last_row",
        "pdf_read_confirmed", "status", "started_at", "last_saved_at",
        "submitted_at",
    ),
    RESPONSES: (
        "response_key", "review_id", "source_id", "object_type", "object_id",
        "claim_id", "question_key", "answer", "comment",
        "updated_at",
    ),
    CONCEPT_RESPONSES: (
        "response_key", "review_id", "source_id", "claim_id", "concept_id",
        "concept_status", "concept_family", "question_key", "answer", "comment",
        "updated_at",
    ),
    RELATION_RESPONSES: (
        "response_key", "review_id", "source_id", "relation_key",
        "relation_type", "from_claim", "to_claim", "from_source", "to_source",
        "grounding", "note",
        "grounding_answer", "grounding_comment",
        "direction_answer", "direction_comment",
        "type_answer", "type_comment",
        "updated_at",
    ),
    MISSING_CONCEPTS: (
        "selection_key", "review_id", "source_id", "claim_id", "concept_id",
        "concept_family", "concept_status", "active", "updated_at",
    ),
    PROPOSED_CONCEPTS: (
        "proposal_key", "review_id", "source_id", "claim_id", "proposal_id",
        "name", "family", "explanation", "active", "updated_at",
    ),
    RESTATEMENTS: (
        "restatement_key", "review_id", "source_id", "group_id", "claim_id",
        "active", "updated_at",
    ),
    SUBMISSIONS: (
        "submission_key", "round_id", "evaluator_id", "phase_id",
        "config_version", "status", "submitted_at",
    ),
}

KEY_COLUMN = {tab: columns[0] for tab, columns in COLUMNS.items()}

#: Rows per write request, so a large preallocation stays inside payload limits.
WRITE_CHUNK = 2000


class StorageError(RuntimeError):
    """A storage operation failed in a way the caller must not paper over."""


class StorageNotConfigured(StorageError):
    """No round workbook is configured. There is no other store to use."""


class QuotaExceeded(StorageError):
    """Google refused the request for now. Nothing is wrong with the workbook."""


def _status_of(error) -> int | None:
    response = getattr(error, "response", None)
    return getattr(response, "status_code", None)


def _api_error(context: str, error) -> StorageError:
    if _status_of(error) == 429:
        return QuotaExceeded(
            f"{context}: Google's request quota for this minute is used up "
            f"(60 requests per minute per user). Nothing is wrong with the "
            f"workbook and nothing was changed — wait a moment and reload."
        )
    return StorageError(f"{context}: {error}. Nothing was created or changed.")


class Workbook(Protocol):
    def tab_titles(self) -> list[str]: ...
    def is_blank(self, title: str) -> bool: ...
    def create_tab(self, tab: str) -> None: ...
    def delete_tab(self, title: str) -> None: ...
    def write_header(self, tab: str) -> None: ...
    def headers(self, tabs) -> dict[str, list[str]]: ...
    def read_tab(self, tab: str) -> list[dict[str, str]]: ...
    def read_range(self, tab: str, first: int, last: int) -> list[dict[str, str]]: ...
    def read_ranges(self, requests) -> list[list[dict[str, str]]]: ...
    def append_rows(self, tab: str, rows: list[dict[str, Any]]) -> int: ...
    def update_rows(self, tab: str, updates) -> None: ...


def column_letter(index: int) -> str:
    """1-based column index to an A1 column letter."""
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def row_index(rows: list[dict[str, str]], tab: str) -> dict[str, int]:
    """key -> sheet row number (header is row 1, so data starts at row 2).

    Where a key occurs more than once — possible only in the selection tabs,
    after two sessions appended the same key at the same moment — the first row
    wins, so every later write lands on one row.
    """
    key_column = KEY_COLUMN[tab]
    index: dict[str, int] = {}
    for number, row in enumerate(rows, start=2):
        key = row.get(key_column)
        if key and key not in index:
            index[key] = number
    return index


def ordered(tab: str, values: dict[str, Any]) -> list[Any]:
    return ["" if values.get(name) is None else values.get(name)
            for name in COLUMNS[tab]]


def as_row(tab: str, raw: list) -> dict[str, str]:
    """A row of raw cell values as a record. Trailing empty cells are omitted."""
    padded = list(raw) + [""] * (len(COLUMNS[tab]) - len(raw))
    return {name: str(value) for name, value in zip(COLUMNS[tab], padded)}


def a1(tab: str, first: int | None = None, last: int | None = None) -> str:
    end = column_letter(len(COLUMNS[tab]))
    if first is None:
        return f"'{tab}'!A2:{end}"
    return f"'{tab}'!A{first}:{end}{last}"


# --------------------------------------------------------------- Google Sheets
def _credentials() -> dict:
    try:
        info = service_account_info()
    except json.JSONDecodeError as error:
        raise StorageError(
            f"{ENV_CREDENTIALS} is neither a readable JSON file path nor inline JSON"
        ) from error
    if info is None:
        raise StorageNotConfigured(configuration_gap())
    return info


class GoogleSheetsWorkbook:
    def __init__(self, identifier: str) -> None:
        self.sheet_id = identifier
        self._sheet = None
        #: tab -> worksheet handle. A lookup costs a metadata request, and the
        #: set of tabs does not change while the app is running.
        self._tabs: dict[str, Any] = {}

    def _open(self):
        if self._sheet is not None:
            return self._sheet
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError as error:                      # pragma: no cover
            raise StorageError(
                "Google Sheets support needs `gspread` and `google-auth`"
            ) from error
        info = _credentials()
        creds = Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        try:
            self._sheet = gspread.authorize(creds).open_by_key(self.sheet_id)
        except Exception as error:                        # pragma: no cover
            raise StorageError(self.explain(error, info.get("client_email", "the "
                                                             "service account"))) from error
        return self._sheet

    def explain(self, error: Exception, account: str) -> str:
        """403 and 404 have different fixes, so they get different messages."""
        text = str(error)
        status = _status_of(error)
        if status == 403 or "PermissionError" in type(error).__name__:
            return (f"The workbook exists, but {account} cannot open it. Share the "
                    f"sheet with that address as an Editor.")
        if status == 404 or "SpreadsheetNotFound" in type(error).__name__:
            return (f"No workbook with id `{self.sheet_id}` exists. {ENV_SHEET_ID} is "
                    f"only the segment between `/d/` and `/edit` in the sheet's URL.")
        return f"Could not open sheet `{self.sheet_id}` as {account}: {text}"

    def _worksheets(self) -> dict[str, Any]:
        import gspread

        try:
            present = {w.title: w for w in self._open().worksheets()}
        except gspread.exceptions.APIError as error:
            raise _api_error("Could not list the workbook's tabs", error) from error
        self._tabs.update(present)
        return present

    def _worksheet(self, tab: str):
        """The tab's handle. Never creates one: that is bootstrap's job."""
        cached = self._tabs.get(tab)
        if cached is not None:
            return cached
        present = self._worksheets()
        if tab not in present:
            raise StorageError(f"The workbook has no {tab} tab. Run "
                               f"`tools/bootstrap_round.py` against it.")
        return present[tab]

    def tab_titles(self) -> list[str]:
        return list(self._worksheets())

    def create_tab(self, tab: str) -> None:
        worksheet = self._open().add_worksheet(
            title=tab, rows=100, cols=len(COLUMNS.get(tab, ())) or 26)
        self._tabs[tab] = worksheet

    def delete_tab(self, title: str) -> None:
        present = self._worksheets()
        if title in present:
            self._open().del_worksheet(present[title])
            self._tabs.pop(title, None)

    def is_blank(self, title: str) -> bool:
        """Whether a tab holds nothing at all (a new workbook's default sheet)."""
        import gspread

        try:
            values = self._open().values_get(f"'{title}'!A1:Z50").get("values") or []
        except gspread.exceptions.APIError as error:
            raise _api_error(f"Could not read tab {title}", error) from error
        return not any(str(cell).strip() for row in values for cell in row)

    def write_header(self, tab: str) -> None:
        self._worksheet(tab).update("A1", [list(COLUMNS[tab])])

    def headers(self, tabs) -> dict[str, list[str]]:
        """Row 1 of each tab, in one request."""
        import gspread

        tabs = list(tabs)
        try:
            answer = self._open().values_batch_get([f"'{t}'!1:1" for t in tabs])
        except gspread.exceptions.APIError as error:
            raise _api_error("Could not read the workbook's headers", error) from error
        found = {}
        for tab, block in zip(tabs, answer.get("valueRanges", [])):
            rows = block.get("values") or [[]]
            found[tab] = [str(cell) for cell in rows[0]]
        return found

    def read_tab(self, tab: str) -> list[dict[str, str]]:
        return self.read_ranges([(tab, None, None)])[0]

    def read_range(self, tab: str, first: int, last: int) -> list[dict[str, str]]:
        if last < first:
            return []
        return self.read_ranges([(tab, first, last)])[0]

    def read_ranges(self, requests) -> list[list[dict[str, str]]]:
        """Several tabs or row blocks in ONE request (`values.batchGet`).

        Opening a paper reads its three preallocated blocks and the two small
        selection tabs together; the Sheets quota counts requests, not cells.
        """
        import gspread

        requests = list(requests)
        if not requests:
            return []
        ranges = [a1(tab, first, last) for tab, first, last in requests]
        try:
            answer = self._open().values_batch_get(ranges)
        except gspread.exceptions.APIError as error:
            raise _api_error("Could not read the workbook", error) from error
        out = []
        for (tab, _, _), block in zip(requests, answer.get("valueRanges", [])):
            out.append([as_row(tab, raw) for raw in (block.get("values") or [])])
        return out

    def append_rows(self, tab: str, rows: list[dict[str, Any]]) -> int:
        import gspread

        if not rows:
            return 0
        worksheet = self._worksheet(tab)
        payload = [ordered(tab, row) for row in rows]
        for start in range(0, len(payload), WRITE_CHUNK):
            try:
                worksheet.append_rows(payload[start:start + WRITE_CHUNK],
                                      value_input_option="RAW",
                                      insert_data_option="INSERT_ROWS",
                                      table_range="A1")
            except gspread.exceptions.APIError as error:
                raise _api_error(f"Could not add rows to {tab}", error) from error
        return len(payload)

    def update_rows(self, tab: str, updates) -> None:
        """Several rows in one request, each still a targeted range."""
        import gspread

        updates = list(updates)
        if not updates:
            return
        worksheet = self._worksheet(tab)
        last = column_letter(len(COLUMNS[tab]))
        payload = [{"range": f"A{number}:{last}{number}",
                    "values": [ordered(tab, values)]}
                   for number, values in updates]
        for start in range(0, len(payload), WRITE_CHUNK):
            try:
                worksheet.batch_update(payload[start:start + WRITE_CHUNK],
                                       value_input_option="RAW")
            except gspread.exceptions.APIError as error:
                raise _api_error(f"Could not save to {tab}", error) from error


def workbook_from_env() -> GoogleSheetsWorkbook:
    """The configured round workbook. Raises when there is none — never falls back."""
    gap = configuration_gap()
    if gap:
        raise StorageNotConfigured(gap)
    return GoogleSheetsWorkbook(sheet_id())
