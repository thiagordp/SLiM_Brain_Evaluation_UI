"""Steps 4.8 and 12 — validate the Sheets backend against a real Google workbook.

Everything else is tested against `sheets.LocalWorkbook`, which exercises the
same `store.py` paths. What only a real workbook can show is how Google actually
behaves: whether `worksheet.get()` truncates trailing empty cells, whether
`batch_update` lands as one request, whether a 25,000-row preallocation fits
inside the payload limits, and what two evaluators writing at once really do.

    export GOOGLE_SHEET_ID='<a disposable, empty workbook>'
    export GOOGLE_SERVICE_ACCOUNT_JSON=.streamlit/service-account.json
    python app/tools/bootstrap_sheets.py --seed
    python app/tools/preallocate.py
    python app/tests/live_sheets.py

Google allows 60 read requests per minute per user. This script makes far more
than an evaluator's session does, so a full run can exhaust the quota near the
end; if it does, wait a minute and run it again. Ordinary use is nowhere near
the limit — opening a paper costs three reads and saving an answer costs none.

**Never point this at the production workbook.** It writes answers into
preallocated rows and asserts row counts. It refuses to run unless
`HE_LIVE_SHEET_OK` is set, so it cannot be started by accident.
"""
import os
import sys

if not os.environ.get("HE_LIVE_SHEET_OK"):
    raise SystemExit(
        "refusing to run: set HE_LIVE_SHEET_OK=1 to confirm GOOGLE_SHEET_ID is a "
        "disposable test workbook and not the production one"
    )

import pathlib, sys, time
sys.path.insert(0, str(pathlib.Path("app").resolve()))
import sheets, store, progress, manifest, spec
from brain import load_brain

BRAIN = load_brain()
PASS = FAIL = 0
def check(ok, msg):
    global PASS, FAIL
    print(("ok    " if ok else "FAIL  ") + msg)
    PASS, FAIL = PASS + bool(ok), FAIL + (not ok)

print(f"workbook: {sheets.sheet_id()}\naccount : {sheets.describe_account()}")
book = store.workbook()

print("\n== schemas as materialised ==")
import gspread
from google.oauth2.service_account import Credentials
gc = gspread.authorize(Credentials.from_service_account_info(
    sheets.service_account_info(),
    scopes=["https://www.googleapis.com/auth/spreadsheets"]))
ss = gc.open_by_key(sheets.sheet_id())
live = {w.title: w for w in ss.worksheets()}
check(set(live) == set(sheets.ALL_TABS), f"seven tabs ({sorted(live)})")
for tab in sheets.ALL_TABS:
    header = live[tab].row_values(1)
    check(header == list(sheets.COLUMNS[tab]),
          f"{tab} header matches the schema ({len(header)} columns)")
check(len(sheets.COLUMNS[sheets.RESPONSES]) == 13, "RESPONSES is 13 columns")
check(len(sheets.COLUMNS[sheets.ASSIGNMENTS]) == 8, "ASSIGNMENTS is 8 columns")
check(len(sheets.COLUMNS[sheets.REVIEWS]) == 22, "REVIEWS is 22 columns")

print("\n== row_count ==")
for tab, expected in ((sheets.RESPONSES, 23635), (sheets.EDGE_RESPONSES, 1752),
                      (sheets.REVIEWS, 82), (sheets.ASSIGNMENTS, 82)):
    n = book.row_count(tab)
    check(n == expected, f"row_count({tab}) == {expected} (got {n})")

print("\n== read_range with trailing empty cells ==")
rid = store.review_id(manifest.AGREEMENT, "vaclav",
                      manifest.assigned_source_ids("vaclav", manifest.AGREEMENT)[0])
review = store._review_row(rid)
first, last = int(review["responses_first_row"]), int(review["responses_last_row"])
rows = book.read_range(sheets.RESPONSES, first, last)
check(len(rows) == last - first + 1, f"the block reads back whole ({len(rows)} rows)")
check(all(set(r) == set(sheets.COLUMNS[sheets.RESPONSES]) for r in rows),
      "every row has all 13 keys despite trailing empties on the wire")
blank_tail = [r for r in rows if not r["answer"] and not r["updated_at"]]
check(blank_tail, f"{len(blank_tail)} rows end in empty cells and still parse")
check(all(r["review_id"] == rid for r in rows), "and all belong to this review")
check(book.read_range(sheets.RESPONSES, 5, 4) == [], "an inverted range is empty")

