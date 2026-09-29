"""Evaluation storage over the round workbook — the only persistent store.

* deterministic keys, so a save is always "find my row and update it";
* preallocated blocks per review, so evaluators never contend for a row, a
  paper opens with one batched read, and resume is trivial;
* narrow updates only — never rewrite a tab;
* ``updated_at`` is compared before overwriting, so the same evaluator in two
  tabs gets a conflict instead of a silent clobber;
* the variable-length tabs (missing and proposed Concepts, restatement
  groups) grow by idempotent upserts, and duplicate keys are collapsed on load.

The UI never talks to the workbook directly; everything goes through here.
"""
from __future__ import annotations

import collections
import dataclasses
import datetime as dt
import functools
import hashlib
import time

import sheets

STATUS_NOT_STARTED = "not_started"
STATUS_IN_PROGRESS = "in_progress"
#: Nothing missing, but still editable until the phase is finally submitted.
STATUS_COMPLETE = "complete"
STATUS_SUBMITTED = "submitted"
EDITABLE_STATUSES = (STATUS_NOT_STARTED, STATUS_IN_PROGRESS, STATUS_COMPLETE)

TRUE, FALSE = "TRUE", "FALSE"


def now() -> str:
    """Microsecond precision: ``updated_at`` is the conflict token, and two edits
    within one second must still be distinguishable."""
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")


# ------------------------------------------------------------ the workbook
_BOOK = None


def use_workbook(book) -> None:
    """Point the store at a workbook object (tests use an in-memory one)."""
    global _BOOK, _READY_FOR
    _BOOK = book
    _READY_FOR = None
    forget_all()


def workbook():
    """The round workbook. Raises `StorageNotConfigured` when there is none."""
    global _BOOK
    if _BOOK is None:
        _BOOK = sheets.workbook_from_env()
    return _BOOK


class StorageIntegrityError(RuntimeError):
    """A write named a row that does not exist.

    Every block row is created by bootstrap, so an unknown key means the
    workbook is not the one this configuration was prepared against. Appending
    would hide the cause; nothing is written instead.
    """


class RoundMismatch(RuntimeError):
    """The workbook holds a different round, instrument or Brain snapshot."""


class SaveConflict(Exception):
    """The row changed since this session loaded it (same evaluator, two tabs)."""


# --------------------------------------------------------------- readiness
_READY_FOR: str | None = None


def forget_ready() -> None:
    global _READY_FOR
    _READY_FOR = None


def check_ready() -> None:
    """Is the workbook reachable, complete and correctly shaped? Once per process.

    Two requests: the tab listing and one batched read of every header.
    """
    global _READY_FOR
    book = workbook()
    identity = str(getattr(book, "sheet_id", None) or id(book))
    if _READY_FOR == identity:
        return
    present = set(book.tab_titles())
    missing = [tab for tab in sheets.ALL_TABS if tab not in present]
    if missing:
        raise sheets.StorageError(
            f"The workbook is missing {', '.join(missing)}. It has not been "
            f"initialised for a round: run `tools/bootstrap_round.py` against it. "
            f"Nothing was created or changed.")
    found = book.headers(sheets.ALL_TABS)
    wrong = [tab for tab in sheets.ALL_TABS
             if found.get(tab) != list(sheets.COLUMNS[tab])]
    if wrong:
        raise sheets.StorageError(
            f"These tabs do not have the headers this version expects: "
            f"{', '.join(wrong)}. The workbook was initialised by a different "
            f"version of the application. Nothing was changed.")
    _READY_FOR = identity


@functools.lru_cache(maxsize=1)
def _round_metadata(generation: int) -> dict[str, str]:
    rows = workbook().read_tab(sheets.ROUND)
    return {r["key"]: r["value"] for r in rows if r.get("key")}


def round_metadata() -> dict[str, str]:
    """ROUND as a mapping: what this workbook says the round is."""
    return _round_metadata(_GENERATION["round"])


# --------------------------------------------------------------- identity
def review_id(round_id: str, phase_id: str, evaluator_id: str, source_id: str) -> str:
    return f"{round_id}|{phase_id}|{evaluator_id}|{source_id}"


def response_key(rid: str, object_type: str, object_id: str, question_key: str) -> str:
    return f"{rid}|{object_type}|{object_id}|{question_key}"


def concept_response_key(rid: str, claim_id: str, concept_id: str,
                         question_key: str) -> str:
    return f"{rid}|{claim_id}|{concept_id}|{question_key}"


