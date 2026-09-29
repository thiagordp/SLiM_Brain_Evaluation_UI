"""Integration check against a REAL, disposable Google Sheets workbook.

Everything else is tested on the in-memory fake (`tests/fakes.py`). Only a real
workbook shows how Google actually behaves: trailing empty cells, batched reads
and writes, appends after preallocated blocks, payload limits.

    export GOOGLE_SHEET_ID='<a new, empty, disposable workbook>'
    export GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
    HE_LIVE_SHEET_OK=1 python app/tests/live_sheets.py

It bootstraps the configured round into that workbook (replacing a round it
created there before) and writes answers. **Never point it at a production
round workbook.** It refuses to run unless `HE_LIVE_SHEET_OK` is set.
"""
from __future__ import annotations

import contextlib
import io
import os
import pathlib
import sys
import time

if not os.environ.get("HE_LIVE_SHEET_OK"):
    raise SystemExit("refusing to run: set HE_LIVE_SHEET_OK=1 to confirm GOOGLE_SHEET_ID "
                     "is a disposable test workbook and not a production round")

APP = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(APP), str(APP / "tools")]

import bootstrap_round  # noqa: E402
import integrity  # noqa: E402
import manifest  # noqa: E402
import sheets  # noqa: E402
import spec  # noqa: E402
import store  # noqa: E402
from brain import load_brain  # noqa: E402

PASS = FAIL = 0


def check(ok, message):
    global PASS, FAIL
    print(("ok    " if ok else "FAIL  ") + message)
    PASS, FAIL = PASS + bool(ok), FAIL + (not ok)


print(f"workbook: {sheets.sheet_id()}\naccount : {sheets.describe_account()}")
book = store.workbook()
held = {r["key"]: r["value"] for r in book.read_tab(sheets.ROUND)}.get("round_id", "") \
    if sheets.ROUND in book.tab_titles() else ""
sys.argv = ["bootstrap_round.py"] + (
    ["--overwrite-round", held, "--discard-evaluations"] if held else [])
output = io.StringIO()
with contextlib.redirect_stdout(output):
    code = bootstrap_round.main()
print(output.getvalue())
check(code == 0, "bootstrap into the real workbook")
store.forget_all()

# Bootstrap used much of this minute's write quota (shared by the whole
# service account); start the checks with a fresh minute.
time.sleep(65)
store.check_ready()
check(store.round_metadata()["round_id"] == manifest.round_id(), "ROUND reads back")
check(bootstrap_round.verify_blocks(book, manifest.round_id()) == [],
      "every block reads back at its recorded rows")

review = next(r for r in book.read_tab(sheets.REVIEWS) if r["phase_id"] == "training")
rid, source = review["review_id"], review["source_id"]
store.start_review(rid, True, eval_spec_version=spec.EVAL_SPEC_VERSION)
data = store.load_review(rid)
claims = [c["id"] for c in load_brain().claims_of(source)]
q2 = "CLAIM_Q02_CENTRAL_THESIS"
row = data.response(q2, claims[0])
long_comment = "=SUM(A1:A2) " + "x" * 4988
stamp = store.write(sheets.RESPONSES, row["response_key"],
                    {**row, "answer": "No", "comment": long_comment},
                    rid=rid, expected_updated_at="")
again = store.load_review(rid).response(q2, claims[0])
check(again["answer"] == "No" and again["comment"] == long_comment,
      "an answer and a 5,000-character comment starting with '=' round-trip as text")
try:
    store.write(sheets.RESPONSES, row["response_key"], {**again, "answer": "Yes",
                "comment": ""}, rid=rid, expected_updated_at="stale")
    check(False, "a stale write is refused")
except store.SaveConflict:
    check(True, "a stale write is refused")

# one stale record in a batch does not stop the others
others = [data.response(q2, c) for c in claims[1:3]]
results = store.save_many(
    [{"tab": sheets.RESPONSES, "key": row["response_key"],
      "values": {**again, "answer": "Yes"}, "rid": rid, "expected_updated_at": "stale"}]
    + [{"tab": sheets.RESPONSES, "key": r["response_key"],
        "values": {**r, "answer": "Yes"}, "rid": rid, "expected_updated_at": ""}
       for r in others])
stored = store.load_review(rid)
check(isinstance(results[0], store.SaveConflict)
      and stored.response(q2, claims[0])["answer"] == "No"
      and all(stored.response(q2, c)["answer"] == "Yes" for c in claims[1:3]),
      "a batch with one stale record writes the others")

relation = next(r for r in stored.relations.values()
                if r["relation_type"] in ("SUPPORTS", "ATTACKS"))
store.write(sheets.RELATION_RESPONSES, relation["response_key"],
            {**relation, "direction_answer": "No", "direction_comment": "reversed"},
            rid=rid)
back = store.load_review(rid).relation(relation["relation_key"])
check(back["direction_answer"] == "No" and back["grounding_answer"] == ""
      and back["type_answer"] == "", "a Direction answer round-trips on its own")

key = store.selection_key(rid, claims[0], "CPT-legal-drafting")
values = {"review_id": rid, "source_id": source, "claim_id": claims[0],
          "concept_id": "CPT-legal-drafting", "active": store.TRUE}
store.upsert_selection(sheets.MISSING_CONCEPTS, key, values, rid=rid)
store.upsert_selection(sheets.MISSING_CONCEPTS, key, values, rid=rid)
check(sum(1 for r in book.read_tab(sheets.MISSING_CONCEPTS) if r["selection_key"] == key)
      == 1, "a repeated selection stays one row")
store.upsert_selection(sheets.MISSING_CONCEPTS, key, {**values, "active": store.FALSE},
                       rid=rid)

group = claims[:2]
gid = store.restatement_group_id(group)
members = {store.restatement_key(rid, gid, c): {
    "review_id": rid, "source_id": source, "group_id": gid, "claim_id": c,
    "active": store.TRUE} for c in group}
store.upsert_selections(sheets.RESTATEMENTS, members, rid=rid)
store.upsert_selections(sheets.RESTATEMENTS, members, rid=rid)
check(store.load_review(rid).active_restatement_groups() == {gid: sorted(group)}
      and len(book.read_tab(sheets.RESTATEMENTS)) == 2,
      "a restatement group round-trips, written once")
store.upsert_selections(sheets.RESTATEMENTS, {k: {**v, "active": store.FALSE}
                                              for k, v in members.items()}, rid=rid)
check(store.load_review(rid).active_restatement_groups() == {},
      "removing the group deactivates its rows")

problems = [p for p in integrity.run(load_brain(), book, manifest.round_id())
            if p.level == integrity.ERROR]
for problem in problems:
    print("   ", problem)
check(not problems, "the integrity audit finds no error after all of this")

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
