"""Evaluation storage: REVIEWS, RESPONSES, EDGE_RESPONSES.

The design fixes the schema and the write strategy, not the engine:

* three tables, long format, one row per human decision;
* deterministic keys, so a save is always "find my row and update it";
* rows are preallocated per review, so two evaluators never contend for the
  same row and resume is trivial;
* narrow updates only — never rewrite the whole store;
* ``updated_at`` is compared before overwriting, so the same evaluator in two
  tabs gets a conflict warning instead of a silent clobber.

Two backends sit behind these functions, chosen by environment:

* **Google Sheets** when ``GOOGLE_SHEET_ID`` is set — the live store for a
  deployed run, because Streamlit Community Cloud does not guarantee that
  runtime-generated local files persist.
* **SQLite** otherwise — for local development, dry runs and tests. It is not a
  safe live store on Community Cloud.

The UI never knows which is active.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import functools
import pathlib
import sqlite3
import time

import sheets

DB_PATH = pathlib.Path(__file__).resolve().parent / "data" / "evaluations.sqlite"

STATUS_NOT_STARTED = "not_started"
STATUS_IN_PROGRESS = "in_progress"
#: Nothing missing, but still editable. Evaluators asked to be able to revisit
#: earlier papers once several have calibrated their judgment, so completion and
#: final submission are separate steps.
STATUS_COMPLETE = "complete"
STATUS_SUBMITTED = "submitted"
EDITABLE_STATUSES = (STATUS_NOT_STARTED, STATUS_IN_PROGRESS, STATUS_COMPLETE)

#: Mirrors spec.NA_ANSWER / spec.AUTO_NA. Duplicated rather than imported so the
#: storage layer stays independent of the instrument; a test pins them together.
NA_ANSWER = "N/A"
AUTO_NA = "auto_na"

SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id           TEXT PRIMARY KEY,
    -- training | agreement | individual. Each phase carries its own
    -- assignments, completion state and final submission.
    phase_id            TEXT NOT NULL,
    evaluator_id        TEXT NOT NULL,
    evaluator_name      TEXT,
    pair_id             TEXT,
    source_id           TEXT NOT NULL,
    work_id             TEXT,
    assignment_key      TEXT,
    -- Provenance. Stamped when work begins, never at row creation: rows are
    -- preallocated long before anyone opens them, and a reservation may be
    -- activated — changing the configuration — in between. Stamping at creation
    -- would record the configuration the storage was made under rather than the
    -- one the evaluation was performed under. Once written it is never rewritten,
    -- so later configuration changes cannot alter what an existing answer means.
    brain_snapshot_id   TEXT,
    eval_spec_version   TEXT,
    config_version      TEXT,
    split_id            TEXT,
    assignment_state    TEXT,
    -- Where this review's preallocated rows sit in the workbook. Reading one
    -- paper is then one narrow range read instead of a whole-tab download.
    -- Meaningless for SQLite, which has a WHERE clause.
    responses_first_row TEXT,
    responses_last_row  TEXT,
    edges_first_row     TEXT,
    edges_last_row      TEXT,
    pdf_read_confirmed  INTEGER NOT NULL DEFAULT 0,
    status              TEXT NOT NULL DEFAULT 'not_started',
    started_at          TEXT,
    last_saved_at       TEXT,
    submitted_at        TEXT
);

CREATE TABLE IF NOT EXISTS responses (
    response_key    TEXT PRIMARY KEY,
    review_id       TEXT NOT NULL,
    source_id       TEXT NOT NULL,
    object_type     TEXT NOT NULL,
    object_id       TEXT NOT NULL,
    question_key    TEXT NOT NULL,
    criterion_id    TEXT NOT NULL,
    field_subitem   TEXT,
    answer          TEXT,
    comment_evidence TEXT,
    -- Legacy. The `Unclear` flag left the human instrument in v3; the column
    -- stays so exports written under v2 still parse, and is never written to.
    unclear         INTEGER NOT NULL DEFAULT 0,
    -- '' before the item is reached, 'applicable' once the evaluator answers,
    -- 'auto_na' when the application itself determined the item inapplicable.
    -- This is what keeps an inapplicable item distinct from an unanswered one.
    applicability   TEXT NOT NULL DEFAULT '',
    updated_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_responses_review ON responses (review_id);

CREATE TABLE IF NOT EXISTS edge_responses (
    edge_response_key    TEXT PRIMARY KEY,
    review_id            TEXT NOT NULL,
    source_id            TEXT NOT NULL,
    host_claim_id        TEXT NOT NULL,
    edge_key             TEXT NOT NULL,
    edge_from            TEXT,
    edge_to              TEXT,
    other_claim_id       TEXT,
    edge_type            TEXT,
    label_correct        TEXT,
    comment_correct_label TEXT,
    updated_at           TEXT
);
CREATE INDEX IF NOT EXISTS idx_edges_review ON edge_responses (review_id);

-- A phase is finally submitted for an evaluator only when a row exists here.
-- Submission touches many review rows and there is no transaction across them
-- in Sheets, so the marker is written last and retrying a half-finished
-- submission is safe.
CREATE TABLE IF NOT EXISTS phase_submissions (
    submission_key  TEXT PRIMARY KEY,
    evaluator_id    TEXT NOT NULL,
    phase_id        TEXT NOT NULL,
    config_version  TEXT,
    status          TEXT NOT NULL,
    submitted_at    TEXT
);
"""


def now() -> str:
    """Microsecond precision on purpose.

    ``updated_at`` is the conflict token: if the same evaluator edits one answer
    from two tabs, the second write is refused because the stored stamp no
    longer matches the one their session loaded. At second resolution two edits
    within the same second are indistinguishable and the conflict is missed.
    """
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")


@contextlib.contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        # Journal mode is a property of the file, set once in init(). Re-setting
        # it per connection takes a brief exclusive lock, which is precisely the
        # thing that fails when the save queue's worker thread is writing at the
        # same time as the page that queued it.
        conn.execute("PRAGMA busy_timeout=30000")
        yield conn
        conn.commit()
    finally:
        conn.close()