def relation_response_key(rid: str, relation_key: str) -> str:
    return f"{rid}|{relation_key}"


def selection_key(rid: str, claim_id: str, concept_id: str) -> str:
    return f"{rid}|{claim_id}|{concept_id}"


def proposal_key(rid: str, claim_id: str, proposal_id: str) -> str:
    return f"{rid}|{claim_id}|{proposal_id}"


def restatement_group_id(claim_ids) -> str:
    """The same set of Claims always names the same group, whatever the order.

    Derived from the sorted, distinct ids, so no member is first or canonical.
    """
    ids = sorted({str(c).strip() for c in claim_ids if str(c).strip()})
    return "RG-" + hashlib.sha256("|".join(ids).encode("utf-8")).hexdigest()[:12]


def restatement_key(rid: str, group_id: str, claim_id: str) -> str:
    return f"{rid}|{group_id}|{claim_id}"


def response_lookup(question_key: str, object_id: str) -> str:
    return f"{question_key}|{object_id}"


def concept_lookup(question_key: str, claim_id: str, concept_id: str) -> str:
    return f"{question_key}|{claim_id}|{concept_id}"


def pair_lookup(claim_id: str, item_id: str) -> str:
    return f"{claim_id}|{item_id}"


def submission_key(round_id: str, phase_id: str, evaluator_id: str) -> str:
    return f"{round_id}|{phase_id}|{evaluator_id}"


# ----------------------------------------------------------- row positions
#: key -> sheet row, per tab. Positions are stable once written — nothing is
#: deleted during a round and an append never moves an existing row — so an
#: entry can only be missing, never wrong.
_ROW_INDEX: dict[str, dict[str, int]] = {}
_GENERATION = collections.Counter()


def forget_all() -> None:
    _ROW_INDEX.clear()
    for name in list(_GENERATION):
        _GENERATION[name] += 1
    _GENERATION["reviews"] += 1
    _GENERATION["round"] += 1


def _remember_rows(tab: str, first_row: int, rows: list[dict]) -> None:
    index = _ROW_INDEX.setdefault(tab, {})
    key_column = sheets.KEY_COLUMN[tab]
    for offset, row in enumerate(rows):
        key = row.get(key_column)
        if key and key not in index:
            index[key] = first_row + offset


def _reindex(tab: str) -> list[dict]:
    rows = workbook().read_tab(tab)
    _ROW_INDEX[tab] = sheets.row_index(rows, tab)
    return rows


def row_number(tab: str, key: str) -> int | None:
    """Where this key lives. A miss verifies once with a whole-tab read."""
    index = _ROW_INDEX.get(tab)
    if index is not None and key in index:
        return index[key]
    _reindex(tab)
    return _ROW_INDEX[tab].get(key)


# ----------------------------------------------------------------- REVIEWS
@functools.lru_cache(maxsize=1)
def _reviews(generation: int) -> list[dict]:
    rows = workbook().read_tab(sheets.REVIEWS)
    _ROW_INDEX[sheets.REVIEWS] = sheets.row_index(rows, sheets.REVIEWS)
    return rows


def forget_reviews() -> None:
    _GENERATION["reviews"] += 1


def all_reviews() -> list[dict]:
    return [dict(r) for r in _reviews(_GENERATION["reviews"])]


def get_review(rid: str) -> dict | None:
    return next((dict(r) for r in _reviews(_GENERATION["reviews"])
                 if r["review_id"] == rid), None)


def reviews_for(round_id: str, evaluator_id: str, phase_id: str) -> dict[str, dict]:
    return {r["source_id"]: dict(r) for r in _reviews(_GENERATION["reviews"])
            if r["round_id"] == round_id and r["evaluator_id"] == evaluator_id
            and r["phase_id"] == phase_id}


def _update_review(rid: str, *, touch: bool = True, **fields) -> None:
    row = get_review(rid)
    if row is None:
        raise StorageIntegrityError(f"REVIEWS has no row for {rid!r}.")
    row.update(fields)
    if touch:
        row["last_saved_at"] = now()
    workbook().update_rows(sheets.REVIEWS, [(row_number(sheets.REVIEWS, rid), row)])
    forget_reviews()


#: Written once, when work begins; never rewritten afterwards.
PROVENANCE = ("brain_snapshot_id", "eval_spec_version", "definitions_id",
              "config_version", "split_id", "assignment_state")


