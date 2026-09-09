"""Step 12 — the phase-submission and conflict behaviour, on a real workbook.

Split out of `live_sheets.py` so it can be re-run on its own: Google allows 60
read requests per minute per user, the Step 4.8 script uses most of that, and
these checks should not have to wait behind it.

    export GOOGLE_SHEET_ID='<a disposable, empty workbook>'
    export GOOGLE_SERVICE_ACCOUNT_JSON=.streamlit/service-account.json
    export HE_LIVE_SHEET_OK=1
    python app/tests/live_step12.py

**Never point this at the production workbook.** It writes answers and
submission markers. It refuses to run unless `HE_LIVE_SHEET_OK` is set.
"""
import os
import pathlib
import sys

if not os.environ.get("HE_LIVE_SHEET_OK"):
    raise SystemExit(
        "refusing to run: set HE_LIVE_SHEET_OK=1 to confirm GOOGLE_SHEET_ID is a "
        "disposable test workbook and not the production one"
    )

sys.path.insert(0, str(pathlib.Path("app").resolve()))
import manifest, progress, sheets, spec, store          # noqa: E402
from brain import load_brain                            # noqa: E402

BRAIN = load_brain()
PASS = FAIL = 0


def check(ok, msg):
    global PASS, FAIL
    print(("ok    " if ok else "FAIL  ") + msg)
    PASS, FAIL = PASS + bool(ok), FAIL + (not ok)


print(f"workbook: {sheets.sheet_id()}\naccount : {sheets.describe_account()}")

pair = [e["evaluator_id"] for e in manifest.evaluators()
        if e["agreement_split"] == "AGR-B"]
shared = manifest.assigned_source_ids(pair[0], manifest.AGREEMENT)[0]
rids = [store.review_id(manifest.AGREEMENT, e, shared) for e in pair]

print("\n== PHASE_SUBMISSIONS on the live workbook ==")
# Written to be re-runnable: what is asserted is each transition, not the state
# the workbook happened to be left in by an earlier run.
who, phase = pair[0], manifest.AGREEMENT
before = store.phase_submission(phase, who)
print(f"      starting from: {before['status'] if before else 'no marker'}")
key = store.record_phase_submission(phase, who, manifest.config_version())
marker = store.phase_submission(phase, who)
check(marker and marker["status"] == store.SUBMITTED,
      f"the marker is written and reads back ({key})")
check(marker["config_version"] == manifest.config_version(),
      "carrying the configuration it was submitted under")
check(store.phase_submitted(phase, who), "so the phase reads as submitted")

store.record_phase_submission(phase, who, manifest.config_version())
rows = store.workbook().read_tab(sheets.PHASE_SUBMISSIONS)
check(len([r for r in rows if r["submission_key"] == key]) == 1,
      f"submitting twice updates the row rather than appending ({len(rows)} rows)")

check(store.retract_phase_submission(phase, who), "reopening retracts it")
check(not store.phase_submitted(phase, who), "so the phase is no longer submitted")
kept = [r for r in store.workbook().read_tab(sheets.PHASE_SUBMISSIONS)
        if r["submission_key"] == key]
check(kept and kept[0]["status"] == store.RETRACTED,
      "and the history is kept, marked retracted rather than deleted")
check(not store.retract_phase_submission(phase, who),
      "retracting again is a no-op")

print("\n== the first-answer window, on the real workbook ==")
# The documented limitation, confirmed where it actually applies. A second tab
# that has never seen the row carries an empty expectation, which skips the
# check because honouring it would cost a read on every first answer.
# An item still blank in this workbook, so the window is exercised rather than
# an already-stamped row being re-tested.
answered = store.load_responses(rids[0])
probe = next((i for i in progress.all_possible_items(BRAIN, shared)
              if not (answered.get(i.lookup) or {}).get("updated_at")), None)
check(probe is not None,
      "there is still an unanswered item to race two tabs on")
def write(rid, answer, expected):
    return store.save_responses([{
        "rid": rid, "object_type": probe.object_type, "object_id": probe.object_id,
        "question_key": probe.question.question_key,
        "criterion_id": probe.question.criterion_id,
        "field_subitem": probe.question.field_subitem, "answer": answer,
        "comment": f"tab said {answer}", "applicability": spec.APPLICABLE,
        "source_id": shared, "expected_updated_at": expected}])[0]

check(not (answered.get(probe.lookup) or {}).get("updated_at"),
      f"and it carries no stamp ({probe.question.criterion_id} on {probe.object_id})")
stamp_a = write(rids[0], "Yes", "")
refused = False
try:
    write(rids[0], "No", "")            # a second tab, also expecting nothing
except store.SaveConflict:
    refused = True
check(not refused, "the second tab is not refused — the documented window")
check(store.load_responses(rids[0])[probe.lookup]["answer"] == "No",
      "and its answer wins")
refused = False
try:
    write(rids[0], "In part", stamp_a)  # the first tab, on the stamp it holds
except store.SaveConflict:
    refused = True
check(refused, "while the first tab's next edit IS refused, as designed")

print("\n== phase switches through CONFIG ==")
# Restored in a finally: a run that stops here for any reason — the read quota,
# a dropped connection — must not leave the workbook with a phase closed.
was = manifest.phase_open(manifest.AGREEMENT)
try:
    manifest.set_phase(manifest.AGREEMENT, not was)
    check(manifest.phase_open(manifest.AGREEMENT) is (not was),
          "a phase switch written to CONFIG takes effect without waiting for a TTL")
    settings = {r["key"]: r["value"] for r in store.workbook().read_tab(sheets.CONFIG)}
    check(str(settings.get("agreement_open", "")).lower() in ("true", "false"),
          f"and is stored as a plain value ({settings.get('agreement_open')})")
finally:
    manifest.set_phase(manifest.AGREEMENT, was)
    manifest.invalidate()
check(manifest.phase_open(manifest.AGREEMENT) is was, "and switches back")


print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
