"""Is what the round workbook holds consistent? A read-only audit.

Everything is checked from one batched read of every tab, against the
instrument (`spec`), the Brain snapshot and the layout bootstrap created
(`progress.review_rows`). Stored rows become evaluation state through the same
function the app uses (`store.review_data`), so the audit sees exactly what an
evaluator's page would.

    error     the stored data is wrong or contradicts itself: a value outside
              its question's options, a block that is not where REVIEWS says,
              a paper marked complete with an item missing, a submission
              without its marker
    warning   possible in normal use but worth a look: a state that the next
              edit will settle, a comment kept after the answer changed
    info      counts and harmless storage artefacts (duplicate selection rows,
              which collapse on load)

Nothing is written, and nothing is repaired: a problem is reported with where
it is, so a person decides.
"""
from __future__ import annotations

import collections
import dataclasses

import progress
import sheets
import spec
import store

ERROR, WARNING, INFO = "error", "warning", "info"


@dataclasses.dataclass(frozen=True)
class Problem:
    level: str
    where: str
    what: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.where}: {self.what}"


def read_all(book) -> tuple[dict[str, list[str]], dict[str, list[dict]]]:
    """(headers, rows) of every round tab: two requests."""
    headers = book.headers(sheets.ALL_TABS)
    rows = dict(zip(sheets.ALL_TABS, book.read_ranges(
        [(tab, None, None) for tab in sheets.ALL_TABS])))
    return headers, rows