def start_review(rid: str, read_confirmed: bool, **provenance) -> None:
    """Begin work, stamping any provenance still blank. Values already recorded
    are kept: a later configuration change must not alter what an answer means."""
    unknown = set(provenance) - set(PROVENANCE)
    if unknown:
        raise TypeError(f"not provenance fields: {sorted(unknown)}")
    row = get_review(rid) or {}
    fields = {name: (row.get(name) or provenance.get(name, "") or "")
              for name in PROVENANCE}
    fields["pdf_read_confirmed"] = int(read_confirmed)
    if row.get("status") != STATUS_SUBMITTED:
        fields["status"] = STATUS_IN_PROGRESS
    fields["started_at"] = row.get("started_at") or now()
    _update_review(rid, **fields)


TOUCH_INTERVAL = 60.0
_TOUCHED: dict[str, float] = {}


def record_activity(rid: str) -> None:
    """An edit withdraws `complete` at once; `last_saved_at` is throttled."""
    review = get_review(rid) or {}
    if review.get("status") == STATUS_COMPLETE:
        _update_review(rid, status=STATUS_IN_PROGRESS)
        _TOUCHED[rid] = time.monotonic()
        return
    if time.monotonic() - _TOUCHED.get(rid, 0.0) >= TOUCH_INTERVAL:
        _TOUCHED[rid] = time.monotonic()
        _update_review(rid)


def mark_complete(rid: str) -> None:
    if (get_review(rid) or {}).get("status") != STATUS_SUBMITTED:
        _update_review(rid, status=STATUS_COMPLETE)


def unmark_complete(rid: str) -> None:
    if (get_review(rid) or {}).get("status") == STATUS_COMPLETE:
        _update_review(rid, status=STATUS_IN_PROGRESS)


def submit_review(rid: str) -> None:
    _update_review(rid, status=STATUS_SUBMITTED, submitted_at=now())


def submit_many(review_ids) -> int:
    """Final batch submission: one REVIEWS write for all of them."""
    stamp = now()
    updates = []
    for rid in review_ids:
        row = get_review(rid)
        if row is None:
            continue
        row.update(status=STATUS_SUBMITTED, submitted_at=stamp, last_saved_at=stamp)
        updates.append((row_number(sheets.REVIEWS, rid), row))
    workbook().update_rows(sheets.REVIEWS, updates)
    forget_reviews()
    return len(updates)


def reopen_review(rid: str) -> bool:
    """Admin reopens one submitted paper, which un-submits its whole phase."""
    row = get_review(rid) or {}
    _update_review(rid, status=STATUS_IN_PROGRESS, submitted_at="")
    return retract_phase_submission(row.get("round_id", ""), row.get("phase_id", ""),
                                    row.get("evaluator_id", ""))


# ------------------------------------------------------------ review data
@dataclasses.dataclass
class ReviewData:
    """Everything stored for one review, keyed for lookup.

    responses  "QUESTION|object_id"          -> RESPONSES row
    concepts   "QUESTION|claim_id|concept_id" -> CONCEPT_RESPONSES row
    relations  relation_key                   -> RELATION_RESPONSES row
    missing    "claim_id|concept_id"          -> effective MISSING_CONCEPTS row
    proposals  "claim_id|proposal_id"         -> effective PROPOSED_CONCEPTS row
    restatements "group_id|claim_id"          -> effective RESTATEMENTS row
    """
    responses: dict = dataclasses.field(default_factory=dict)
    concepts: dict = dataclasses.field(default_factory=dict)
    relations: dict = dataclasses.field(default_factory=dict)
    missing: dict = dataclasses.field(default_factory=dict)
    proposals: dict = dataclasses.field(default_factory=dict)
    restatements: dict = dataclasses.field(default_factory=dict)

    def response(self, question_key: str, object_id: str) -> dict:
        return self.responses.get(response_lookup(question_key, object_id), {})

    def concept(self, question_key: str, claim_id: str, concept_id: str) -> dict:
        return self.concepts.get(concept_lookup(question_key, claim_id, concept_id), {})

    def relation(self, relation_key: str) -> dict:
        return self.relations.get(relation_key, {})

    def active_missing(self, claim_id: str) -> list[dict]:
        return sorted((r for r in self.missing.values()
                       if r.get("claim_id") == claim_id and r.get("active") == TRUE),
                      key=lambda r: r.get("concept_id", ""))

    def active_proposals(self, claim_id: str) -> list[dict]:
        return sorted((r for r in self.proposals.values()
                       if r.get("claim_id") == claim_id and r.get("active") == TRUE),
                      key=lambda r: r.get("name", "").lower())

    def active_restatement_groups(self) -> dict[str, list[str]]:
        """group_id -> its active member Claims, sorted. As stored: not validated
        (see `progress.restatement_groups` for what counts)."""
        groups: dict[str, list[str]] = {}
        for row in self.restatements.values():
            if row.get("active") == TRUE and row.get("group_id") and row.get("claim_id"):
                groups.setdefault(row["group_id"], []).append(row["claim_id"])
        return {gid: sorted(set(ids)) for gid, ids in groups.items()}

    def copy(self) -> "ReviewData":
        return ReviewData(*(
            {k: dict(v) for k, v in getattr(self, f.name).items()}
            for f in dataclasses.fields(self)))