#: Which workbook has been found reachable and correctly shaped, or None.
#: Streamlit re-runs the whole script on every interaction, so without this the
#: readiness check would be repeated on every keystroke of the password field.
#: It records *which* workbook rather than merely that one was checked: point
#: the app at a different sheet and the answer for the old one says nothing.
_READY_FOR: str | None = None


def forget_ready() -> None:
    """Make the next `init()` check the workbook again. For tests and reloads."""
    global _READY_FOR
    _READY_FOR = None


def _workbook_identity(book) -> str:
    return str(getattr(book, "sheet_id", None)
               or getattr(book, "directory", None)
               or id(book))


def init() -> None:
    """Prepare the store. Cheap, and on Sheets it happens once per process.

    It used to call `ensure_tabs()`, which fetches the workbook's metadata once
    per tab and then reads each header: fifteen requests, repeated on every
    Streamlit rerun. Creating tabs and fixing headers is what
    `bootstrap_sheets.py` is for; a running app only needs to know that the
    workbook is there and shaped as expected, which costs two.
    """
    global _READY_FOR
    if using_sheets():
        book = workbook()
        identity = _workbook_identity(book)
        if _READY_FOR != identity:
            book.check_ready()
            _READY_FOR = identity
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with contextlib.closing(sqlite3.connect(DB_PATH, timeout=30)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")     # persistent, set once
    with connect() as conn:
        conn.executescript(SCHEMA)
        _add_missing_columns(conn)


#: Columns added after the first release. A store created by an earlier version
#: is upgraded in place rather than rebuilt, because CREATE TABLE IF NOT EXISTS
#: silently leaves an existing table on the old layout.
ADDED_COLUMNS = {
    "responses": (("applicability", "TEXT NOT NULL DEFAULT ''"),),
    "reviews": (("config_version", "TEXT"), ("assignment_key", "TEXT"),
                ("split_id", "TEXT"), ("assignment_state", "TEXT"),
                ("responses_first_row", "TEXT"), ("responses_last_row", "TEXT"),
                ("edges_first_row", "TEXT"), ("edges_last_row", "TEXT")),
}


def _add_missing_columns(conn) -> None:
    for table, columns in ADDED_COLUMNS.items():
        present = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, declaration in columns:
            if name not in present:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")


# ------------------------------------------------------- deterministic keys
def review_id(phase_id: str, evaluator_id: str, source_id: str) -> str:
    return f"{phase_id}|{evaluator_id}|{source_id}"


def response_key(rid: str, object_type: str, object_id: str, question_key: str) -> str:
    return f"{rid}|{object_type}|{object_id}|{question_key}"


def edge_key_of(edge: dict) -> str:
    """edges.jsonl carries no id, so derive one: type + from + to + grounding."""
    return "|".join([
        edge.get("type", ""), edge.get("from", ""),
        edge.get("to", ""), edge.get("grounding", ""),
    ])


def edge_response_key(rid: str, host_claim_id: str, edge_key: str) -> str:
    return f"{rid}|{host_claim_id}|{edge_key}"


# --------------------------------------------------------------- backend
@functools.lru_cache(maxsize=1)
def workbook() -> sheets.Workbook | None:
    """The live workbook, or None when running on the local SQLite store."""
    return sheets.workbook_from_env()


def using_sheets() -> bool:
    return workbook() is not None


def backend_name() -> str:
    return "google-sheets" if using_sheets() else "sqlite (local/dev)"


def _index(tab: str) -> tuple[list[dict], dict[str, int]]:
    """Whole-tab read. Only for tabs small enough to afford it, or a rebuild."""
    rows = workbook().read_tab(tab)
    return rows, sheets.row_index(rows, tab)


#: key -> sheet row number, per tab. Partial by design: it is filled in as
#: reviews are opened, because reading one review's contiguous block already
#: tells us where every one of its rows lives. Row positions are stable once
#: preallocated — an append never moves an existing row, and nothing deletes one
#: during a round — so an entry can only be missing, never wrong.
_ROW_INDEX: dict[str, dict[str, int]] = {}


def forget_row_index(tab: str | None = None) -> None:
    if tab is None:
        _ROW_INDEX.clear()
    else:
        _ROW_INDEX.pop(tab, None)


def _remember_rows(tab: str, first_row: int, rows: list[dict]) -> None:
    """Index a block just read, using its offset. Costs no extra request.

    This is what removes the last whole-tab read from ordinary use: opening a
    review reads its block, and the block's own row numbers are exactly the index
    its later writes need.
    """
    key_column = sheets.KEY_COLUMN[tab]
    index = _ROW_INDEX.setdefault(tab, {})
    for offset, row in enumerate(rows):
        key = row.get(key_column)
        if key:
            index[key] = first_row + offset


def row_number(tab: str, key: str, *, rebuild: bool = True) -> int | None:
    """Where this key lives.

    A hit is trusted. A miss means either that the key was never preallocated or
    that this session has not read the block it lives in, and only a full read
    can tell those apart — so a miss verifies once, and callers decide what an
    absence means.
    """
    index = _ROW_INDEX.get(tab)
    if index is not None and key in index:
        return index[key]
    if not rebuild:
        return None
    rows, rebuilt = _index(tab)
    _ROW_INDEX[tab] = {**rebuilt, **(index or {})}
    return _ROW_INDEX[tab].get(key)


class StorageIntegrityError(RuntimeError):
    """A write named a row that does not exist.

    During a live round every row has been preallocated, so an unknown key is
    not something to paper over by appending: it means the workbook is not the
    one this configuration was prepared against — a rewritten tab, a wrong sheet
    id, a preallocation that never ran or did not finish. Appending would half-fix
    it and hide the cause, leaving rows outside every review's recorded range.
    """


def _sheet_upsert(tab: str, key: str, values: dict, *,
                  allow_append: bool = False) -> None:
    """Update the row that owns this key.

    ``allow_append`` is for bootstrap, preallocation, migration and local
    development — never for an ordinary evaluation write.
    """
    book = workbook()
    number = row_number(tab, key)
    if number is not None:
        book.update_row(tab, number, values)
        return
    if not allow_append:
        raise StorageIntegrityError(
            f"{tab} has no row for {key!r}. Every row is created in advance by "
            f"tools/preallocate.py, so this means the workbook is not the one "
            f"this configuration was prepared against, or preallocation did not "
            f"finish. Nothing was written."
        )
    book.append_rows(tab, [values])
    forget_row_index(tab)


# -------------------------------------------------------------- REVIEWS
def get_review(phase_id: str, evaluator_id: str, source_id: str) -> dict | None:
    rid = review_id(phase_id, evaluator_id, source_id)
    if using_sheets():
        # Through the cached row: the page asks for this on every rerun, and
        # REVIEWS is re-read only after something writes to it.
        row = _review_row(rid)
        return dict(row) if row else None
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM reviews WHERE review_id=?", (rid,),
        ).fetchone()
    return dict(row) if row else None