print("\n== auto-N/A round-trip ==")
na = [r for r in rows if r["applicability"] == spec.AUTO_NA]
check(na, f"{len(na)} auto-N/A rows preallocated in this block")
check(all(r["answer"] == spec.NA_ANSWER for r in na), "each already answered N/A")
check(all(r["updated_at"] for r in na), "and stamped")
blank = [r for r in rows if not r["applicability"]]
check(blank and all(not r["answer"] for r in blank),
      f"while {len(blank)} unanswered rows are blank — the two stay distinct")

print("\n== targeted read/write requests ==")
class Counted:
    def __init__(s_, inner): s_.inner, s_.n = inner, {}
    def __getattr__(s_, name):
        attr = getattr(s_.inner, name)
        if not callable(attr): return attr
        def wrapped(*a, **k):
            s_.n[f"{name}:{a[0]}" if a else name] = s_.n.get(f"{name}:{a[0]}" if a else name, 0) + 1
            return attr(*a, **k)
        return wrapped
counted = Counted(book)
store.workbook = lambda: counted
store.forget_row_index(); store.forget_reviews(); store._TOUCHED.clear()

counted.n = {}
responses = store.load_responses(rid)
edges = store.load_edge_responses(rid)
check(counted.n.get("read_tab:RESPONSES", 0) == 0, "opening reads no whole RESPONSES tab")
check(counted.n.get("read_range:RESPONSES", 0) == 1, "one range read for responses")
check(counted.n.get("read_range:EDGE_RESPONSES", 0) == 1, "one for edges")
print(f"      requests to open a {len(responses)}-row review: {counted.n}")

item = progress.all_possible_items(BRAIN, review["source_id"])[0]
counted.n = {}
t0 = time.monotonic()
store.save_response(rid, object_type=item.object_type, object_id=item.object_id,
                    question_key=item.question.question_key,
                    criterion_id=item.question.criterion_id,
                    field_subitem=item.question.field_subitem,
                    answer="Yes", comment="live 4.8 probe",
                    applicability=spec.APPLICABLE, source_id=review["source_id"])
check(counted.n.get("read_tab:RESPONSES", 0) == 0, "saving reads no whole tab")
check(counted.n.get("read_range", 0) == 0, "and re-reads no range")
print(f"      requests to save one answer: {counted.n}  ({time.monotonic()-t0:.2f}s)")

back = store.load_responses(rid)[item.lookup]
check(back["answer"] == "Yes" and back["comment_evidence"] == "live 4.8 probe",
      "the answer round-trips through the live workbook")
check(back["applicability"] == spec.APPLICABLE, "with its applicability")

print("\n== update_rows / batch_update ==")
items = progress.all_possible_items(BRAIN, review["source_id"])[1:9]
counted.n = {}
t0 = time.monotonic()
store.save_responses([{
    "rid": rid, "object_type": i.object_type, "object_id": i.object_id,
    "question_key": i.question.question_key, "criterion_id": i.question.criterion_id,
    "field_subitem": i.question.field_subitem, "answer": "In part",
    "comment": "batched", "applicability": spec.APPLICABLE,
    "source_id": review["source_id"]} for i in items])
check(counted.n.get("update_rows:RESPONSES", 0) == 1,
      f"eight answers in one batch_update request ({counted.n})")
print(f"      {time.monotonic()-t0:.2f}s")
back = store.load_responses(rid)
check(all(back[i.lookup]["answer"] == "In part" for i in items),
      "all eight landed, each in its own row")
untouched = [k for k, r in back.items()
             if r["answer"] and r["applicability"] == spec.AUTO_NA]
check(len(untouched) == len(na), "and the N/A rows beside them are unchanged")

store.workbook = lambda: book

import concurrent.futures as cf
import pathlib, sys, time
sys.path.insert(0, str(pathlib.Path("app").resolve()))

print("\n== two evaluators on the same agreement paper ==")
pair = [e["evaluator_id"] for e in manifest.evaluators()
        if e["agreement_split"] == "AGR-B"]
shared = manifest.assigned_source_ids(pair[0], manifest.AGREEMENT)[0]
check(shared in manifest.assigned_source_ids(pair[1], manifest.AGREEMENT),
      f"{pair} both hold {shared}")