def _block(review: dict, tab: str) -> tuple[int, int] | None:
    prefix = sheets.BLOCK_PREFIX[tab]
    first = str(review.get(f"{prefix}_first_row") or "").strip()
    last = str(review.get(f"{prefix}_last_row") or "").strip()
    if first.isdigit() and last.isdigit():
        return int(first), int(last)
    return None


def effective(rows: list[dict], key_column: str) -> dict[str, dict]:
    """Collapse rows sharing a deterministic key to one: the latest write wins.

    Two sessions appending the same selection at the same instant could leave a
    key twice in a selection tab. Whatever the storage holds, the effective
    state has one row per key.
    """
    out: dict[str, dict] = {}
    for row in rows:
        key = row.get(key_column)
        if not key:
            continue
        if key not in out or (row.get("updated_at") or "") > (out[key].get("updated_at") or ""):
            out[key] = row
    return out


def load_review(rid: str) -> ReviewData:
    """Every stored answer for one review, in ONE request.

    The three preallocated blocks come back by their recorded row ranges, and
    the small selection tabs whole; the batch read is a single
    `values.batchGet`.
    """
    review = get_review(rid)
    if review is None:
        raise StorageIntegrityError(f"REVIEWS has no row for {rid!r}.")
    requests, where = [], []
    for tab in sheets.BLOCK_TABS:
        block = _block(review, tab)
        if block is not None:
            requests.append((tab, block[0], block[1]))
            where.append((tab, block[0]))
    for tab in sheets.SELECTION_TABS:
        requests.append((tab, None, None))
        where.append((tab, 2))
    results = workbook().read_ranges(requests)

    rows_by_tab = {}
    for (tab, first), rows in zip(where, results):
        if tab in sheets.SELECTION_TABS:
            _ROW_INDEX[tab] = sheets.row_index(rows, tab)
        else:
            _remember_rows(tab, first, rows)
        rows_by_tab[tab] = rows
    return review_data(rid, rows_by_tab)


def review_data(rid: str, rows_by_tab: dict[str, list[dict]]) -> ReviewData:
    """One review's stored answers from raw tab rows, keyed as `ReviewData` is.

    The single definition of how stored rows become the evaluation state: the
    app's `load_review` and the integrity audit both use it. Rows of other
    reviews are ignored; selection tabs are collapsed to their effective rows.
    """
    data = ReviewData()
    for tab, rows in rows_by_tab.items():
        mine = [r for r in rows if r.get("review_id") == rid]
        if tab == sheets.RESPONSES:
            data.responses = {response_lookup(r["question_key"], r["object_id"]): r
                              for r in mine}
        elif tab == sheets.CONCEPT_RESPONSES:
            data.concepts = {concept_lookup(r["question_key"], r["claim_id"],
                                            r["concept_id"]): r for r in mine}
        elif tab == sheets.RELATION_RESPONSES:
            data.relations = {r["relation_key"]: r for r in mine}
        elif tab == sheets.MISSING_CONCEPTS:
            data.missing = {pair_lookup(r["claim_id"], r["concept_id"]): r
                            for r in effective(mine, "selection_key").values()}
        elif tab == sheets.PROPOSED_CONCEPTS:
            data.proposals = {pair_lookup(r["claim_id"], r["proposal_id"]): r
                              for r in effective(mine, "proposal_key").values()}
        elif tab == sheets.RESTATEMENTS:
            data.restatements = {pair_lookup(r["group_id"], r["claim_id"]): r
                                 for r in effective(mine, "restatement_key").values()}
    return data