def reviews_for(evaluator_id: str, phase_id: str) -> dict[str, dict]:
    if using_sheets():
        rows, _ = _index(sheets.REVIEWS)
        return {r["source_id"]: dict(r) for r in rows
                if r["evaluator_id"] == evaluator_id and r["phase_id"] == phase_id}
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM reviews WHERE evaluator_id=? AND phase_id=?",
            (evaluator_id, phase_id),
        ).fetchall()
    return {r["source_id"]: dict(r) for r in rows}


def all_reviews() -> list[dict]:
    if using_sheets():
        rows, _ = _index(sheets.REVIEWS)
        return [dict(r) for r in rows]
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM reviews ORDER BY evaluator_id, phase_id, source_id"
        ).fetchall()]


#: Written once, when work begins. `start_review` fills any of these that is
#: still blank and never overwrites one that is not.
PROVENANCE = ("brain_snapshot_id", "eval_spec_version", "config_version",
              "split_id", "assignment_state")


def ensure_review(*, phase_id, evaluator_id, evaluator_name, pair_id, source_id,
                  work_id, brain_snapshot_id="", eval_spec_version="",
                  config_version="", assignment_key: str = "") -> str:
    """Create the row if it is absent. Identity only — provenance comes later.

    Preallocation calls this for every assignment, reservations included, long
    before anyone opens anything. The provenance arguments are accepted for
    callers that create a row and immediately start it, but a row created here
    and started later is stamped by ``start_review`` with the configuration in
    force at that moment.
    """
    rid = review_id(phase_id, evaluator_id, source_id)
    assignment_key = assignment_key or f"{phase_id}|{evaluator_id}|{source_id}"
    if using_sheets():
        _, index = _index(sheets.REVIEWS)
        if rid not in index:
            forget_reviews()
            workbook().append_rows(sheets.REVIEWS, [{
                "review_id": rid, "phase_id": phase_id, "evaluator_id": evaluator_id,
                "evaluator_name": evaluator_name, "pair_id": pair_id,
                "source_id": source_id, "work_id": work_id,
                "assignment_key": assignment_key,
                "brain_snapshot_id": brain_snapshot_id,
                "eval_spec_version": eval_spec_version,
                "config_version": config_version,
                "pdf_read_confirmed": 0, "status": STATUS_NOT_STARTED,
            }])
        return rid
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO reviews (review_id, phase_id, evaluator_id, evaluator_name,
                                 pair_id, source_id, work_id, assignment_key,
                                 brain_snapshot_id, eval_spec_version,
                                 config_version, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT (review_id) DO NOTHING
            """,
            (rid, phase_id, evaluator_id, evaluator_name, pair_id, source_id, work_id,
             assignment_key, brain_snapshot_id, eval_spec_version, config_version,
             STATUS_NOT_STARTED),
        )
    return rid


#: `last_saved_at` says when the evaluator was last working, which is worth a
#: second's resolution, not a workbook write per keystroke. Writing it on every
#: answer doubled the request count for no information anyone reads.
TOUCH_INTERVAL = 60.0
_TOUCHED: dict[str, float] = {}


def touch_review(rid: str, *, force: bool = False) -> None:
    last = _TOUCHED.get(rid, 0.0)
    if not force and time.monotonic() - last < TOUCH_INTERVAL:
        return
    _TOUCHED[rid] = time.monotonic()
    if using_sheets():
        _set_review_fields(rid)
        return
    with connect() as conn:
        conn.execute("UPDATE reviews SET last_saved_at=? WHERE review_id=?",
                     (now(), rid))


def record_activity(rid: str) -> None:
    """Note that the evaluator changed something.

    Two things follow from an edit, and they have different urgencies.

    ``complete`` is a claim about the current answers, so any edit invalidates it
    and the paper returns to ``in_progress`` **immediately**. It is not worth
    working out whether this particular edit is the one that broke completeness:
    a conditional follow-up can become required as a side effect of its parent
    changing, and an optimistic "still complete" is a lie the evaluator would
    only discover at submission.

    ``last_saved_at`` is merely when they were last working, and is throttled.
    """
    status = current_status(rid)
    if status == STATUS_COMPLETE:
        unmark_complete(rid)
        _TOUCHED[rid] = time.monotonic()
        return
    touch_review(rid)


def current_status(rid: str) -> str:
    """This review's status, from the cached row where there is one."""
    if using_sheets():
        row = _review_row(rid)
        return str((row or {}).get("status") or "")
    with connect() as conn:
        row = conn.execute(
            "SELECT status FROM reviews WHERE review_id=?", (rid,)).fetchone()
    return str(row["status"]) if row else ""


def _set_review_fields(rid: str, *, touch: bool = True, **fields) -> None:
    """REVIEWS is small — one row per evaluator per paper — so a read is cheap.

    ``touch=False`` writes the fields without moving ``last_saved_at``. That
    matters: preallocation records each review's row ranges, and stamping the
    save time while doing so would make every preallocated review look like
    work in progress — locking the whole configuration before anyone had opened
    the application.
    """
    rows, index = _index(sheets.REVIEWS)
    _ROW_INDEX[sheets.REVIEWS] = index
    row = next((r for r in rows if r["review_id"] == rid), None)
    if row is None:
        return
    updated = dict(row)
    updated.update(fields)
    if touch:
        updated["last_saved_at"] = now()
    workbook().update_row(sheets.REVIEWS, index[rid], updated)
    forget_reviews()


def start_review(rid: str, read_confirmed: bool, **provenance) -> None:
    """Begin work, stamping provenance that is still blank.

    This is the moment a preallocated row becomes a real evaluation, so it is the
    moment its provenance is fixed. Values already recorded are never rewritten:
    a later configuration change must not alter what an existing answer means.
    """
    unknown = set(provenance) - set(PROVENANCE)
    if unknown:
        raise TypeError(f"not provenance fields: {sorted(unknown)}")

    def stamped(row: dict) -> dict:
        return {name: (row.get(name) or provenance.get(name, "") or "")
                for name in PROVENANCE}

    if using_sheets():
        rows, index = _index(sheets.REVIEWS)
        row = next((r for r in rows if r["review_id"] == rid), None)
        if row is not None:
            updated = dict(row)
            updated.update(stamped(row))
            updated["pdf_read_confirmed"] = int(read_confirmed)
            if updated.get("status") != STATUS_SUBMITTED:
                updated["status"] = STATUS_IN_PROGRESS
            updated["started_at"] = updated.get("started_at") or now()
            updated["last_saved_at"] = now()
            workbook().update_row(sheets.REVIEWS, index[rid], updated)
        forget_reviews()
        return
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM reviews WHERE review_id=?", (rid,)).fetchone()
        if row is None:
            return
        fields = stamped(dict(row))
        assignments = ", ".join(f"{name} = ?" for name in PROVENANCE)
        conn.execute(
            f"""
            UPDATE reviews
               SET {assignments},
                   pdf_read_confirmed = ?,
                   status = CASE WHEN status = 'submitted' THEN status ELSE 'in_progress' END,
                   started_at = COALESCE(started_at, ?),
                   last_saved_at = ?
             WHERE review_id = ?
            """,
            (*[fields[name] for name in PROVENANCE],
             int(read_confirmed), now(), now(), rid),
        )


def submit_review(rid: str) -> None:
    if using_sheets():
        _set_review_fields(rid, status=STATUS_SUBMITTED, submitted_at=now())
        return
    stamp = now()
    with connect() as conn:
        conn.execute(
            "UPDATE reviews SET status=?, submitted_at=?, last_saved_at=? WHERE review_id=?",
            (STATUS_SUBMITTED, stamp, stamp, rid),
        )


def mark_complete(rid: str) -> None:
    """Nothing missing; the paper stays editable until final submission."""
    if using_sheets():
        _set_review_fields(rid, status=STATUS_COMPLETE)
        return
    with connect() as conn:
        conn.execute(
            "UPDATE reviews SET status=?, last_saved_at=? WHERE review_id=? AND status<>?",
            (STATUS_COMPLETE, now(), rid, STATUS_SUBMITTED),
        )


def unmark_complete(rid: str) -> None:
    """The evaluator reopened a completed paper to change an answer."""
    if using_sheets():
        _set_review_fields(rid, status=STATUS_IN_PROGRESS)
        return
    with connect() as conn:
        conn.execute(
            "UPDATE reviews SET status=?, last_saved_at=? WHERE review_id=? AND status=?",
            (STATUS_IN_PROGRESS, now(), rid, STATUS_COMPLETE),
        )


def submit_many(review_ids) -> int:
    """Final batch submission: lock every completed paper together."""
    count = 0
    for rid in review_ids:
        submit_review(rid)
        count += 1
    return count


def reopen_review(rid: str) -> bool:
    """Admin reopens one submitted paper, which un-submits its whole phase.

    A phase submission is a claim about a set: "every paper I was assigned in
    this phase is finished and locked." Reopening one of them makes that claim
    false, so the marker is retracted and the evaluator submits the phase again
    once they are done. Returns whether a marker was retracted.
    """
    phase_id, evaluator_id, _ = rid.split("|", 2)
    if using_sheets():
        _set_review_fields(rid, status=STATUS_IN_PROGRESS, submitted_at="")
    else:
        with connect() as conn:
            conn.execute(
                "UPDATE reviews SET status=?, submitted_at=NULL, last_saved_at=?"
                " WHERE review_id=?",
                (STATUS_IN_PROGRESS, now(), rid),
            )
    return retract_phase_submission(phase_id, evaluator_id)


# ------------------------------------------------------------ RESPONSES
def _recorded_range(rid: str, prefix: str) -> tuple[int, int] | None:
    """The block preallocation gave this review, if it recorded one."""
    review = _review_row(rid)
    if review is None:
        return None
    first = str(review.get(f"{prefix}_first_row") or "").strip()
    last = str(review.get(f"{prefix}_last_row") or "").strip()
    if first.isdigit() and last.isdigit():
        return int(first), int(last)
    return None


@functools.lru_cache(maxsize=256)
def _cached_review_row(rid: str, generation: int) -> dict | None:
    rows, index = _index(sheets.REVIEWS)
    _ROW_INDEX[sheets.REVIEWS] = index
    return next((dict(r) for r in rows if r["review_id"] == rid), None)


_REVIEW_GENERATION = 0


def _review_row(rid: str) -> dict | None:
    return _cached_review_row(rid, _REVIEW_GENERATION)


def forget_reviews() -> None:
    """Called after any REVIEWS write, so the cached row cannot go stale."""
    global _REVIEW_GENERATION
    _REVIEW_GENERATION += 1


def load_responses(rid: str) -> dict[str, dict]:
    if using_sheets():
        block = _recorded_range(rid, "responses")
        if block is not None:
            rows = workbook().read_range(sheets.RESPONSES, *block)
            _remember_rows(sheets.RESPONSES, block[0], rows)
        else:
            rows, index = _index(sheets.RESPONSES)
            _ROW_INDEX[sheets.RESPONSES] = index
        return {f"{r['question_key']}|{r['object_id']}": dict(r)
                for r in rows if r["review_id"] == rid}
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM responses WHERE review_id=?", (rid,)
        ).fetchall()
    out = {}
    for row in rows:
        record = dict(row)
        out[record["question_key"] + "|" + record["object_id"]] = record
    return out