rids = [store.review_id(manifest.AGREEMENT, e, shared) for e in pair]
blocks = {}
for e, rid in zip(pair, rids):
    row = store._review_row(rid)
    blocks[e] = (int(row["responses_first_row"]), int(row["responses_last_row"]))
check(blocks[pair[0]] != blocks[pair[1]], f"their blocks are disjoint: {blocks}")
a0, a1 = blocks[pair[0]]; b0, b1 = blocks[pair[1]]
check(a1 < b0 or b1 < a0, "and do not overlap at all")

items = progress.all_possible_items(BRAIN, shared)[:6]
def work(evaluator, rid, value):
    out = []
    for i in items:
        out.append(store.save_response(
            rid, object_type=i.object_type, object_id=i.object_id,
            question_key=i.question.question_key,
            criterion_id=i.question.criterion_id,
            field_subitem=i.question.field_subitem, answer=value,
            comment=f"{evaluator} concurrent", applicability=spec.APPLICABLE,
            source_id=shared))
    return out

for rid in rids:
    store.load_responses(rid)                 # index each block, as a session would
t0 = time.monotonic()
with cf.ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(work, pair[0], rids[0], "Yes"),
               pool.submit(work, pair[1], rids[1], "No")]
    [f.result() for f in futures]
print(f"      12 concurrent writes in {time.monotonic()-t0:.1f}s")

for evaluator, rid, expected in ((pair[0], rids[0], "Yes"), (pair[1], rids[1], "No")):
    got = store.load_responses(rid)
    mine = [got[i.lookup] for i in items]
    check(all(r["answer"] == expected for r in mine),
          f"{evaluator} sees only their own answers ({expected})")
    check(all(f"{evaluator} concurrent" == r["comment_evidence"] for r in mine),
          f"and their own comments")
check(len({r["review_id"] for r in store.load_responses(rids[0]).values()}) == 1,
      "neither range leaked into the other")

print("\n== integrity after preallocation ==")
rows = store.workbook().read_tab(sheets.REVIEWS)
check(len(rows) == 82, f"82 reviews ({len(rows)})")
ranges = sorted((int(r["responses_first_row"]), int(r["responses_last_row"]))
                for r in rows if r["responses_first_row"])
gaps = [(ranges[i][1], ranges[i+1][0]) for i in range(len(ranges)-1)
        if ranges[i+1][0] != ranges[i][1] + 1]
check(not gaps, f"response blocks are contiguous and disjoint ({gaps[:2]})")
check(ranges[0][0] == 2 and ranges[-1][1] == 23636,
      f"covering rows 2..{ranges[-1][1]} of {store.workbook().row_count(sheets.RESPONSES)+1}")

check(not any(r.get("last_saved_at") and not r.get("started_at")
              and r["review_id"] not in rids
              and r["review_id"] != store.review_id(
                  manifest.AGREEMENT, "vaclav",
                  manifest.assigned_source_ids("vaclav", manifest.AGREEMENT)[0])
              for r in rows),
      "preallocation left last_saved_at unset except where we wrote")
untouched = [r for r in rows if not r.get("last_saved_at")]
check(len(untouched) >= 78, f"{len(untouched)} reviews still show no activity")
check(not any(any(r.get(f) for f in store.PROVENANCE) for r in untouched),
      "and none of them carries provenance")
locked = manifest.active_assignment_keys(untouched)
check(not locked, "so they lock no assignment")
held = manifest.reserved()
check(len(held) == 14 and not any(
    manifest.is_locked(h["assignment_key"], rows) for h in held),
    "the 14 IND-1 reservations are preallocated yet still activatable")

print("\n== an unknown key is refused on the live workbook ==")
before = store.workbook().row_count(sheets.RESPONSES)
try:
    store.save_response(rids[0], object_type="claim", object_id="CLM-0000-000",
                        question_key="CLAIM_HE03", criterion_id="HE-03",
                        field_subitem="", answer="Yes", comment=None,
                        applicability=spec.APPLICABLE, source_id=shared)
    check(False, "an unpreallocated key is refused")
except store.StorageIntegrityError as e:
    check("Nothing was written" in str(e), "an unpreallocated key is refused")
check(store.workbook().row_count(sheets.RESPONSES) == before,
      f"and the tab is unchanged at {before} rows")

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