# ------------------------------------------------------------------ writes
def write(tab: str, key: str, values: dict, *, rid: str,
          expected_updated_at: str | None = None, also_accept=()) -> str:
    """One row of a preallocated tab. Same path as a batch of one; a conflict
    is raised here rather than returned."""
    result = save_many([{"tab": tab, "key": key, "values": values, "rid": rid,
                         "expected_updated_at": expected_updated_at,
                         "also_accept": also_accept}])[0]
    if isinstance(result, SaveConflict):
        raise result
    return result


def _same_content(stored: dict, values: dict, tab: str) -> bool:
    """Whether a stored row already holds exactly these values (the stamp aside).

    Stored cells come back as text, so both sides are compared as text.
    """
    return all(str(stored.get(column) or "") == str(values.get(column) or "")
               for column in sheets.COLUMNS[tab] if column != "updated_at")


def save_many(records: list[dict]) -> list:
    """Several row writes: one conflict read and one write request per tab.

    Each record: tab, key, values (the complete row), rid, expected_updated_at,
    and optionally ``also_accept`` — the stamps this session itself has written
    to that row. An edit queued while the session's previous write to the same
    row was still in flight carries the older stamp; the row having moved on to
    a stamp this session wrote is not a conflict.

    Returns one result per record, in order: the new stamp, or a `SaveConflict`
    for a record whose row was changed elsewhere. **Conflicts are per record**:
    the other records of the batch are still written. Every tab's conflicts are
    determined before anything is written.

    A row that already holds exactly the values being written is never a
    conflict, whatever its stamp. That is a retry whose first attempt reached
    the workbook although its response was lost (a timeout, a quota error), and
    refusing it would report a stored answer as not applied.
    """
    if not records:
        return []
    book = workbook()
    results: list = [None] * len(records)
    by_tab: dict[str, list] = collections.defaultdict(list)
    for index, record in enumerate(records):
        stamp = now()
        tab, key = record["tab"], record["key"]
        number = row_number(tab, key)
        if number is None:
            raise StorageIntegrityError(
                f"{tab} has no row for {key!r}. Every row is created by "
                f"`tools/bootstrap_round.py`, so this workbook is not the one this "
                f"configuration was prepared against. Nothing was written.")
        values = {**record["values"], sheets.KEY_COLUMN[tab]: key, "updated_at": stamp}
        accepted = set(record.get("also_accept") or ())
        if record.get("expected_updated_at"):
            accepted.add(record["expected_updated_at"])
        by_tab[tab].append((index, number, values, key, accepted))

    writes = {}
    for tab, updates in by_tab.items():
        stored = {}
        if any(accepted for *_, accepted in updates):
            numbers = [number for _, number, *_ in updates]
            stored = {row.get(sheets.KEY_COLUMN[tab]): row
                      for row in book.read_range(tab, min(numbers), max(numbers))}
        keep = []
        for index, number, values, key, accepted in updates:
            row = stored.get(key) or {}
            stamp = row.get("updated_at") or ""
            if (accepted and stamp and stamp not in accepted
                    and not _same_content(row, values, tab)):
                results[index] = SaveConflict(key)
                continue
            keep.append((number, values))
            results[index] = values["updated_at"]
        writes[tab] = keep

    for tab, rows in writes.items():
        book.update_rows(tab, rows)
    for rid in {record["rid"] for record in records}:
        record_activity(rid)
    return results


def upsert_selection(tab: str, key: str, values: dict, *, rid: str) -> str:
    """Write one row of a selection tab, idempotently."""
    return upsert_selections(tab, {key: values}, rid=rid)


def upsert_selections(tab: str, rows: dict[str, dict], *, rid: str) -> str:
    """Write rows of MISSING_CONCEPTS, PROPOSED_CONCEPTS or RESTATEMENTS.

    The key column is re-read first, so a row that already exists — from an
    earlier selection, or from another session — is updated in place instead of
    appended again. Removal is `active = FALSE` on the same row, so re-selecting
    reactivates it and row positions never move. Several rows (the members of
    one restatement group) cost one re-read, one update and one append.
    """
    if tab not in sheets.SELECTION_TABS:
        raise ValueError(f"{tab} is not a selection tab")
    book = workbook()
    stamp = now()
    _reindex(tab)
    updates, appends = [], []
    for key, values in rows.items():
        row = {**values, sheets.KEY_COLUMN[tab]: key, "updated_at": stamp}
        number = _ROW_INDEX[tab].get(key)
        if number is None:
            appends.append(row)
        else:
            updates.append((number, row))
    if updates:
        book.update_rows(tab, updates)
    if appends:
        book.append_rows(tab, appends)
        _reindex(tab)
    record_activity(rid)
    return stamp