def load_edge_responses(rid: str) -> dict[str, dict]:
    if using_sheets():
        block = _recorded_range(rid, "edges")
        if block is not None:
            rows = workbook().read_range(sheets.EDGE_RESPONSES, *block)
            _remember_rows(sheets.EDGE_RESPONSES, block[0], rows)
        else:
            rows, index = _index(sheets.EDGE_RESPONSES)
            _ROW_INDEX[sheets.EDGE_RESPONSES] = index
        return {r["edge_key"]: dict(r) for r in rows if r["review_id"] == rid}
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM edge_responses WHERE review_id=?", (rid,)
        ).fetchall()
    return {r["edge_key"]: dict(r) for r in rows}


class SaveConflict(Exception):
    """The row changed since this session loaded it (same evaluator, two tabs)."""


def _response_row(rid: str, key: str, *, object_type, object_id, question_key,
                  criterion_id, field_subitem, answer, comment, applicability,
                  source_id, stamp) -> dict:
    """The complete row, built from what the caller already knows.

    Deliberately reads nothing first. Every column is supplied by the caller or
    derived from the key, so an ordinary save is a single targeted write rather
    than a read of the whole tab followed by a merge.
    """
    return {
        "response_key": key, "review_id": rid, "source_id": source_id,
        "object_type": object_type, "object_id": object_id,
        "question_key": question_key, "criterion_id": criterion_id,
        "field_subitem": field_subitem, "answer": answer,
        "comment_evidence": comment, "unclear": 0,
        "applicability": applicability, "updated_at": stamp,
    }


