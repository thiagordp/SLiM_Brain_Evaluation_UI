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

if not os.environ.get("HE_LIVE_SHEET_OK"):
    raise SystemExit("refusing to run: set HE_LIVE_SHEET_OK=1 to confirm GOOGLE_SHEET_ID "
                     "is a disposable test workbook and not a production round")

APP = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(APP), str(APP / "tools")]

import bootstrap_round  # noqa: E402
import manifest  # noqa: E402
import sheets  # noqa: E402
import spec  # noqa: E402
import store  # noqa: E402

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

store.check_ready()
check(store.round_metadata()["round_id"] == manifest.round_id(), "ROUND reads back")
check(bootstrap_round.verify_blocks(book, manifest.round_id()) == [],
      "every block reads back at its recorded rows")

rid = store.review_id(manifest.round_id(), "agreement", "thiago", "SRC-0001")
store.start_review(rid, True, eval_spec_version=spec.EVAL_SPEC_VERSION)
data = store.load_review(rid)
claim = next(iter(data.responses.values()))["object_id"]
row = data.response(spec.Q1.key, claim)
stamp = store.write(sheets.RESPONSES, row["response_key"], {**row, "answer": "Yes",
                    "related_claim_id": "CLM-0001-002"}, rid=rid, expected_updated_at="")
again = store.load_review(rid).response(spec.Q1.key, claim)
check(again["answer"] == "Yes" and again["related_claim_id"] == "CLM-0001-002",
      "a structured answer round-trips")
try:
    store.write(sheets.RESPONSES, row["response_key"], {**row, "answer": "No"}, rid=rid,
                expected_updated_at="stale")
    check(False, "a stale write is refused")
except store.SaveConflict:
    check(True, "a stale write is refused")

key = store.selection_key(rid, claim, "CPT-legal-drafting")
values = {"review_id": rid, "source_id": "SRC-0001", "claim_id": claim,
          "concept_id": "CPT-legal-drafting", "active": store.TRUE}
store.upsert_selection(sheets.MISSING_CONCEPTS, key, values, rid=rid)
store.upsert_selection(sheets.MISSING_CONCEPTS, key, values, rid=rid)
check(sum(1 for r in book.read_tab(sheets.MISSING_CONCEPTS) if r["selection_key"] == key)
      == 1, "a repeated selection stays one row")

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