# ------------------------------------------------------------ preallocation
def preallocate(reviews: list[dict], blocks: dict[str, dict[str, list[dict]]]) -> dict:
    """Create review rows and their blocks in a handful of requests.

    ``reviews``: complete REVIEWS rows (without row ranges).
    ``blocks``: review_id -> {tab: [rows]} for the three block tabs.
    Reviews already present are skipped with their blocks: bootstrap may extend
    a round with new assignments, but never rewrites what exists.
    """
    book = workbook()
    existing_reviews = {r["review_id"] for r in book.read_tab(sheets.REVIEWS)}
    counts = {tab: len(book.read_tab(tab)) for tab in sheets.BLOCK_TABS}
    next_row = {tab: counts[tab] + 2 for tab in sheets.BLOCK_TABS}
    payload = {tab: [] for tab in sheets.BLOCK_TABS}
    new_reviews = []
    for review in reviews:
        rid = review["review_id"]
        if rid in existing_reviews:
            continue
        row = dict(review)
        for tab in sheets.BLOCK_TABS:
            rows = blocks.get(rid, {}).get(tab, [])
            prefix = sheets.BLOCK_PREFIX[tab]
            if rows:
                row[f"{prefix}_first_row"] = str(next_row[tab])
                row[f"{prefix}_last_row"] = str(next_row[tab] + len(rows) - 1)
                next_row[tab] += len(rows)
                payload[tab].extend(rows)
        new_reviews.append(row)
    for tab in sheets.BLOCK_TABS:
        book.append_rows(tab, payload[tab])
    book.append_rows(sheets.REVIEWS, new_reviews)
    forget_all()
    return {"reviews": len(new_reviews),
            **{tab: len(rows) for tab, rows in payload.items()}}


# -------------------------------------------------------------- submissions
SUBMITTED, RETRACTED = "submitted", "retracted"


def all_submissions() -> list[dict]:
    return workbook().read_tab(sheets.SUBMISSIONS)


def phase_submission(round_id: str, phase_id: str, evaluator_id: str) -> dict | None:
    key = submission_key(round_id, phase_id, evaluator_id)
    return next((r for r in all_submissions() if r.get("submission_key") == key), None)


def phase_submitted(round_id: str, phase_id: str, evaluator_id: str) -> bool:
    row = phase_submission(round_id, phase_id, evaluator_id)
    return bool(row and row.get("status") == SUBMITTED)


def record_phase_submission(round_id: str, phase_id: str, evaluator_id: str,
                            config_version: str = "") -> str:
    """The marker that makes a phase finally submitted. Written last, on purpose."""
    key = submission_key(round_id, phase_id, evaluator_id)
    row = {"submission_key": key, "round_id": round_id, "evaluator_id": evaluator_id,
           "phase_id": phase_id, "config_version": config_version,
           "status": SUBMITTED, "submitted_at": now()}
    book = workbook()
    rows = book.read_tab(sheets.SUBMISSIONS)
    index = sheets.row_index(rows, sheets.SUBMISSIONS)
    if key in index:
        book.update_rows(sheets.SUBMISSIONS, [(index[key], row)])
    else:
        book.append_rows(sheets.SUBMISSIONS, [row])
    return key


def retract_phase_submission(round_id: str, phase_id: str, evaluator_id: str) -> bool:
    """Kept and marked `retracted`, never deleted: that it happened is history."""
    key = submission_key(round_id, phase_id, evaluator_id)
    book = workbook()
    rows = book.read_tab(sheets.SUBMISSIONS)
    index = sheets.row_index(rows, sheets.SUBMISSIONS)
    if key not in index:
        return False
    row = dict(next(r for r in rows if r["submission_key"] == key))
    if row.get("status") != SUBMITTED:
        return False
    row["status"] = RETRACTED
    book.update_rows(sheets.SUBMISSIONS, [(index[key], row)])
    return True


# ------------------------------------------------------------------ export
def export(tab: str) -> list[dict]:
    """A whole tab, as stored. For the administrator's exports only."""
    if tab not in sheets.ALL_TABS:
        raise ValueError(tab)
    return [dict(r) for r in workbook().read_tab(tab)]