def _check_conflict(key: str, expected_updated_at: str) -> None:
    """Best-effort two-tab detection: one targeted read of the row we own."""
    number = row_number(sheets.RESPONSES, key)
    if number is None:
        return
    rows = workbook().read_range(sheets.RESPONSES, number, number)
    if not rows:
        return
    stored = rows[0].get("updated_at") or ""
    if stored and stored != expected_updated_at:
        raise SaveConflict(key)


def _check_conflicts(expectations: dict[str, str], updates) -> None:
    """The same check across a batch, in one read.

    The batch's rows lie inside one review's preallocated block, so the span from
    its lowest to its highest row is a single range — one request whatever the
    batch's size or spread. Batching is therefore what keeps conflict detection
    affordable: without it each edit would cost its own read.
    """
    numbers = [number for number, _ in updates]
    first, last = min(numbers), max(numbers)
    rows = workbook().read_range(sheets.RESPONSES, first, last)
    stored = {row["response_key"]: (row.get("updated_at") or "")
              for row in rows if row.get("response_key")}
    conflicted = [key for key, expected in expectations.items()
                  if stored.get(key) and stored[key] != expected]
    if conflicted:
        raise SaveConflict(", ".join(sorted(conflicted)))


def save_responses(records: list[dict]) -> list[str]:
    """Several answers in one request. Same semantics, fewer round trips.

    Conflict checking survives batching. The rows all belong to one review, so
    they sit inside one preallocated block: their stored timestamps come back in
    a single range read spanning the batch, rather than one read per answer.
    """
    if not records:
        return []
    if not using_sheets():
        return [save_response(**record) for record in records]

    allow_append = any(r.pop("allow_append", False) for r in records)
    updates, appends, missing, stamps = [], [], [], []
    expectations: dict[str, str] = {}
    for record in records:
        stamp = record.get("stamp") or now()
        stamps.append(stamp)
        expected = record.get("expected_updated_at")
        key = response_key(record["rid"], record["object_type"],
                           record["object_id"], record["question_key"])
        if expected is not None:
            expectations[key] = expected
        row = _response_row(record["rid"], key, stamp=stamp, **{
            name: record[name] for name in
            ("object_type", "object_id", "question_key", "criterion_id",
             "field_subitem", "answer", "comment", "applicability", "source_id")})
        number = row_number(sheets.RESPONSES, key)
        if number is not None:
            updates.append((number, row))
        elif allow_append:
            appends.append(row)
        else:
            missing.append(key)
    if missing:
        raise StorageIntegrityError(
            f"{sheets.RESPONSES} has no row for {len(missing)} keys, first "
            f"{missing[0]!r}. Nothing was written."
        )
    expectations = {k: v for k, v in expectations.items() if v}
    if expectations and updates:
        _check_conflicts(expectations, updates)
    workbook().update_rows(sheets.RESPONSES, updates)
    if appends:
        workbook().append_rows(sheets.RESPONSES, appends)
        forget_row_index(sheets.RESPONSES)
    for rid in {r["rid"] for r in records}:
        record_activity(rid)
    return stamps