def audit(brain, headers: dict[str, list[str]], raw: dict[str, list[dict]],
          round_id: str) -> list[Problem]:
    out: list[Problem] = []
    add = lambda level, where, what: out.append(Problem(level, where, what))

    # ------------------------------------------------------------ structure
    for tab in sheets.ALL_TABS:
        if headers.get(tab) != list(sheets.COLUMNS[tab]):
            add(ERROR, tab, "header differs from what this version expects")
    if any(p.level == ERROR for p in out):
        return out                         # nothing else can be read reliably

    meta = {r["key"]: r["value"] for r in raw[sheets.ROUND]}
    expected_meta = {"round_id": round_id, "eval_spec_version": spec.EVAL_SPEC_VERSION,
                     "definitions_id": spec.definitions_id(),
                     "brain_snapshot_id": brain.snapshot_id}
    for key, value in expected_meta.items():
        if meta.get(key) != value:
            add(ERROR, "ROUND", f"{key} is {meta.get(key)!r}, this deployment has {value!r}")

    reviews = [r for r in raw[sheets.REVIEWS] if r.get("review_id")]
    by_rid = {r["review_id"]: r for r in reviews}
    if len(by_rid) != len(reviews):
        add(ERROR, "REVIEWS", "a review id occurs more than once")
    assignments = {a["assignment_key"] for a in raw[sheets.ASSIGNMENTS]}
    for review in reviews:
        if review.get("assignment_key") not in assignments:
            add(ERROR, review["review_id"], "has no ASSIGNMENTS row")

    for tab in sheets.BLOCK_TABS:
        rows = raw[tab]
        keys = collections.Counter(r.get(sheets.KEY_COLUMN[tab]) for r in rows
                                   if r.get(sheets.KEY_COLUMN[tab]))
        for key, n in keys.items():
            if n > 1:
                add(ERROR, tab, f"key {key} occurs {n} times")
        per_review = collections.Counter(r.get("review_id") for r in rows)
        prefix = sheets.BLOCK_PREFIX[tab]
        for rid, review in by_rid.items():
            first = str(review.get(f"{prefix}_first_row") or "")
            last = str(review.get(f"{prefix}_last_row") or "")
            if not (first.isdigit() and last.isdigit()):
                if per_review.get(rid):
                    add(ERROR, rid, f"{tab} rows exist but REVIEWS records no block")
                continue
            block = rows[int(first) - 2:int(last) - 1]     # row n is rows[n - 2]
            size = int(last) - int(first) + 1
            if len(block) != size or any(r.get("review_id") != rid for r in block):
                add(ERROR, rid, f"{tab} rows {first}–{last} are not all this review's")
            elif per_review.get(rid, 0) != size:
                add(ERROR, rid, f"{tab} has {per_review.get(rid, 0)} rows for this "
                                f"review, its block has {size}")

    # --------------------------------------- rows match instrument and Brain
    for rid, review in by_rid.items():
        source = review.get("source_id", "")
        if source not in brain.sources:
            add(ERROR, rid, f"Source {source} is not in the Brain snapshot")
            continue
        wanted = progress.review_rows(brain, rid, source)
        for tab in sheets.BLOCK_TABS:
            key = sheets.KEY_COLUMN[tab]
            have = {r[key] for r in raw[tab] if r.get("review_id") == rid}
            need = {r[key] for r in wanted[tab]}
            if need - have:
                add(ERROR, rid, f"{tab} lacks {len(need - have)} row(s) the instrument "
                                f"needs, e.g. {sorted(need - have)[0]}")
            if have - need:
                add(ERROR, rid, f"{tab} has {len(have - need)} row(s) the instrument "
                                f"does not ask, e.g. {sorted(have - need)[0]}")

    # ------------------------------------------------------- stored values
    def check_answer(where, question, answer, comment):
        if question is spec.Q14:
            if answer not in spec.Q14_STATES:
                add(ERROR, where, f"Question 14 state {answer!r} is not a known state")
            return
        if question.free_text:
            return
        if answer and answer not in question.options:
            add(ERROR, where, f"{question.title}: {answer!r} is not one of its options")
        if (comment or "").strip() and not spec.comment_visible(question, answer):
            add(WARNING, where, f"{question.title}: a comment is stored with answer "
                                f"{answer or '(none)'!r}, which does not show one — "
                                f"most likely written before the answer was changed")

    for row in raw[sheets.RESPONSES]:
        question = spec.BY_KEY.get(row.get("question_key", ""))
        where = row.get("response_key", "RESPONSES")
        if question is None:
            add(ERROR, where, f"unknown question {row.get('question_key')!r}")
            continue
        check_answer(where, question, row.get("answer", ""), row.get("comment", ""))
    for row in raw[sheets.CONCEPT_RESPONSES]:
        question = spec.BY_KEY.get(row.get("question_key", ""))
        where = row.get("response_key", "CONCEPT_RESPONSES")
        if question is None:
            add(ERROR, where, f"unknown question {row.get('question_key')!r}")
            continue
        check_answer(where, question, row.get("answer", ""), row.get("comment", ""))
    for row in raw[sheets.RELATION_RESPONSES]:
        where = row.get("response_key", "RELATION_RESPONSES")
        asked = spec.relation_questions({"type": row.get("relation_type")})
        for question in spec.relation_questions():
            answer = row.get(f"{question.column}_answer", "")
            comment = row.get(f"{question.column}_comment", "")
            if question not in asked:
                if answer or comment:
                    add(ERROR, where, f"{question.title} is stored for a "
                                      f"{row.get('relation_type')} relation, which "
                                      f"does not ask it")
                continue
            check_answer(where, question, answer, comment)

    # -------------------------------------------------- selection-type tabs
    for tab in sheets.SELECTION_TABS:
        key = sheets.KEY_COLUMN[tab]
        counts = collections.Counter(r.get(key) for r in raw[tab] if r.get(key))
        dupes = sum(1 for n in counts.values() if n > 1)
        if dupes:
            add(INFO, tab, f"{dupes} key(s) stored more than once; they collapse to "
                           f"one on load")
        for row in raw[tab]:
            rid = row.get("review_id", "")
            if rid not in by_rid:
                add(ERROR, row.get(key, tab), "belongs to no review")
                continue
            claims = {c["id"] for c in brain.claims_of(by_rid[rid]["source_id"])}
            if row.get("claim_id") not in claims:
                add(ERROR, row.get(key, tab), f"Claim {row.get('claim_id')} is not a "
                                              f"Claim of {by_rid[rid]['source_id']}")
            if row.get("active") not in (store.TRUE, store.FALSE):
                add(ERROR, row.get(key, tab), f"active is {row.get('active')!r}")

    # ------------------------------------------------ state, per review
    submissions = {r["submission_key"]: r for r in raw[sheets.SUBMISSIONS]}
    for rid, review in sorted(by_rid.items()):
        source = review.get("source_id", "")
        if source not in brain.sources:
            continue
        data = store.review_data(rid, raw)
        for claim in brain.claims_of(source):
            cid = claim["id"]
            state = data.response(spec.Q14.key, cid).get("answer", "")
            chosen = data.active_missing(cid) or data.active_proposals(cid)
            if state == spec.Q14_MISSING and not chosen:
                add(WARNING, f"{rid} · {cid}", "Question 14 says Concepts are missing "
                                               "but none is selected or proposed")
            if state == spec.Q14_NONE_MISSING and chosen:
                add(ERROR, f"{rid} · {cid}", "Question 14 says none is missing but "
                                             "Concepts are selected or proposed")
        answer = data.response(spec.RESTATEMENTS.key, source).get("answer", "")
        groups, problems = progress.restatement_groups(
            [c["id"] for c in brain.claims_of(source)], data)
        for problem in problems:
            add(ERROR, rid, f"restatement {problem}")
        if answer == spec.RESTATEMENTS_NONE and data.active_restatement_groups():
            add(ERROR, rid, "Restatements answered No while groups are active")
        if answer not in ("", *spec.RESTATEMENT_CODES):
            add(ERROR, rid, f"Restatements state {answer!r} is not a known state")

        status = review.get("status", "")
        if status in (store.STATUS_COMPLETE, store.STATUS_SUBMITTED):
            missing = progress.missing_items(brain, source, data)
            if missing:
                add(ERROR, rid, f"marked {status} but {len(missing)} item(s) are "
                                f"missing, e.g. {missing[0].where}: {missing[0].what} "
                                f"({missing[0].reason})")
        marker = submissions.get(store.submission_key(
            review.get("round_id", ""), review.get("phase_id", ""),
            review.get("evaluator_id", "")))
        marked = bool(marker and marker.get("status") == store.SUBMITTED)
        if status == store.STATUS_SUBMITTED and not marked:
            add(ERROR, rid, "submitted, but its phase has no submission marker")
        if marked and status != store.STATUS_SUBMITTED:
            add(ERROR, rid, f"its phase is submitted, but this paper is {status!r}")

    started = sum(1 for r in reviews if r.get("status") not in ("", "not_started"))
    add(INFO, "round", f"{len(reviews)} reviews, {started} started")
    return out


def run(brain, book, round_id: str) -> list[Problem]:
    headers, raw = read_all(book)
    return audit(brain, headers, raw, round_id)