def save_response(rid: str, *, object_type: str, object_id: str, question_key: str,
                  criterion_id: str, field_subitem: str, answer, comment,
                  applicability: str = "", source_id: str = "",
                  expected_updated_at: str | None = None,
                  allow_append: bool = False) -> str:
    key = response_key(rid, object_type, object_id, question_key)
    stamp = now()
    if using_sheets():
        row = _response_row(rid, key, object_type=object_type, object_id=object_id,
                            question_key=question_key, criterion_id=criterion_id,
                            field_subitem=field_subitem, answer=answer,
                            comment=comment, applicability=applicability,
                            source_id=source_id, stamp=stamp)
        # Only where there is something to conflict with. A row nobody has
        # written yet has no stored stamp to compare against, so the read would
        # tell us nothing — and first answers are most of the writes in a pass.
        if expected_updated_at:
            _check_conflict(key, expected_updated_at)
        _sheet_upsert(sheets.RESPONSES, key, row, allow_append=allow_append)
        record_activity(rid)
        return stamp
    with connect() as conn:
        row = conn.execute(
            "SELECT updated_at FROM responses WHERE response_key=?", (key,)
        ).fetchone()
        if (row and expected_updated_at is not None
                and row["updated_at"] and row["updated_at"] != expected_updated_at):
            raise SaveConflict(key)
        conn.execute(
            """
            INSERT INTO responses (response_key, review_id, source_id, object_type,
                                   object_id, question_key, criterion_id, field_subitem,
                                   answer, comment_evidence, unclear, applicability,
                                   updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT (response_key) DO UPDATE SET
                answer = excluded.answer,
                comment_evidence = excluded.comment_evidence,
                applicability = excluded.applicability,
                updated_at = excluded.updated_at
            """,
            (key, rid, source_id, object_type, object_id, question_key, criterion_id,
             field_subitem, answer, comment, 0, applicability, stamp),
        )
        conn.execute("UPDATE reviews SET last_saved_at=? WHERE review_id=?",
                     (stamp, rid))
    record_activity(rid)
    return stamp


def save_edge_response(rid: str, *, host_claim_id: str, edge_key: str, edge_from: str,
                       edge_to: str, other_claim_id: str, edge_type: str,
                       label_correct, comment, source_id: str = "",
                       allow_append: bool = False) -> str:
    key = edge_response_key(rid, host_claim_id, edge_key)
    stamp = now()
    if using_sheets():
        _sheet_upsert(sheets.EDGE_RESPONSES, key, {
            "edge_response_key": key, "review_id": rid,
            "source_id": source_id, "host_claim_id": host_claim_id,
            "edge_key": edge_key, "edge_from": edge_from, "edge_to": edge_to,
            "other_claim_id": other_claim_id, "edge_type": edge_type,
            "label_correct": label_correct, "comment_correct_label": comment,
            "updated_at": stamp,
        }, allow_append=allow_append)
        record_activity(rid)
        return stamp
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO edge_responses (edge_response_key, review_id, source_id,
                                        host_claim_id, edge_key, edge_from, edge_to,
                                        other_claim_id, edge_type, label_correct,
                                        comment_correct_label, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT (edge_response_key) DO UPDATE SET
                label_correct = excluded.label_correct,
                comment_correct_label = excluded.comment_correct_label,
                updated_at = excluded.updated_at
            """,
            (key, rid, source_id, host_claim_id, edge_key, edge_from, edge_to,
             other_claim_id, edge_type, label_correct, comment, stamp),
        )
        conn.execute("UPDATE reviews SET last_saved_at=? WHERE review_id=?", (stamp, rid))
    record_activity(rid)
    return stamp


# ---------------------------------------------------------- preallocation
def _expected(expected_responses):
    """Normalise preallocation rows to (object_type, object_id, question, applicability).

    Callers may pass a 3-tuple for an ordinary question, or a 4-tuple whose last
    element is the applicability an item is known to have before anyone opens the
    paper — ``auto_na`` for a criterion the Brain record already settles.
    """
    for row in expected_responses:
        if len(row) == 4:
            yield row
        else:
            object_type, object_id, question = row
            yield object_type, object_id, question, ""


def _preallocate_sheets(rid, source_id, expected_responses, expected_edges) -> int:
    """Append every row this review will need, once, in two batched writes.

    The block is contiguous, and its first and last row numbers are recorded on
    the review. Opening the paper afterwards is one range read of a few hundred
    cells rather than a download of a tab holding tens of thousands of rows.
    """
    book = workbook()
    _, response_index = _index(sheets.RESPONSES)
    _, edge_index = _index(sheets.EDGE_RESPONSES)
    _ROW_INDEX[sheets.RESPONSES] = response_index
    _ROW_INDEX[sheets.EDGE_RESPONSES] = edge_index
    first_response = len(response_index) + 2
    first_edge = len(edge_index) + 2

    new_responses = []
    for object_type, object_id, question, applicability in _expected(expected_responses):
        key = response_key(rid, object_type, object_id, question.question_key)
        if key in response_index:
            continue
        row = {
            "response_key": key, "review_id": rid, "source_id": source_id,
            "object_type": object_type, "object_id": object_id,
            "question_key": question.question_key,
            "criterion_id": question.criterion_id,
            "field_subitem": question.field_subitem,
            "applicability": applicability,
        }
        if applicability == AUTO_NA:
            row["answer"] = NA_ANSWER
            row["updated_at"] = now()
        new_responses.append(row)

    new_edges = []
    for host_claim_id, edge in expected_edges:
        ekey = edge_key_of(edge)
        key = edge_response_key(rid, host_claim_id, ekey)
        if key in edge_index:
            continue
        other = edge.get("other_claim_id") or (
            edge.get("to") if edge.get("from") == host_claim_id else edge.get("from")
        )
        new_edges.append({
            "edge_response_key": key, "review_id": rid, "source_id": source_id,
            "host_claim_id": host_claim_id, "edge_key": ekey,
            "edge_from": edge.get("from"), "edge_to": edge.get("to"),
            "other_claim_id": other, "edge_type": edge.get("type"),
        })

    created = book.append_rows(sheets.RESPONSES, new_responses)
    created += book.append_rows(sheets.EDGE_RESPONSES, new_edges)

    if new_responses or new_edges:
        forget_row_index(sheets.RESPONSES)
        forget_row_index(sheets.EDGE_RESPONSES)
    ranges = {}
    if new_responses:
        ranges["responses_first_row"] = str(first_response)
        ranges["responses_last_row"] = str(first_response + len(new_responses) - 1)
    if new_edges:
        ranges["edges_first_row"] = str(first_edge)
        ranges["edges_last_row"] = str(first_edge + len(new_edges) - 1)
    if ranges:
        # touch=False: preallocation is not evaluator activity.
        _set_review_fields(rid, touch=False, **ranges)
    return created


def is_preallocated(rid: str) -> bool:
    """Whether this review already has its block, so the app need not build one.

    True once `tools/preallocate.py` has run. The app keeps a lazy fallback for
    local development, where nobody has run it.
    """
    if not using_sheets():
        with connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM responses WHERE review_id=?", (rid,)
            ).fetchone()
        return bool(row and row["n"])
    return _recorded_range(rid, "responses") is not None


def preallocate_bulk(entries) -> dict:
    """Preallocate many reviews in a handful of requests.

    One review at a time costs a read and a write per review for the REVIEWS row,
    twice over — around 330 requests for this configuration, against a limit of
    sixty writes a minute. Done together it is one read of REVIEWS, one append of
    the missing review rows, one append per data tab (chunked), and one batched
    update carrying every review's row range.

    ``entries``: dicts with the review fields plus ``items`` and ``edges``.
    Returns a summary. Appending is expected here — this is what creates the rows
    everything else then refuses to create.
    """
    if not using_sheets():
        made = 0
        for entry in entries:
            rid = ensure_review(**{k: entry[k] for k in (
                "phase_id", "evaluator_id", "evaluator_name", "pair_id",
                "source_id", "work_id", "assignment_key")})
            made += preallocate(rid, entry["source_id"], entry["items"], entry["edges"])
        return {"reviews": len(entries), "rows": made}

    book = workbook()
    review_rows, review_index = _index(sheets.REVIEWS)
    _ROW_INDEX[sheets.REVIEWS] = review_index

    new_reviews, numbers = [], {}
    next_review = len(review_rows) + 2
    for entry in entries:
        rid = review_id(entry["phase_id"], entry["evaluator_id"], entry["source_id"])
        entry["review_id"] = rid
        if rid in review_index:
            numbers[rid] = review_index[rid]
            continue
        numbers[rid] = next_review + len(new_reviews)
        new_reviews.append({
            "review_id": rid, "phase_id": entry["phase_id"],
            "evaluator_id": entry["evaluator_id"],
            "evaluator_name": entry["evaluator_name"], "pair_id": entry["pair_id"],
            "source_id": entry["source_id"], "work_id": entry["work_id"],
            "assignment_key": entry["assignment_key"],
            "pdf_read_confirmed": 0, "status": STATUS_NOT_STARTED,
        })
    if new_reviews:
        book.append_rows(sheets.REVIEWS, new_reviews)

    existing_responses = len(_index(sheets.RESPONSES)[1])
    existing_edges = len(_index(sheets.EDGE_RESPONSES)[1])
    response_rows, edge_rows, ranges = [], [], {}
    first_response = existing_responses + 2
    first_edge = existing_edges + 2

    for entry in entries:
        rid = entry["review_id"]
        start_r = first_response + len(response_rows)
        for object_type, object_id, question, applicability in _expected(entry["items"]):
            key = response_key(rid, object_type, object_id, question.question_key)
            row = {
                "response_key": key, "review_id": rid, "source_id": entry["source_id"],
                "object_type": object_type, "object_id": object_id,
                "question_key": question.question_key,
                "criterion_id": question.criterion_id,
                "field_subitem": question.field_subitem,
                "applicability": applicability,
            }
            if applicability == AUTO_NA:
                row["answer"] = NA_ANSWER
                row["updated_at"] = now()
            response_rows.append(row)
        start_e = first_edge + len(edge_rows)
        for host_claim_id, edge in entry["edges"]:
            ekey = edge_key_of(edge)
            other = edge.get("other_claim_id") or (
                edge.get("to") if edge.get("from") == host_claim_id else edge.get("from"))
            edge_rows.append({
                "edge_response_key": edge_response_key(rid, host_claim_id, ekey),
                "review_id": rid, "source_id": entry["source_id"],
                "host_claim_id": host_claim_id, "edge_key": ekey,
                "edge_from": edge.get("from"), "edge_to": edge.get("to"),
                "other_claim_id": other, "edge_type": edge.get("type"),
            })
        block = {}
        if first_response + len(response_rows) > start_r:
            block["responses_first_row"] = str(start_r)
            block["responses_last_row"] = str(first_response + len(response_rows) - 1)
        if first_edge + len(edge_rows) > start_e:
            block["edges_first_row"] = str(start_e)
            block["edges_last_row"] = str(first_edge + len(edge_rows) - 1)
        if block:
            ranges[rid] = block

    book.append_rows(sheets.RESPONSES, response_rows)
    book.append_rows(sheets.EDGE_RESPONSES, edge_rows)
    forget_row_index(sheets.RESPONSES)
    forget_row_index(sheets.EDGE_RESPONSES)

    # One batched write for every review's range. touch=False by construction:
    # preallocation is not evaluator activity.
    by_id = {r["review_id"]: r for r in review_rows}
    by_id.update({r["review_id"]: r for r in new_reviews})
    updates = [(numbers[rid], {**by_id.get(rid, {}), "review_id": rid, **block})
               for rid, block in ranges.items()]
    book.update_rows(sheets.REVIEWS, updates)
    forget_reviews()

    return {"reviews": len(entries), "new_reviews": len(new_reviews),
            "responses": len(response_rows), "edges": len(edge_rows),
            "rows": len(new_reviews) + len(response_rows) + len(edge_rows)}


def preallocate(rid: str, source_id: str, expected_responses, expected_edges) -> int:
    """Create every row this review will need, empty.

    ``expected_responses``: (object_type, object_id, question[, applicability]).
    ``expected_edges``: (host_claim_id, edge) tuples.

    An item marked ``auto_na`` is written with its answer already set. Waiting for
    the evaluator to render the section would leave a paper they submitted without
    opening that section exporting a blank where the criterion is in fact
    inapplicable — which is exactly the distinction the column exists to record.
    """
    created = 0
    if using_sheets():
        return _preallocate_sheets(rid, source_id, expected_responses, expected_edges)
    with connect() as conn:
        for object_type, object_id, question, applicability in _expected(expected_responses):
            key = response_key(rid, object_type, object_id, question.question_key)
            answer = NA_ANSWER if applicability == AUTO_NA else None
            stamp = now() if applicability == AUTO_NA else None
            cur = conn.execute(
                """
                INSERT INTO responses (response_key, review_id, source_id, object_type,
                                       object_id, question_key, criterion_id, field_subitem,
                                       answer, applicability, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT (response_key) DO NOTHING
                """,
                (key, rid, source_id, object_type, object_id, question.question_key,
                 question.criterion_id, question.field_subitem, answer,
                 applicability, stamp),
            )
            created += cur.rowcount if cur.rowcount > 0 else 0
        for host_claim_id, edge in expected_edges:
            ekey = edge_key_of(edge)
            key = edge_response_key(rid, host_claim_id, ekey)
            other = edge.get("other_claim_id") or (
                edge.get("to") if edge.get("from") == host_claim_id else edge.get("from")
            )
            cur = conn.execute(
                """
                INSERT INTO edge_responses (edge_response_key, review_id, source_id,
                                            host_claim_id, edge_key, edge_from, edge_to,
                                            other_claim_id, edge_type)
                VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT (edge_response_key) DO NOTHING
                """,
                (key, rid, source_id, host_claim_id, ekey, edge.get("from"),
                 edge.get("to"), other, edge.get("type")),
            )
            created += cur.rowcount if cur.rowcount > 0 else 0
    return created


# ---------------------------------------------------------------- exports
EXPORTABLE = ("reviews", "responses", "edge_responses", "phase_submissions")


SUBMITTED, RETRACTED = "submitted", "retracted"


def submission_key(phase_id: str, evaluator_id: str) -> str:
    return f"{phase_id}|{evaluator_id}"


def record_phase_submission(phase_id: str, evaluator_id: str,
                            config_version: str = "") -> str:
    """The marker that makes a phase finally submitted. Written last, on purpose.

    Marking the individual reviews takes many writes with no transaction around
    them. If that is interrupted, the phase is *not* submitted — no marker — and
    the evaluator can simply submit again, because submitting an already
    submitted review changes nothing.
    """
    key = submission_key(phase_id, evaluator_id)
    row = {
        "submission_key": key, "evaluator_id": evaluator_id, "phase_id": phase_id,
        "config_version": config_version, "status": SUBMITTED,
        "submitted_at": now(),
    }
    if using_sheets():
        rows, index = _index(sheets.PHASE_SUBMISSIONS)
        if key in index:
            workbook().update_row(sheets.PHASE_SUBMISSIONS, index[key], row)
        else:
            workbook().append_rows(sheets.PHASE_SUBMISSIONS, [row])
        forget_row_index(sheets.PHASE_SUBMISSIONS)
        return key
    with connect() as conn:
        conn.execute(
            "INSERT INTO phase_submissions (submission_key, evaluator_id, phase_id,"
            " config_version, status, submitted_at) VALUES (?,?,?,?,?,?)"
            " ON CONFLICT(submission_key) DO UPDATE SET"
            " config_version=excluded.config_version, status=excluded.status,"
            " submitted_at=excluded.submitted_at",
            (key, evaluator_id, phase_id, config_version, SUBMITTED, row["submitted_at"]),
        )
    return key


def retract_phase_submission(phase_id: str, evaluator_id: str) -> bool:
    """Reopening submitted work un-submits the phase it belongs to.

    The row is kept and marked ``retracted`` rather than deleted: that a phase
    was once submitted and then reopened is part of what happened, and an export
    that quietly loses it would misdescribe the run.
    """
    key = submission_key(phase_id, evaluator_id)
    if using_sheets():
        rows, index = _index(sheets.PHASE_SUBMISSIONS)
        if key not in index:
            return False
        row = dict(next(r for r in rows if r["submission_key"] == key))
        if row.get("status") != SUBMITTED:
            return False
        row["status"] = RETRACTED
        workbook().update_row(sheets.PHASE_SUBMISSIONS, index[key], row)
        forget_row_index(sheets.PHASE_SUBMISSIONS)
        return True
    with connect() as conn:
        changed = conn.execute(
            "UPDATE phase_submissions SET status=? WHERE submission_key=? AND status=?",
            (RETRACTED, key, SUBMITTED),
        ).rowcount
    return bool(changed)


def phase_submission(phase_id: str, evaluator_id: str) -> dict | None:
    key = submission_key(phase_id, evaluator_id)
    return next((r for r in all_phase_submissions()
                 if r.get("submission_key") == key), None)


def phase_submitted(phase_id: str, evaluator_id: str) -> bool:
    """The one question the rest of the app asks. The marker is the answer."""
    row = phase_submission(phase_id, evaluator_id)
    return bool(row and row.get("status") == SUBMITTED)


def all_phase_submissions() -> list[dict]:
    if using_sheets():
        rows, _ = _index(sheets.PHASE_SUBMISSIONS)
        return [dict(r) for r in rows]
    with connect() as conn:
        return [dict(r) for r in
                conn.execute("SELECT * FROM phase_submissions").fetchall()]


def export(table: str) -> list[dict]:
    if using_sheets():
        tab = {"reviews": sheets.REVIEWS, "responses": sheets.RESPONSES,
               "edge_responses": sheets.EDGE_RESPONSES,
               "phase_submissions": sheets.PHASE_SUBMISSIONS}[table]
        rows, _ = _index(tab)
        return [dict(r) for r in rows]
    if table not in EXPORTABLE:
        raise ValueError(table)
    with connect() as conn:
        return [dict(r) for r in conn.execute(f"SELECT * FROM {table}").fetchall()]
