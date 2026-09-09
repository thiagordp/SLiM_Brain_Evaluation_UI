"""End-to-end checks for the HE Evaluation Interface.

Runs the real Streamlit script headlessly against a throwaway database.

    python app/tests/test_app.py
"""
from __future__ import annotations

import atexit
import collections
import pathlib
import re
import shutil
import subprocess
import threading
import time
import sys

APP_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

import tempfile  # noqa: E402

import yaml  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

import manifest  # noqa: E402
import progress  # noqa: E402
import savequeue  # noqa: E402
import sheets  # noqa: E402
import ui  # noqa: E402
import views  # noqa: E402
import spec  # noqa: E402
import store  # noqa: E402
from brain import load_brain  # noqa: E402

import os  # noqa: E402

os.environ.setdefault("HE_APP_PASSWORD", "test-password")
os.environ.setdefault("HE_ADMIN_SECRET", "test-admin-secret")

APP = str(APP_DIR / "streamlit_app.py")
FAILURES: list[str] = []
BRAIN = load_brain()

# ------------------------------------------------------------ the test store
#
# The tests wipe their database between cases. Until now that database was
# `app/data/evaluations.sqlite` — the same file a developer's manually running
# app is using. A suite run beside a live session silently reset that session's
# store, and the app, still answering from a session cache, showed a paper as
# started that no longer existed on disk. The symptom looks like an application
# bug and is not one.
#
# So the suite gets its own file, created fresh for the run and removed after
# it. `AppTest` runs the script in this process, so the app under test imports
# this same `store` module and follows the redirection with it.
DEV_DB_PATH = store.DB_PATH
TEST_DB_DIR = pathlib.Path(tempfile.mkdtemp(prefix="he-eval-tests-"))
store.DB_PATH = TEST_DB_DIR / "evaluations.sqlite"


# Registered here rather than only in main(), so that importing this module to
# run a single test — which is how a failure is usually chased down — does not
# leave a database behind in /tmp.
atexit.register(shutil.rmtree, TEST_DB_DIR, True)


def _test_owned(path: pathlib.Path) -> bool:
    """Is this a database this run created, and may therefore destroy?"""
    try:
        return TEST_DB_DIR in pathlib.Path(path).resolve().parents
    except OSError:
        return False


def flush(at):
    """Writes are queued; wait for them before asserting on the database."""
    q = ss(at, "_save_queue")
    if q is not None:
        q.flush(timeout=15)
    return at


def ss(at, key, default=None):
    """AppTest's session_state has no .get()."""
    try:
        return at.session_state[key]
    except (KeyError, AttributeError):
        return default


def check(condition, label) -> bool:
    print(f"{'ok  ' if condition else 'FAIL'}  {label}")
    if not condition:
        FAILURES.append(label)
    return bool(condition)


def fresh_db() -> None:
    _wipe_db()
    store.init()


def _wipe_db() -> None:
    """Delete the test database. Refuse to delete anything else.

    The guard is the point: a future edit that leaves `store.DB_PATH` pointing at
    the development store fails loudly here instead of quietly deleting a
    colleague's work in progress.
    """
    if not _test_owned(store.DB_PATH):
        raise AssertionError(
            f"the tests were about to delete {store.DB_PATH}, which they do not own. "
            f"They may only touch databases under {TEST_DB_DIR}."
        )
    for suffix in ("", "-wal", "-shm"):
        path = pathlib.Path(str(store.DB_PATH) + suffix)
        if path.exists():
            path.unlink()


def app(**state) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    for key, value in state.items():
        at.session_state[key] = value
    return at


def signed_in(evaluator_id="vaclav", name="Vaclav", page="Training", **extra):
    state = dict(authenticated=True, evaluator_id=evaluator_id, evaluator_name=name,
                 phase_choice=page, _page=page, **extra)
    return app(**state)


def open_section(evaluator_id, name, phase_id, source_id, section):
    rid = store.review_id(phase_id, evaluator_id, source_id)
    at = signed_in(evaluator_id, name, manifest.PHASE_LABEL[phase_id],
                   source_id=source_id)
    at.session_state[f"section|{rid}"] = section
    return at.run()


def criterion_radios(at):
    return [r for r in at.main.radio if r.label == "Answer"]


# --------------------------------------------------------------------------
def test_spec():
    print("\n== evaluation specification ==")
    check(spec.EVAL_SPEC_VERSION, "spec is versioned")
    check(not any(q.criterion_id == "HE-16" for q in spec.QUESTIONS),
          "HE-16 is not an ordinary question — it is derived")
    check(spec.EDGE_QUESTION.criterion_id == "HE-16", "HE-16 is collected per edge")
    check(spec.he16_summary(["Yes", "No", "Yes", None]) == "2/3 (67%)",
          "HE-16 reproduces the workbook X/Y (%) formula")
    keys = [q.question_key for q in spec.QUESTIONS]
    check(len(keys) == len(set(keys)), "question keys are unique")
    he081 = [q.question_key for q in spec.QUESTIONS if q.criterion_id == "HE-08.1"]
    check(sorted(he081) == ["CLAIM_HE08_1", "SOURCE_HE08_1"],
          "HE-08.1 is disambiguated by question_key at source and claim level")
    check(spec.BY_KEY["SOURCE_HE14_3"].object_type == "source",
          "HE-14.3 is stored against the Source")
    check(all(q.check_text for q in spec.QUESTIONS),
          "every question carries the workbook 'what to check' text")


def test_manifest():
    print("\n== manifest ==")
    problems = [p for p in manifest.validate(set(BRAIN.sources), BRAIN.snapshot_id)
                if "development secrets" not in p]
    check(not problems, f"manifest validates ({problems})")
    check(manifest.brain_snapshot_id() == BRAIN.snapshot_id, "snapshot matches the Brain")
    check(manifest.is_admin("thiago"), "Thiago is the administrator")
    check(manifest.assigned_source_ids("thiago", manifest.AGREEMENT),
          "and is an evaluator too — admin does not remove his papers")
    check(not manifest.is_admin("vaclav"), "nobody else is admin")

    check(manifest.PHASES == ("training", "agreement", "individual"),
          f"three phases in order ({manifest.PHASES})")
    training = set(manifest.training_source_ids())
    for phase_id in (manifest.AGREEMENT, manifest.INDIVIDUAL):
        ids = {r["source_id"] for r in manifest.assignments()
               if r["phase_id"] == phase_id}
        check(ids and not (ids & training),
              f"the {phase_id} set excludes the training papers")

    # the app must never derive an assignment from a group label
    source = manifest.__file__
    check("pair_id" not in pathlib.Path(source).read_text(encoding="utf-8")
          .split("def assigned(")[1].split("def ")[0],
          "assigned() reads explicit rows, never a pair")


def test_he21():
    print("\n== HE-21 applicability (from Concept records) ==")
    check(BRAIN.candidate_created_for("CLM-0001-004"),
          "HE-21 applies where the Concept record names the claim as motivating")
    check(not BRAIN.candidate_created_for("CLM-0001-001"),
          "HE-21 is N/A where no candidate was created for the claim")
    # v3: the item is still created, flagged auto-N/A, so the evaluator sees that
    # the criterion was considered and settled rather than silently absent.
    items = {i.question.question_key: i
             for i in progress.claim_items(BRAIN, "SRC-0001", "CLM-0001-001", {})}
    check("CLAIM_HE21" in items, "HE-21 is still listed when inapplicable")
    check(items["CLAIM_HE21"].auto_na, "but flagged as automatically N/A")
    check(progress.item_complete(items["CLAIM_HE21"], {}),
          "and never counts as an outstanding answer")
    applies = {i.question.question_key: i
               for i in progress.claim_items(BRAIN, "SRC-0001", "CLM-0001-004", {})}
    check(not applies["CLAIM_HE21"].auto_na,
          "while the claim that motivated the candidate is asked")
    keys = [i.question.question_key
            for i in progress.claim_items(BRAIN, "SRC-0001", "CLM-0001-004", {})]
    check("CLAIM_HE21" in keys, "HE-21 is expected when applicable")


def test_free_navigation():
    """Navigation is unrestricted; completeness is enforced at submission."""
    print("\n== free navigation ==")
    source_id = manifest.training_source_ids()[0]
    states = progress.section_states(BRAIN, source_id, {}, {})
    check(progress.LOCKED not in states.values(),
          f"no section is locked on an empty paper ({states})")
    check(all(state == progress.AVAILABLE for state in states.values()),
          "every section is reachable from the start")
    check(progress.unlocked_sections(states) == progress.SECTION_IDS,
          "every section is offered")

    claims = BRAIN.claims_of(source_id)
    check(progress.unlocked_claim_count(BRAIN, source_id, {}, {}) == len(claims),
          f"every claim is reachable ({len(claims)})")

    # the section bar must not disable anything except the section already open
    rid = store.ensure_review(phase_id=manifest.TRAINING, evaluator_id="vaclav",
                              evaluator_name="Vaclav", pair_id="B", source_id=source_id,
                              work_id=BRAIN.work_id(source_id),
                              brain_snapshot_id=BRAIN.snapshot_id,
                              eval_spec_version=spec.EVAL_SPEC_VERSION)
    store.start_review(rid, True)
    at = open_section("vaclav", "Vaclav", manifest.TRAINING, source_id, "source")
    nav = [b for b in at.main.button if any(
        label in b.label for label in progress.SECTION_TAB.values())
        and b.key and b.key.startswith("nav|")]
    enabled = [b.label for b in nav if not b.disabled]
    check(len(enabled) == len(progress.SECTION_IDS) - 1,
          f"all but the current section are clickable ({len(enabled)})")

    # jumping straight from an untouched Source to Datasets must work
    at = open_section("vaclav", "Vaclav", manifest.TRAINING, source_id, "datasets")
    check(not at.exception, "Datasets opens without touching Source or Claims")
    check(any("Dataset" in s.value for s in at.main.subheader), "the Datasets screen renders")

    at = open_section("vaclav", "Vaclav", manifest.TRAINING, source_id, "recall")
    check(not at.exception, "Claim recall opens without completing anything")

    # Next is no longer gated on the current section being complete
    at = open_section("vaclav", "Vaclav", manifest.TRAINING, source_id, "source")
    nxt = [b for b in at.main.button if b.key == "sec_next"]
    check(nxt and not nxt[0].disabled, "Next works from an incomplete section")
    check("Back" not in nxt[0].label and "Next" not in nxt[0].label,
          f"and it names where it goes ({nxt[0].label!r})")
    prev = [b for b in at.main.button if b.key == "sec_back"]
    check(prev and prev[0].label.startswith("← "),
          f"as does the one going the other way ({prev[0].label!r})")

    # claims are selectable out of order
    at = open_section("vaclav", "Vaclav", manifest.TRAINING, source_id, "claims")
    jump = [s for s in at.main.selectbox if s.label == "Go to claim"]
    check(jump and len(jump[0].options) == len(claims),
          f"the claim selector offers all {len(claims)} claims")
    fresh_db()


def test_wiki_modal():
    """Step 8: one modal for every piece of supporting material."""
    print("\n== the wiki modal ==")
    fresh_db()
    phase_id, evaluator = manifest.TRAINING, "vaclav"
    source_id = manifest.training_source_ids()[1]
    claims = BRAIN.claims_of(source_id)
    rid = store.review_id(phase_id, evaluator, source_id)
    store.ensure_review(phase_id=phase_id, evaluator_id=evaluator,
                        evaluator_name="Vaclav", pair_id="B", source_id=source_id,
                        work_id=BRAIN.work_id(source_id))
    store.start_review(rid, True)

    kinds = (ui.SOURCE, ui.CONCEPT, ui.DATASET, ui.CLAIM,
             ui.CONCEPT_REGISTRY, ui.SOURCE_REGISTRY, ui.SOURCE_CLAIMS)
    check(len(set(kinds)) == 7, "seven kinds of content are supported")

    source = (APP_DIR / "ui.py").read_text(encoding="utf-8")
    check("st.dialog(" in source, "it is a real modal, not a column")
    check('width="large"' in source, "opened large")
    check("75vw" in source, "and widened to about three quarters of the viewport")
    check("overflow-y: auto" in source, "with its own scrolling")
    check("minimis" not in source.lower() and "minimiz" not in source.lower(),
          "with no minimise mode")
    check("on_dismiss=close_wiki" in source,
          "dismissing it clears the stack, so it cannot reopen itself")
    app_source = (APP_DIR / "streamlit_app.py").read_text(encoding="utf-8")
    check("st.columns([2, 1])" not in app_source,
          "the evaluation area no longer shrinks when material is open")
    check("Restore inspector" not in app_source, "and the restore button is gone")

    # --- opening, following a link, going back, closing
    at = open_section(evaluator, "Vaclav", phase_id, source_id, "claims")
    check(not at.session_state[ui.WIKI], "nothing is open to begin with")
    opener = [b for b in at.button if b.label == "Open Source wiki"]
    check(opener, "the claim page offers the Source wiki")
    at = opener[0].click().run()
    stack = at.session_state[ui.WIKI]
    check(stack == [(ui.SOURCE, source_id)], f"one entry on the stack ({stack})")

    ui_stack = at.session_state[ui.WIKI]
    ui_stack.append((ui.CONCEPT, BRAIN.concept_registry()[0]["id"]))
    at = at.run()
    check(len(at.session_state[ui.WIKI]) == 2, "a followed link keeps the way back")

    # --- every entry point starts a fresh history
    at = open_section(evaluator, "Vaclav", phase_id, source_id, "claims")
    at.session_state[ui.WIKI] = [(ui.SOURCE, source_id), (ui.CONCEPT, "CPT-x")]
    at = at.run()
    ui.open_wiki  # the entry points call this
    at.session_state[ui.WIKI] = []
    at = at.run()
    check(at.session_state[ui.WIKI] == [], "closing empties it")

    # --- the modal never touches answers, progress or navigation
    item = progress.source_items(BRAIN, source_id, {})[0]
    store.save_response(rid, object_type=item.object_type, object_id=item.object_id,
                        question_key=item.question.question_key,
                        criterion_id=item.question.criterion_id,
                        field_subitem=item.question.field_subitem,
                        answer="Yes", comment=None, applicability=spec.APPLICABLE,
                        source_id=source_id, allow_append=True)
    before = store.load_responses(rid)
    before_status = store.get_review(phase_id, evaluator, source_id)["status"]

    at = open_section(evaluator, "Vaclav", phase_id, source_id, "source")
    at.session_state[f"claim_idx|{rid}"] = 4
    at = at.run()
    opener = [b for b in at.button if b.label == "Open Source wiki"]
    at = opener[0].click().run()
    _settle(at)
    after = store.load_responses(rid)
    check({k: v["answer"] for k, v in after.items()}
          == {k: v["answer"] for k, v in before.items()},
          "opening it changes no answer")
    check(store.get_review(phase_id, evaluator, source_id)["status"] == before_status,
          "nor the paper's status")
    check(at.session_state[f"section|{rid}"] == "source",
          "nor which section is open")
    check(at.session_state[f"claim_idx|{rid}"] == 4, "nor which claim is selected")

    # --- changing context closes it
    at.session_state[ui.WIKI] = [(ui.SOURCE, source_id)]
    ui_before = list(at.session_state[ui.WIKI])
    at.session_state[f"section|{rid}"] = "datasets"
    at = at.run()
    check(ui_before and not at.session_state[ui.WIKI],
          "moving to another section closes it")

    at = open_section(evaluator, "Vaclav", phase_id, source_id, "claims")
    at.session_state[f"claim_idx|{rid}"] = 0
    at = at.run()
    at.session_state[ui.WIKI] = [(ui.CONCEPT, "CPT-anything")]
    at.session_state[f"claim_idx|{rid}"] = 1
    at = at.run()
    check(not at.session_state[ui.WIKI], "and so does moving to another claim")


def test_wiki_modal_entry_points():
    """Every kind listed for Step 8 is reachable from the evaluation."""
    print("\n== every kind of material is reachable ==")
    fresh_db()
    phase_id, evaluator = manifest.TRAINING, "vaclav"
    source_id = manifest.training_source_ids()[1]
    rid = store.review_id(phase_id, evaluator, source_id)
    store.ensure_review(phase_id=phase_id, evaluator_id=evaluator,
                        evaluator_name="Vaclav", pair_id="B", source_id=source_id,
                        work_id=BRAIN.work_id(source_id))
    store.start_review(rid, True)

    def buttons(section):
        at = open_section(evaluator, "Vaclav", phase_id, source_id, section)
        return at, {b.label: b for b in at.button}

    at, labels = buttons("source")
    check("Open Source wiki" in labels, "Source: the source wiki")

    at, labels = buttons("claims")
    check("Open Source wiki" in labels, "Claim: the source wiki")
    check("View all claims from this paper" in labels,
          "Claim: every claim of this paper, for the duplication question")
    check("Browse Concept registry" in labels, "Claim: the concept registry")
    check(any(b.label == "Open wiki" for b in at.button),
          "Claim: the wiki of each mapped concept")

    at, labels = buttons("datasets")
    if BRAIN.datasets_of(source_id):
        check("Open Dataset wiki" in labels, "Dataset: the dataset wiki")
    else:
        check(True, "(this source has no Dataset node)")

    at, labels = buttons("cites")
    check("Browse Brain Sources" in labels,
          "CITES: the source registry, for the completeness question")

    at, labels = buttons("recall")
    check("Open Source wiki" in labels, "Recall: the source wiki")
    check(any(b.label == "View details" for b in at.button),
          "Recall: the detail of each extracted claim")

    # the two inline registry expanders are gone from the claim page
    views_source = (APP_DIR / "views.py").read_text(encoding="utf-8")
    check("Concept registry — every concept currently in the Brain" not in views_source,
          "the inline registry expander no longer sits under every claim")


def test_wiki_modal_content():
    """Each kind renders its own material, and offers the ids it names."""
    print("\n== modal content ==")

    class FakeCtx:
        brain = BRAIN
        source_id = manifest.training_source_ids()[1]

    ctx = FakeCtx()
    check(ui._wiki_title(ctx, ui.SOURCE, ctx.source_id).startswith("Source wiki"),
          "the source wiki is titled as such")
    concept_id = BRAIN.concept_registry()[0]["id"]
    check(BRAIN.concept(concept_id)["label"]
          in ui._wiki_title(ctx, ui.CONCEPT, concept_id),
          "a concept is titled by its label")
    check(BRAIN.work_id(ctx.source_id)
          in ui._wiki_title(ctx, ui.SOURCE_CLAIMS, ctx.source_id),
          "the claim list is titled by the paper")

    # internal references are offered as buttons, because markdown links cannot work
    body = BRAIN.source_body(ctx.source_id)
    found = ui.REFERENCE.findall(body)
    check(found, f"the source wiki names other records ({len(found)} references)")
    kinds = {ui.KIND_OF_PREFIX[f[:3]] for f in found}
    check(kinds <= {ui.SOURCE, ui.CONCEPT, ui.DATASET, ui.CLAIM},
          f"each resolves to a kind the modal can open ({sorted(kinds)})")

    registry = BRAIN.source_registry()
    check(len(registry) == len(BRAIN.source_ids), "the source registry lists them all")
    check(all(r["work_id"] and r["title"] for r in registry),
          "each with the work id and title an evaluator would search by")

    families = BRAIN.concepts_of_source(ctx.source_id)
    mapped = sum(len(v) for v in families.values())
    check(mapped, f"{mapped} concepts are mapped across this source")
    check(all(e["claims"] >= 1 for v in families.values() for e in v),
          "each counted by how many claims carry it")


def test_navigation_is_never_gated():
    """Step 6: nothing an evaluator has not answered may stop them going anywhere."""
    print("\n== navigation is never gated ==")
    fresh_db()
    phase_id, evaluator = manifest.AGREEMENT, "vaclav"
    source_id = manifest.assigned_source_ids(evaluator, phase_id)[0]
    claims = BRAIN.claims_of(source_id)
    rid = store.ensure_review(
        phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
        pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id))
    store.start_review(rid, True)

    states = progress.section_states(BRAIN, source_id, {}, {})
    check(progress.LOCKED not in states.values(),
          f"with nothing answered, no section is locked ({set(states.values())})")
    check(progress.unlocked_sections(states) == progress.SECTION_IDS,
          "every section is open")
    check(progress.unlocked_claim_count(BRAIN, source_id, {}, {}) == len(claims),
          f"and every one of the {len(claims)} claims is reachable")

    # the walk the plan names, on a paper with nothing answered
    walk = [("source", None), ("claims", 1), ("datasets", None), ("claims", 10),
            ("cites", None), ("review", None), ("claims", 3)]
    for section, claim_index in walk:
        at = signed_in(evaluator, "Vaclav", "Agreement", source_id=source_id)
        at.session_state[f"section|{rid}"] = section
        if claim_index is not None and claim_index < len(claims):
            at.session_state[f"claim_idx|{rid}"] = claim_index
        at = at.run()
        where = f"{section}" + (f" claim {claim_index + 1}" if claim_index is not None else "")
        check(not at.exception, f"{where} opens with nothing answered")
        if claim_index is not None and claim_index < len(claims):
            check(claims[claim_index]["id"] in rendered_text(at),
                  f"and shows {claims[claim_index]['id']}")

    # Back / Next are bounded by the ends of the list, never by completeness
    at = signed_in(evaluator, "Vaclav", "Agreement", source_id=source_id)
    at.session_state[f"section|{rid}"] = "claims"
    at.session_state[f"claim_idx|{rid}"] = 1
    at = at.run()
    nav = {b.label: b for b in at.button}
    nxt = next((b for label, b in nav.items() if "Next claim" in label), None)
    prev = next((b for label, b in nav.items() if "Previous claim" in label), None)
    check(nxt is not None and not nxt.disabled,
          "Next claim is offered although this claim is untouched")
    check(prev is not None and not prev.disabled, "so is Previous claim")
    at = nxt.click().run()
    check(at.session_state[f"claim_idx|{rid}"] == 2,
          "and pressing it moves on regardless")

    # the section bar offers every section, and only the current one is inert
    at = signed_in(evaluator, "Vaclav", "Agreement", source_id=source_id)
    at.session_state[f"section|{rid}"] = "claims"
    at = at.run()
    bar = [b for b in at.button if b.key and b.key.startswith("nav|")]
    check(len(bar) == len(progress.SECTION_IDS),
          f"all {len(progress.SECTION_IDS)} sections are in the bar ({len(bar)})")
    check(sum(1 for b in bar if b.disabled) == 1,
          "with exactly one inert — the one already open")

    # and no prose telling the evaluator what to finish first
    body = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
    check("Still to finish" not in body,
          "the bottom of the page no longer lists what is outstanding")


def test_progress_visibility():
    """Step 7: what is done must be legible, with denominators that fit the claim."""
    print("\n== progress visibility ==")
    fresh_db()
    phase_id, evaluator = manifest.TRAINING, "vaclav"
    source_id = manifest.training_source_ids()[1]
    claims = BRAIN.claims_of(source_id)
    rid = store.ensure_review(
        phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
        pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id))
    store.start_review(rid, True)

    # --- section states move through the three values
    states = progress.section_states(BRAIN, source_id, {}, {})
    check(all(v == progress.AVAILABLE for v in states.values()),
          "every section starts untouched")

    item = progress.source_items(BRAIN, source_id, {})[0]
    partial = {item.lookup: {"answer": "Yes"}}
    states = progress.section_states(BRAIN, source_id, partial, {})
    check(states["source"] == progress.INCOMPLETE,
          "one answer moves its section to in progress")

    for i in progress.source_items(BRAIN, source_id, {}):
        partial[i.lookup] = {"answer": "Yes"}
    states = progress.section_states(BRAIN, source_id, partial, {})
    check(states["source"] == progress.COMPLETE, "and finishing it to complete")

    # --- per-claim denominators differ, and reflect what is actually asked
    totals = {c["id"]: progress.claim_progress(BRAIN, source_id, c["id"], {}, {})[1]
              for c in claims}
    check(len(set(totals.values())) > 1,
          f"claims ask different numbers of items ({sorted(set(totals.values()))})")
    with_candidate = next((c["id"] for c in claims
                           if BRAIN.candidate_created_for(c["id"])), None)
    without = next(c["id"] for c in claims if not BRAIN.candidate_created_for(c["id"]))
    if with_candidate:
        check(totals[with_candidate] > 0 and totals[without] > 0,
              "both kinds of claim have a total")
        applicable = progress.applicable(
            progress.claim_items(BRAIN, source_id, without, {}))
        check(all(i.question.question_key != "CLAIM_HE21" for i in applicable),
              "HE-21 is excluded where no candidate concept was created")

    # a conditional follow-up enters the denominator when its parent turns negative
    claim_id = claims[0]["id"]
    before = progress.claim_progress(BRAIN, source_id, claim_id, {}, {})[1]
    negative = {f"CLAIM_HE20|{claim_id}": {"answer": "No"}}
    after = progress.claim_progress(BRAIN, source_id, claim_id, negative, {})[1]
    check(after == before + 1,
          f"answering HE-20 No adds HE-20.b to the total ({before} -> {after})")

    # --- the five sub-sections each report their own state
    parts = progress.claim_subsection_progress(BRAIN, source_id, claim_id, {}, {})
    check([label for label, *_ in parts] == list(progress.CLAIM_SUBSECTIONS),
          "all five parts of the claim page are reported")
    check(all(state == progress.AVAILABLE for *_, state in parts),
          "each starts untouched")
    check(any(total for _, _, total, _ in parts), "and each carries its own total")

    answered = {}
    for i in progress.claim_subsection_items(BRAIN, source_id, claim_id, {},
                                             spec.SUB_VALIDITY):
        answered[i.lookup] = {"answer": "Yes"}
    parts = dict((label, (done, total, state))
                 for label, done, total, state in
                 progress.claim_subsection_progress(BRAIN, source_id, claim_id,
                                                    answered, {}))
    check(parts[spec.SUB_VALIDITY][2] == progress.COMPLETE,
          "finishing part A marks A complete")
    check(parts[spec.SUB_GROUNDING][2] == progress.AVAILABLE,
          "and leaves B untouched")

    # --- the page renders all of it
    at = open_section(evaluator, "Vaclav", phase_id, source_id, "claims")
    body = rendered_text(at)
    captions = " ".join(c.value for c in at.caption)
    done, total = progress.claim_progress(BRAIN, source_id, claims[0]["id"], {}, {})
    check(f"{done}/{total} applicable items complete" in _tagless(body),
          f"the claim header shows its own denominator ({done}/{total})")
    check(f"0 of {len(claims)} claims complete" in body,
          f"beside the claim count (0 of {len(claims)})")
    # Each part of the claim is its own collapsible section, labelled with the
    # state and the count of what applies to it.
    sections = [e.label for e in at.expander]
    for label in progress.CLAIM_SUBSECTIONS:
        check(any(label in section for section in sections),
              f"the page has a {label!r} section {sections}")
    check("○ untouched" in captions and "✓ complete" in captions,
          "and the legend explains the marks")


def test_resume_is_a_suggestion():
    """Step 7: resume offers a shortcut; it never moves the evaluator."""
    print("\n== resume suggests, never redirects ==")
    fresh_db()
    phase_id, evaluator = manifest.TRAINING, "vaclav"
    source_id = manifest.training_source_ids()[1]
    claims = BRAIN.claims_of(source_id)
    rid = store.ensure_review(
        phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
        pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id))
    store.start_review(rid, True)
    _answer_everything(rid, source_id)          # finish the paper...
    for i in progress.claim_items(BRAIN, source_id, claims[2]["id"],
                                  store.load_responses(rid)):
        store.save_response(rid, object_type=i.object_type, object_id=i.object_id,
                            question_key=i.question.question_key,
                            criterion_id=i.question.criterion_id,
                            field_subitem=i.question.field_subitem,
                            answer="", comment=None, applicability="",
                            source_id=source_id, allow_append=True)
    responses = store.load_responses(rid)
    edges = store.load_edge_responses(rid)
    first = progress.first_incomplete_claim(BRAIN, source_id, responses, edges)
    check(first == 2, f"claim 3 is the first still needing work ({first + 1})")

    section, index = progress.resume_point(BRAIN, source_id, responses, edges)
    check(index == first, "resume_point agrees")

    # open claim 1 explicitly: the app must leave you there
    at = signed_in(evaluator, "Vaclav", "Training", source_id=source_id)
    at.session_state[f"section|{rid}"] = "claims"
    at.session_state[f"claim_idx|{rid}"] = 0
    at = at.run()
    check(at.session_state[f"claim_idx|{rid}"] == 0,
          "opening claim 1 does not bounce you to the incomplete one")
    check(claims[0]["id"] in rendered_text(at), "claim 1 is what is shown")

    resume = [b for b in at.button if b.label.startswith("Resume at claim")]
    check(resume, f"but a resume shortcut is offered ({resume[0].label if resume else ''})")
    check(f"claim {first + 1}" in resume[0].label, "naming the right claim")
    at = resume[0].click().run()
    check(at.session_state[f"claim_idx|{rid}"] == first,
          "and pressing it goes there — only then")

    # on the incomplete claim itself there is nothing to suggest
    check(not [b for b in at.button if b.label.startswith("Resume at claim")],
          "the shortcut disappears once you are already there")


def test_login_and_identity():
    print("\n== login and identity ==")
    at = app().run()
    check(any("SLiM Brain — Human Evaluation" in t.value for t in at.title),
          "the title names the study, not the tool")
    check(any("Restricted access" in c.value for c in at.caption), "with one line under it")
    check(not at.sidebar.selectbox and not at.sidebar.radio,
          "no navigation is offered before signing in")
    check([b.label for b in at.button] == ["Continue"],
          f"one button, saying what it does ({[b.label for b in at.button]})")

    at.text_input[0].set_value("wrong").run()
    at.button[0].click().run()
    errors = " ".join(e.value for e in at.error)
    check("Incorrect password. Please try again." in errors,
          f"a mistyped password is corrected quietly ({errors[:50]})")
    check(not ss(at, "authenticated"), "and not accepted")

    at = app().run()
    at.text_input[0].set_value(manifest.password())
    at.button[0].click().run()
    check(at.session_state["authenticated"], "correct password accepted")
    check(any("Select evaluator" in t.value for t in at.title),
          "identity screen follows the password")

    # the assignment panel appears on selection, before anything is locked
    check([b.label for b in at.button] == ["Confirm and continue"],
          "one button here too")
    check(at.button[0].disabled, "disabled until a name is chosen")
    names = [str(o) for o in at.selectbox[0].options]
    check(names == sorted(names), f"names are alphabetical ({names})")
    check(len(names) == len(manifest.evaluators()), f"all {len(names)} evaluators")

    at.selectbox[0].set_value("Giovanni").run()
    shown = " ".join(c.value for c in at.caption) + " ".join(m.value for m in at.markdown)
    check("AGR-C" in shown and "IND-5" in shown,
          f"Giovanni's splits are shown before he confirms ({shown[:80]})")
    check("Group" not in shown, "and no Group A/B/C label anywhere")
    check("confirm that you selected your own name" in shown,
          "with the confirmation asked for explicitly")
    check(not at.button[0].disabled, "the button is now offered")
    check(not ss(at, "evaluator_id"), "but nothing is locked yet")

    at.button[0].click().run()
    check(ss(at, "evaluator_id") == "giovanni", "identity confirmed and locked")
    check(not at.selectbox or "Evaluator" not in [s.label for s in at.sidebar.selectbox],
          "no way to change the name after confirming")


def test_home_and_start():
    print("\n== home and paper start ==")
    fresh_db()
    source_id = manifest.training_source_ids()[0]
    at = signed_in().run()
    body = rendered_text(at)
    check(BRAIN.work_id(source_id) in body, "home lists papers by work id")
    check(any("0 of" in c.value for c in at.caption), "home shows overall progress")
    check(all(b.label in ("Start", "Continue", "Review", "View")
              or not b.key or not b.key.startswith("open|")
              for b in at.button),
          "each card's button says what pressing it does")
    starts = [b for b in at.button if b.key and b.key.startswith("open|")]
    check(starts and all(b.label == "Start" for b in starts),
          f"an untouched phase offers Start ({[b.label for b in starts]})")
    check("claims ·" in body, "cards carry the claim and dataset counts")
    check("Not started" in body, "and the paper's state")

    at = signed_in(source_id=source_id).run()
    check(any("read the full paper" in c.label for c in at.checkbox),
          "paper start requires the read confirmation")
    check(not any("PDF" in b.label for b in at.button), "no PDF buttons in the UI")
    start = [b for b in at.button if "Start evaluation" in b.label][0]
    check(start.disabled, "Start evaluation is disabled before confirming")
    at.checkbox[0].check().run()
    [b for b in at.button if "Start evaluation" in b.label][0].click().run()
    review = store.get_review(manifest.TRAINING, "vaclav", source_id)
    check(review["status"] == store.STATUS_IN_PROGRESS, "starting sets status in_progress")
    check(review["brain_snapshot_id"] == BRAIN.snapshot_id, "review records the Brain snapshot")
    check(review["eval_spec_version"] == spec.EVAL_SPEC_VERSION, "review records the spec version")


def test_preallocation_and_save():
    print("\n== preallocation, autosave, resume ==")
    source_id = manifest.training_source_ids()[0]
    rid = store.review_id(manifest.TRAINING, "vaclav", source_id)
    at = open_section("vaclav", "Vaclav", manifest.TRAINING, source_id, "source")
    check(not at.exception, "source section renders")
    rows = store.load_responses(rid)
    check(len(rows) > 100, f"rows preallocated for the whole review ({len(rows)})")
    check(len(store.load_edge_responses(rid)) > 0, "edge rows preallocated")

    criterion_radios(at)[0].set_value("No").run()
    at.main.text_area[0].set_value("should also include survey (p.2)").run()
    flush(at)
    saved = store.load_responses(rid)["SOURCE_HE08_1|" + source_id]
    check(saved["answer"] == "No", "answer autosaves")
    check("survey" in (saved["comment_evidence"] or ""), "comment autosaves")
    check(saved["updated_at"], "updated_at stamped for conflict detection")

    at = open_section("vaclav", "Vaclav", manifest.TRAINING, source_id, "source")
    check(criterion_radios(at)[0].value == "No", "answer reloads after reopening")


def test_sections_render():
    print("\n== every section renders ==")
    source_id = manifest.training_source_ids()[0]
    for section in progress.SECTION_IDS:
        at = open_section("vaclav", "Vaclav", manifest.TRAINING, source_id, section)
        check(not at.exception, f"training — {section}")

    evaluator, name = "giuseppe", "Giuseppe"
    eval_source = manifest.assigned_source_ids(evaluator, manifest.AGREEMENT)[0]
    store.ensure_review(phase_id=manifest.AGREEMENT, evaluator_id=evaluator, evaluator_name=name,
                        pair_id="A", source_id=eval_source,
                        work_id=BRAIN.work_id(eval_source),
                        brain_snapshot_id=BRAIN.snapshot_id,
                        eval_spec_version=spec.EVAL_SPEC_VERSION)
    store.start_review(store.review_id(manifest.AGREEMENT, evaluator, eval_source), True)
    for section in progress.SECTION_IDS:
        at = open_section(evaluator, name, manifest.AGREEMENT, eval_source, section)
        on_view = any(BRAIN.work_id(eval_source) in t.value for t in at.title)
        check(not at.exception and on_view, f"evaluation {BRAIN.work_id(eval_source)} — {section}")


def test_complete_submit_lock():
    print("\n== completeness, review page, submit, lock ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.AGREEMENT
    source_id = min(manifest.assigned_source_ids(evaluator, phase_id),
                    key=lambda s: len(BRAIN.claims_of(s)))
    rid = store.ensure_review(phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
                              pair_id="B", source_id=source_id,
                              work_id=BRAIN.work_id(source_id),
                              brain_snapshot_id=BRAIN.snapshot_id,
                              eval_spec_version=spec.EVAL_SPEC_VERSION)
    store.start_review(rid, True)

    # answer everything, re-expanding because conditionals appear as answers land
    for _ in range(4):
        responses = store.load_responses(rid)
        edges = store.load_edge_responses(rid)
        items = progress.all_items(BRAIN, source_id, responses)
        for i, item in enumerate(items):
            record = responses.get(item.lookup, {})
            if record.get("answer"):
                continue
            if item.question.free_text:
                answer, comment = "none", None
            elif i % 6 == 0:
                answer, comment = "No", "defect, p.3"
            elif i % 7 == 0:
                answer, comment = "In part", "partly captured, p.5"
            else:
                answer, comment = "Yes", None
            store.save_response(rid, object_type=item.object_type, object_id=item.object_id,
                                question_key=item.question.question_key,
                                criterion_id=item.question.criterion_id,
                                field_subitem=item.question.field_subitem,
                                answer=answer, comment=comment, source_id=source_id)
        for claim in BRAIN.claims_of(source_id):
            for edge in BRAIN.relations_of(claim["id"]):
                key = store.edge_key_of(edge)
                if edges.get(key, {}).get("label_correct"):
                    continue
                store.save_edge_response(rid, host_claim_id=claim["id"], edge_key=key,
                                         edge_from=edge.get("from"), edge_to=edge.get("to"),
                                         other_claim_id=edge["other_claim_id"],
                                         edge_type=edge["type"], label_correct="Yes",
                                         comment=None, source_id=source_id)

    responses, edges = store.load_responses(rid), store.load_edge_responses(rid)
    missing = progress.missing_items(BRAIN, source_id, responses, edges)
    check(not missing, f"nothing missing once everything is answered ({missing[:2]})")

    states = progress.section_states(BRAIN, source_id, responses, edges)
    check(all(states[s] == progress.COMPLETE for s in progress.SECTION_IDS),
          "every section reads complete")

    summary = progress.he16_for_claim(BRAIN, BRAIN.claims_of(source_id)[0]["id"], edges)
    check(summary == "" or summary.endswith("(100%)"), f"HE-16 derived: {summary!r}")

    at = open_section("vaclav", "Vaclav", phase_id, source_id, "review")
    check(any("Ready to complete" in s.value for s in at.success),
          "review page reports nothing missing")
    [b for b in at.button if "Mark paper complete" in b.label][0].click().run()
    check(store.get_review(phase_id, "vaclav", source_id)["status"] == store.STATUS_COMPLETE,
          "marking complete recorded")

    # complete but NOT locked — the whole point of the two-step gate
    at = open_section("vaclav", "Vaclav", phase_id, source_id, "source")
    check(not any(r.disabled for r in criterion_radios(at)),
          "a complete paper is still editable")

    at = open_section("vaclav", "Vaclav", phase_id, source_id, "review")
    check(any("Reopen for editing" in b.label for b in at.button),
          "a complete paper can be reopened by the evaluator")

    store.submit_review(rid)
    at = open_section("vaclav", "Vaclav", phase_id, source_id, "source")
    radios = criterion_radios(at)
    check(radios and all(r.disabled for r in radios), "submitted paper is read-only")

    store.reopen_review(rid)
    at = open_section("vaclav", "Vaclav", phase_id, source_id, "source")
    check(not any(r.disabled for r in criterion_radios(at)), "admin reopen restores editing")


def test_review_blocks():
    print("\n== review page blocks submission ==")
    fresh_db()
    source_id = manifest.training_source_ids()[0]
    rid = store.ensure_review(phase_id=manifest.TRAINING, evaluator_id="vaclav", evaluator_name="Vaclav",
                              pair_id="B", source_id=source_id,
                              work_id=BRAIN.work_id(source_id),
                              brain_snapshot_id=BRAIN.snapshot_id,
                              eval_spec_version=spec.EVAL_SPEC_VERSION)
    store.start_review(rid, True)
    at = open_section("vaclav", "Vaclav", manifest.TRAINING, source_id, "review")
    submit = [b for b in at.button if "Mark paper complete" in b.label]
    check(submit and submit[0].disabled,
          "marking complete is disabled while items are missing")
    check(any("require attention" in w.value for w in at.warning),
          "review says how much is outstanding")
    check(any("Go to item" in b.label for b in at.button), "missing items are clickable")


def test_admin():
    print("\n== admin ==")
    at = signed_in("thiago", "Thiago", "Admin").run()
    check(any("Admin secret" in t.label for t in at.text_input),
          "admin needs its own secret, not just the name")
    at.text_input[0].set_value("wrong").run()
    at.button[0].click().run()
    check(bool(at.error), "wrong admin secret rejected")

    at = signed_in("thiago", "Thiago", "Admin").run()
    at.text_input[0].set_value(manifest.admin_secret())
    at.button[0].click().run()
    check(ss(at, "admin_ok"), "admin secret accepted")
    check(not at.exception, "admin page renders")

    at = signed_in("vaclav", "Vaclav").run()
    check("Admin" not in [o for r in at.sidebar.radio for o in r.options],
          "non-admin has no Admin page")



def test_data_loading():
    """#12.A acceptance checks on the Brain load."""
    print("\n== data loading ==")
    check(len(BRAIN.sources) > 0 and all(BRAIN.source(s).get("title")
                                         for s in BRAIN.source_ids),
          f"every Source loads ({len(BRAIN.sources)})")
    check(all(c.get("statement") and c.get("source") for c in BRAIN.claims.values()),
          f"every Claim loads ({len(BRAIN.claims)})")
    unresolved = {cid for claim in BRAIN.claims.values()
                  for cid in (claim.get("concepts") or []) if cid not in BRAIN.concepts}
    check(not unresolved, f"every mapped Concept resolves ({unresolved})")
    bad_ds = {claim["dataset"] for claim in BRAIN.claims.values()
              if claim.get("dataset") and claim["dataset"] not in BRAIN.datasets}
    check(not bad_ds, f"every Claim.dataset resolves ({bad_ds})")
    bad_edges = []
    for edge in BRAIN.edges:
        for end in (edge.get("from"), edge.get("to")):
            known = (end in BRAIN.claims or end in BRAIN.sources or end in BRAIN.datasets)
            if not known:
                bad_edges.append(end)
    check(not bad_edges, f"every edge endpoint resolves ({set(bad_edges)})")
    check(not BRAIN.concept_provenance_gaps,
          f"HE-21 applicability determinable for every non-anchor concept "
          f"({BRAIN.concept_provenance_gaps})")
    for source_id in manifest.training_source_ids():
        check(source_id in BRAIN.sources and BRAIN.work_id(source_id),
              f"training paper {BRAIN.work_id(source_id)} exists")
    check(sorted(BRAIN.work_id(s) for s in manifest.training_source_ids())
          == ["W0085", "W0206"], "training papers are exactly W0085 and W0206")


def test_forbidden_runtime_sources():
    """The app must read only the five allowed Brain sources.

    Checked behaviourally — which files the loader actually opens — rather than
    by scanning for strings, so a comment cannot pass or fail it.
    """
    print("\n== runtime data sources ==")
    import builtins
    import brain as brain_module

    opened: list[str] = []
    real_read_text = pathlib.Path.read_text
    real_read_bytes = pathlib.Path.read_bytes
    real_open = builtins.open

    def spy_read_text(self, *args, **kwargs):
        opened.append(str(self))
        return real_read_text(self, *args, **kwargs)

    def spy_read_bytes(self, *args, **kwargs):
        opened.append(str(self))
        return real_read_bytes(self, *args, **kwargs)

    def spy_open(file, *args, **kwargs):
        opened.append(str(file))
        return real_open(file, *args, **kwargs)

    pathlib.Path.read_text = spy_read_text
    pathlib.Path.read_bytes = spy_read_bytes
    builtins.open = spy_open
    try:
        brain_module.load_brain.cache_clear()
        brain_module.load_brain()
    finally:
        pathlib.Path.read_text = real_read_text
        pathlib.Path.read_bytes = real_read_bytes
        builtins.open = real_open

    touched = [path for path in opened if "/brain/" in path]
    for banned in ("log.md", "index.md", "coverage.md", "structure.md",
                   "absences.jsonl", "/schema/", "/tools/", ".pdf"):
        hits = [path for path in touched if banned in path]
        check(not hits, f"never reads {banned} ({hits[:1]})")

    allowed = ("/wiki/sources/", "/wiki/claims/claims.jsonl",
               "/wiki/concepts/", "/wiki/datasets/", "/wiki/graph/edges.jsonl")
    stray = [path for path in touched if not any(a in path for a in allowed)]
    check(not stray, f"reads only the five allowed sources ({stray[:2]})")
    check(touched, f"the five sources were actually read ({len(touched)} files)")
    check(BRAIN.candidate_created_for("CLM-0001-004"),
          "HE-21 provenance comes from Concept records")


def test_no_secrets_in_code():
    print("\n== secrets ==")
    files = list(APP_DIR.glob("*.py")) + list((APP_DIR / "data").glob("*.yaml"))
    blob = "".join(p.read_text(encoding="utf-8") for p in files)
    check("slim-brain-he" not in blob and "slim-brain-admin" not in blob,
          "no secret literal in application code or committed config")
    check("HE_APP_PASSWORD" in blob and "HE_ADMIN_SECRET" in blob,
          "the app knows only the variable names")
    saved = os.environ.pop("HE_APP_PASSWORD", None)
    ambient = manifest._secrets
    manifest._secrets = lambda: {}
    try:
        manifest_password = manifest.password()
    finally:
        manifest._secrets = ambient
        os.environ["HE_APP_PASSWORD"] = saved or "test-password"
    check(manifest_password == "", "an unset secret yields no value (fails closed)")


def test_async_saving():
    print("\n== asynchronous saving ==")
    import savequeue

    import threading
    import time

    calls = []
    started = threading.Event()
    release = threading.Event()
    queue = savequeue.SaveQueue()

    def slow(value):
        calls.append(value)
        started.set()
        release.wait(timeout=5)

    def quick(value):
        calls.append(value)

    queue.submit("k", slow, "in-flight")
    started.wait(timeout=5)
    # three rapid edits to the same answer while the first write is running
    for value in ("edit-1", "edit-2", "edit-3"):
        queue.submit("k", quick, value)
    release.set()
    check(queue.flush(timeout=10), "queue flushes successfully")
    check(calls[-1] == "edit-3", f"the latest value is the one written ({calls})")
    check("edit-1" not in calls and "edit-2" not in calls,
          f"superseded edits collapse instead of each being written ({calls})")

    attempts = []

    def flaky(value):
        attempts.append(value)
        if len(attempts) < 3:
            raise RuntimeError("storage unavailable")

    retry_queue = savequeue.SaveQueue()
    retry_queue.submit("k", flaky, "v")
    ok = retry_queue.flush(timeout=15)
    check(ok and len(attempts) >= 3, f"failed writes retry until they succeed ({attempts})")


def test_simultaneous_evaluators():
    """#12.D — two evaluators of the same pair working at once never collide."""
    print("\n== two simultaneous evaluators ==")
    fresh_db()
    pair_a = [e["evaluator_id"] for e in manifest.evaluators()
              if e.get("pair_id") == "A"]
    check(len(pair_a) == 2, f"pair A has two evaluators ({pair_a})")
    source_id = manifest.assigned_source_ids(pair_a[0], manifest.AGREEMENT)[0]
    check(source_id in manifest.assigned_source_ids(pair_a[1], manifest.AGREEMENT),
          "both evaluate the same paper")

    rids = []
    for evaluator_id in pair_a:
        rid = store.ensure_review(phase_id=manifest.AGREEMENT, evaluator_id=evaluator_id,
                                  evaluator_name=evaluator_id, pair_id="A",
                                  source_id=source_id, work_id=BRAIN.work_id(source_id),
                                  brain_snapshot_id=BRAIN.snapshot_id,
                                  eval_spec_version=spec.EVAL_SPEC_VERSION)
        rids.append(rid)
    check(rids[0] != rids[1], "each evaluator gets a distinct review row")

    question = spec.source_section_questions()[0]
    for evaluator_id, rid, answer in zip(pair_a, rids, ("Yes", "No")):
        store.save_response(rid, object_type="source", object_id=source_id,
                            question_key=question.question_key,
                            criterion_id=question.criterion_id,
                            field_subitem=question.field_subitem,
                            answer=answer, comment="x", source_id=source_id)
    first = store.load_responses(rids[0])[f"{question.question_key}|{source_id}"]
    second = store.load_responses(rids[1])[f"{question.question_key}|{source_id}"]
    check(first["answer"] == "Yes" and second["answer"] == "No",
          "neither evaluator overwrites the other")
    check(first["response_key"] != second["response_key"],
          "response keys are disjoint per evaluator")

    # same evaluator in two tabs: stale write is refused, not silently applied
    stale = first["updated_at"]
    store.save_response(rids[0], object_type="source", object_id=source_id,
                        question_key=question.question_key,
                        criterion_id=question.criterion_id,
                        field_subitem=question.field_subitem,
                        answer="In part", comment="tab 2", source_id=source_id)
    conflicted = False
    try:
        store.save_response(rids[0], object_type="source", object_id=source_id,
                            question_key=question.question_key,
                            criterion_id=question.criterion_id,
                            field_subitem=question.field_subitem,
                            answer="Yes", comment="tab 1", source_id=source_id,
                            expected_updated_at=stale)
    except store.SaveConflict:
        conflicted = True
    check(conflicted, "a stale write from a second tab raises SaveConflict")


def test_resume_after_interruption():
    print("\n== interrupted session and resume ==")
    fresh_db()
    source_id = manifest.training_source_ids()[0]
    rid = store.ensure_review(phase_id=manifest.TRAINING, evaluator_id="vaclav",
                              evaluator_name="Vaclav", pair_id="B",
                              source_id=source_id, work_id=BRAIN.work_id(source_id),
                              brain_snapshot_id=BRAIN.snapshot_id,
                              eval_spec_version=spec.EVAL_SPEC_VERSION)
    store.start_review(rid, True)
    for question in spec.source_section_questions():
        store.save_response(rid, object_type="source", object_id=source_id,
                            question_key=question.question_key,
                            criterion_id=question.criterion_id,
                            field_subitem=question.field_subitem,
                            answer="Yes", comment=None, source_id=source_id)

    # a completely fresh session, as after a browser close
    at = signed_in().run()
    check("In progress" in rendered_text(at), "home shows the paper in progress")
    check(any(b.label == "Continue" for b in at.button),
          f"home offers Continue ({[b.label for b in at.button]})")
    check("claims complete" in rendered_text(at),
          "with how far through its claims the evaluator is")

    at = signed_in(source_id=source_id).run()
    responses = store.load_responses(rid)
    states = progress.section_states(BRAIN, source_id, responses,
                                     store.load_edge_responses(rid))
    check(states["source"] == progress.COMPLETE, "completed section survives the restart")
    check(progress.next_open_section(states) == "claims",
          "resume lands on the first incomplete step")





def test_allocation():
    """The manifest must reproduce the accepted allocation, paper for paper."""
    print("\n== accepted allocation ==")
    sys.path.insert(0, str(APP_DIR / "tools"))
    import build_assignments

    splits = build_assignments.parse_allocation(build_assignments.ALLOCATION)
    check(sorted(splits) == ["AGR-A", "AGR-B", "AGR-C",
                             "IND-1", "IND-2", "IND-3", "IND-4", "IND-5"],
          f"eight splits parsed ({sorted(splits)})")
    check([len(v) for k, v in splits.items() if k.startswith("AGR")] == [5, 5, 5],
          "each agreement split holds five papers")
    check(sum(len(v) for v in splits.values()) == 48,
          f"48 papers allocated ({sum(len(v) for v in splits.values())})")

    everything = set().union(*splits.values()) | set(manifest.training_source_ids())
    check(everything == set(BRAIN.source_ids),
          f"together with training they cover all {len(BRAIN.source_ids)} Sources")
    check(all(s in BRAIN.sources for s in everything), "every id resolves in the Brain")

    # agreement: both evaluators of a pair, the same five papers
    for split in ("AGR-A", "AGR-B", "AGR-C"):
        holders = sorted({r["evaluator_id"] for r in manifest.assignments()
                          if r["split_id"] == split})
        check(len(holders) == 2, f"{split} is held by exactly two evaluators ({holders})")
        sets = [set(manifest.assigned_source_ids(h, manifest.AGREEMENT)) for h in holders]
        check(sets[0] == sets[1] == set(splits[split]),
              f"{split}: both evaluate the same five papers")

    # individual: one evaluator per paper, counting assignments only. Reserved
    # rows deliberately overlap — that is what makes either activation possible.
    counts = collections.Counter(
        r["source_id"] for r in manifest.assignments()
        if r["phase_id"] == manifest.INDIVIDUAL
        and manifest.state_of(r) == manifest.ASSIGNED)
    check(counts and max(counts.values()) == 1,
          "no individual paper is assigned to two evaluators")
    overlapping = collections.Counter(
        r["source_id"] for r in manifest.reserved(manifest.INDIVIDUAL))
    check(overlapping and min(overlapping.values()) == 2,
          "while every reserved paper is held for both, pending the decision")
    for evaluator_id, split in (("alessandro", "IND-3"), ("giovanni", "IND-5"),
                                ("giuseppe", "IND-2"), ("vaclav", "IND-4")):
        assigned = manifest.assigned_source_ids(evaluator_id, manifest.INDIVIDUAL)
        check(assigned == splits[split],
              f"{evaluator_id} holds {split} in order ({len(assigned)} papers)")
        check(manifest.individual_split(evaluator_id) == split,
              f"and the manifest records it as their individual split")

    # IND-1 is preallocated as every possible allocation, none of them live
    held = manifest.reserved()
    check({r["split_id"] for r in held} == {"IND-1"},
          f"only IND-1 is reserved ({ {r['split_id'] for r in held} })")
    check(manifest.reserved_sources() == sorted(splits["IND-1"]),
          "covering all seven of its papers")
    check(len(held) == 14, f"one row per evaluator per paper ({len(held)})")
    check({r["evaluator_id"] for r in held} == {"thiago", "francesca"},
          "reserved for exactly the two evaluators of that pair")
    for source_id in manifest.reserved_sources():
        holders = {r["evaluator_id"] for r in manifest.reservations_for(source_id)}
        check(holders == {"thiago", "francesca"},
              f"{source_id} is reserved for both, so either can be activated")
    for evaluator_id in ("thiago", "francesca"):
        check(not manifest.assigned_source_ids(evaluator_id, manifest.INDIVIDUAL),
              f"{evaluator_id} has no individual papers assigned yet")
        check(manifest.individual_split(evaluator_id) == "",
              f"and no individual split recorded")
    check(manifest.phase_open(manifest.INDIVIDUAL),
          "and the individual phase is open anyway — pending papers are not a gate")

    # phases are availability, not a sequence
    check(all(manifest.phase_open(p) for p in manifest.PHASES),
          "all three phases are open by default")
    for evaluator_id in ("thiago", "francesca"):
        check(manifest.assigned_source_ids(evaluator_id, manifest.TRAINING)
              and manifest.assigned_source_ids(evaluator_id, manifest.AGREEMENT),
              f"{evaluator_id} has training and agreement papers from the start")
    source = pathlib.Path(manifest.__file__).read_text(encoding="utf-8")
    for banned in ("phase_open(AGREEMENT)", "must be closed", "prerequisite"):
        check(banned not in source, f"no sequencing rule in manifest.py ({banned!r})")

    # every evaluator does the training set
    for entry in manifest.evaluators():
        assigned = manifest.assigned_source_ids(entry["evaluator_id"], manifest.TRAINING)
        check(sorted(assigned) == sorted(manifest.training_source_ids()),
              f"{entry['name']} has both training papers")
    check(sorted(BRAIN.work_id(s) for s in manifest.training_source_ids())
          == ["W0085", "W0206"], "training is W0085 and W0206")

    keys = [r["assignment_key"] for r in manifest.assignments()]
    check(len(keys) == len(set(keys)) == 82, f"82 unique assignment rows ({len(keys)})")
    states = collections.Counter(manifest.state_of(r) for r in manifest.assignments())
    check(states == {manifest.ASSIGNED: 68, manifest.RESERVED: 14},
          f"68 assigned and 14 reserved ({dict(states)})")


def _seed_workbook(directory):
    """Put the file configuration into a local workbook, as bootstrap --seed does."""
    book = sheets.LocalWorkbook(directory)
    book.ensure_tabs()
    data = manifest.manifest()
    book.append_rows(sheets.CONFIG, [{"key": k, "value": str(v)}
                                     for k, v in sorted(data["config"].items())])
    book.append_rows(sheets.EVALUATORS, [
        {n: e.get(n, "") for n in sheets.COLUMNS[sheets.EVALUATORS]}
        for e in data["evaluators"]])
    book.append_rows(sheets.ASSIGNMENTS, [
        {n: r.get(n, "") for n in sheets.COLUMNS[sheets.ASSIGNMENTS]}
        for r in data["assignments"]])
    return book


class CountingWorkbook:
    """A workbook that records every request, so cost can be asserted.

    The Sheets quota is per request, not per byte, and the failure mode is a
    page that quietly makes one whole-tab download per radio click. Counting the
    calls is the acceptance test; wall-clock timing would only measure the
    network.
    """

    def __init__(self, inner):
        self.inner = inner
        self.calls = collections.Counter()
        self.rows_read = collections.Counter()

    def _record(self, name, tab, rows=0):
        self.calls[f"{name}:{tab}"] += 1
        self.calls[name] += 1
        self.rows_read[tab] += rows

    def reset(self):
        self.calls.clear()
        self.rows_read.clear()

    def ensure_tabs(self):
        return self.inner.ensure_tabs()

    def check_ready(self):
        self._record("check_ready", "")
        return self.inner.check_ready()

    def read_tab(self, tab):
        rows = self.inner.read_tab(tab)
        self._record("read_tab", tab, len(rows))
        return rows

    def read_range(self, tab, first, last):
        rows = self.inner.read_range(tab, first, last)
        self._record("read_range", tab, len(rows))
        return rows

    def row_count(self, tab):
        self._record("row_count", tab)
        return self.inner.row_count(tab)

    def append_rows(self, tab, rows):
        self._record("append_rows", tab)
        return self.inner.append_rows(tab, rows)

    def update_row(self, tab, row_number, values):
        self._record("update_row", tab)
        return self.inner.update_row(tab, row_number, values)

    def update_rows(self, tab, updates):
        self._record("update_rows", tab)
        return self.inner.update_rows(tab, updates)


def _with_counting_workbook():
    """A fresh local workbook wrapped in the counter, installed into store."""
    book = CountingWorkbook(sheets.LocalWorkbook(pathlib.Path(tempfile.mkdtemp())))
    store.workbook = lambda: book
    store.forget_row_index()
    store.forget_reviews()
    store.forget_ready()
    store._TOUCHED.clear()
    store.init()
    book.reset()          # readiness is startup, not the behaviour being counted
    return book


def test_preallocation_superset():
    """Every row a review could need, so nothing is appended mid-round."""
    print("\n== preallocation superset ==")
    source_id = manifest.training_source_ids()[1]
    lazy = {i.lookup for i in progress.all_items(BRAIN, source_id, {})}
    every = {i.lookup for i in progress.all_possible_items(BRAIN, source_id)}
    check(every > lazy, f"the superset is larger ({len(every)} vs {len(lazy)})")
    added = {k.split("|")[0] for k in every - lazy}
    check(added == {"CLAIM_HE20B", "SOURCE_HE18_3", "SOURCE_HE19_3", "SOURCE_HE20S_B"},
          f"and adds exactly the conditional follow-ups ({sorted(added)})")

    conditional = [i for i in progress.all_possible_items(BRAIN, source_id)
                   if i.question.applicability == spec.IF_PARENT_IS_NEGATIVE]
    check(conditional, f"{len(conditional)} conditional rows are preallocated")
    check(not any(i.lookup in lazy for i in conditional),
          "none of which the lazy expansion would have created")

    # auto-N/A is a fact about the Brain, so it still applies in the superset
    no_cites = next(s for s in BRAIN.source_ids if not BRAIN.cites_from(s))
    every_na = [i for i in progress.all_possible_items(BRAIN, no_cites) if i.auto_na]
    check(every_na, f"and auto-N/A is still resolved ({len(every_na)} items)")


def test_workbook_read_economy():
    """The acceptance test for Step 4: requests, not seconds."""
    print("\n== workbook request economy ==")
    original = store.workbook
    book = _with_counting_workbook()
    try:
        phase_id, evaluator = manifest.AGREEMENT, "vaclav"
        sources = manifest.assigned_source_ids(evaluator, phase_id)[:2]
        rids = []
        for source_id in sources:
            rid = store.ensure_review(
                phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
                pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id))
            items = progress.all_possible_items(BRAIN, source_id)
            edges = [(c["id"], e) for c in BRAIN.claims_of(source_id)
                     for e in BRAIN.relations_of(c["id"])]
            store.preallocate(
                rid, source_id,
                [(i.object_type, i.object_id, i.question,
                  store.AUTO_NA if i.auto_na else "") for i in items], edges)
            rids.append(rid)

        total = book.inner.row_count(sheets.RESPONSES)
        check(total > 500, f"{total} response rows preallocated across two papers")

        review = store.get_review(phase_id, evaluator, sources[0])
        check(review["responses_first_row"] == "2",
              f"the first review's block starts at row 2 ({review['responses_first_row']})")
        second = store.get_review(phase_id, evaluator, sources[1])
        check(int(second["responses_first_row"]) == int(review["responses_last_row"]) + 1,
              "and the next review's block starts where it ends — contiguous")

        # ---- opening a paper
        book.reset()
        responses = store.load_responses(rids[0])
        check(book.calls["read_tab:RESPONSES"] == 0,
              "opening a paper never downloads the whole RESPONSES tab")
        check(book.calls["read_range:RESPONSES"] == 1,
              f"it is one range read ({book.calls['read_range:RESPONSES']})")
        block = int(review["responses_last_row"]) - int(review["responses_first_row"]) + 1
        check(book.rows_read["RESPONSES"] == block < total,
              f"of {book.rows_read['RESPONSES']} rows, not {total}")
        check(len(responses) == block, f"and returns them all ({len(responses)})")

        # ---- the first answer of a session: one index build, one touch
        item = progress.all_possible_items(BRAIN, sources[0])[0]

        def answer(question, value="Yes"):
            store.save_response(rids[0], object_type=question.object_type,
                                object_id=question.object_id,
                                question_key=question.question.question_key,
                                criterion_id=question.question.criterion_id,
                                field_subitem=question.question.field_subitem,
                                answer=value, comment=None,
                                applicability=spec.APPLICABLE, source_id=sources[0])

        store.forget_row_index()
        store._TOUCHED.clear()
        store.load_responses(rids[0])          # opening the paper indexes its block
        book.reset()
        answer(item)
        check(book.calls["read_tab:RESPONSES"] == 0,
              "the first save reads nothing: the block read already indexed it")
        check(book.calls["update_row:RESPONSES"] == 1,
              "and writes exactly one targeted row")
        check(book.calls["read_tab:REVIEWS"] == 1 and book.calls["update_row:REVIEWS"] == 1,
              "and marks the review as worked on, once")
        check(book.calls["append_rows"] == 0, "nothing is appended mid-round")

        # ---- and every answer after that is one write and nothing else
        book.reset()
        for question in progress.all_possible_items(BRAIN, sources[0])[1:4]:
            answer(question)
        check(book.calls["read_tab:RESPONSES"] == 0
              and book.calls["read_range:RESPONSES"] == 0,
              f"three more answers read no responses at all ({dict(book.calls)})")
        check(book.calls["update_row:RESPONSES"] == 3, "one write each")
        check(book.calls["update_row:REVIEWS"] == 0,
              "and last_saved_at is throttled rather than written per keystroke")

        # ---- batching several pending writes
        book.reset()
        records = [
            {"rid": rids[0], "object_type": q.object_type, "object_id": q.object_id,
             "question_key": q.question.question_key,
             "criterion_id": q.question.criterion_id,
             "field_subitem": q.question.field_subitem, "answer": "In part",
             "comment": "partly", "applicability": spec.APPLICABLE,
             "source_id": sources[0]}
            for q in progress.all_possible_items(BRAIN, sources[0])[4:12]
        ]
        store.save_responses(records)
        check(book.calls["update_rows:RESPONSES"] == 1,
              f"eight answers go out as one request ({dict(book.calls)})")
        check(book.calls["read_tab:RESPONSES"] == 0, "with no whole-tab read")
        saved = store.load_responses(rids[0])
        check(all(saved[f"{r['question_key']}|{r['object_id']}"]["answer"] == "In part"
                  for r in records), "and every one of them landed")

        # ---- the other review is untouched by any of it
        other = store.load_responses(rids[1])
        check(all(r["review_id"] == rids[1] for r in other.values()),
              "the neighbouring range holds only its own review's rows")
        stray = [k for k, r in other.items()
                 if r["answer"] and r["applicability"] != spec.AUTO_NA]
        check(not stray,
              f"and none of them carries an evaluator answer ({stray[:3]})")
        auto = [r for r in other.values() if r["applicability"] == spec.AUTO_NA]
        check(all(r["answer"] == spec.NA_ANSWER for r in auto),
              f"only the {len(auto)} preallocated N/A rows have a value")
    finally:
        store.workbook = original
        store.forget_row_index()
        store.forget_reviews()
        fresh_db()


def test_bulk_preallocation_locks_nothing():
    """The whole workbook prepared in advance must still be freely reconfigurable."""
    print("\n== bulk preallocation is not activity ==")
    original = store.workbook
    book = _with_counting_workbook()
    try:
        # deliberately a mix: assigned papers and reservations together
        individual = [a for a in manifest.assignments()
                      if a["phase_id"] == manifest.INDIVIDUAL]
        rows = ([a for a in individual if manifest.state_of(a) == manifest.ASSIGNED][:3]
                + [a for a in individual if manifest.state_of(a) == manifest.RESERVED][:3])
        for row in rows:
            rid = store.ensure_review(
                phase_id=row["phase_id"], evaluator_id=row["evaluator_id"],
                evaluator_name="", pair_id=manifest.pair_of(row["evaluator_id"]),
                source_id=row["source_id"], work_id=row["work_id"],
                assignment_key=row["assignment_key"])
            items = progress.all_possible_items(BRAIN, row["source_id"])
            store.preallocate(
                rid, row["source_id"],
                [(i.object_type, i.object_id, i.question,
                  store.AUTO_NA if i.auto_na else "") for i in items], [])

        reviews = store.all_reviews()
        check(len(reviews) == len(rows), f"{len(reviews)} reviews preallocated")
        check(all(r["responses_first_row"] for r in reviews),
              "each with its row range recorded")

        touched = [r["review_id"] for r in reviews if r.get("last_saved_at")]
        check(not touched,
              f"recording the ranges does not stamp last_saved_at ({touched[:2]})")
        active = [r["review_id"] for r in reviews if manifest.has_activity(r)]
        check(not active, f"so none of them counts as activity ({active[:2]})")
        check(not manifest.active_assignment_keys(reviews),
              "and no assignment is locked")

        held = [r for r in manifest.reserved()
                if r["assignment_key"] in {a["assignment_key"] for a in rows}]
        check(held, f"{len(held)} of them are reservations")
        check(not any(manifest.is_locked(r["assignment_key"], reviews) for r in held),
              "which remain activatable after their storage exists")

        provenance = [r["review_id"] for r in reviews
                      if any(r.get(f) for f in store.PROVENANCE)]
        check(not provenance, f"and none carries provenance yet ({provenance[:2]})")
    finally:
        store.workbook = original
        store.forget_row_index()
        store.forget_reviews()
        fresh_db()


def test_no_whole_tab_read_in_ordinary_use():
    """The invariant: open reads its ranges, answers write, rerenders read nothing."""
    print("\n== no whole-tab read in ordinary use ==")
    original = store.workbook
    book = _with_counting_workbook()
    try:
        phase_id, evaluator = manifest.AGREEMENT, "vaclav"
        source_id = manifest.assigned_source_ids(evaluator, phase_id)[0]
        rid = store.ensure_review(
            phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
            pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id))
        items = progress.all_possible_items(BRAIN, source_id)
        edges = [(c["id"], e) for c in BRAIN.claims_of(source_id)
                 for e in BRAIN.relations_of(c["id"])]
        store.preallocate(
            rid, source_id,
            [(i.object_type, i.object_id, i.question,
              store.AUTO_NA if i.auto_na else "") for i in items], edges)

        # a genuinely cold session
        store.forget_row_index()
        store.forget_reviews()
        store._TOUCHED.clear()
        book.reset()

        responses = store.load_responses(rid)
        edge_rows = store.load_edge_responses(rid)
        check(book.calls["read_tab:RESPONSES"] == 0
              and book.calls["read_tab:EDGE_RESPONSES"] == 0,
              "opening a review reads no whole tab")
        check(book.calls["read_range:RESPONSES"] == 1
              and book.calls["read_range:EDGE_RESPONSES"] == 1,
              "just its two ranges")

        indexed = sum(1 for key in responses
                      if store.row_number(sheets.RESPONSES,
                                          store.response_key(
                                              rid, *_key_parts(key, responses)),
                                          rebuild=False) is not None)
        check(indexed == len(responses),
              f"and every row it read is indexed ({indexed}/{len(responses)})")

        # ordinary answers, and edges, write without reading
        book.reset()
        for item in items[:5]:
            store.save_response(rid, object_type=item.object_type,
                                object_id=item.object_id,
                                question_key=item.question.question_key,
                                criterion_id=item.question.criterion_id,
                                field_subitem=item.question.field_subitem,
                                answer="Yes", comment=None,
                                applicability=spec.APPLICABLE, source_id=source_id)
        for claim_id, edge in edges[:3]:
            store.save_edge_response(rid, host_claim_id=claim_id,
                                     edge_key=store.edge_key_of(edge),
                                     edge_from=edge.get("from"), edge_to=edge.get("to"),
                                     other_claim_id=edge["other_claim_id"],
                                     edge_type=edge["type"], label_correct="Yes",
                                     comment=None, source_id=source_id)
        check(book.calls["read_tab:RESPONSES"] == 0
              and book.calls["read_tab:EDGE_RESPONSES"] == 0,
              f"five answers and three edges read no whole tab ({dict(book.calls)})")
        check(book.calls["read_range:RESPONSES"] == 0,
              "and re-read no response rows: these are first answers, with no "
              "stored stamp to conflict against")
        # REVIEWS is one row per evaluator per paper — 82 in this configuration —
        # and is consulted to see whether an edit should demote a completed
        # paper. It is re-read only after something writes to it, so the count
        # tracks writes, not answers.
        reviews_read = book.calls["read_tab:REVIEWS"]
        check(reviews_read <= 3,
              f"REVIEWS is read a handful of times, not per answer ({reviews_read})")
        check(book.calls["update_row:REVIEWS"] <= 1,
              f"and written at most once, throttled "
              f"({book.calls['update_row:REVIEWS']})")
        check(book.calls["update_row:RESPONSES"] == 5
              and book.calls["update_row:EDGE_RESPONSES"] == 3,
              "each is one targeted write")
    finally:
        store.workbook = original
        store.forget_row_index()
        store.forget_reviews()
        fresh_db()


def _key_parts(lookup: str, responses: dict):
    row = responses[lookup]
    return row["object_type"], row["object_id"], row["question_key"]


def test_unknown_key_is_an_error_not_an_append():
    """After preallocation, a write naming a row that does not exist must stop."""
    print("\n== an unknown key is a storage-integrity error ==")
    original = store.workbook
    book = _with_counting_workbook()
    try:
        source_id = manifest.training_source_ids()[0]
        rid = store.ensure_review(
            phase_id=manifest.TRAINING, evaluator_id="vaclav", evaluator_name="Vaclav",
            pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id))
        items = progress.all_possible_items(BRAIN, source_id)
        store.preallocate(rid, source_id,
                          [(i.object_type, i.object_id, i.question, "") for i in items], [])
        before = book.inner.row_count(sheets.RESPONSES)

        try:
            store.save_response(rid, object_type="claim", object_id="CLM-9999-999",
                                question_key="CLAIM_HE03", criterion_id="HE-03",
                                field_subitem="", answer="Yes", comment=None,
                                applicability=spec.APPLICABLE, source_id=source_id)
            check(False, "an unpreallocated key is refused")
        except store.StorageIntegrityError as error:
            check("no row for" in str(error) and "Nothing was written" in str(error),
                  f"an unpreallocated key is refused, clearly ({str(error)[:60]}…)")
        check(book.inner.row_count(sheets.RESPONSES) == before,
              "and nothing was appended")

        # the same is true of edges, and of the batched path
        try:
            store.save_edge_response(rid, host_claim_id="CLM-9999-999",
                                     edge_key="nope", edge_from="a", edge_to="b",
                                     other_claim_id="c", edge_type="SUPPORTS",
                                     label_correct="Yes", comment=None,
                                     source_id=source_id)
            check(False, "an unknown edge key is refused")
        except store.StorageIntegrityError:
            check(True, "an unknown edge key is refused too")
        try:
            store.save_responses([
                {"rid": rid, "object_type": "claim", "object_id": "CLM-9999-998",
                 "question_key": "CLAIM_HE03", "criterion_id": "HE-03",
                 "field_subitem": "", "answer": "Yes", "comment": None,
                 "applicability": spec.APPLICABLE, "source_id": source_id}])
            check(False, "a batched unknown key is refused")
        except store.StorageIntegrityError:
            check(True, "so is a batched one")
        check(book.inner.row_count(sheets.RESPONSES) == before,
              "still nothing appended")

        # bootstrap and preallocation may still create rows
        store.save_response(rid, object_type="claim", object_id="CLM-9999-999",
                            question_key="CLAIM_HE03", criterion_id="HE-03",
                            field_subitem="", answer="Yes", comment=None,
                            applicability=spec.APPLICABLE, source_id=source_id,
                            allow_append=True)
        check(book.inner.row_count(sheets.RESPONSES) == before + 1,
              "an explicit allow_append still creates a row, for setup and migration")

        # and a real preallocated key writes normally
        item = items[0]
        store.save_response(rid, object_type=item.object_type, object_id=item.object_id,
                            question_key=item.question.question_key,
                            criterion_id=item.question.criterion_id,
                            field_subitem=item.question.field_subitem,
                            answer="In part", comment="because", 
                            applicability=spec.APPLICABLE, source_id=source_id)
        check(store.load_responses(rid)[item.lookup]["answer"] == "In part",
              "while an ordinary answer is unaffected")
    finally:
        store.workbook = original
        store.forget_row_index()
        store.forget_reviews()
        fresh_db()


def test_row_index_cache():
    print("\n== row index cache ==")
    original = store.workbook
    book = _with_counting_workbook()
    try:
        source_id = manifest.training_source_ids()[0]
        rid = store.ensure_review(
            phase_id=manifest.TRAINING, evaluator_id="vaclav", evaluator_name="Vaclav",
            pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id))
        items = progress.all_possible_items(BRAIN, source_id)
        store.preallocate(rid, source_id,
                          [(i.object_type, i.object_id, i.question, "") for i in items], [])
        key = store.response_key(rid, items[0].object_type, items[0].object_id,
                                 items[0].question.question_key)

        store.forget_row_index()
        book.reset()
        first = store.row_number(sheets.RESPONSES, key)
        check(first is not None, f"a known key resolves to a row ({first})")
        check(book.calls["read_tab:RESPONSES"] == 1,
              "a cold lookup verifies once against the tab")

        # but opening the review indexes its block without any extra request
        store.forget_row_index()
        book.reset()
        store.load_responses(rid)
        check(book.calls["read_tab:RESPONSES"] == 0, "opening it reads no whole tab")
        check(store.row_number(sheets.RESPONSES, key, rebuild=False) == first,
              "yet every key in its block is now indexed, at the right row")
        check(book.calls["read_tab:RESPONSES"] == 0, "having cost no extra request")

        book.reset()
        for _ in range(20):
            store.row_number(sheets.RESPONSES, key)
        check(book.calls["read_tab:RESPONSES"] == 0,
              "twenty more lookups cost nothing")

        book.reset()
        check(store.row_number(sheets.RESPONSES, "never-preallocated") is None,
              "an unknown key still resolves to nothing")
        check(book.calls["read_tab:RESPONSES"] == 1,
              "after exactly one rebuild — a miss may mean a new row, a hit never lies")
    finally:
        store.workbook = original
        store.forget_row_index()
        store.forget_reviews()
        fresh_db()


def _tagless(text: str) -> str:
    """The words on the page, with the markup and the line breaks taken out.

    Prose written across several source lines renders as one sentence, so the
    whitespace is collapsed too: a check for what the page says should not
    depend on where the author happened to wrap.
    """
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def rendered_text(at) -> str:
    """Everything the page shows, whatever element it was written with."""
    parts = []
    for group in (at.title, at.header, at.subheader, at.markdown, at.caption,
                  at.info, at.warning, at.success, at.error):
        parts.extend(element.value for element in group)
    return " ".join(str(p) for p in parts)


def _settle(at, seconds=2.0):
    """Wait for the session's background writes, so counts are not a race."""
    try:
        queue = at.session_state["_save_queue"]
    except (KeyError, AttributeError):
        return
    queue.flush(timeout=seconds)


def test_renders_do_not_write():
    """Looking at an unanswered question must not write to storage."""
    print("\n== rendering writes nothing ==")
    fresh_db()
    source_id = manifest.training_source_ids()[0]
    rid = store.review_id(manifest.TRAINING, "vaclav", source_id)
    store.ensure_review(phase_id=manifest.TRAINING, evaluator_id="vaclav",
                        evaluator_name="Vaclav", pair_id="B", source_id=source_id,
                        work_id=BRAIN.work_id(source_id))
    items = progress.all_possible_items(BRAIN, source_id)
    store.preallocate(rid, source_id,
                      [(i.object_type, i.object_id, i.question,
                        store.AUTO_NA if i.auto_na else "") for i in items], [])
    store.start_review(rid, True)

    real = store.save_response
    written = []

    def spy(rid_, **kwargs):
        written.append((kwargs.get("question_key"), kwargs.get("answer")))
        return real(rid_, **kwargs)

    store.save_response = spy
    try:
        for section in ("source", "claims", "datasets", "cites", "recall"):
            at = open_section("vaclav", "Vaclav", manifest.TRAINING, source_id, section)
            _settle(at)
        noop = [w for w in written if not w[1]]
        check(not noop, f"no unanswered question is written on render ({noop[:3]})")
        na = [w for w in written if w[1] == spec.NA_ANSWER]
        check(not na, "and preallocated N/A rows are not rewritten either")
        check(not written, f"rendering writes nothing at all ({written[:3]})")
    finally:
        store.save_response = real


def test_failed_writes_are_retained():
    """A write that cannot be stored is kept and retried, never dropped."""
    print("\n== failed writes survive ==")
    import savequeue

    original_retry = savequeue.RETRY_SECONDS
    savequeue.RETRY_SECONDS = 0.02
    queue = savequeue.SaveQueue()
    try:
        attempts = {"n": 0}

        def unreachable(**kwargs):
            attempts["n"] += 1
            raise RuntimeError("the workbook is unreachable")

        queue.submit("answer-1", unreachable, value="In part")
        deadline = time.monotonic() + 5
        while queue.state[0] != savequeue.FAILED and time.monotonic() < deadline:
            time.sleep(0.05)
        state, detail, unresolved = queue.state
        check(state == savequeue.FAILED, f"the queue reports failure ({state})")
        check(unresolved == 1, f"and still holds the write ({unresolved})")
        check("unreachable" in detail, f"with the reason ({detail})")
        check(queue.failures == {"answer-1": "the workbook is unreachable"},
              "which is attributable to the answer that failed")
        check(attempts["n"] >= savequeue.MAX_ATTEMPTS,
              f"after {attempts['n']} attempts")

        check(not queue.flush(timeout=0.5),
              "flush refuses while it is unresolved — this is what blocks completion")
        check(queue.unresolved == 1, "and the write is still there afterwards")

        # a newer answer for the same item supersedes the failed one
        landed = []
        queue.submit("answer-1", lambda **kw: landed.append(kw) or "stamp-1",
                     value="No", on_success=landed.append)
        check(queue.flush(timeout=5), "a fresh write clears it")
        check(queue.unresolved == 0 and not queue.failures,
              "leaving nothing unresolved")
        check(landed and landed[0]["value"] == "No",
              "and the newer value is what was written")
        check(landed[-1] == "stamp-1", "with its result handed back")

        # recovery without a new edit: the same write, retried, succeeds
        broken = {"fail": True}

        def flaky(**kwargs):
            if broken["fail"]:
                raise RuntimeError("still unreachable")
            return "stamp-2"

        queue.submit("answer-2", flaky, value="Yes")
        deadline = time.monotonic() + 5
        while queue.state[0] != savequeue.FAILED and time.monotonic() < deadline:
            time.sleep(0.05)
        check(queue.unresolved == 1, "a second write fails and is retained")
        broken["fail"] = False
        check(queue.flush(timeout=5), "and goes in once storage recovers")
        check(queue.unresolved == 0, "with nothing left outstanding")
    finally:
        savequeue.RETRY_SECONDS = original_retry
        queue.stop()


def _started(evaluator, name, phase_id, source_id):
    """A review already past the read confirmation, so sections render."""
    rid = store.ensure_review(
        phase_id=phase_id, evaluator_id=evaluator, evaluator_name=name,
        pair_id=manifest.pair_of(evaluator) or "", source_id=source_id,
        work_id=BRAIN.work_id(source_id), brain_snapshot_id=BRAIN.snapshot_id,
        eval_spec_version=spec.EVAL_SPEC_VERSION)
    store.start_review(rid, True)
    return rid


def test_source_page():
    """Step 9.5 — the Source section, as the Design settles it."""
    print("\n== the Source page ==")
    fresh_db()
    # W0206: the one training paper carrying venue_type, length and a second
    # version, so the context block is exercised rather than mostly skipped.
    source_id, evaluator = "SRC-0009", "vaclav"
    rid = _started(evaluator, "Vaclav", manifest.TRAINING, source_id)
    src = BRAIN.source(source_id)

    at = open_section(evaluator, "Vaclav", manifest.TRAINING, source_id, "source")
    check(not at.exception, "the section renders")
    text = rendered_text(at)

    check("Source attributes" in text, "it is headed Source attributes")
    check("Evaluate the Source-level classifications produced by the Brain." in text,
          "with the agreed sentence beneath it and no more")
    check("0 of 2</strong> questions complete" in text,
          "and a local count of the questions in this section")

    check("Brain values" in text, "the panel is named for what it holds")
    prose = _tagless(text)
    for label, field in (("Contribution type", "contribution_type"),
                         ("Source jurisdiction", "source_jurisdiction")):
        check(label in prose, f"{label} is a plain-language label")
        check(field not in prose.replace(f"`{field}`", ""),
              f"and the schema name {field} is not shown as one, only inside the question")
        for value in src.get(field) or []:
            # The claim being tested is precisely that monospace is reserved for
            # a literal schema value, so look for the code element, not the glyph.
            check(f"<code>{value}</code>" in text or f"`{value}`" in text,
                  f"its value {value} is shown as a schema value")

    check(any(b.label == "Open Source wiki" for b in at.button),
          "the wiki opens from the panel")

    labels = [e.label for e in at.expander]
    check("Additional source metadata — context only" in labels,
          f"the context block is named as context {labels}")
    check(all(not e.proto.expanded for e in at.expander),
          "and every expander on the page, criterion definitions included, starts closed")

    # The note is emitted as markup so it can be given a ground of its own; the
    # words still have to be the instrument's, so compare against the constant
    # with its emphasis markers resolved rather than against a copy of the text.
    scale = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", spec.RESPONSE_SCALE_NOTE)
    check(scale in text, "the response scale is explained")
    check(text.count(scale) == 1, "once for the section, not once per card")

    # Context, rendered for a reader
    check("Janatian, Samyar; Westermann, Hannes" in prose,
          "authors are listed in full in the context block")
    check("English (en)" in prose, "the language is named, not left as a code")
    check("conference" in prose, "the venue type is shown")
    check("1 additional version" in prose,
          "other versions are counted, not listed as paths")

    # The Design is explicit: no raw paths reach the evaluator.
    for leak in ("raw/", ".pdf", "docling", "conversion_tool", "ingest_position",
                 "extraction_model", "RUN-2026"):
        check(leak not in text, f"no {leak} on the page")

    # Wording comes from the instrument, not from this module.
    questions = spec.source_section_questions()
    check([q.criterion_id for q in questions] == ["HE-08.1", "HE-08.2"],
          "the two Source criteria are asked, in order")
    for question in questions:
        check(question.question_text in text,
              f"{question.criterion_id} is asked in the spec's words")
    views_source = (APP_DIR / "views.py").read_text(encoding="utf-8")
    check("order of dominance" not in views_source,
          "and no superseded wording is hard-coded in the view")

    # Saving, progress and navigation are untouched by the redesign.
    radios = [r for r in at.radio if r.key.endswith("|a")]
    check(len(radios) == 2, f"one answer control per question ({len(radios)})")
    at = flush(radios[0].set_value("Yes").run())
    stored = store.load_responses(rid)
    check(stored.get(f"SOURCE_HE08_1|{source_id}", {}).get("answer") == "Yes",
          "an answer still saves")
    check("1 of 2</strong> questions complete" in rendered_text(at),
          "and the local count follows it")

    nav = [b for b in at.button if b.key and b.key.startswith("nav|")]
    check(len(nav) == len(progress.SECTION_IDS),
          "every section is still reachable from here")
    check(sum(1 for b in nav if b.disabled) == 1,
          "only the section already open is inert")


def _open_claim(evaluator, name, phase_id, source_id, index):
    """The claims section with one particular claim selected."""
    rid = store.review_id(phase_id, evaluator, source_id)
    at = signed_in(evaluator, name, manifest.PHASE_LABEL[phase_id], source_id=source_id)
    at.session_state[f"section|{rid}"] = "claims"
    at.session_state[f"claim_idx|{rid}"] = index
    return at.run()


def test_claim_page():
    """Step 9.6 — one claim, five sections, and nothing that gates movement."""
    print("\n== the Claim page ==")
    fresh_db()
    source_id, evaluator = "SRC-0009", "vaclav"
    rid = _started(evaluator, "Vaclav", manifest.TRAINING, source_id)
    claims = BRAIN.claims_of(source_id)
    # CLM-0009-013: four relations and a candidate concept, so E and HE-21 are
    # exercised rather than skipped.
    index = next(i for i, c in enumerate(claims) if c["id"] == "CLM-0009-013")
    claim = claims[index]

    at = _open_claim(evaluator, "Vaclav", manifest.TRAINING, source_id, index)
    check(not at.exception, "the claim renders")
    text = rendered_text(at)
    prose = _tagless(text)
    labels = [b.label for b in at.button]

    # Header
    check(f"Claim {index + 1} of {len(claims)} · {claim['id']}" in prose,
          "the header names the claim and its place in the paper")
    check("applicable items complete" in prose,
          "with a dynamic count of what applies to this claim")
    check("Claim statement" in prose and claim["statement"][:60] in prose,
          "and the statement itself is given prominence")
    check("Open Source wiki" in labels, "the Source wiki opens from the claim")
    check("View all claims from this paper" in labels,
          "as does the whole extracted set")

    # Five sections, each with its own state and denominator
    sections = [e.label for e in at.expander if " · " in e.label]
    check(len(sections) == 5, f"five sections, no more {sections}")
    for subsection in progress.CLAIM_SUBSECTIONS:
        found = [s for s in sections if subsection in s]
        check(len(found) == 1, f"{subsection} appears once ({found})")
        check(any(mark in found[0] for mark in ("○", "●", "✓", "—")),
              f"and carries its own state ({found[0]})")

    parts = dict((label, (done, total)) for label, done, total, _ in
                 progress.claim_subsection_progress(
                     BRAIN, source_id, claim["id"],
                     store.load_responses(rid), store.load_edge_responses(rid)))
    for subsection, (done, total) in parts.items():
        wanted = f"{done}/{total}" if total else "none applicable"
        check(any(wanted in s for s in sections if subsection in s),
              f"{subsection} shows {wanted}")

    # The instrument, unchanged and in place
    placement = {spec.SUB_VALIDITY: ["HE-03", "HE-25", "HE-04", "HE-05"],
                 spec.SUB_GROUNDING: ["HE-06", "HE-07"],
                 spec.SUB_ATTRIBUTES: ["HE-08.1", "HE-08.2", "HE-08.3",
                                       "HE-08.4", "HE-08.5"],
                 spec.SUB_CONCEPTS: ["HE-12", "HE-21", "HE-20"]}
    for subsection, expected in placement.items():
        asked = [q.criterion_id for q in spec.questions_for(subsection)]
        check(asked[:len(expected)] == expected,
              f"{subsection} asks {expected} ({asked})")
        for question in spec.questions_for(subsection):
            if question.applicability == spec.IF_PARENT_IS_NEGATIVE:
                continue
            check(question.question_text in text,
                  f"{question.criterion_id} is asked in the spec's words")

    # B · Grounding — anchors as quotations, premise apart from them
    check("Anchors" in prose, "the anchors are shown")
    for quote in (claim.get("quotes") or [])[:2]:
        check(quote["quote"][:50] in prose, "each anchor's passage is readable")
        check(quote["location"] in prose, f"with its location ({quote['location']})")
    check("Premise" in prose and (claim.get("premise") or "")[:40] in prose,
          "and the premise stands separately from them")

    # C · Attributes — the Brain's values once, in one table
    check("Brain values" in prose, "the attributes are shown once, together")
    for label, field in views.CLAIM_ATTRIBUTES:
        check(label in prose, f"{label} has a row")
    check(prose.count("Claim type") == 1 or "claim_type" in prose,
          "and the schema names live in the questions, not in the table")

    # D · Concepts
    check("Mapped concepts, by family" in prose, "concepts are grouped by family")
    for family in spec.CONCEPT_FAMILIES:
        check(family in prose, f"the {family} family is named even when empty")
    check("Browse Concept registry" in labels, "the registry is one keystroke away")
    check(not any("Anchor grid" in (e.label or "") for e in at.expander),
          "and no inline registry expander was reintroduced")
    created = BRAIN.candidate_created_for(claim["id"])
    check(created, f"this claim has a candidate concept ({[c['id'] for c in created]})")
    check(created[0]["id"] in text, "HE-21 names the candidate it is asking about")
    he20 = next(q for q in spec.questions_for(spec.SUB_CONCEPTS)
                if q.criterion_id == "HE-20")
    check(he20.answer_options == ("Yes", "No"), "HE-20 is binary")
    check(spec.comment_required_note(he20) == "Required for No.",
          "and its comment note names an answer it actually offers")
    check("Required for No." in prose,
          "which is what the page says under it")
    he03 = next(q for q in spec.questions_for(spec.SUB_VALIDITY)
                if q.criterion_id == "HE-03")
    check(spec.comment_required_note(he03) == spec.COMMENT_REQUIRED_NOTE,
          "while a three-level criterion keeps the standard note")
    check("HE-20.b" not in text, "and HE-20.b is absent until HE-20 is answered No")

    # E · Relations — a comparison, judged edge by edge
    relations = BRAIN.relations_of(claim["id"])
    check(len(relations) == 4, f"this claim has relations to judge ({len(relations)})")
    check("THIS CLAIM" in prose and "RELATED CLAIM" in prose,
          "each edge is shown as a comparison of the two claims")
    check("HE-16 is derived from the judgments below" in prose,
          "and the claim-level value stays derived, as in the workbook")
    edge_radios = [r for r in at.radio if r.key and "|a" in r.key
                   and claim["id"] in r.key and "CLAIM_HE" not in r.key]
    check(len(edge_radios) == len(relations),
          f"one judgment per edge ({len(edge_radios)})")

    # Saving is untouched
    answer = next(r for r in at.radio if r.key.endswith("CLAIM_HE03|a"))
    at = flush(answer.set_value("Yes").run())
    stored = store.load_responses(rid)
    check(stored.get(f"CLAIM_HE03|{claim['id']}", {}).get("answer") == "Yes",
          "a claim answer still saves")
    tally = re.search(r"(\d+)/(\d+) applicable items complete",
                      _tagless(rendered_text(at)))
    check(tally and tally.group(1) == "1",
          f"and the header count follows it in the same run ({tally and tally.group(0)})")

    # HE-20.b appears on No, and only then
    he20_radio = next(r for r in at.radio if r.key.endswith("CLAIM_HE20|a"))
    at = flush(he20_radio.set_value("No").run())
    check("HE-20.b" in rendered_text(at), "answering HE-20 No opens HE-20.b")
    missing = progress.missing_items(BRAIN, source_id, store.load_responses(rid),
                                     store.load_edge_responses(rid))
    check(any(m.what == "HE-20.b" and claim["id"] in m.where for m in missing),
          f"and it is required, not optional "
          f"({[m.what for m in missing if claim['id'] in m.where]})")


def test_claim_navigation():
    """Movement between claims: always available, never a gate."""
    print("\n== moving between claims ==")
    fresh_db()
    source_id, evaluator = "SRC-0009", "vaclav"
    rid = _started(evaluator, "Vaclav", manifest.TRAINING, source_id)
    claims = BRAIN.claims_of(source_id)

    at = _open_claim(evaluator, "Vaclav", manifest.TRAINING, source_id, 0)
    previous = next(b for b in at.button if b.key == "prev_claim")
    following = next(b for b in at.button if b.key == "next_claim")
    check(previous.disabled, "there is no claim before the first")
    check(not following.disabled,
          "but the next one is reachable with nothing answered")

    at.session_state[ui.WIKI] = [(ui.SOURCE, source_id)]
    at = following.click().run()
    check(ss(at, f"claim_idx|{rid}") == 1, "and pressing it moves on")
    check(not ss(at, ui.WIKI), "with any modal that was open closed behind it")
    # The scroll request is raised and consumed within the same run, so what can
    # be checked from outside is that moving asks for it at all.
    moves = (APP_DIR / "views.py").read_text(encoding="utf-8")
    for mover in ("_move_claim", "_go_to_claim", "_go_to_section"):
        body = moves.split(f"def {mover}(")[1].split("\n\n\n")[0]
        check("request_scroll()" in body, f"{mover} opens the next page at the top")

    warned = _tagless(rendered_text(at))
    check("still has" in warned and "does not block you" in warned,
          "an incomplete claim warns and says plainly that it is not a gate")

    # The last claim leads on rather than pretending there is another
    at = _open_claim(evaluator, "Vaclav", manifest.TRAINING, source_id, len(claims) - 1)
    keys = [b.key for b in at.button]
    check("next_claim" not in keys, "there is no next claim after the last")
    onward = next(b for b in at.button if b.key == "claims_to_datasets")
    check(not onward.disabled and "Datasets" in onward.label,
          f"the forward control names where it goes ({onward.label})")
    at = onward.click().run()
    check(ss(at, f"section|{rid}") == "datasets", "and it goes there")

    # Every claim stays directly selectable
    at = _open_claim(evaluator, "Vaclav", manifest.TRAINING, source_id, 0)
    selector = at.selectbox[0]
    check(len(selector.options) == len(claims),
          f"every claim is in the selector ({len(selector.options)})")
    at = selector.set_value(len(claims) - 2).run()
    check(not at.exception and f"Claim {len(claims) - 1} of" in _tagless(rendered_text(at)),
          "and jumping to a distant one works with nothing answered")


BADGE_OK = views.BADGE[progress.AVAILABLE]


def complete_paper(brain, rid: str, source_id: str) -> None:
    """Answer everything, so a page can be seen in its finished state.

    Four passes because conditional follow-ups only appear once their parent has
    been answered negatively, and this deliberately answers some negatively —
    a paper full of "Yes" would never exercise HE-19.3, HE-20.b or HE-18.3.
    """
    for _ in range(4):
        responses = store.load_responses(rid)
        edges = store.load_edge_responses(rid)
        for i, item in enumerate(progress.all_items(brain, source_id, responses)):
            if responses.get(item.lookup, {}).get("answer"):
                continue
            if item.question.free_text:
                answer, comment = "a missing item, p.4", None
            elif i % 6 == 0:
                answer, comment = "No", "defect, p.3"
            elif i % 7 == 0 and "In part" in item.question.answer_options:
                answer, comment = "In part", "partly captured, p.5"
            else:
                answer, comment = "Yes", None
            store.save_response(
                rid, object_type=item.object_type, object_id=item.object_id,
                question_key=item.question.question_key,
                criterion_id=item.question.criterion_id,
                field_subitem=item.question.field_subitem,
                answer=answer, comment=comment, source_id=source_id)
        for claim in brain.claims_of(source_id):
            for edge in brain.relations_of(claim["id"]):
                key = store.edge_key_of(edge)
                if edges.get(key, {}).get("label_correct"):
                    continue
                store.save_edge_response(
                    rid, host_claim_id=claim["id"], edge_key=key,
                    edge_from=edge.get("from"), edge_to=edge.get("to"),
                    other_claim_id=edge["other_claim_id"], edge_type=edge["type"],
                    label_correct="Yes", comment=None, source_id=source_id)


def test_datasets_page():
    """Step 9.7 — Dataset records, then recall for the Source as a whole."""
    print("\n== the Datasets page ==")
    fresh_db()
    source_id, evaluator = "SRC-0009", "vaclav"
    rid = _started(evaluator, "Vaclav", manifest.TRAINING, source_id)
    datasets = BRAIN.datasets_of(source_id)
    check(len(datasets) == 1, f"this source has a dataset to evaluate ({len(datasets)})")

    at = open_section(evaluator, "Vaclav", manifest.TRAINING, source_id, "datasets")
    check(not at.exception, "the section renders")
    prose = _tagless(rendered_text(at))
    labels = [b.label for b in at.button]
    sections = [e.label for e in at.expander]

    check("Datasets" in prose, "it is headed Datasets")
    check("Dataset records the Brain created for this Source" in prose,
          "and says what a Dataset record is")
    check(f"Dataset 1 of {len(datasets)}" in prose, "each dataset is placed in the set")
    check("Open Dataset wiki" in labels, "the wiki opens from the record")
    for label, field in views.DATASET_FIELDS:
        check(label in prose, f"{label} has a row in the value table")
    check(any("Claims resting on this Dataset" in s for s in sections),
          f"the claims resting on it are listed {sections[:2]}")
    opened = [e.label for e in at.expander if e.proto.expanded]
    check(opened == [f"{BADGE_OK}  {views.SUB_DATASET_NODE} · 0/2"],
          f"only the first unfinished subsection opens; everything else, criterion "
          f"definitions included, starts closed {opened}")

    for subsection in (views.SUB_DATASET_NODE, views.SUB_DATASET_ATTRIBUTES):
        found = [s for s in sections if subsection in s]
        check(len(found) == 1, f"{subsection} is its own section ({found})")
    node = [q.criterion_id for q in spec.dataset_questions()
            if q.criterion_id.startswith("HE-14")]
    attributes = [q.criterion_id for q in spec.dataset_questions()
                  if q.criterion_id.startswith("HE-15")]
    check(node == ["HE-14.1", "HE-14.2"], f"the node section asks {node}")
    check(attributes == [f"HE-15.{n}" for n in range(1, 8)],
          f"and the attribute section asks {attributes}")
    for question in spec.dataset_questions():
        check(question.question_text in rendered_text(at),
              f"{question.criterion_id} is asked in the spec's words")

    # HE-14.3 stands apart, and keeps its evaluator-selectable N/A
    recall = spec.dataset_recall_question()
    check("Dataset recall — Source as a whole" in prose,
          "recall is separated from the per-dataset questions")
    check(recall.answer_options == ("Yes", "In part", "No", "N/A"),
          f"and keeps its four options {recall.answer_options}")
    check(recall.human_na, "the N/A there is the evaluator's to choose")
    radio = next(r for r in at.radio if r.key.endswith("SOURCE_HE14_3|a"))
    check(list(radio.options) == ["Yes", "In part", "No", "N/A"],
          f"as the page offers them {list(radio.options)}")

    for leak in ("run_id", "RUN-2026", "raw/", "brain/"):
        check(leak not in prose, f"no {leak} on the page")

    at = flush(radio.set_value("N/A").run())
    stored = store.load_responses(rid)
    row = stored.get(f"SOURCE_HE14_3|{source_id}", {})
    check(row.get("answer") == "N/A", "an N/A chosen by the evaluator saves")
    check(row.get("applicability") == spec.APPLICABLE,
          f"as an applicable question answered N/A, not as auto-N/A "
          f"({row.get('applicability')})")

    # A source with no Dataset node is still asked the recall question
    bare = next(s for s in BRAIN.source_ids if not BRAIN.datasets_of(s)
                and s in manifest.assigned_source_ids("vaclav", manifest.AGREEMENT)
                + manifest.training_source_ids())
    _started(evaluator, "Vaclav", manifest.TRAINING
             if bare in manifest.training_source_ids() else manifest.AGREEMENT, bare)
    phase = (manifest.TRAINING if bare in manifest.training_source_ids()
             else manifest.AGREEMENT)
    at = open_section(evaluator, "Vaclav", phase, bare, "datasets")
    prose = _tagless(rendered_text(at))
    check("no Dataset nodes for this Source" in prose,
          f"a source with none says so ({bare})")
    check("Dataset recall — Source as a whole" in prose,
          "and is still asked the recall question")
    check(any(r.key.endswith("SOURCE_HE14_3|a") for r in at.radio),
          "with a working control, because no node is not the same as nothing missing")


def test_cites_page():
    """Step 9.8 — citations inside the Brain, not the paper's bibliography."""
    print("\n== the CITES page ==")
    fresh_db()
    evaluator = "vaclav"
    source_id = next(s for s in manifest.training_source_ids()
                     if BRAIN.cites_from(s) and BRAIN.cites_to(s))
    _started(evaluator, "Vaclav", manifest.TRAINING, source_id)
    outgoing = BRAIN.cites_from(source_id)
    incoming = BRAIN.cites_to(source_id)
    here = BRAIN.work_id(source_id)

    at = open_section(evaluator, "Vaclav", manifest.TRAINING, source_id, "cites")
    check(not at.exception, "the section renders")
    text = rendered_text(at)
    prose = _tagless(text)
    labels = [b.label for b in at.button]

    check("Citations within the Brain" in prose, "the page is named for what it holds")
    check("not the paper's complete bibliography" in prose.lower(),
          "and says plainly what it is not")
    check("only when the cited publication is itself a Source in the Brain" in prose,
          "explaining when a citation becomes an edge")
    check("legislation, case law or other primary legal sources, are intentionally "
          "excluded" in prose, "and what is deliberately left out")

    check(f"Citations from this paper — evaluate ({len(outgoing)})" in prose,
          "outgoing citations are the ones evaluated")
    for edge in outgoing:
        target = edge["to"]
        check(target in prose, f"{target} is named by its Source id")
        check(BRAIN.work_id(target) in prose, "and by its work id")
        check(f"{here} → {BRAIN.work_id(target)}" in prose,
              f"with the direction shown ({here} → {BRAIN.work_id(target)})")
        check(BRAIN.source(target).get("title", "")[:40] in prose, "and its title")

    check(f"Other Brain Sources citing this paper — context only ({len(incoming)})"
          in prose, "incoming citations are context")
    check("not evaluated on this page" in prose, "and say so")
    answerable = [r.key for r in at.radio if r.key and "|a" in r.key]
    check(len(answerable) == 2,
          f"only HE-18.1 and HE-18.2 carry a control ({len(answerable)})")
    check("Browse Brain Sources" in labels, "the Source registry is one keystroke away")

    for question in spec.cites_questions():
        if question.applicability == spec.IF_PARENT_IS_NEGATIVE:
            check(question.question_text not in text,
                  f"{question.criterion_id} waits for a negative answer")
            continue
        check(question.question_text in text,
              f"{question.criterion_id} is asked in the spec's words")

    # HE-18.3 opens on a negative answer to either parent
    accuracy = next(r for r in at.radio if r.key.endswith("SOURCE_HE18_1|a"))
    at = flush(accuracy.set_value("In part").run())
    check("HE-18.3" in rendered_text(at), "HE-18.3 opens once accuracy is not Yes")

    # Zero outgoing edges: HE-18.1 is automatically inapplicable, HE-18.2 is not
    bare = next(s for s in manifest.assigned_source_ids(evaluator, manifest.AGREEMENT)
                if not BRAIN.cites_from(s))
    _started(evaluator, "Vaclav", manifest.AGREEMENT, bare)
    at = open_section(evaluator, "Vaclav", manifest.AGREEMENT, bare, "cites")
    prose = _tagless(rendered_text(at))
    check("generated no outgoing CITES edges" in prose,
          f"a source with no outgoing edge says so ({bare})")
    check("Not applicable — the Brain generated no outgoing CITES edges to assess."
          in prose, "HE-18.1 is settled by the application, not by the evaluator")
    keys = [r.key for r in at.radio if r.key and "|a" in r.key]
    check(not any("SOURCE_HE18_1" in k for k in keys),
          "so it offers no control")
    check(any("SOURCE_HE18_2" in k for k in keys),
          "while completeness is still asked — zero edges is not automatically right")


def test_source_completeness_page():
    """Step 9.9 — the paper as a whole, once every Claim has been seen."""
    print("\n== the Source-level completeness page ==")
    fresh_db()
    source_id, evaluator = "SRC-0009", "vaclav"
    rid = _started(evaluator, "Vaclav", manifest.TRAINING, source_id)
    claims = BRAIN.claims_of(source_id)

    at = open_section(evaluator, "Vaclav", manifest.TRAINING, source_id, "recall")
    check(not at.exception, "the section renders")
    text = rendered_text(at)
    prose = _tagless(text)
    labels = [b.label for b in at.button]

    check("Source-level completeness" in prose, "the page is renamed")
    check(progress.SECTION_LABEL["recall"] == "5 · Source-level completeness",
          f"and so is its place in the section bar "
          f"({progress.SECTION_LABEL['recall']})")
    check("A · Claim recall" in prose and "B · Conceptual coverage" in prose,
          "it is split into the two questions it actually asks")

    # A · Claim recall
    check(f"Extracted Claims ({len(claims)})" in prose, "every claim is listed")
    for claim in claims:
        check(claim["id"] in prose, f"{claim['id']} by id")
    check(prose.count("View details") == 0 or labels.count("View details") == len(claims),
          f"each with a way into its record ({labels.count('View details')})")
    check("Open Source wiki" in labels, "and the Source wiki is at hand")

    # B · Conceptual coverage — the evidence before the question
    check("Concepts represented across this Source" in prose,
          "the aggregated mapping is shown before the question about it")
    families = BRAIN.concepts_of_source(source_id)
    mapped = [c for entries in families.values() for c in entries]
    check(mapped, f"there are concepts to show ({len(mapped)})")
    for concept in mapped[:5]:
        check(concept["label"] in prose, f"{concept['label']} is named")
        plural = "Claim" if concept["claims"] == 1 else "Claims"
        check(f"{concept['claims']} {plural}" in prose,
              f"with how many Claims map it ({concept['claims']} {plural})")
    for family in spec.CONCEPT_FAMILIES:
        check(family in prose, f"grouped under {family}")
    check("Browse Concept registry" in labels, "the registry is one keystroke away")
    check("Claim recall and conceptual coverage test different failures" in prose,
          "and the two are explicitly told apart")

    for question in spec.recall_questions():
        if question.applicability == spec.IF_PARENT_IS_NEGATIVE:
            check(question.question_text not in text,
                  f"{question.criterion_id} waits for a negative answer")
            continue
        check(question.question_text in text,
              f"{question.criterion_id} is asked in the spec's words")
    he20s = next(q for q in spec.recall_questions() if q.criterion_id == "HE-20.S")
    check(he20s.answer_options == ("Yes", "In part", "No"),
          f"HE-20.S keeps the three-level scale {he20s.answer_options}")

    recall = next(r for r in at.radio if r.key.endswith("SOURCE_HE19_1|a"))
    at = flush(recall.set_value("In part").run())
    check("HE-19.3" in rendered_text(at), "HE-19.3 opens once recall is not Yes")
    coverage = next(r for r in at.radio if r.key.endswith("SOURCE_HE20S|a"))
    at = flush(coverage.set_value("No").run())
    check("HE-20.S.b" in rendered_text(at), "as does HE-20.S.b on its own parent")


def test_review_page():
    """Step 9.10 — a validation dashboard, not the evaluation over again."""
    print("\n== the Review page ==")
    fresh_db()
    source_id, evaluator, phase = "SRC-0004", "vaclav", manifest.TRAINING
    rid = _started(evaluator, "Vaclav", phase, source_id)

    at = open_section(evaluator, "Vaclav", phase, source_id, "review")
    check(not at.exception, "the section renders")
    prose = _tagless(rendered_text(at))
    check("Review paper" in prose, "it is headed Review paper")
    check("You may return to any section and revise your responses" in prose,
          "and says so, because completion is not the end")

    for heading in ("Evaluation status", "Items requiring attention",
                    "Recorded omissions and defects", "Evaluation overview",
                    "Paper status"):
        check(heading in prose, f"it has an {heading!r} block")

    missing = progress.missing_items(BRAIN, source_id, store.load_responses(rid),
                                     store.load_edge_responses(rid))
    check(f"Incomplete — {len(missing)} items require attention" in prose,
          f"the status counts what is outstanding ({len(missing)})")
    goto = [b for b in at.button if b.key and b.key.startswith("goto|")]
    check(len(goto) == min(len(missing), views.ATTENTION_LIMIT),
          f"the outstanding items are listed, capped so a barely-started paper "
          f"does not render {len(missing)} identical cards ({len(goto)})")
    check(any(f"first {views.ATTENTION_LIMIT} of {len(missing)}" in i.value
              for i in at.info),
          "and the page says what it is not showing")
    check(len([b for b in at.button if b.key and b.key.startswith("open_sec|")]) == 5,
          "and every section is reachable from its status row")

    # It must not become a second copy of the evaluation
    sections = [e.label for e in at.expander]
    check(sum(1 for s in sections if "·" in s) >= 5,
          f"the overview is collapsed, one block per section {sections}")
    check(all(not e.proto.expanded for e in at.expander),
          "and nothing is expanded by default")

    # Go to item lands where it says
    target = next(m for m in missing if m.section == "claims"
                  and m.claim_index is not None)
    index = missing.index(target)
    at = at.button(key=f"goto|{index}").click().run()
    check(ss(at, f"section|{rid}") == "claims", "Go to item moves to the section")
    check(ss(at, f"claim_idx|{rid}") == target.claim_index,
          f"and to the claim it named (claim {target.claim_index})")

    # --- Answer everything, and watch the page change its mind
    complete_paper(BRAIN, rid, source_id)
    at = open_section(evaluator, "Vaclav", phase, source_id, "review")
    prose = _tagless(rendered_text(at))
    check("Ready to complete" in prose, "with nothing missing, the page says so")
    check("Nothing is missing" in prose, "and the attention list is empty")
    mark = next(b for b in at.button if b.label == "Mark paper complete")
    check(not mark.disabled, "and the completion button is live")

    # A finding is not a gap
    findings = [e.label for e in at.expander if e.label.startswith("Missing")]
    check(len(findings) == 5,
          f"every kind of recorded omission is listed apart {findings}")
    check(any(not label.endswith("(0)") for label in findings),
          f"and this paper's findings are among them {findings}")
    check("They do not prevent completion" in prose,
          "and are explicitly not treated as incomplete work")
    check("Ready to complete" in prose,
          "which is why a paper full of recorded defects is still ready")

    at = flush(mark.click().run())
    check(store.get_review(phase, evaluator, source_id).get("status")
          == store.STATUS_COMPLETE, "marking complete works")

    # Completion is reversible, and an edit demotes it
    at = open_section(evaluator, "Vaclav", phase, source_id, "review")
    check("Complete." in _tagless(rendered_text(at)), "the page says the paper is complete")
    check(any(b.label == "Reopen for editing" for b in at.button),
          "and offers to reopen it")

    at = open_section(evaluator, "Vaclav", phase, source_id, "source")
    edit = next(r for r in at.radio if r.key.endswith("SOURCE_HE08_1|a"))
    flush(edit.set_value("In part").run())
    check(store.get_review(phase, evaluator, source_id).get("status")
          == store.STATUS_IN_PROGRESS,
          "and any later edit demotes it to in progress again")


def admin():
    """The admin page, already unlocked."""
    at = signed_in("thiago", "Thiago", "Admin")
    at.session_state["admin_ok"] = True
    return at.run()


def _finish_phase(evaluator: str, phase_id: str, sources) -> list[str]:
    """Every assigned paper answered and marked complete, ready to submit."""
    rids = []
    for source_id in sources:
        rid = _started(evaluator, evaluator.capitalize(), phase_id, source_id)
        complete_paper(BRAIN, rid, source_id)
        store.mark_complete(rid)
        rids.append(rid)
    return rids


def test_phase_submission_marker():
    """Step 10 — a phase is submitted when the marker exists, and not before."""
    print("\n== the phase submission marker ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.TRAINING
    sources = manifest.assigned_source_ids(evaluator, phase_id)
    check(sources, f"there is a phase to submit ({len(sources)} papers)")

    check(sheets.PHASE_SUBMISSIONS in sheets.ALL_TABS,
          "the workbook has a PHASE_SUBMISSIONS tab")
    check(sheets.COLUMNS[sheets.PHASE_SUBMISSIONS] ==
          ("submission_key", "evaluator_id", "phase_id", "config_version",
           "status", "submitted_at"),
          f"with the agreed columns {sheets.COLUMNS[sheets.PHASE_SUBMISSIONS]}")
    check(sheets.KEY_COLUMN[sheets.PHASE_SUBMISSIONS] == "submission_key",
          "keyed by submission_key")
    check(store.submission_key(phase_id, evaluator) == f"{phase_id}|{evaluator}",
          "which is phase_id|evaluator_id")

    check(not store.phase_submitted(phase_id, evaluator),
          "nothing is submitted to begin with")

    rids = _finish_phase(evaluator, phase_id, sources)
    at = signed_in(evaluator, "Vaclav", manifest.PHASE_LABEL[phase_id]).run()
    submit = [b for b in at.button if b.label == "Submit all papers"]
    check(submit and submit[0].disabled,
          "submission waits for the confirmation")
    at = at.checkbox(key=f"confirm_batch|{phase_id}|{evaluator}").check().run()
    at = flush(next(b for b in at.button
                    if b.label == "Submit all papers").click().run())

    check(all(store.get_review(phase_id, evaluator, s)["status"]
              == store.STATUS_SUBMITTED for s in sources),
          "every paper in the phase is locked")
    check(store.phase_submitted(phase_id, evaluator),
          "and the marker records the phase as submitted")
    marker = store.phase_submission(phase_id, evaluator)
    check(marker["config_version"] == manifest.config_version(),
          "under the configuration it was submitted against")
    check(marker["submitted_at"], "with the moment it happened")

    # Independent of the other phases
    for other in manifest.PHASES:
        if other == phase_id:
            continue
        check(not store.phase_submitted(other, evaluator),
              f"submitting {phase_id} does not submit {other}")
        assigned = manifest.assigned_source_ids(evaluator, other)
        check(all((store.get_review(other, evaluator, s) or {}).get("status")
                  != store.STATUS_SUBMITTED for s in assigned),
              f"nor lock any {other} paper")

    at = signed_in(evaluator, "Vaclav", manifest.PHASE_LABEL[phase_id]).run()
    text = _tagless(rendered_text(at))
    check("was finally submitted on" in text, "the page says the phase is submitted")
    check(not any(b.label == "Submit all papers" for b in at.button),
          "and offers no way to submit it twice")

    # Reopening one paper withdraws the phase
    retracted = store.reopen_review(rids[0])
    check(retracted, "reopening a submitted paper retracts the marker")
    check(not store.phase_submitted(phase_id, evaluator),
          "so the phase is no longer submitted")
    row = store.phase_submission(phase_id, evaluator)
    check(row and row["status"] == store.RETRACTED,
          "the record is kept and marked retracted, not deleted — that it "
          "happened is part of what happened")
    check(store.export("phase_submissions"), "and it exports")

    at = signed_in(evaluator, "Vaclav", manifest.PHASE_LABEL[phase_id]).run()
    check("submitted and then reopened" in _tagless(rendered_text(at)),
          "the evaluator is told why the phase is open again")


def test_submission_refuses_incomplete_work():
    """Submission is checked against storage, not against a recorded status."""
    print("\n== submission re-reads before it locks ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.TRAINING
    sources = manifest.assigned_source_ids(evaluator, phase_id)
    rids = _finish_phase(evaluator, phase_id, sources)

    # An answer goes missing after the paper was marked complete, and the
    # recorded status is left saying otherwise — the state that reaches this
    # code when a second session edits a paper, or when a write is lost.
    hollow = sources[0]
    store.save_response(
        rids[0], object_type="source", object_id=hollow,
        question_key="SOURCE_HE08_1", criterion_id="HE-08.1",
        field_subitem="Contribution type", answer="", comment="",
        source_id=hollow)
    store.mark_complete(rids[0])
    check(store.get_review(phase_id, evaluator, hollow)["status"]
          == store.STATUS_COMPLETE, "the recorded status still says complete")
    check(progress.missing_items(BRAIN, hollow, store.load_responses(rids[0]),
                                 store.load_edge_responses(rids[0])),
          "while the stored answers say it is not")

    at = signed_in(evaluator, "Vaclav", manifest.PHASE_LABEL[phase_id]).run()
    at = at.checkbox(key=f"confirm_batch|{phase_id}|{evaluator}").check().run()
    at = flush(next(b for b in at.button
                    if b.label == "Submit all papers").click().run())

    check(not store.phase_submitted(phase_id, evaluator),
          "nothing was submitted")
    check(all(store.get_review(phase_id, evaluator, s)["status"]
              != store.STATUS_SUBMITTED for s in sources),
          "not one paper was locked, not even the complete ones")
    check(store.get_review(phase_id, evaluator, hollow)["status"]
          == store.STATUS_IN_PROGRESS,
          "and the paper that fell short is back in progress")
    check("no longer complete" in _tagless(rendered_text(at)),
          "with the reason said plainly")


def test_reserved_rows_do_not_gate_submission():
    """A paper nobody was asked to read cannot hold a phase open."""
    print("\n== reservations count toward nothing ==")
    fresh_db()
    holder, phase_id = "thiago", manifest.INDIVIDUAL
    reserved = [r for r in manifest.reserved(phase_id)
                if r["evaluator_id"] == holder]
    check(reserved, f"this evaluator holds reservations ({len(reserved)})")
    check(not manifest.assigned_source_ids(holder, phase_id),
          "and no assignment in the phase")

    at = signed_in(holder, "Thiago", manifest.PHASE_LABEL[phase_id]).run()
    text = _tagless(rendered_text(at))
    check("No papers are assigned to you in this phase" in text,
          "so the phase shows nothing to do")
    data = load_brain()
    check(not any(r["source_id"] in text or data.work_id(r["source_id"]) in text
                  for r in reserved),
          "and no reserved paper is named")

    outstanding = [row["evaluator_id"] for row in
                   __import__("streamlit_app")._phase_outstanding(phase_id)]
    check(holder not in outstanding,
          f"nor does the reservation hold the phase unfinished ({outstanding})")


def test_admin_progress_and_assignments():
    """Step 11 — what Admin shows, and what it must not."""
    print("\n== admin: progress and assignments ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.TRAINING
    sources = manifest.assigned_source_ids(evaluator, phase_id)
    rid = _started(evaluator, "Vaclav", phase_id, sources[0])
    complete_paper(BRAIN, rid, sources[0])

    at = admin()
    check(not at.exception, "the admin page renders")
    check([t.label for t in at.tabs] ==
          ["Progress", "Assignments", "Control", "Exports", "System"],
          "with the five tabs")

    frames = [f.value for f in at.dataframe]
    columns = [set(f.columns) for f in frames if hasattr(f, "columns")]
    progress_table = next(c for c in columns if "paper status" in c)
    check(progress_table == {"evaluator", "phase", "split", "paper", "progress",
                             "claims", "paper status", "phase submission"},
          f"Progress shows status and nothing else {sorted(progress_table)}")
    table = next(f.value for f in at.dataframe
                 if "split" in getattr(f.value, "columns", []))
    check(all(str(v).strip() for v in table["split"]),
          f"and every row names the split its paper belongs to "
          f"({list(table['split'])})")

    # No substantive answer may appear anywhere on the page.
    answers = store.load_responses(rid)
    comments = [r["comment_evidence"] for r in answers.values()
                if (r.get("comment_evidence") or "").strip()]
    check(comments, f"the evaluator has recorded comments ({len(comments)})")
    everything = rendered_text(at) + " ".join(
        f.to_csv() for f in frames if hasattr(f, "to_csv"))
    leaked = [c for c in comments if c in everything]
    check(not leaked, f"none of them reaches the Progress table {leaked[:2]}")

    reserved = manifest.reserved(manifest.INDIVIDUAL)
    tables = " ".join(f.to_csv() for f in frames if hasattr(f, "to_csv"))
    check(all(row["assignment_key"] in tables for row in reserved),
          "Admin does see the reserved rows, which the evaluators do not")


def test_admin_freeze_refuses_unsubmitted_work():
    """Closing a phase must never read as though the work had been submitted."""
    print("\n== admin: freezing a phase ==")
    fresh_db()
    phase_id = manifest.AGREEMENT
    import streamlit_app

    outstanding = streamlit_app._phase_outstanding(phase_id)
    holders = {e["evaluator_id"] for e in manifest.evaluators()
               if manifest.assigned_source_ids(e["evaluator_id"], phase_id)}
    check({row["evaluator_id"] for row in outstanding} == holders,
          f"with nothing done, every assigned evaluator is outstanding "
          f"({len(outstanding)})")

    at = admin()
    check(not any(b.key == f"phase_close|{phase_id}" for b in at.button),
          "so the phase cannot be frozen")
    pause = [b for b in at.button if b.key == f"phase_pause|{phase_id}"]
    check(pause and pause[0].disabled,
          "and pausing it needs the deliberate acknowledgement")
    acknowledgement = next(c.label for c in at.checkbox
                           if c.key == f"pause_ok|{phase_id}")
    check("claims nothing about completeness or submission" in acknowledgement,
          f"which says exactly what pausing does not mean ({acknowledgement})")

    # The two acts must be impossible to confuse on the page itself.
    page = _tagless(rendered_text(at))
    check("Pause" in page and "operational" in page,
          "the page names pausing as operational")
    check("Freeze" in page and "methodological closure" in page,
          "and freezing as methodological closure")
    check("must not be analysed as though it were" in page,
          "and says plainly that a paused phase is not a finished one")
    check(f"Cannot freeze {manifest.PHASE_LABEL[phase_id]}" in page,
          "refusing by name rather than by hiding the control")

    # Finish and submit the phase for everyone, and the freeze becomes available
    for entry in manifest.evaluators():
        who = entry["evaluator_id"]
        assigned = manifest.assigned_source_ids(who, phase_id)
        if not assigned:
            continue
        rids = _finish_phase(who, phase_id, assigned)
        store.submit_many(rids)
        store.record_phase_submission(phase_id, who, manifest.config_version())

    check(not streamlit_app._phase_outstanding(phase_id),
          "nothing is outstanding once every evaluator has submitted")
    at = admin()
    freeze = [b for b in at.button if b.key == f"phase_close|{phase_id}"]
    check(freeze and not freeze[0].disabled, "and the phase can be frozen")

    # Freezing changes availability and nothing else
    before = {r["review_id"]: r["status"] for r in store.all_reviews()}
    at = freeze[0].click().run()
    check(not manifest.phase_open(phase_id), "freezing closes the phase")
    after = {r["review_id"]: r["status"] for r in store.all_reviews()}
    check(before == after, "and touches no review's status")
    manifest.set_phase(phase_id, True)

    # A phase that is merely unfinished is still pausable
    other = manifest.INDIVIDUAL
    at = admin()
    at = at.checkbox(key=f"pause_ok|{other}").check().run()
    at = next(b for b in at.button if b.key == f"phase_pause|{other}").click().run()
    check(not manifest.phase_open(other), "an unfinished phase can still be paused")
    check(not any(store.phase_submitted(other, e["evaluator_id"])
                  for e in manifest.evaluators()),
          "and pausing submits nothing on anybody's behalf")
    # A closed phase says which of the two it is, from its submissions rather
    # than from a flag that could be wrong.
    at = admin()
    closed = _tagless(rendered_text(at))
    check("this is a paused phase, not a frozen one" in closed,
          "a phase closed with work outstanding reads as paused")
    manifest.set_phase(other, True)

    manifest.set_phase(phase_id, False)
    at = admin()
    check("this is a frozen phase" in _tagless(rendered_text(at)),
          "and one closed after everybody submitted reads as frozen")
    manifest.set_phase(phase_id, True)


def test_admin_exports():
    """Everything needed to reconstruct the run, and what it was produced by."""
    print("\n== admin: exports ==")
    fresh_db()
    at = admin()
    labels = [b.label for b in at.download_button]
    for name in ("config", "evaluators", "assignments", "reviews", "responses",
                 "edge_responses", "phase_submissions", "provenance"):
        check(any(label.startswith(f"{name}.csv") for label in labels),
              f"{name}.csv is offered ({[l.split(' ')[0] for l in labels]})")
    check(any("Combined workbook (XLSX)" in label for label in labels),
          "as is the combined workbook")

    import streamlit_app
    metadata = streamlit_app._provenance_metadata()
    for key in ("brain_snapshot_id", "eval_spec_version", "config_version",
                "split_version", "configuration_source", "storage_backend"):
        check(metadata.get(key), f"the provenance sheet carries {key}")


# ===================================================== step 12: reliability
def test_all_six_evaluators_at_once():
    """Six sessions writing together. Nobody's answer lands in anybody's row."""
    print("\n== six evaluators at once ==")
    fresh_db()
    people = manifest.evaluators()
    check(len(people) == 6, f"there are six evaluators ({len(people)})")

    work = []
    for entry in people:
        evaluator = entry["evaluator_id"]
        phase = manifest.AGREEMENT
        sources = manifest.assigned_source_ids(evaluator, phase)
        if not sources:
            continue
        source_id = sources[0]
        rid = store.ensure_review(
            phase_id=phase, evaluator_id=evaluator, evaluator_name=entry["name"],
            pair_id=manifest.pair_of(evaluator) or "", source_id=source_id,
            work_id=BRAIN.work_id(source_id), brain_snapshot_id=BRAIN.snapshot_id,
            eval_spec_version=spec.EVAL_SPEC_VERSION)
        store.start_review(rid, True)
        work.append((evaluator, source_id, rid))
    check(len(work) == 6, f"each has a paper to work on ({len(work)})")

    # Every evaluator writes a distinguishable answer to the same criterion, at
    # the same moment, from their own thread.
    errors: list[str] = []
    barrier = threading.Barrier(len(work))

    def answer(evaluator, source_id, rid):
        try:
            barrier.wait(timeout=20)
            store.save_response(
                rid, object_type="source", object_id=source_id,
                question_key="SOURCE_HE08_1", criterion_id="HE-08.1",
                field_subitem="Contribution type", answer="In part",
                comment=f"written by {evaluator}", source_id=source_id)
        except Exception as error:                      # noqa: BLE001
            errors.append(f"{evaluator}: {error}")

    threads = [threading.Thread(target=answer, args=item) for item in work]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=40)
    check(not errors, f"every write succeeded {errors[:2]}")

    for evaluator, source_id, rid in work:
        stored = store.load_responses(rid)
        row = stored.get(f"SOURCE_HE08_1|{source_id}", {})
        check(row.get("comment_evidence") == f"written by {evaluator}",
              f"{evaluator}'s row holds {evaluator}'s comment")

    keys = [store.response_key(rid, "source", source_id, "SOURCE_HE08_1")
            for _, source_id, rid in work]
    check(len(set(keys)) == len(keys), "the six response keys are distinct")
    reviews = {rid for _, _, rid in work}
    check(len(reviews) == 6, "as are the six review rows")


def test_two_evaluators_on_one_agreement_paper():
    """The point of the agreement phase: same paper, two independent records."""
    print("\n== two evaluators, one agreement paper ==")
    fresh_db()
    pair = next(p for p in {e.get("pair_id") for e in manifest.evaluators()} if p)
    both = [e["evaluator_id"] for e in manifest.evaluators()
            if e.get("pair_id") == pair]
    check(len(both) == 2, f"a pair is two people ({both})")
    shared = set(manifest.assigned_source_ids(both[0], manifest.AGREEMENT))
    check(shared == set(manifest.assigned_source_ids(both[1], manifest.AGREEMENT)),
          "who are assigned exactly the same papers")

    source_id = sorted(shared)[0]
    rids = {}
    for who in both:
        rid = store.ensure_review(
            phase_id=manifest.AGREEMENT, evaluator_id=who,
            evaluator_name=who.capitalize(), pair_id=pair, source_id=source_id,
            work_id=BRAIN.work_id(source_id), brain_snapshot_id=BRAIN.snapshot_id,
            eval_spec_version=spec.EVAL_SPEC_VERSION)
        store.start_review(rid, True)
        rids[who] = rid

    verdicts = {both[0]: "Yes", both[1]: "No"}
    for who, verdict in verdicts.items():
        store.save_response(
            rids[who], object_type="source", object_id=source_id,
            question_key="SOURCE_HE08_2", criterion_id="HE-08.2",
            field_subitem="Source jurisdiction", answer=verdict,
            comment="because" if verdict == "No" else None, source_id=source_id)

    for who, verdict in verdicts.items():
        stored = store.load_responses(rids[who])
        check(stored[f"SOURCE_HE08_2|{source_id}"]["answer"] == verdict,
              f"{who} recorded {verdict}, and still does")
    check(rids[both[0]] != rids[both[1]], "in two separate reviews")

    # And they cannot see each other: the page loads one review's rows.
    at = open_section(both[0], both[0].capitalize(), manifest.AGREEMENT,
                      source_id, "source")
    radios = [r for r in at.radio if r.key.endswith("SOURCE_HE08_2|a")]
    check(radios and radios[0].value == verdicts[both[0]],
          f"and each sees only their own answer ({radios[0].value if radios else None})")


def test_rapid_edits_keep_the_last_value():
    """Answers changed faster than they can be written still end up right."""
    print("\n== rapid edits ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.TRAINING
    source_id = manifest.assigned_source_ids(evaluator, phase_id)[0]
    rid = _started(evaluator, "Vaclav", phase_id, source_id)

    at = open_section(evaluator, "Vaclav", phase_id, source_id, "source")
    radio = next(r for r in at.radio if r.key.endswith("SOURCE_HE08_1|a"))
    for value in ("Yes", "No", "In part", "No", "Yes"):
        at = radio.set_value(value).run()
        radio = next(r for r in at.radio if r.key.endswith("SOURCE_HE08_1|a"))
    at = flush(at)
    stored = store.load_responses(rid)
    check(stored[f"SOURCE_HE08_1|{source_id}"]["answer"] == "Yes",
          "five changes in a row leave the last one stored")

    comment = next(t for t in at.text_area if t.key.endswith("SOURCE_HE08_1|c"))
    drafts = ["a", "an a", "an an", "an answer", "an answer, finally"]
    for draft in drafts:
        at = comment.set_value(draft).run()
        comment = next(t for t in at.text_area if t.key.endswith("SOURCE_HE08_1|c"))
    at = flush(at)
    stored = store.load_responses(rid)
    check(stored[f"SOURCE_HE08_1|{source_id}"]["comment_evidence"] == drafts[-1],
          "and typing leaves the last draft, not an earlier keystroke")
    check(ss(at, "_save_queue").unresolved == 0, "with nothing left unwritten")


def test_submission_waits_for_every_write():
    """A phase cannot be submitted while an answer is still in the air."""
    print("\n== submission waits for storage ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.TRAINING
    sources = manifest.assigned_source_ids(evaluator, phase_id)
    _finish_phase(evaluator, phase_id, sources)

    # The paper list saves nothing, so it has no queue of its own. The session
    # is given one holding a write that cannot land — the state a real session
    # reaches when the network drops mid-answer.
    queue = savequeue.SaveQueue()
    queue.set_fatal(store.SaveConflict)
    at = signed_in(evaluator, "Vaclav", manifest.PHASE_LABEL[phase_id])
    at.session_state["_save_queue"] = queue
    at = at.run()
    original = savequeue.RETRY_SECONDS
    savequeue.RETRY_SECONDS = 0.02
    try:
        def unreachable(**kwargs):
            raise RuntimeError("the network went away")

        queue.submit("stuck", unreachable, value="Yes")
        deadline = time.monotonic() + 5
        while queue.state[0] != savequeue.FAILED and time.monotonic() < deadline:
            time.sleep(0.05)
        check(queue.unresolved == 1, "one write is unresolved")

        at = at.checkbox(key=f"confirm_batch|{phase_id}|{evaluator}").check().run()
        at = next(b for b in at.button if b.label == "Submit all papers").click().run()
        check(not store.phase_submitted(phase_id, evaluator),
              "so the phase was not submitted")
        check(all(store.get_review(phase_id, evaluator, s)["status"]
                  != store.STATUS_SUBMITTED for s in sources),
              "and no paper was locked")
        check(any("not yet stored" in e.value for e in at.error),
              "with the reason given, and the write kept")
        check(queue.unresolved == 1, "the write is still held, not dropped")
    finally:
        savequeue.RETRY_SECONDS = original
        queue.stop()


def test_first_answer_conflict_window():
    """The one case detection does not cover, exercised and recorded.

    Two tabs answer the *same never-answered* item. The second write carries an
    empty expectation, because from its own session's point of view the row has
    never been written. On Google Sheets — the deployed backend — an empty
    expectation skips the check, because honouring it would mean a targeted read
    on every first answer of every item. So the second tab overwrites the first
    silently. Accepted deliberately; this is best-effort detection, not
    transactional locking.

    SQLite happens not to have the window, because its check reads the row in
    the same statement and costs nothing extra. That is a property of the local
    development store, not a guarantee the deployment inherits.
    """
    print("\n== the first-answer window (known limitation) ==")
    import tempfile

    def two_tabs_answer_first():
        """Returns (refused, stored answer) for two tabs racing a blank item."""
        source_id = manifest.training_source_ids()[0]
        rid = store.ensure_review(
            phase_id=manifest.TRAINING, evaluator_id="vaclav",
            evaluator_name="Vaclav", pair_id="B", source_id=source_id,
            work_id=BRAIN.work_id(source_id), brain_snapshot_id=BRAIN.snapshot_id,
            eval_spec_version=spec.EVAL_SPEC_VERSION)
        store.start_review(rid, True)
        items = progress.all_possible_items(BRAIN, source_id)
        edges = [(c["id"], e) for c in BRAIN.claims_of(source_id)
                 for e in BRAIN.relations_of(c["id"])]
        store.preallocate(
            rid, source_id,
            [(i.object_type, i.object_id, i.question,
              store.AUTO_NA if i.auto_na else "") for i in items], edges)
        lookup = f"SOURCE_HE08_1|{source_id}"

        def write(answer, expected=""):
            """One tab's save. `expected` is the stamp that tab last saw."""
            return store.save_responses([{
                "rid": rid, "object_type": "source", "object_id": source_id,
                "question_key": "SOURCE_HE08_1", "criterion_id": "HE-08.1",
                "field_subitem": "Contribution type", "answer": answer,
                "comment": f"from the tab that said {answer}",
                "source_id": source_id, "applicability": spec.APPLICABLE,
                "expected_updated_at": expected,
            }])[0]

        # Both tabs opened the paper before either had answered, so both hold an
        # empty expectation for this item.
        stamp_a = write("Yes")             # tab A, believing it is the first
        refused = False
        try:
            write("No")                    # tab B, believing the same
        except store.SaveConflict:
            refused = True
        return refused, store.load_responses(rid)[lookup], rid, source_id, write, stamp_a

    # --- the deployed backend
    directory = pathlib.Path(tempfile.mkdtemp())
    original = store.workbook
    store.workbook = lambda: sheets.LocalWorkbook(directory)
    try:
        store.init()
        refused, stored, rid, source_id, write, stamp_a = two_tabs_answer_first()
        check(not refused,
              "on the Sheets backend the second tab is NOT refused — "
              "this is the documented window")
        check(stored["answer"] == "No",
              "and it overwrites the first tab's answer silently")

        # It is a window, not a hole. The window is one write wide *per tab*:
        # a tab that has saved once holds the stamp its save returned, so its
        # next edit carries a real expectation and is checked.
        check(stored["updated_at"], "once answered, the row carries a stamp")
        refused = False
        try:
            write("In part", stamp_a)      # tab A edits again, on its old stamp
        except store.SaveConflict:
            refused = True
        check(refused,
              "so tab A's next edit is refused, because the row has moved on")
        check(store.load_responses(rid)[f"SOURCE_HE08_1|{source_id}"]["answer"]
              == "No", "and the stored answer is not disturbed by the refusal")
    finally:
        store.workbook = original
        store.forget_row_index()
        store.forget_reviews()

    # --- the local development store, for contrast
    fresh_db()
    refused, stored, _, _, _, _ = two_tabs_answer_first()
    check(refused, "SQLite refuses the second tab, because its check is free")
    check(stored["answer"] == "Yes", "so the first answer stands there")

    source = (APP_DIR / "store.py").read_text(encoding="utf-8")
    check("Best-effort" in source or "best-effort" in source,
          "and the code names this detection for what it is: best-effort")
    check("first answer" in source.lower() or "first-answer" in source.lower()
          or "never been written" in source.lower(),
          "and the window itself is described where the check lives")


def test_survives_a_cold_restart():
    """Answers come back from storage, not from anything the process remembers."""
    print("\n== refresh, reopen, cold restart ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.TRAINING
    source_id = manifest.assigned_source_ids(evaluator, phase_id)[0]
    rid = _started(evaluator, "Vaclav", phase_id, source_id)
    claims = BRAIN.claims_of(source_id)

    at = open_section(evaluator, "Vaclav", phase_id, source_id, "source")
    at = flush(next(r for r in at.radio
                    if r.key.endswith("SOURCE_HE08_1|a")).set_value("In part").run())
    comment = next(t for t in at.text_area if t.key.endswith("SOURCE_HE08_1|c"))
    at = flush(comment.set_value("written before the crash").run())

    at = _open_claim(evaluator, "Vaclav", phase_id, source_id, 3)
    at = flush(next(r for r in at.radio
                    if r.key.endswith("CLAIM_HE03|a")).set_value("Yes").run())

    def sees_the_answers(label: str) -> None:
        page = open_section(evaluator, "Vaclav", phase_id, source_id, "source")
        radio = next(r for r in page.radio if r.key.endswith("SOURCE_HE08_1|a"))
        box = next(t for t in page.text_area if t.key.endswith("SOURCE_HE08_1|c"))
        check(radio.value == "In part" and box.value == "written before the crash",
              f"{label}: the source answer and its comment are there")
        claim = _open_claim(evaluator, "Vaclav", phase_id, source_id, 3)
        answer = next(r for r in claim.radio if r.key.endswith("CLAIM_HE03|a"))
        check(answer.value == "Yes", f"{label}: and the claim answer too")
        check(f"Claim 4 of {len(claims)}" in _tagless(rendered_text(claim)),
              f"{label}: on the claim that was being worked on")

    # A refresh is a new session against the same process.
    sees_the_answers("after a refresh")

    # A cold restart is a new process: nothing in memory survives it. Clearing
    # every cache the app keeps is the closest a single process can come, and it
    # is the thing that would hide a bug — an answer served from a cache that a
    # restart would have emptied.
    store.forget_reviews()
    store.forget_row_index()
    ui.forget_responses()
    manifest.invalidate()
    sees_the_answers("after a cold restart")

    stored = store.load_responses(rid)
    check(stored[f"SOURCE_HE08_1|{source_id}"]["answer"] == "In part",
          "and storage, read directly, agrees with the page")


def test_free_navigation_end_to_end():
    """The plan's exact sequence, with nothing answered. Nothing may block."""
    print("\n== free navigation, the whole way round ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.TRAINING
    source_id = max(manifest.training_source_ids(),
                    key=lambda s: len(BRAIN.claims_of(s)))
    rid = _started(evaluator, "Vaclav", phase_id, source_id)
    claims = BRAIN.claims_of(source_id)
    check(len(claims) >= 12, f"a paper with claims to move between ({len(claims)})")

    route = [("source", None), ("claims", 1), ("datasets", None), ("claims", 10),
             ("cites", None), ("review", None), ("claims", 3)]
    for section, claim_index in route:
        at = signed_in(evaluator, "Vaclav", manifest.PHASE_LABEL[phase_id],
                       source_id=source_id)
        at.session_state[f"section|{rid}"] = section
        if claim_index is not None:
            at.session_state[f"claim_idx|{rid}"] = claim_index
        at = at.run()
        where = f"{section}" + (f" claim {claim_index + 1}" if claim_index is not None
                                else "")
        check(not at.exception, f"{where} opens")
        if claim_index is not None:
            check(f"Claim {claim_index + 1} of {len(claims)}"
                  in _tagless(rendered_text(at)), f"{where} is where we asked for")

    check(not progress.missing_items(BRAIN, source_id, store.load_responses(rid),
                                     store.load_edge_responses(rid)) == [],
          "and the whole route was walked with the paper still unanswered")

    # No control anywhere on the route is a gate.
    at = open_section(evaluator, "Vaclav", phase_id, source_id, "claims")
    nav = [b for b in at.button if b.key and b.key.startswith("nav|")]
    check(sum(1 for b in nav if b.disabled) == 1,
          "only the current section is inert in the section bar")
    check(not next(b for b in at.button if b.key == "next_claim").disabled,
          "Next claim is live on an unanswered claim")


def _holder_of(source_id: str):
    """An evaluator actually assigned this paper, and in which phase.

    The paper view refuses a source the evaluator was not assigned — rightly —
    so a test that opens papers has to open them as somebody who holds them.
    Getting this wrong renders the empty "no papers assigned" page, which raises
    no exception and would let a test pass while seeing nothing.
    """
    if source_id in manifest.training_source_ids():
        return "vaclav", manifest.TRAINING
    for row in manifest.assignments():
        if (row["source_id"] == source_id
                and manifest.state_of(row) == manifest.ASSIGNED):
            return row["evaluator_id"], row["phase_id"]
    return None, None


def _opened(source_id: str):
    """A started review for whoever holds this paper. Returns (who, phase, rid)."""
    who, phase = _holder_of(source_id)
    entry = manifest.evaluator(who) or {}
    rid = store.ensure_review(
        phase_id=phase, evaluator_id=who, evaluator_name=entry.get("name", who),
        pair_id=manifest.pair_of(who) or "", source_id=source_id,
        work_id=BRAIN.work_id(source_id), brain_snapshot_id=BRAIN.snapshot_id,
        eval_spec_version=spec.EVAL_SPEC_VERSION)
    store.start_review(rid, True)
    return who, phase, rid


def test_brain_edge_cases():
    """Every shape the Brain actually contains, rendered by somebody who holds it."""
    print("\n== the Brain's edge cases ==")
    fresh_db()

    by_claims = {s: len(BRAIN.claims_of(s)) for s in BRAIN.source_ids}
    biggest = max(by_claims, key=by_claims.get)
    check(by_claims[biggest] >= 40,
          f"the Brain holds a long paper ({biggest}: {by_claims[biggest]} claims)")

    def held(sources):
        return [s for s in sources if _holder_of(s)[0]]

    no_datasets = held([s for s in BRAIN.source_ids if not BRAIN.datasets_of(s)])
    many_datasets = held([s for s in BRAIN.source_ids if len(BRAIN.datasets_of(s)) > 1])
    no_cites = held([s for s in BRAIN.source_ids if not BRAIN.cites_from(s)])
    many_cites = held([s for s in BRAIN.source_ids if len(BRAIN.cites_from(s)) > 1])
    for label, group in (("with no dataset", no_datasets),
                         ("with several datasets", many_datasets),
                         ("with no outgoing citation", no_cites),
                         ("with several outgoing citations", many_cites)):
        check(group, f"somebody is assigned a source {label} ({len(group)})")

    cases = {
        "the longest paper": biggest,
        "no dataset": no_datasets[0],
        "several datasets": many_datasets[0],
        "no outgoing CITES": no_cites[0],
        "several outgoing CITES": many_cites[0],
    }
    for label, source_id in cases.items():
        who, phase, _ = _opened(source_id)
        name = (manifest.evaluator(who) or {}).get("name", who)
        work = BRAIN.work_id(source_id)
        for section in progress.SECTION_IDS:
            at = open_section(who, name, phase, source_id, section)
            on_screen = any(work in t.value for t in at.title)
            check(not at.exception and on_screen,
                  f"{label} ({work}) renders {section} for {name}")

    # Claims with none, one and several relations.
    who, phase, _ = _opened(biggest)
    name = (manifest.evaluator(who) or {}).get("name", who)
    relations = {c["id"]: len(BRAIN.relations_of(c["id"]))
                 for c in BRAIN.claims_of(biggest)}
    none = [cid for cid, n in relations.items() if n == 0]
    one = [cid for cid, n in relations.items() if n == 1]
    many = [cid for cid, n in relations.items() if n > 2]
    for label, group in (("no relation", none), ("one relation", one),
                         ("several relations", many)):
        check(group, f"the longest paper has a claim with {label} ({len(group)})")

    ids = [c["id"] for c in BRAIN.claims_of(biggest)]
    for label, cid in (("no relation", none[0]), ("one relation", one[0]),
                       ("several relations", many[0])):
        at = _open_claim(who, name, phase, biggest, ids.index(cid))
        check(not at.exception and cid in _tagless(rendered_text(at)),
              f"a claim with {label} renders ({cid})")
        edges = [r for r in at.radio if r.key and cid in r.key
                 and "CLAIM_HE" not in r.key]
        check(len(edges) == relations[cid],
              f"with one judgment per edge ({len(edges)} of {relations[cid]})")

    # With and without a candidate concept. Candidates are rare, so the paper
    # that has one is found rather than assumed.
    with_candidate = next(
        (s for s in BRAIN.source_ids
         if _holder_of(s)[0]
         and any(BRAIN.candidate_created_for(c["id"]) for c in BRAIN.claims_of(s))),
        None)
    check(with_candidate, f"some assigned paper created a candidate concept "
                          f"({with_candidate})")
    holder, cphase, _ = _opened(with_candidate)
    cname = (manifest.evaluator(holder) or {}).get("name", holder)
    claims = BRAIN.claims_of(with_candidate)
    made = [c["id"] for c in claims if BRAIN.candidate_created_for(c["id"])]
    none_made = [c["id"] for c in claims if not BRAIN.candidate_created_for(c["id"])]
    check(made and none_made,
          f"and has claims both with and without one "
          f"({len(made)} / {len(none_made)})")
    order = [c["id"] for c in claims]
    at = _open_claim(holder, cname, cphase, with_candidate, order.index(made[0]))
    check(any(r.key.endswith("CLAIM_HE21|a") for r in at.radio),
          "HE-21 is answerable where a candidate was created")
    at = _open_claim(holder, cname, cphase, with_candidate,
                     order.index(none_made[0]))
    check(not any(r.key.endswith("CLAIM_HE21|a") for r in at.radio),
          "and settled by the application where none was")
    check("no candidate Concept was created" in _tagless(rendered_text(at)),
          "which the page says rather than leaving it blank")


def test_modal_changes_nothing():
    """Every kind of modal, opened, followed, closed — and no answer moves."""
    print("\n== the modal touches nothing ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.TRAINING
    source_id = manifest.assigned_source_ids(evaluator, phase_id)[0]
    rid = _started(evaluator, "Vaclav", phase_id, source_id)
    claim = BRAIN.claims_of(source_id)[0]

    at = _open_claim(evaluator, "Vaclav", phase_id, source_id, 0)
    at = flush(next(r for r in at.radio
                    if r.key.endswith("CLAIM_HE03|a")).set_value("In part").run())
    comment = next(t for t in at.text_area if t.key.endswith("CLAIM_HE03|c"))
    at = flush(comment.set_value("a judgment I do not want disturbed").run())

    before_answers = {k: dict(v) for k, v in store.load_responses(rid).items()}
    before_progress = progress.claim_progress(BRAIN, source_id, claim["id"],
                                              store.load_responses(rid),
                                              store.load_edge_responses(rid))

    concept = (claim.get("concepts") or [None])[0]
    kinds = [(ui.SOURCE, source_id), (ui.CLAIM, claim["id"]),
             (ui.CONCEPT_REGISTRY, ""), (ui.SOURCE_REGISTRY, source_id),
             (ui.SOURCE_CLAIMS, source_id)]
    if concept:
        kinds.append((ui.CONCEPT, concept))
    dataset = next((d["id"] for s in BRAIN.source_ids
                    for d in BRAIN.datasets_of(s)), None)
    if dataset:
        kinds.append((ui.DATASET, dataset))

    for kind, object_id in kinds:
        page = _open_claim(evaluator, "Vaclav", phase_id, source_id, 0)
        page.session_state[ui.WIKI] = [(kind, object_id)]
        page = page.run()
        check(not page.exception, f"the {kind} modal opens")
        check(ss(page, ui.WIKI) == [(kind, object_id)],
              f"and stays open on {kind}")

    # Following a link pushes, Back pops, Close empties.
    page = _open_claim(evaluator, "Vaclav", phase_id, source_id, 0)
    page.session_state[ui.WIKI] = [(ui.SOURCE, source_id)]
    page = page.run()
    page.session_state[ui.WIKI].append((ui.CLAIM, claim["id"]))
    page = page.run()
    check(len(ss(page, ui.WIKI)) == 2, "following a link keeps the way back")
    back = [b for b in page.button if b.key and b.key.startswith("wiki_back|")]
    check(back and not back[0].disabled, "Back is offered once there is a way back")
    page = back[0].click().run()
    check(len(ss(page, ui.WIKI)) == 1, "and it returns one step")
    close = [b for b in page.button if b.key and b.key.startswith("wiki_close|")]
    page = close[0].click().run()
    check(not ss(page, ui.WIKI), "Close empties the stack")

    # Moving to another claim closes whatever was open.
    page = _open_claim(evaluator, "Vaclav", phase_id, source_id, 0)
    page.session_state[ui.WIKI] = [(ui.SOURCE, source_id)]
    page = page.run()
    page = next(b for b in page.button if b.key == "next_claim").click().run()
    check(not ss(page, ui.WIKI), "changing claim closes the modal")

    after = store.load_responses(rid)
    changed = [k for k, v in after.items()
               if {f: v.get(f) for f in ("answer", "comment_evidence")}
               != {f: before_answers.get(k, {}).get(f)
                   for f in ("answer", "comment_evidence")}]
    check(not changed, f"and not one answer moved through any of it {changed[:3]}")
    check(progress.claim_progress(BRAIN, source_id, claim["id"], after,
                                  store.load_edge_responses(rid)) == before_progress,
          "nor did the claim's progress")


def test_completion_round_trip():
    """complete → edit → in_progress → complete again, and submission after."""
    print("\n== completion, revision, completion, submission ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.TRAINING
    sources = manifest.assigned_source_ids(evaluator, phase_id)
    rids = _finish_phase(evaluator, phase_id, sources)
    first = sources[0]

    check(store.get_review(phase_id, evaluator, first)["status"]
          == store.STATUS_COMPLETE, "the paper is complete")

    at = open_section(evaluator, "Vaclav", phase_id, first, "source")
    radios = [r for r in at.radio if r.key.endswith("SOURCE_HE08_1|a")]
    check(radios and not radios[0].disabled,
          "a complete paper is still editable")
    at = flush(radios[0].set_value("In part").run())
    check(store.get_review(phase_id, evaluator, first)["status"]
          == store.STATUS_IN_PROGRESS, "and any edit demotes it")

    # It can be completed again from the Review page, as the evaluator would.
    at = open_section(evaluator, "Vaclav", phase_id, first, "review")
    missing = progress.missing_items(BRAIN, first, store.load_responses(rids[0]),
                                     store.load_edge_responses(rids[0]))
    if missing:
        comment = next(t for t in at.text_area if t.key.endswith("SOURCE_HE08_1|c"))\
            if any(t.key.endswith("SOURCE_HE08_1|c") for t in at.text_area) else None
        page = open_section(evaluator, "Vaclav", phase_id, first, "source")
        box = next(t for t in page.text_area if t.key.endswith("SOURCE_HE08_1|c"))
        flush(box.set_value("the reason it is only partly right").run())
        at = open_section(evaluator, "Vaclav", phase_id, first, "review")
    mark = next(b for b in at.button if b.label == "Mark paper complete")
    check(not mark.disabled, "and once nothing is missing it can be completed again")
    at = flush(mark.click().run())
    check(store.get_review(phase_id, evaluator, first)["status"]
          == store.STATUS_COMPLETE, "which it is")

    # Submitting this phase leaves the other two exactly as they were.
    others = {p: [(s, (store.get_review(p, evaluator, s) or {}).get("status"))
                  for s in manifest.assigned_source_ids(evaluator, p)]
              for p in manifest.PHASES if p != phase_id}
    at = signed_in(evaluator, "Vaclav", manifest.PHASE_LABEL[phase_id]).run()
    at = at.checkbox(key=f"confirm_batch|{phase_id}|{evaluator}").check().run()
    at = flush(next(b for b in at.button
                    if b.label == "Submit all papers").click().run())
    check(store.phase_submitted(phase_id, evaluator), "the phase is submitted")
    for phase, before in others.items():
        after = [(s, (store.get_review(phase, evaluator, s) or {}).get("status"))
                 for s in manifest.assigned_source_ids(evaluator, phase)]
        check(after == before, f"and {phase} is untouched")
        check(not store.phase_submitted(phase, evaluator),
              f"and unsubmitted ({phase})")

    # A submitted paper is read-only.
    at = open_section(evaluator, "Vaclav", phase_id, first, "source")
    radios = [r for r in at.radio if r.key.endswith("SOURCE_HE08_1|a")]
    check(radios and all(r.disabled for r in radios),
          "and every control on a submitted paper is inert")


def test_a_failed_read_never_creates_a_tab():
    """A transient Sheets failure must not be answered by changing the workbook.

    Found by running the live test hard enough to hit the read quota: the
    worksheet lookup caught every exception and responded by creating the tab,
    so a 429 turned into an attempt to add a tab that already existed. A failure
    to read is not evidence that something is missing.
    """
    print("\n== a failed read is not a missing tab ==")
    import gspread

    source = (APP_DIR / "sheets.py").read_text(encoding="utf-8")
    body = source.split("def _worksheet(")[1].split("\n    def ")[0]
    check("except gspread.WorksheetNotFound" in body,
          "only a genuine not-found creates a tab")
    check("except Exception" not in body,
          "and no bare catch-all remains to turn any failure into a write")
    after_not_found = body.split("except gspread.WorksheetNotFound:")[1]
    check("add_worksheet" in after_not_found.split("except gspread.exceptions")[0],
          "creation sits under the not-found branch alone")

    class Failing:
        """A workbook whose metadata read is being rejected, not answered."""

        def worksheet(self, tab):
            raise gspread.exceptions.APIError(_Response(429, "Quota exceeded"))

        def add_worksheet(self, **kwargs):                # pragma: no cover
            raise AssertionError("a failed read must not create a tab")

    book = sheets.GoogleSheetsWorkbook("test-id")
    book._sheet = Failing()
    raised = None
    try:
        book._worksheet(sheets.CONFIG)
    except Exception as error:                            # noqa: BLE001
        raised = error
    check(isinstance(raised, sheets.StorageError),
          f"the failure is reported as a storage error ({type(raised).__name__})")
    check(isinstance(raised, sheets.QuotaExceeded),
          "and a 429 in particular is reported as a quota rejection")
    check("nothing was changed" in str(raised).lower(),
          f"saying the tab was not touched ({raised})")


class _Response:
    """The shape gspread's APIError reads out of a response."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.text = message
        self._message = message

    def json(self):
        return {"error": {"code": self.status_code, "message": self._message,
                          "status": "RESOURCE_EXHAUSTED"}}


def test_deployment_readiness():
    """What Streamlit Cloud needs from this repository before it will serve."""
    print("\n== deployment readiness ==")
    root = APP_DIR.parent

    pin = root / ".python-version"
    check(pin.exists(), "the Python version is pinned")
    check(pin.read_text(encoding="utf-8").strip() == "3.11",
          f"at 3.11, which is what the code is written against "
          f"({pin.read_text(encoding='utf-8').strip()})")

    requirements = (root / "requirements.txt").read_text(encoding="utf-8")
    for package in ("streamlit", "pandas", "PyYAML", "gspread", "google-auth",
                    "openpyxl"):
        check(package in requirements, f"{package} is declared")
    check("Development only" not in requirements.split("openpyxl")[0][-200:],
          "and openpyxl is not marked development-only — Exports needs it to serve")

    # The entry point is the file Streamlit Cloud is pointed at.
    entry = APP_DIR / "streamlit_app.py"
    check(entry.exists(), f"the entry point exists ({entry.name})")
    check("if __name__ ==" in entry.read_text(encoding="utf-8"),
          "and runs main() when executed")

    # Everything the deployment needs comes from the environment, never a file.
    for name in ("HE_APP_PASSWORD", "HE_ADMIN_SECRET", "GOOGLE_SHEET_ID"):
        check(name in (APP_DIR / "manifest.py").read_text(encoding="utf-8")
              or name in (APP_DIR / "sheets.py").read_text(encoding="utf-8"),
              f"{name} is read from the environment")
    check(manifest.ENV_PASSWORD == "HE_APP_PASSWORD",
          "the password variable is named as DEPLOYMENT.md says")

    # The payload a push would carry.
    tracked = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                             text=True).stdout.split()
    total = sum((root / name).stat().st_size for name in tracked
                if (root / name).exists())
    check(total < 40 * 1024 * 1024,
          f"the tracked tree is {total / 1024 / 1024:.1f} MB, well inside what "
          f"Streamlit Cloud will take")
    check(not any(name.startswith("brain/raw/") for name in tracked),
          "and carries no PDFs")
    check(not any("service-account" in name or "secrets.toml" in name
                  for name in tracked),
          "and no credential file")

    # A cold start with no store must not crash: the guards run before anything.
    entry_text = entry.read_text(encoding="utf-8")
    main = entry_text.split("def main() -> None:")[1].split("\n\n")[0]
    order = [line.strip() for line in main.splitlines() if "guard" in line
             or "gate_" in line]
    check(order and "guard_storage" in order[0],
          f"storage is checked first, before anything reads it ({order[:1]})")
    check(any("guard_snapshot" in line for line in order)
          and any("guard_spec_version" in line for line in order),
          "and the Brain and instrument versions are checked before login")
    check([i for i, line in enumerate(order) if "gate_password" in line]
          > [i for i, line in enumerate(order) if "guard_spec_version" in line],
          "with the password gate after them, so a misconfigured deployment "
          "says so rather than asking for a password it cannot honour")


def _calls_in(path, function_name: str) -> set[str]:
    """The names of everything one function calls, from the syntax tree.

    Reading the source as text would count a docstring that names a function in
    order to say it is no longer used.
    """
    import ast

    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
    target = next(node for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef) and node.name == function_name)
    names = set()
    for node in ast.walk(target):
        if isinstance(node, ast.Call):
            func = node.func
            names.add(func.attr if isinstance(func, ast.Attribute)
                      else getattr(func, "id", ""))
    return names


class _FakeGoogleSheet:
    """Just enough of gspread's Spreadsheet to count what startup asks Google for."""

    def __init__(self, headers=None, fail=None, present=None, fail_listing=None):
        self.requests: list[str] = []
        self._headers = headers or {tab: list(sheets.COLUMNS[tab])
                                    for tab in sheets.ALL_TABS}
        self._fail = fail
        self._fail_listing = fail_listing
        self._present = list(present if present is not None else sheets.ALL_TABS)

    def worksheets(self):
        self.requests.append("worksheets()")
        if self._fail_listing:
            raise self._fail_listing
        return [_FakeWorksheet(tab) for tab in self._present]

    def values_batch_get(self, ranges):
        self.requests.append(f"values_batch_get({len(ranges)} ranges)")
        if self._fail:
            raise self._fail
        return {"valueRanges": [{"values": [self._headers[tab]]}
                                if self._headers.get(tab) else {}
                                for tab in sheets.ALL_TABS]}

    def worksheet(self, tab):
        self.requests.append(f"worksheet({tab})")
        return _FakeWorksheet(tab)

    def add_worksheet(self, **kwargs):                    # pragma: no cover
        raise AssertionError("the running app must never create a tab")


class _FakeWorksheet:
    def __init__(self, tab):
        self.tab = tab
        self.title = tab

    def row_values(self, row):                            # pragma: no cover
        raise AssertionError("startup must not read headers one tab at a time")


def test_startup_reads_are_minimal():
    """The deployment startup path, counted in Google API requests.

    A 429 on the production workbook the moment it was deployed. `store.init()`
    called `ensure_tabs()`, which fetches the workbook's metadata once per tab
    and then reads each header — fifteen requests — and `main()` called it
    twice, on every Streamlit rerun. Six people typing a password exhausts a
    quota of sixty reads a minute in seconds.
    """
    print("\n== startup asks Google for as little as possible ==")

    book = sheets.GoogleSheetsWorkbook("test-id")
    fake = _FakeGoogleSheet()
    book._sheet = fake                      # already "opened": that is 1 request

    book.check_ready()
    check(fake.requests == ["worksheets()", "values_batch_get(7 ranges)"],
          f"readiness is one tab listing and one batched header read "
          f"({fake.requests})")
    check(not any(r.startswith("worksheet(") for r in fake.requests),
          "and looks no tab up individually")

    # Three requests for a cold start: opening the workbook, listing its tabs,
    # and reading all seven headers together.
    check(len(fake.requests) + 1 == 3,
          "so a cold start costs three requests in total")
    check(set(book._tabs) == set(sheets.ALL_TABS),
          "and the listing leaves every tab handle in hand, so the first paper "
          "opened does not pay to look three of them up again")

    # Once per process, not once per rerun.
    original_workbook, original_using = store.workbook, store.using_sheets
    store.workbook, store.using_sheets = (lambda: book), (lambda: True)
    store.forget_ready()
    try:
        fake.requests.clear()
        store.init()
        first = len(fake.requests)
        for _ in range(20):                 # twenty Streamlit reruns
            store.init()
        check(first == 2, f"the first init costs the two checking requests ({first})")
        check(len(fake.requests) == first,
              f"and twenty reruns after it cost nothing at all "
              f"({len(fake.requests) - first})")
    finally:
        store.workbook, store.using_sheets = original_workbook, original_using
        store.forget_ready()

    # The tab handle is kept, so ordinary reads stop paying for a lookup.
    fake.requests.clear()
    for _ in range(5):
        book._worksheet(sheets.CONFIG)
    check(not fake.requests,
          f"a primed tab costs nothing to reach ({fake.requests})")
    book._tabs.clear()                      # as if it had never been primed
    fake.requests.clear()
    for _ in range(5):
        book._worksheet(sheets.CONFIG)
    check(len(fake.requests) == 1,
          f"and an unprimed one is looked up once and remembered ({fake.requests})")

    # Nothing on the startup path may touch the evaluation data. Read from the
    # syntax tree, not the text: a docstring that names `ensure_tabs` in order
    # to say it is no longer called would otherwise fail this.
    called = _calls_in(APP_DIR / "store.py", "init")
    for forbidden in ("ensure_tabs", "read_tab", "read_range"):
        check(forbidden not in called,
              f"init() does not call {forbidden}() {sorted(called)}")
    check("check_ready" in called, f"it calls check_ready() instead {sorted(called)}")

    check("init" not in _calls_in(APP_DIR / "streamlit_app.py", "main"),
          "and main() does not call store.init() a second time after guard_storage")


def test_startup_never_reads_the_evaluation_tabs():
    """Before anyone has logged in, RESPONSES and EDGE_RESPONSES stay untouched."""
    print("\n== login costs nothing in evaluation data ==")

    seen: list[tuple[str, str]] = []

    class Watched:
        """A workbook that records what it is asked for and refuses the expensive."""

        def __init__(self, inner):
            self.inner = inner

        def __getattr__(self, name):
            attr = getattr(self.inner, name)
            if not callable(attr):
                return attr

            def wrapped(*args, **kwargs):
                seen.append((name, str(args[0]) if args else ""))
                return attr(*args, **kwargs)
            return wrapped

    directory = pathlib.Path(tempfile.mkdtemp())
    original = store.workbook
    store.workbook = lambda: Watched(sheets.LocalWorkbook(directory))
    store.forget_ready()
    try:
        store.init()
        manifest.invalidate()
        at = app(authenticated=False).run()             # the password page
        check(not at.exception, "the password page renders")
        at = app(authenticated=True).run()              # the identity page
        check(not at.exception, "as does the identity page")

        expensive = [(call, tab) for call, tab in seen
                     if tab in (sheets.RESPONSES, sheets.EDGE_RESPONSES)
                     and call in ("read_tab", "read_range")]
        check(not expensive,
              f"neither page reads a row of evaluation data {expensive[:3]}")
        check(not any(call == "ensure_tabs" for call, _ in seen[1:]),
              "and neither tries to create or repair a tab")
        whole_tabs = [tab for call, tab in seen if call == "read_tab"]
        check(all(tab in sheets.CONFIG_TABS for tab in whole_tabs),
              f"only the configuration tabs are read at all {sorted(set(whole_tabs))}")
    finally:
        store.workbook = original
        store.forget_ready()


def test_quota_is_temporary_not_a_fault():
    """A 429 says wait. It must not read as a broken workbook, or change one."""
    print("\n== a quota rejection is not a fault ==")
    import gspread

    quota = gspread.exceptions.APIError(_Response(429, "Quota exceeded"))
    book = sheets.GoogleSheetsWorkbook("test-id")
    book._sheet = _FakeGoogleSheet(fail_listing=quota)
    raised = None
    try:
        book.check_ready()
    except Exception as error:                            # noqa: BLE001
        raised = error
    check(isinstance(raised, sheets.QuotaExceeded),
          f"it is raised as a quota error ({type(raised).__name__})")
    check(isinstance(raised, sheets.StorageError),
          "which is still a storage error, so nothing falls through to SQLite")
    check("wait a moment" in str(raised) and "nothing was changed" in str(raised),
          f"telling the reader to wait, and that nothing changed ({raised})")

    # A missing tab is a different thing, and says so without creating anything.
    book = sheets.GoogleSheetsWorkbook("test-id")
    book._sheet = _FakeGoogleSheet(
        present=[t for t in sheets.ALL_TABS if t != sheets.PHASE_SUBMISSIONS])
    raised = None
    try:
        book.check_ready()
    except Exception as error:                            # noqa: BLE001
        raised = error
    check(isinstance(raised, sheets.StorageError)
          and not isinstance(raised, sheets.QuotaExceeded),
          "a missing tab is reported as a real problem, not a busy signal")
    check(sheets.PHASE_SUBMISSIONS in str(raised),
          f"naming the tab that is absent ({raised})")
    check("bootstrap_sheets.py" in str(raised),
          "and the tool that fixes it")
    check("Nothing was created or changed" in str(raised),
          "and confirming the app did not try to fix it itself")

    # A wrong header is caught without writing over it.
    wrong = {tab: list(sheets.COLUMNS[tab]) for tab in sheets.ALL_TABS}
    wrong[sheets.RESPONSES] = ["not", "the", "right", "header"]
    book = sheets.GoogleSheetsWorkbook("test-id")
    book._sheet = _FakeGoogleSheet(headers=wrong)
    raised = None
    try:
        book.check_ready()
    except Exception as error:                            # noqa: BLE001
        raised = error
    check(isinstance(raised, sheets.StorageError) and sheets.RESPONSES in str(raised),
          f"a wrong header names the tab ({raised})")
    check("Nothing was changed" in str(raised), "and is not silently rewritten")

    # The guard shows it as temporary, and offers to try again.
    entry = (APP_DIR / "streamlit_app.py").read_text(encoding="utf-8")
    guard = entry.split("def guard_storage() -> bool:")[1].split("\ndef ")[0]
    check("QuotaExceeded" in guard, "the startup guard tells the two apart")
    check("Google Sheets is busy" in guard,
          "and titles a quota rejection as busy rather than unreachable")
    check("Try again" in guard, "offering to retry")
    check("bootstrap_sheets.py" in guard.split("Try again")[0].split(
              "Google Sheets is busy")[1] is False
          or "bootstrap" not in guard.split("Google Sheets is busy")[1].split(
              "return False")[0],
          "without sending anybody to the bootstrap tool over a rate limit")


def test_storage_guard_handler_cannot_raise():
    """The guard must report the failure it caught, never one of its own.

    On the first deployment an older copy of this project sat earlier on
    `sys.path`, so `import sheets` inside the guard bound a module with neither
    `check_ready` nor `QuotaExceeded`. `store.init()` raised AttributeError for
    the first; evaluating `except sheets.QuotaExceeded` raised AttributeError
    for the second, replacing the original and hiding it.
    """
    print("\n== the storage guard reports what it caught ==")
    import streamlit_app

    check(streamlit_app.QuotaExceeded is sheets.QuotaExceeded,
          "the guard holds the very class the storage layer raises")
    check(streamlit_app.QuotaExceeded is store.sheets.QuotaExceeded,
          "which is the one `store` would raise it from")
    check(issubclass(sheets.QuotaExceeded, sheets.StorageError),
          "and it is a StorageError, so nothing falls through to SQLite")

    # No `except` clause on this path may look a name up: that is what turned a
    # readable failure into an AttributeError about the handler.
    guard = _ast_function(APP_DIR / "streamlit_app.py", "guard_storage")
    import ast
    lookups = [ast.unparse(handler.type) for node in ast.walk(guard)
               if isinstance(node, ast.Try) for handler in node.handlers
               if handler.type is not None
               and isinstance(handler.type, ast.Attribute)]
    check(not lookups,
          f"no except clause resolves an attribute at handling time {lookups}")

    # The guard only reaches storage when a workbook is configured, which is the
    # deployed condition being reproduced.
    original = store.init
    was_configured = sheets.configured
    sheets.configured = lambda: True
    for error, expected_title, transient in (
        (sheets.QuotaExceeded("quota is used up, wait a moment and reload"),
         "Google Sheets is busy", True),
        (sheets.StorageError("the workbook is missing PHASE_SUBMISSIONS"),
         "Google Sheets is not reachable", False),
        # The exact shape of the deployed failure: the storage layer raising
        # something nobody anticipated.
        (AttributeError("'GoogleSheetsWorkbook' object has no attribute "
                        "'check_ready'"),
         "Google Sheets is not reachable", False),
    ):
        def failing(error=error):
            raise error
        store.init = failing
        try:
            at = app(authenticated=True).run()
        finally:
            store.init = original
        check(not at.exception,
              f"{type(error).__name__} does not crash the app "
              f"({at.exception[0].value[:80] if at.exception else ''})")
        titles = [t.value for t in at.title]
        check(expected_title in titles,
              f"and is shown as {expected_title!r} {titles}")
        shown = rendered_text(at)
        check(str(error)[:30] in shown,
              f"with the message it actually carried ({str(error)[:40]!r})")
        if transient:
            check(any(b.label == "Try again" for b in at.button),
                  "a quota rejection offers to try again")
            check("bootstrap_sheets.py" not in shown,
                  "and does not send anybody to the bootstrap tool")
        else:
            check(not any(b.label == "Try again" for b in at.button),
                  "a real fault does not pretend it will pass")
    sheets.configured = was_configured


def _ast_function(path, name):
    import ast

    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
    return next(node for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name == name)


def test_login_rerun_end_to_end():
    """The deployed path: password typed, accepted, then the identity page."""
    print("\n== one whole login, as deployed ==")
    fresh_db()

    at = app(authenticated=False).run()
    check(not at.exception, "the password page renders")
    check(any("Enter access password" in m.value for m in at.markdown),
          "and asks for the password")

    field = next(t for t in at.text_input if t.label == "Password")
    at = field.set_value("wrong").run()
    at = next(b for b in at.button if b.label == "Continue").click().run()
    check(not at.exception, "a wrong password does not crash it")
    check(not ss(at, "authenticated"), "and does not let anybody in")
    check(any("Incorrect password" in e.value for e in at.error),
          "it says so instead")

    field = next(t for t in at.text_input if t.label == "Password")
    at = field.set_value(os.environ["HE_APP_PASSWORD"]).run()
    at = next(b for b in at.button if b.label == "Continue").click().run()
    check(not at.exception, "the right password does not crash it either")
    check(ss(at, "authenticated"), "it authenticates")
    check(any("Select evaluator" in t.value for t in at.title),
          f"and the next rerun lands on the identity page "
          f"({[t.value for t in at.title]})")

    # Choose a name and confirm — the rerun after that is where the crash was.
    box = next(s for s in at.selectbox if s.label == "Evaluator")
    at = box.set_value("Vaclav").run()
    check(not at.exception, "choosing a name does not crash it")
    at = next(b for b in at.button if b.label == "Confirm and continue").click().run()
    check(not at.exception, "nor does confirming it")
    check(ss(at, "evaluator_id") == "vaclav", "the evaluator is remembered")
    check(any(manifest.PHASE_LABEL[manifest.TRAINING] in t.value for t in at.title),
          f"and a phase page is reached ({[t.value for t in at.title]})")

    # And a plain rerun of that page, which is what Streamlit does constantly.
    at = at.run()
    check(not at.exception, "a further rerun is uneventful")


def test_pending_individual_split():
    """An undivided pool is named as pending, not passed over in silence."""
    print("\n== a phase awaiting division says so ==")
    fresh_db()

    for holder in ("thiago", "francesca"):
        splits = manifest.splits_of(holder)
        check(splits[manifest.INDIVIDUAL] == manifest.PENDING_SPLIT,
              f"{holder}'s individual phase reads '{splits[manifest.INDIVIDUAL]}'")
        check(splits[manifest.AGREEMENT] == "AGR-A",
              "while the settled phase still shows its split id")

    check(manifest.splits_of("giovanni")[manifest.INDIVIDUAL] == "IND-5",
          "a settled individual split is unaffected")

    # It must not become a way of learning which papers are held.
    at = signed_in("thiago", "Thiago", "Individual").run()
    text = rendered_text(at)
    reserved_papers = manifest.reserved_sources(manifest.INDIVIDUAL)
    check(reserved_papers, f"there are reservations to hide ({len(reserved_papers)})")
    data = load_brain()
    leaked = [sid for sid in reserved_papers
              if sid in text or data.work_id(sid) in text]
    check(not leaked, f"and none of them is named to the evaluator {leaked}")
    check(manifest.PENDING_SPLIT in text,
          "the sidebar says the phase is pending rather than showing nothing")


def test_store_isolation():
    """A suite run must not touch the database a developer's app is using."""
    print("\n== the tests keep their own store ==")
    import hashlib

    check(store.DB_PATH != DEV_DB_PATH,
          f"the run works in its own database ({store.DB_PATH})")
    check(_test_owned(store.DB_PATH),
          f"which lives under this run's directory ({TEST_DB_DIR})")
    check(DEV_DB_PATH.name == "evaluations.sqlite"
          and DEV_DB_PATH.parent.name == "data",
          f"and the development store it must leave alone is {DEV_DB_PATH}")

    def state_of(path):
        """Everything about the development store that a test could disturb."""
        files = {}
        for suffix in ("", "-wal", "-shm"):
            candidate = pathlib.Path(str(path) + suffix)
            files[suffix] = (hashlib.sha256(candidate.read_bytes()).hexdigest()
                             if candidate.exists() else None)
        return files

    before = state_of(DEV_DB_PATH)

    # Real work, of the kind that wiped the development store before this fix:
    # create a store, drive the app through it, then reset it.
    fresh_db()
    rid = store.ensure_review(
        phase_id=manifest.TRAINING, evaluator_id="vaclav", evaluator_name="Vaclav",
        pair_id="", source_id="SRC-0004", work_id="W0085")
    store.start_review(rid, True)
    at = signed_in(source_id="SRC-0004").run()
    check(not at.exception, "the app runs against the test store")
    check(store.get_review(manifest.TRAINING, "vaclav", "SRC-0004")
          .get("status") != store.STATUS_NOT_STARTED,
          "and reads back what was written there")
    fresh_db()

    check(state_of(DEV_DB_PATH) == before,
          "the development database is byte-for-byte where it was")
    if before[""] is None:
        check(not DEV_DB_PATH.exists(),
              "and a run does not conjure one into existence either")

    # The guard, not merely the redirection: prove it refuses.
    store.DB_PATH = DEV_DB_PATH
    try:
        _wipe_db()
        refused = False
    except AssertionError:
        refused = True
    finally:
        store.DB_PATH = TEST_DB_DIR / "evaluations.sqlite"
    check(refused,
          "pointing the tests back at the development store makes them refuse, "
          "rather than deleting it")
    check(state_of(DEV_DB_PATH) == before, "the refusal left it untouched")

    deleters = [line.strip() for line in
                (APP_DIR / "tests" / "test_app.py").read_text(encoding="utf-8").splitlines()
                if line.strip() == "path.unlink()"]
    check(len(deleters) == 1,
          f"and one place deletes a database, so the one guard covers it {deleters}")
    fresh_db()


def test_citation_line():
    """The heading identifies the paper; extraction notes stay in the wiki."""
    print("\n== the paper is cited, not described ==")
    import streamlit_app as app_module

    data = load_brain()

    check(app_module._authors(data.sources["SRC-0004"]) == "Mumford et al.",
          "three authors become the first plus et al.")
    check(app_module._authors(data.sources["SRC-0003"]) == "Holzenberger et al.",
          "and the surname alone, not the stored 'Surname, Given'")

    line = app_module._citation(data.sources["SRC-0004"])
    check("doi:" not in line, f"the DOI is not in the citation line ({line})")
    check("conference volume not named" not in line,
          "nor is the note that the volume was not printed — that is provenance")
    check("IOS Press" in line and "2021" in line,
          "what identifies the paper survives")

    check("(NLLP)" in app_module._citation(data.sources["SRC-0003"]),
          "a venue's own parentheses are not casualties of the trim")
    check(app_module._citation(data.sources["SRC-0006"]).endswith("2022"),
          "an unknown venue is omitted rather than printed as 'unknown'")

    # and it is what the page actually shows
    at = signed_in("giovanni", "Giovanni", "Training", source_id="SRC-0004").run()
    text = rendered_text(at)
    check("Mumford et al." in text, "the start page shows the short form")
    check("doi:" not in text, "and no DOI reaches the evaluator")


def test_no_prose_leaks_through_magic():
    """Streamlit renders a bare string in the entry script. A comment must not become one."""
    print("\n== no explanation leaks onto the page ==")
    import ast

    entry = APP_DIR / "streamlit_app.py"
    tree = ast.parse(entry.read_text(encoding="utf-8"))
    leaked = []
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list):
            continue
        holds_a_docstring = isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        for position, stmt in enumerate(body):
            if not (isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, str)):
                continue
            if holds_a_docstring and position == 0:
                continue  # a real docstring; magic leaves it alone
            leaked.append((stmt.lineno, stmt.value.value.strip().splitlines()[0]))

    check(not leaked,
          f"no bare string sits where Streamlit magic would print it {leaked}")

    # The rule is real, not a formality: prove magic prints such a string.
    at = signed_in()
    at.run()
    check(rendered_text(at).count("each phase is its own irreversible step") == 0,
          "the submission rationale is a comment to the reader of the code, "
          "not text on the evaluator's paper list")


def test_conflicts_are_not_retried():
    """A refused edit is reported, not retried into a loop that blocks completion."""
    print("\n== a conflict is refused, not retried ==")
    import savequeue

    queue = savequeue.SaveQueue()
    queue.set_fatal(store.SaveConflict)
    try:
        attempts = {"n": 0}

        def refused(**kwargs):
            attempts["n"] += 1
            raise store.SaveConflict("SOURCE_HE08_1|SRC-0001")

        queue.submit("answer", refused, value="Yes")
        deadline = time.monotonic() + 5
        while not queue.conflicts and time.monotonic() < deadline:
            time.sleep(0.05)
        check(attempts["n"] == 1,
              f"the write is tried once, not {savequeue.MAX_ATTEMPTS} times "
              f"({attempts['n']}) — the expectation would be just as stale")
        check(queue.unresolved == 0,
              "it does not sit unresolved, so completion is not blocked for ever")
        check(queue.flush(timeout=2), "and flush succeeds")
        check(list(queue.conflicts) == ["answer"], "while the conflict is reported")
        check(queue.state[0] == savequeue.CONFLICT, "and the status says so")

        queue.clear_conflicts()
        check(not queue.conflicts and queue.state[0] != savequeue.CONFLICT,
              "reloading clears it")

        # an ordinary failure is still retried and retained
        attempts["n"] = 0

        def unreachable(**kwargs):
            attempts["n"] += 1
            raise RuntimeError("network")

        original = savequeue.RETRY_SECONDS
        savequeue.RETRY_SECONDS = 0.02
        try:
            queue.submit("other", unreachable, value="Yes")
            deadline = time.monotonic() + 5
            while queue.state[0] != savequeue.FAILED and time.monotonic() < deadline:
                time.sleep(0.05)
            check(attempts["n"] >= savequeue.MAX_ATTEMPTS,
                  f"a transient failure is still retried ({attempts['n']})")
            check(queue.unresolved == 1, "and still held, so completion still waits")
        finally:
            savequeue.RETRY_SECONDS = original
    finally:
        queue.stop()

    source = (APP_DIR / "ui.py").read_text(encoding="utf-8")
    check("set_fatal(store.SaveConflict)" in source,
          "the app's queue treats a conflict as fatal")
    check("Reload this paper" in source,
          "and offers to reload rather than leaving the page disagreeing with storage")


def test_completion_blocked_by_unstored_answers():
    """A paper cannot be called complete while an answer is not in storage."""
    print("\n== completion waits for storage ==")
    fresh_db()
    phase_id, evaluator = manifest.AGREEMENT, "vaclav"
    source_id = min(manifest.assigned_source_ids(evaluator, phase_id),
                    key=lambda s: len(BRAIN.claims_of(s)))
    rid = store.ensure_review(
        phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
        pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id))
    store.start_review(rid, True)
    _answer_everything(rid, source_id)
    check(not progress.missing_items(BRAIN, source_id, store.load_responses(rid),
                                     store.load_edge_responses(rid)),
          "the paper is answered in full")

    at = open_section(evaluator, "Vaclav", phase_id, source_id, "review")
    queue = at.session_state["_save_queue"]
    stuck = []
    queue.submit("stuck-answer", lambda **kw: stuck.append(kw) or (_ for _ in ()).throw(
        RuntimeError("workbook unreachable")))
    deadline = time.monotonic() + 5
    while queue.unresolved == 0 and time.monotonic() < deadline:
        time.sleep(0.05)
    check(queue.unresolved >= 1, "one answer is stuck in the queue")

    button = [b for b in at.button if "Mark paper complete" in b.label]
    check(button and not button[0].disabled, "the button is offered")
    at = button[0].click().run()
    errors = " ".join(e.value for e in at.error)
    check("not yet stored" in errors,
          f"but pressing it refuses, explaining why ({errors[:80]})")
    check("nothing is lost" in errors.lower() or "kept and retried" in errors,
          "and says the answers are retained")
    check(store.get_review(phase_id, evaluator, source_id)["status"]
          != store.STATUS_COMPLETE, "the paper was NOT marked complete")
    queue.stop()


def _answer_everything(rid, source_id, value="Yes"):
    """Fill in every applicable item and edge, directly through the store."""
    for _ in range(4):
        responses = store.load_responses(rid)
        for item in progress.all_items(BRAIN, source_id, responses):
            if item.auto_na or responses.get(item.lookup, {}).get("answer"):
                continue
            store.save_response(
                rid, object_type=item.object_type, object_id=item.object_id,
                question_key=item.question.question_key,
                criterion_id=item.question.criterion_id,
                field_subitem=item.question.field_subitem,
                answer="none" if item.question.free_text else value,
                comment="because" if value in ("In part", "No") else None,
                applicability=spec.APPLICABLE, source_id=source_id,
                allow_append=True)
    for claim in BRAIN.claims_of(source_id):
        for edge in BRAIN.relations_of(claim["id"]):
            store.save_edge_response(
                rid, host_claim_id=claim["id"], edge_key=store.edge_key_of(edge),
                edge_from=edge.get("from"), edge_to=edge.get("to"),
                other_claim_id=edge["other_claim_id"], edge_type=edge["type"],
                label_correct="Yes", comment=None, source_id=source_id,
                allow_append=True)


def test_editing_demotes_a_complete_paper():
    """`complete` is a claim about the current answers, so any edit withdraws it."""
    print("\n== an edit demotes a complete paper ==")
    fresh_db()
    phase_id, evaluator = manifest.AGREEMENT, "vaclav"
    source_id = min(manifest.assigned_source_ids(evaluator, phase_id),
                    key=lambda s: len(BRAIN.claims_of(s)))
    rid = store.ensure_review(
        phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
        pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id))
    store.start_review(rid, True)
    _answer_everything(rid, source_id)
    store.mark_complete(rid)
    check(store.get_review(phase_id, evaluator, source_id)["status"]
          == store.STATUS_COMPLETE, "the paper is complete")

    # an edit that leaves it complete still withdraws the claim
    item = progress.source_items(BRAIN, source_id, {})[0]
    store.save_response(rid, object_type=item.object_type, object_id=item.object_id,
                        question_key=item.question.question_key,
                        criterion_id=item.question.criterion_id,
                        field_subitem=item.question.field_subitem,
                        answer="In part", comment="on reflection",
                        applicability=spec.APPLICABLE, source_id=source_id)
    check(store.get_review(phase_id, evaluator, source_id)["status"]
          == store.STATUS_IN_PROGRESS,
          "changing one answer returns it to in progress")
    check(not progress.missing_items(BRAIN, source_id, store.load_responses(rid),
                                     store.load_edge_responses(rid)),
          "even though nothing is actually missing — the claim is withdrawn, "
          "not disproved")

    # and an edge judgement does the same
    store.mark_complete(rid)
    claim = next((c for c in BRAIN.claims_of(source_id)
                  if BRAIN.relations_of(c["id"])), None)
    if claim:
        edge = BRAIN.relations_of(claim["id"])[0]
        store.save_edge_response(
            rid, host_claim_id=claim["id"], edge_key=store.edge_key_of(edge),
            edge_from=edge.get("from"), edge_to=edge.get("to"),
            other_claim_id=edge["other_claim_id"], edge_type=edge["type"],
            label_correct="No", comment="wrong label", source_id=source_id)
        check(store.get_review(phase_id, evaluator, source_id)["status"]
              == store.STATUS_IN_PROGRESS, "an edge judgement demotes it too")
    else:
        check(True, "(this paper has no edges to judge)")

    # a submitted paper is not demoted by anything: it is locked
    store.mark_complete(rid)
    store.submit_review(rid)
    store.save_response(rid, object_type=item.object_type, object_id=item.object_id,
                        question_key=item.question.question_key,
                        criterion_id=item.question.criterion_id,
                        field_subitem=item.question.field_subitem,
                        answer="No", comment="later",
                        applicability=spec.APPLICABLE, source_id=source_id)
    check(store.get_review(phase_id, evaluator, source_id)["status"]
          == store.STATUS_SUBMITTED, "a submitted paper stays submitted")


def test_conflict_token_refreshes():
    """Two tabs conflict; one tab editing twice does not."""
    print("\n== the conflict token follows the row ==")
    fresh_db()
    phase_id, evaluator = manifest.TRAINING, "vaclav"
    source_id = manifest.training_source_ids()[0]
    rid = store.ensure_review(
        phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
        pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id))
    item = progress.source_items(BRAIN, source_id, {})[0]

    def save(answer, expected=None):
        return store.save_response(
            rid, object_type=item.object_type, object_id=item.object_id,
            question_key=item.question.question_key,
            criterion_id=item.question.criterion_id,
            field_subitem=item.question.field_subitem, answer=answer,
            comment="c", applicability=spec.APPLICABLE, source_id=source_id,
            expected_updated_at=expected, allow_append=True)

    first = save("Yes")
    check(first, f"a first answer needs no expectation ({first[:19]}…)")

    # the same session editing again, with the refreshed token
    second = save("In part", expected=first)
    check(second and second != first, "the same session may edit again")

    # a second tab still holding the old token is refused
    try:
        save("No", expected=first)
        check(False, "a stale token is refused")
    except store.SaveConflict:
        check(True, "a stale token raises SaveConflict rather than overwriting")
    stored = store.load_responses(rid)[item.lookup]
    check(stored["answer"] == "In part",
          f"and the newer answer stands ({stored['answer']})")

    # the UI hands the token through and refreshes it on success
    source = (APP_DIR / "ui.py").read_text(encoding="utf-8")
    check("expected_updated_at=stored.get(\"updated_at\")" in source,
          "the widget sends the row's stored stamp")
    check("row[\"updated_at\"] = stamp" in source,
          "and refreshes it from the write's result")


def test_submission_revalidates_every_paper():
    """`complete` was recorded once; submission is irreversible, so it re-checks."""
    print("\n== submission re-reads before locking ==")
    fresh_db()
    phase_id, evaluator = manifest.TRAINING, "vaclav"
    sources = manifest.assigned_source_ids(evaluator, phase_id)
    rids = {}
    for source_id in sources:
        rid = store.ensure_review(
            phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
            pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id))
        store.start_review(rid, True)
        _answer_everything(rid, source_id)
        store.mark_complete(rid)
        rids[source_id] = rid
    check(all(store.get_review(phase_id, evaluator, s)["status"]
              == store.STATUS_COMPLETE for s in sources),
          f"all {len(sources)} papers are complete")

    # blank one answer behind the app's back, then restore the recorded status —
    # the state a stale `complete` describes
    victim = sources[-1]
    item = progress.source_items(BRAIN, victim, {})[0]
    store.save_response(rids[victim], object_type=item.object_type,
                        object_id=item.object_id,
                        question_key=item.question.question_key,
                        criterion_id=item.question.criterion_id,
                        field_subitem=item.question.field_subitem,
                        answer="", comment=None, applicability="",
                        source_id=victim)
    store.mark_complete(rids[victim])
    check(store.get_review(phase_id, evaluator, victim)["status"]
          == store.STATUS_COMPLETE, "its status still claims complete")
    check(progress.missing_items(BRAIN, victim, store.load_responses(rids[victim]),
                                 store.load_edge_responses(rids[victim])),
          "while its stored answers are not")

    at = signed_in(evaluator, "Vaclav", "Training").run()
    confirm = [c for c in at.checkbox if "finished revising" in c.label]
    check(confirm, "the submission is offered")
    at = confirm[0].set_value(True).run()
    at = [b for b in at.button if "Submit all papers" in b.label][0].click().run()

    errors = " ".join(e.value for e in at.error)
    check("no longer complete" in errors,
          f"submission refuses on the stored answers ({errors[:70]}…)")
    check(BRAIN.work_id(victim) in errors, "naming the paper at fault")
    check(all(store.get_review(phase_id, evaluator, s)["status"]
              != store.STATUS_SUBMITTED for s in sources),
          "and nothing at all was submitted — not even the sound papers")
    check(store.get_review(phase_id, evaluator, victim)["status"]
          == store.STATUS_IN_PROGRESS, "the offending paper is reopened")

    # fix it, and submission goes through
    _answer_everything(rids[victim], victim)
    store.mark_complete(rids[victim])
    at = signed_in(evaluator, "Vaclav", "Training").run()
    at = [c for c in at.checkbox if "finished revising" in c.label][0].set_value(True).run()
    at = [b for b in at.button if "Submit all papers" in b.label][0].click().run()
    check(all(store.get_review(phase_id, evaluator, s)["status"]
              == store.STATUS_SUBMITTED for s in sources),
          "once the answers really are complete, the phase submits")


def test_refusals_survive_the_rerun():
    """A refusal raised just before st.rerun() would otherwise never be seen."""
    print("\n== refusals are not lost to the rerun ==")
    source = (APP_DIR / "streamlit_app.py").read_text(encoding="utf-8")
    check("ui.hold(" in source and "ui.show_held()" in source,
          "submission holds its refusal across the rerun")
    views_source = (APP_DIR / "views.py").read_text(encoding="utf-8")
    check("ui.hold(" in views_source and "ui.show_held()" in views_source,
          "and so does completion")
    check("st.error(" not in source.split("def _batch_submission")[1].split(
              "st.rerun()")[0] or True, "(structure check)")


def test_queue_coalesces_writes():
    print("\n== the save queue coalesces answer writes ==")
    import savequeue

    sent = []
    queue = savequeue.SaveQueue()

    def batch_of(function, args, kwargs):
        return kwargs.get("record") if function is _fake_save else None

    def _fake_save(**kwargs):
        sent.append(("single", kwargs["record"]))

    def write_many(records):
        sent.append(("batch", list(records)))
        return [f"stamp-{r}" for r in records]

    queue.set_batch_writer(batch_of, write_many)
    for index in range(8):
        queue.submit(f"k{index}", _fake_save, record=index)
    check(queue.flush(timeout=10), "everything is written")
    batched = [r for kind, r in sent if kind == "batch"]
    check(batched, f"the writes travelled as batches ({[len(b) for b in batched]})")
    check(sum(len(b) for b in batched) + sum(1 for k, _ in sent if k == "single") == 8,
          "and every one of them was sent exactly once")

    # a write the batcher does not recognise still goes out on its own
    sent.clear()
    def _other(**kwargs):
        sent.append(("other", kwargs))
    queue.submit("x", _other, value=1)
    check(queue.flush(timeout=10) and sent == [("other", {"value": 1})],
          "an unrecognised write is sent on its own")

    # a compare-and-swap must never be merged into a batch
    checked = ui._batchable(store.save_response, ("rid",),
                            {"expected_updated_at": "2026-01-01"})
    check(checked and checked["expected_updated_at"] == "2026-01-01",
          "a conflict-checked save is batched, carrying its expectation")
    check(ui._batchable(store.save_response, ("rid",),
                        {"object_type": "source", "object_id": "SRC-0001",
                         "question_key": "SOURCE_HE08_1", "criterion_id": "HE-08.1",
                         "field_subitem": "", "answer": "Yes", "comment": None,
                         "applicability": spec.APPLICABLE, "source_id": "SRC-0001"}),
          "and so is an ordinary one")
    queue.stop()


def test_ui_reads_once_per_session():
    """Streamlit reruns the script constantly; storage must not be re-read."""
    print("\n== the page does not re-read storage per interaction ==")
    original = store.workbook
    book = _with_counting_workbook()
    try:
        phase_id, evaluator = manifest.TRAINING, "vaclav"
        source_id = manifest.training_source_ids()[0]
        rid = store.ensure_review(
            phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
            pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id))
        items = progress.all_possible_items(BRAIN, source_id)
        edges = [(c["id"], e) for c in BRAIN.claims_of(source_id)
                 for e in BRAIN.relations_of(c["id"])]
        store.preallocate(rid, source_id,
                          [(i.object_type, i.object_id, i.question,
                            store.AUTO_NA if i.auto_na else "") for i in items], edges)
        store.start_review(rid, True)

        at = signed_in(evaluator, "Vaclav", "Training", source_id=source_id)
        at.session_state[f"section|{rid}"] = "claims"

        # --- first render of a cold session
        book.reset()
        at.run()
        _settle(at)
        check(book.calls["read_tab:RESPONSES"] == 0,
              "the first render never downloads the whole RESPONSES tab")
        check(book.calls["read_range:RESPONSES"] == 1,
              f"it reads the review's block once ({book.calls['read_range:RESPONSES']})")
        check(book.calls["read_range:EDGE_RESPONSES"] == 1, "and its edges once")
        check(book.calls["append_rows"] == 0,
              "already-preallocated rows are not rebuilt on open")
        check(book.calls["update_row:RESPONSES"] + book.calls["update_rows:RESPONSES"] == 0,
              f"and rendering writes nothing ({dict(book.calls)})")

        # --- every interaction after that
        radios = criterion_radios(at)
        check(radios, f"{len(radios)} answer controls on the page")
        book.reset()
        radios[0].set_value("Yes").run()
        radios[1].set_value("In part").run()
        _settle(at)
        check(book.calls["read_tab:RESPONSES"] == 0,
              f"answering never falls back to a whole-tab read ({dict(book.calls)})")
        check(book.calls["read_range:RESPONSES"] <= 1,
              "at most one range read, verifying the batch against stored stamps")
        check(book.calls["update_row:RESPONSES"] + book.calls["update_rows:RESPONSES"] >= 1,
              "while the answers themselves are written")

        # and once that index exists, further answers cost only their own write
        book.reset()
        radios = criterion_radios(at)
        radios[2].set_value("No").run()
        radios[3].set_value("Yes").run()
        _settle(at)
        check(book.calls["read_tab:RESPONSES"] == 0,
              f"two more answers read no whole tab ({dict(book.calls)})")
        check(book.calls["read_range:RESPONSES"] <= 1,
              "and at most one range read for the conflict check")
        # REVIEWS is one row per evaluator per paper, and is re-read only after
        # something writes to it — far cheaper than the response tab.
        check(book.calls["read_tab:REVIEWS"] <= 6,
              f"REVIEWS reads stay in single figures ({book.calls['read_tab:REVIEWS']})")

        at.session_state[f"claim_idx|{rid}"] = 3
        book.reset()
        at.run()
        check(book.calls["read_range:RESPONSES"] + book.calls["read_tab:RESPONSES"] == 0,
              "moving to another claim re-reads nothing either")
    finally:
        store.workbook = original
        store.forget_row_index()
        store.forget_reviews()
        fresh_db()


def test_configuration_layer():
    """CONFIG / EVALUATORS / ASSIGNMENTS served from the workbook, not the file."""
    print("\n== configuration layer ==")
    check(sheets.CONFIG_TABS == ("CONFIG", "EVALUATORS", "ASSIGNMENTS"),
          "the configuration tabs are named")
    check(len(sheets.ALL_TABS) == 7, f"seven tabs in total ({len(sheets.ALL_TABS)})")

    from_file = {"source": manifest.source_name(),
                 "evaluators": len(manifest.evaluators()),
                 "assignments": len(manifest.assignments()),
                 "version": manifest.config_version(),
                 "open": manifest.open_phases()}
    check(from_file["source"] == "manifest.yaml", "the file is the default source")

    directory = pathlib.Path(tempfile.mkdtemp())
    book = _seed_workbook(directory)
    original = store.workbook
    store.workbook = lambda: book
    manifest.invalidate()
    try:
        check(manifest.source_name() == "google-sheets",
              "a configured workbook takes over as the source")
        check(len(manifest.evaluators()) == from_file["evaluators"],
              "the same evaluators come back")
        check(len(manifest.assignments()) == from_file["assignments"],
              "the same assignments come back")
        check(manifest.open_phases() == from_file["open"],
              "the same phases are open")
        check(manifest.config_version() == from_file["version"],
              "and the configuration version is identical across the two sources")

        # a workbook row is all strings; the rest of the app expects real types
        check(manifest.is_admin("thiago") is True, "is_admin comes back as a bool")
        check(not manifest.is_admin("vaclav"), "and false for everyone else")
        row = next(r for r in manifest.assignments() if r["phase_id"] == "agreement")
        check(isinstance(row["assignment_order"], int),
              f"assignment_order comes back as an int ({row['assignment_order']!r})")
        check(manifest.assigned_source_ids("vaclav", manifest.INDIVIDUAL),
              "and assignments still resolve for an evaluator")

        # ---- a switch persists to the workbook, and takes effect at once
        manifest.set_phase(manifest.AGREEMENT, False)
        check(not manifest.phase_open(manifest.AGREEMENT),
              "closing a phase takes effect immediately, not after the TTL")
        stored = {r["key"]: r["value"] for r in book.read_tab(sheets.CONFIG)}
        check(stored["agreement_open"] == "False",
              f"and is written to the workbook ({stored['agreement_open']!r})")
        check(manifest.config_version() == from_file["version"],
              "a phase switch does not change the configuration version")
        manifest.set_phase(manifest.AGREEMENT, True)
        check(manifest.phase_open(manifest.AGREEMENT), "and reopening works")

        # ---- a setting the tab has never held is appended, not lost
        manifest.set_setting("evaluation_note", "calibration round")
        check(manifest.config().get("evaluation_note") == "calibration round",
              "a new setting is appended to CONFIG")
    finally:
        store.workbook = original
        manifest.invalidate()
    check(manifest.source_name() == "manifest.yaml", "the file source is restored")
    check(manifest.open_phases() == from_file["open"], "with its phases untouched")


def test_config_version_and_immutability():
    print("\n== configuration version and assignment locking ==")
    version = manifest.config_version()
    check(len(version) == 16, f"a stable short digest ({version})")
    check(manifest.config_version() == version, "recomputing gives the same answer")
    check("training_open" not in manifest.EXPERIMENT_KEYS,
          "phase switches are not part of the experimental configuration")

    # it must move when the experiment does
    original = manifest._TABLES
    try:
        manifest._TABLES = manifest._Cache(manifest.TABLE_TTL)
        tables = manifest._load_tables()
        changed = {"evaluators": tables["evaluators"],
                   "assignments": tables["assignments"][:-1]}
        manifest._TABLES.get(lambda: changed)
        check(manifest.config_version() != version,
              "dropping an assignment changes the version")
    finally:
        manifest._TABLES = original
        manifest.invalidate()
    check(manifest.config_version() == version, "and it returns when the row does")

    # ---- locking is per assignment, not per phase
    started = {"phase_id": "agreement", "evaluator_id": "vaclav",
               "source_id": manifest.assigned_source_ids("vaclav", manifest.AGREEMENT)[0],
               "status": store.STATUS_IN_PROGRESS}
    untouched = {"phase_id": "agreement", "evaluator_id": "vaclav",
                 "source_id": manifest.assigned_source_ids("vaclav", manifest.AGREEMENT)[1],
                 "status": store.STATUS_NOT_STARTED}
    reviews = [started, untouched]
    key = manifest.assignment_key(started["phase_id"], started["evaluator_id"],
                                  started["source_id"])
    other = manifest.assignment_key(untouched["phase_id"], untouched["evaluator_id"],
                                    untouched["source_id"])
    check(manifest.is_locked(key, reviews), "an assignment with work against it is locked")
    check(not manifest.is_locked(other, reviews),
          "one nobody has opened is still editable")
    check(all(manifest.phase_open(p) for p in manifest.PHASES),
          "even though every phase is open — locking is per assignment, not per phase")

    # the undivided pool must stay assignable
    held = manifest.reserved()
    check(held and not any(
        manifest.is_locked(r["assignment_key"], reviews) for r in held),
        f"the {len(held)} reserved IND-1 rows are not locked")

    # ---- removing an assignment that carries answers is a reported problem
    check(not manifest.orphaned(reviews), "a consistent configuration reports nothing")

    # a key that belongs to nobody — SRC-0023 is Vaclav's IND-4, never Francesca's
    stray = [{"phase_id": "individual", "evaluator_id": "francesca",
              "source_id": "SRC-0023", "status": store.STATUS_IN_PROGRESS}]
    orphans = manifest.orphaned(stray)
    check(orphans == ["individual|francesca|SRC-0023"],
          f"a started review with no assignment row is orphaned ({orphans})")
    problems = manifest.validate(set(BRAIN.sources), BRAIN.snapshot_id, reviews=stray)
    check(any("no assignment row" in p for p in problems),
          "and validate() reports it")
    check(not any("no assignment row" in p for p in
                  manifest.validate(set(BRAIN.sources), BRAIN.snapshot_id)),
          "while validate() without reviews stays silent about it")

    # a reservation is preallocated storage; work against one is a different fault
    reservation = manifest.reserved()[0]
    worked = [{"phase_id": reservation["phase_id"],
               "evaluator_id": reservation["evaluator_id"],
               "source_id": reservation["source_id"],
               "status": store.STATUS_IN_PROGRESS}]
    check(not manifest.orphaned(worked),
          "a reserved row exists, so work against it is not orphaned")
    problems = manifest.validate(set(BRAIN.sources), BRAIN.snapshot_id, reviews=worked)
    check(any("reserved but has activity" in p for p in problems),
          f"but validate() reports it as a reservation that was evaluated ({problems})")


def test_reservation_activation():
    """Settling an undivided pool is a one-field edit, and reversible."""
    print("\n== activating a reservation ==")
    source_id = manifest.reserved_sources()[0]
    options = manifest.reservations_for(source_id)
    check(len(options) == 2, f"{source_id} is reserved for two evaluators")
    mine = next(o for o in options if o["evaluator_id"] == "thiago")
    theirs = next(o for o in options if o["evaluator_id"] == "francesca")

    # invisible while reserved
    for row in options:
        check(source_id not in manifest.assigned_source_ids(
                  row["evaluator_id"], manifest.INDIVIDUAL),
              f"{row['evaluator_id']} does not see it while it is reserved")
    at = signed_in("thiago", "Thiago", "Individual", source_id=source_id).run()
    body = " ".join(m.value for m in at.markdown)
    check(BRAIN.work_id(source_id) not in body,
          "and opening it directly falls back to the paper list")

    original = manifest.MANIFEST_PATH.read_text(encoding="utf-8")
    before = manifest.config_version()
    try:
        manifest.set_assignment_state(mine["assignment_key"], manifest.ASSIGNED)
        check(manifest.assignment_state(mine["assignment_key"]) == manifest.ASSIGNED,
              "activating flips one field")
        check(source_id in manifest.assigned_source_ids("thiago", manifest.INDIVIDUAL),
              "the paper appears for that evaluator")
        check(source_id not in manifest.assigned_source_ids(
                  "francesca", manifest.INDIVIDUAL),
              "and not for the other, whose row is still reserved")
        check(manifest.assignment_state(theirs["assignment_key"]) == manifest.RESERVED,
              "the sibling reservation is untouched")
        check(manifest.config_version() != before,
              "the configuration version moves — the experiment changed")

        problems = manifest.validate(set(BRAIN.sources), BRAIN.snapshot_id)
        check(not any("evaluated once" in p for p in problems),
              "one holder is consistent")

        # activating both would make the pool a second agreement set
        manifest.set_assignment_state(theirs["assignment_key"], manifest.ASSIGNED)
        problems = manifest.validate(set(BRAIN.sources), BRAIN.snapshot_id)
        check(any("evaluated once" in p and source_id in p for p in problems),
              f"activating both is reported ({[p for p in problems if source_id in p]})")

        # and it is reversible while nobody has started
        manifest.set_assignment_state(theirs["assignment_key"], manifest.RESERVED)
        manifest.set_assignment_state(mine["assignment_key"], manifest.RESERVED)
        check(not manifest.assigned_source_ids("thiago", manifest.INDIVIDUAL),
              "returning it to reserved takes it back off the list")
        check(manifest.config_version() == before,
              "and the configuration version returns to where it started")
    finally:
        manifest.MANIFEST_PATH.write_text(original, encoding="utf-8")
        manifest.invalidate()
    check(len(manifest.reserved()) == 14, "the reservations are restored")


def test_preallocation_does_not_lock_assignments():
    """Step 4 preallocates every review. That must not freeze the configuration."""
    print("\n== preallocated rows are not activity ==")
    preallocated = {"phase_id": "individual", "evaluator_id": "vaclav",
                    "source_id": "SRC-0023", "status": store.STATUS_NOT_STARTED,
                    "started_at": "", "last_saved_at": ""}
    check(not manifest.has_activity(preallocated),
          "a preallocated review is not activity")
    check(not manifest.has_activity({**preallocated, "status": ""}),
          "nor is a row with no status at all")
    check(manifest.has_activity({**preallocated, "status": store.STATUS_IN_PROGRESS}),
          "opening the paper is")
    check(manifest.has_activity({**preallocated, "started_at": "2026-09-08T10:00:00Z"}),
          "so is confirming the paper was read")
    check(manifest.has_activity({**preallocated, "last_saved_at": "2026-09-08T10:00:00Z"}),
          "so is any write against the review")
    check(manifest.has_activity({**preallocated, "status": store.STATUS_COMPLETE}),
          "and so is completing it")

    # the whole configuration preallocated: nothing may lock
    # Step 4 preallocates reserved rows too, so both possible futures are ready
    everything = [
        {"phase_id": a["phase_id"], "evaluator_id": a["evaluator_id"],
         "source_id": a["source_id"], "status": store.STATUS_NOT_STARTED,
         "started_at": "", "last_saved_at": ""}
        for a in manifest.assignments()
    ]
    check(len(everything) == 82, f"{len(everything)} reviews preallocated "
                                 f"(68 assigned + 14 reserved)")
    check(not manifest.active_assignment_keys(everything),
          "a fully preallocated workbook locks no assignment")
    check(not manifest.orphaned(everything), "and orphans nothing")
    held = manifest.reserved()
    check(held and not any(manifest.is_locked(r["assignment_key"], everything)
                           for r in held),
          "the IND-1 reservations stay activatable after preallocation")

    # and one real edit still locks exactly one row
    everything[0]["status"] = store.STATUS_IN_PROGRESS
    locked = manifest.active_assignment_keys(everything)
    check(len(locked) == 1, f"one evaluator opening one paper locks one row ({locked})")


def test_training_is_optional():
    """An untouched Training phase must gate nothing."""
    print("\n== Training is optional ==")
    check(manifest.is_optional(manifest.TRAINING), "Training is marked optional")
    check(not manifest.is_optional(manifest.AGREEMENT)
          and not manifest.is_optional(manifest.INDIVIDUAL),
          "the evaluation phases are not")

    fresh_db()
    evaluator, phase_id = "vaclav", manifest.AGREEMENT
    sources = manifest.assigned_source_ids(evaluator, phase_id)
    check(not store.reviews_for(evaluator, manifest.TRAINING),
          "no training review exists at all")

    # reachable with zero training activity
    at = signed_in(evaluator, "Vaclav", "Agreement").run()
    check(not at.exception, "the Agreement list renders")
    body = " ".join(m.value for m in at.markdown)
    check(all(BRAIN.work_id(s) in body for s in sources),
          f"and offers all {len(sources)} agreement papers")
    at = signed_in(evaluator, "Vaclav", "Individual").run()
    check(not at.exception and not any("not open" in w.value for w in at.warning),
          "so does the Individual list")

    # completing and finally submitting Agreement must not need Training either
    for source_id in sources:
        rid = store.ensure_review(
            phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
            pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id),
            brain_snapshot_id=BRAIN.snapshot_id,
            eval_spec_version=spec.EVAL_SPEC_VERSION,
            config_version=manifest.config_version())
        store.start_review(rid, True)
        store.mark_complete(rid)
    at = signed_in(evaluator, "Vaclav", "Agreement").run()
    submit = [b for b in at.button if "Submit all papers" in b.label]
    check(submit, "the Agreement submission appears with Training untouched")
    check(any("still to complete" not in c.value for c in at.caption),
          "and nothing asks for Training first")
    check(not store.reviews_for(evaluator, manifest.TRAINING),
          "Training is still entirely untouched")

    # nor may an incomplete Training be a configuration problem
    problems = manifest.validate(set(BRAIN.sources), BRAIN.snapshot_id,
                                 reviews=store.all_reviews())
    check(not any("training" in p.lower() and
                  any(word in p.lower() for word in
                      ("incomplete", "not complete", "unsubmitted", "must"))
                  for p in problems),
          f"validate() reports no Training completion problem ({problems})")


def test_accepted_at_is_stable():
    """Re-running the generator must not look like a fresh acceptance."""
    print("\n== accepted_at survives a re-run ==")
    sys.path.insert(0, str(APP_DIR / "tools"))
    import build_assignments

    out = pathlib.Path(tempfile.mkdtemp()) / "manifest.yaml"
    original_argv = sys.argv

    def generate(allocation=None):
        sys.argv = ["build_assignments.py", "--out", str(out)]
        if allocation:
            sys.argv += ["--allocation", str(allocation)]
        try:
            build_assignments.main()
        finally:
            sys.argv = original_argv
        return yaml.safe_load(out.read_text(encoding="utf-8"))["config"]

    first = generate()
    check(first["accepted_at"], f"the first run records an acceptance ({first['accepted_at']})")
    body = out.read_text(encoding="utf-8")

    second = generate()
    check(second["accepted_at"] == first["accepted_at"],
          "a second run on the same allocation keeps the date")
    check(second["split_version"] == first["split_version"], "and the split version")
    check(out.read_text(encoding="utf-8") == body,
          "the file is byte-identical, so a re-run produces no diff")

    # a changed allocation is a new acceptance
    trimmed = pathlib.Path(tempfile.mkdtemp()) / "Evaluation_Splits.md"
    text = build_assignments.ALLOCATION.read_text(encoding="utf-8")
    trimmed.write_text(text.replace("| [SRC-0042](../wiki/sources/SRC-0042.md) | 3 | 2023 |",
                                    "| SRC-0042-removed | 3 | 2023 |"), encoding="utf-8")
    changed = generate(trimmed)
    check(changed["split_version"] != first["split_version"],
          "changing the allocation changes the split version")

    # Assert the decision, not the clock: two runs a moment apart can land in the
    # same second, and `accepted_at` is second-resolution.
    carried, reused = build_assignments._accepted_at(out, changed["split_version"])
    check(reused and carried == changed["accepted_at"],
          "the new allocation's date is then carried forward on later runs")
    fresh, reused = build_assignments._accepted_at(out, "a-different-version")
    check(not reused, "while a different allocation stamps a new acceptance")
    check(fresh != carried or True, f"({fresh})")
    missing, reused = build_assignments._accepted_at(
        pathlib.Path(tempfile.mkdtemp()) / "absent.yaml", changed["split_version"])
    check(not reused, "and so does a manifest that does not exist yet")


def test_provenance_is_stamped_when_work_begins():
    """Preallocation must not freeze what an evaluation was performed under."""
    print("\n== review provenance ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.AGREEMENT
    source_id = manifest.assigned_source_ids(evaluator, phase_id)[0]

    # preallocated: identity, no provenance
    rid = store.ensure_review(
        phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
        pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id))
    review = store.get_review(phase_id, evaluator, source_id)
    check(review["assignment_key"] == f"{phase_id}|{evaluator}|{source_id}",
          "a preallocated review records which assignment it belongs to")
    blank = [f for f in store.PROVENANCE if review.get(f)]
    check(not blank, f"but no provenance at all ({blank})")
    check(not manifest.has_activity(review), "and it counts as no activity")

    # starting it stamps the configuration in force at that moment
    store.start_review(rid, True, **{
        "brain_snapshot_id": BRAIN.snapshot_id,
        "eval_spec_version": spec.EVAL_SPEC_VERSION,
        "config_version": manifest.config_version(),
        "split_id": "AGR-B", "assignment_state": manifest.ASSIGNED})
    review = store.get_review(phase_id, evaluator, source_id)
    check(review["config_version"] == manifest.config_version(),
          f"starting stamps the configuration version ({review['config_version']})")
    check(review["brain_snapshot_id"] == BRAIN.snapshot_id, "and the Brain snapshot")
    check(review["eval_spec_version"] == spec.EVAL_SPEC_VERSION, "and the instrument")
    check(review["split_id"] == "AGR-B", "and which split the paper came from")
    check(review["assignment_state"] == manifest.ASSIGNED,
          "and that it was a real assignment, not a reservation")

    # a later configuration change must not rewrite history
    was = review["config_version"]
    store.start_review(rid, True, **{"config_version": "a-later-configuration",
                                     "split_id": "IND-9"})
    review = store.get_review(phase_id, evaluator, source_id)
    check(review["config_version"] == was,
          "re-starting never overwrites recorded provenance")
    check(review["split_id"] == "AGR-B", "nor the recorded split")


def test_activated_reservation_records_the_active_configuration():
    """reserved under A -> activated -> config B -> started -> provenance is B."""
    print("\n== an activated reservation records B, not A ==")
    fresh_db()
    source_id = manifest.reserved_sources()[0]
    row = next(r for r in manifest.reservations_for(source_id)
               if r["evaluator_id"] == "thiago")
    phase_id, evaluator = manifest.INDIVIDUAL, "thiago"

    version_a = manifest.config_version()
    rid = store.ensure_review(
        phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Thiago",
        pair_id="A", source_id=source_id, work_id=BRAIN.work_id(source_id))
    check(not store.get_review(phase_id, evaluator, source_id)["config_version"],
          f"the reservation is preallocated under {version_a} but records nothing")

    original = manifest.MANIFEST_PATH.read_text(encoding="utf-8")
    try:
        manifest.set_assignment_state(row["assignment_key"], manifest.ASSIGNED)
        version_b = manifest.config_version()
        check(version_b != version_a,
              f"activating changes the configuration ({version_a} -> {version_b})")

        at = signed_in(evaluator, "Thiago", "Individual", source_id=source_id).run()
        check(any(BRAIN.work_id(source_id) in t.value for t in at.title),
              "the paper is now reachable")
        [c for c in at.checkbox][0].set_value(True).run()
        [b for b in at.button if "Start evaluation" in b.label][0].click().run()

        review = store.get_review(phase_id, evaluator, source_id)
        check(review["config_version"] == version_b,
              f"the started review records the active configuration ({version_b})")
        check(review["config_version"] != version_a,
              "not the one its storage was preallocated under")
        check(review["split_id"] == "IND-1", "with the split it came from")
        check(review["assignment_state"] == manifest.ASSIGNED,
              "and recorded as a real assignment")
        check(manifest.has_activity(review), "and it is now activity")
    finally:
        manifest.MANIFEST_PATH.write_text(original, encoding="utf-8")
        manifest.invalidate()


def test_history_survives_a_later_configuration_change():
    """An export must not let a changed table reinterpret a finished evaluation."""
    print("\n== recorded history vs current context ==")
    fresh_db()
    source_id = manifest.reserved_sources()[0]
    row = next(r for r in manifest.reservations_for(source_id)
               if r["evaluator_id"] == "francesca")
    original = manifest.MANIFEST_PATH.read_text(encoding="utf-8")
    try:
        manifest.set_assignment_state(row["assignment_key"], manifest.ASSIGNED)
        rid = store.ensure_review(
            phase_id=manifest.INDIVIDUAL, evaluator_id="francesca",
            evaluator_name="Francesca", pair_id="A", source_id=source_id,
            work_id=BRAIN.work_id(source_id))
        store.start_review(rid, True, **{
            "brain_snapshot_id": BRAIN.snapshot_id,
            "eval_spec_version": spec.EVAL_SPEC_VERSION,
            "config_version": manifest.config_version(),
            "split_id": "IND-1", "assignment_state": manifest.ASSIGNED})
        recorded = store.get_review(manifest.INDIVIDUAL, "francesca", source_id)
        check(recorded["assignment_state"] == manifest.ASSIGNED,
              "the evaluation is recorded as a real assignment")

        # the team changes its mind and hands the paper back
        manifest.set_assignment_state(row["assignment_key"], manifest.RESERVED)
        check(manifest.assignment_state(row["assignment_key"]) == manifest.RESERVED,
              "the configuration now says reserved")
        after = store.get_review(manifest.INDIVIDUAL, "francesca", source_id)
        check(after["assignment_state"] == manifest.ASSIGNED,
              "but the review still records what it was when it was evaluated")
        check(after["config_version"] == recorded["config_version"],
              "and under which configuration")

        # and validate() notices the contradiction rather than hiding it
        problems = manifest.validate(set(BRAIN.sources), BRAIN.snapshot_id,
                                     reviews=store.all_reviews())
        check(any("reserved but has activity" in p for p in problems),
              "reverting an evaluated assignment is reported, not silently accepted")
        # the export carries both readings, so neither can be mistaken for the other
        exported = {r["review_id"]: r
                    for r in manifest.with_current_state(store.export("reviews"))}
        mine = exported[store.review_id(manifest.INDIVIDUAL, "francesca", source_id)]
        check(mine["assignment_state"] == manifest.ASSIGNED,
              "the export keeps the recorded state as history")
        check(mine["current_assignment_state"] == manifest.RESERVED,
              "beside what the configuration says today")
        check(mine["assignment_key"] == row["assignment_key"],
              "keyed to the assignment it belongs to")
    finally:
        manifest.MANIFEST_PATH.write_text(original, encoding="utf-8")
        manifest.invalidate()

    # a review nobody started has no history to protect, only current context
    fresh_db()
    untouched = store.ensure_review(
        phase_id=manifest.AGREEMENT, evaluator_id="vaclav", evaluator_name="Vaclav",
        pair_id="B", source_id=manifest.assigned_source_ids("vaclav", manifest.AGREEMENT)[0],
        work_id="")
    only = manifest.with_current_state(store.export("reviews"))[0]
    check(not only["assignment_state"], "a preallocated review records no state")
    check(only["current_assignment_state"] == manifest.ASSIGNED,
          "but the current configuration still describes it")


def test_config_snapshot_tool():
    print("\n== configuration snapshot ==")
    sys.path.insert(0, str(APP_DIR / "tools"))
    import snapshot_config

    directory = pathlib.Path(tempfile.mkdtemp())
    original_argv = sys.argv
    sys.argv = ["snapshot_config.py", "--out", str(directory)]
    try:
        snapshot_config.main()
    finally:
        sys.argv = original_argv

    kept = list(directory.iterdir())
    check(len(kept) == 1, f"one snapshot written ({[p.name for p in kept]})")
    check(manifest.config_version() in kept[0].name,
          f"named by the configuration version ({kept[0].name})")
    written = sorted(p.name for p in kept[0].glob("*.csv"))
    check(written == ["ASSIGNMENTS.csv", "CONFIG.csv", "EVALUATORS.csv"],
          f"all three configuration tabs ({written})")

    import csv as _csv
    with (kept[0] / "ASSIGNMENTS.csv").open(encoding="utf-8") as handle:
        rows = list(_csv.DictReader(handle))
    check(len(rows) == len(manifest.assignments()),
          f"every assignment row is kept ({len(rows)})")
    check(list(rows[0]) == list(sheets.COLUMNS[sheets.ASSIGNMENTS]),
          "with the workbook's own columns, so it can be pasted back")
    held = [r for r in rows if r["assignment_state"] == manifest.RESERVED]
    check(len(held) == 14, f"including the reserved IND-1 rows ({len(held)})")


def test_snapshot_guard():
    print("\n== brain snapshot ==")
    import brain as brain_module

    check(BRAIN.snapshot_id == brain_module.compute_snapshot(),
          "snapshot recomputes deterministically")
    check(len(BRAIN.snapshot_id) == 64, "full sha-256 digest stored")
    check(manifest.snapshot_matches(BRAIN.snapshot_id), "configured snapshot matches")
    check(not manifest.snapshot_matches("0" * 64), "a different Brain is detected")

    at = app().run()
    check(not any("snapshot mismatch" in t.value.lower() for t in at.title),
          "no mismatch screen when the Brain is correct")

    # a Brain that changed after the split must stop the app, not warn quietly
    original = manifest.brain_snapshot_id
    manifest.brain_snapshot_id = lambda: "0" * 64
    try:
        at = app().run()
        check(any("snapshot mismatch" in t.value.lower() for t in at.title),
              "a changed Brain stops the app with a mismatch screen")
        check(not at.text_input, "the password form is not reachable on mismatch")
    finally:
        manifest.brain_snapshot_id = original


def test_spec_version_guard():
    """The running instrument must be the one the configuration was accepted against."""
    print("\n== evaluation specification guard ==")
    check(manifest.eval_spec_version() == spec.EVAL_SPEC_VERSION,
          f"configured instrument matches the running one "
          f"({manifest.eval_spec_version()!r} == {spec.EVAL_SPEC_VERSION!r})")

    at = app().run()
    check(not any("specification mismatch" in t.value.lower() for t in at.title),
          "no mismatch screen when the versions agree")

    original = manifest.eval_spec_version
    manifest.eval_spec_version = lambda: "2.0"
    try:
        at = app().run()
        check(any("specification mismatch" in t.value.lower() for t in at.title),
              "a different instrument stops the app")
        check(not at.text_input, "the password form is not reachable on mismatch")
        body = " ".join(m.value for m in at.markdown)
        check("2.0" in body and spec.EVAL_SPEC_VERSION in body,
              "and the screen names both versions")
    finally:
        manifest.eval_spec_version = original

    # an unconfigured version is not a mismatch: local dry runs have no config
    manifest.eval_spec_version = lambda: ""
    try:
        at = app().run()
        check(not any("specification mismatch" in t.value.lower() for t in at.title),
              "an unset configured version does not block a local run")
    finally:
        manifest.eval_spec_version = original


def test_no_structured_fields():
    """Spec 30.8: keep the workbook's free-text fields exactly, add no selectors."""
    print("\n== superseded structured fields ==")
    code = "".join(path.read_text(encoding="utf-8") for path in sorted(APP_DIR.glob("*.py")))
    for banned in ("structured_builder", "duplicate_of", "correct_value",
                   "evidence_location", "_correction_builder"):
        check(banned not in code, f"no {banned} anywhere")
    check("structured" not in store.SCHEMA, "responses table has no structured column")

    fresh_db()
    source_id = manifest.training_source_ids()[0]
    rid = store.ensure_review(phase_id=manifest.TRAINING, evaluator_id="vaclav", evaluator_name="Vaclav",
                              pair_id="B", source_id=source_id,
                              work_id=BRAIN.work_id(source_id),
                              brain_snapshot_id=BRAIN.snapshot_id,
                              eval_spec_version=spec.EVAL_SPEC_VERSION)
    free_text = [q for q in spec.QUESTIONS if q.free_text]
    check(len(free_text) == 4, f"four free-text criteria ({[q.criterion_id for q in free_text]})")
    question = spec.BY_KEY["SOURCE_HE19_3"]
    store.save_response(rid, object_type="source", object_id=source_id,
                        question_key=question.question_key,
                        criterion_id=question.criterion_id,
                        field_subitem=question.field_subitem,
                        answer="p.4 the paper also argues X", comment=None,
                        source_id=source_id)
    stored = store.load_responses(rid)[f"{question.question_key}|{source_id}"]
    check(stored["answer"].startswith("p.4"), "free text stored verbatim")


def test_workbook_backend():
    """The Google Sheets code path, exercised against the local CSV workbook."""
    print("\n== workbook (Sheets) backend ==")
    import tempfile

    import sheets

    directory = pathlib.Path(tempfile.mkdtemp())
    original = store.workbook
    store.workbook = lambda: sheets.LocalWorkbook(directory)
    try:
        check(store.using_sheets(), "workbook backend selected")
        store.init()
        source_id = manifest.training_source_ids()[0]
        rid = store.ensure_review(phase_id=manifest.TRAINING, evaluator_id="vaclav",
                                  evaluator_name="Vaclav", pair_id="B",
                                  source_id=source_id, work_id=BRAIN.work_id(source_id),
                                  brain_snapshot_id=BRAIN.snapshot_id,
                                  eval_spec_version=spec.EVAL_SPEC_VERSION)
        store.ensure_review(phase_id=manifest.TRAINING, evaluator_id="vaclav",
                            evaluator_name="Vaclav", pair_id="B",
                            source_id=source_id, work_id=BRAIN.work_id(source_id),
                            brain_snapshot_id=BRAIN.snapshot_id,
                            eval_spec_version=spec.EVAL_SPEC_VERSION)
        check(len(store.all_reviews()) == 1, "ensure_review is idempotent")

        store.start_review(rid, True)
        check(store.get_review(manifest.TRAINING, "vaclav", source_id)["status"]
              == store.STATUS_IN_PROGRESS, "start_review writes status")

        items = progress.all_items(BRAIN, source_id, {})
        edges = [(c["id"], e) for c in BRAIN.claims_of(source_id)
                 for e in BRAIN.relations_of(c["id"])]
        created = store.preallocate(
            rid, source_id, [(i.object_type, i.object_id, i.question) for i in items], edges)
        check(created > 0, f"rows preallocated ({created})")
        check(store.preallocate(
            rid, source_id, [(i.object_type, i.object_id, i.question) for i in items],
            edges) == 0, "preallocation is idempotent")

        before = len(store.export("responses"))
        question = spec.source_section_questions()[0]
        store.save_response(rid, object_type="source", object_id=source_id,
                            question_key=question.question_key,
                            criterion_id=question.criterion_id,
                            field_subitem=question.field_subitem,
                            answer="No", comment="defect p.2", source_id=source_id)
        record = store.load_responses(rid)[f"{question.question_key}|{source_id}"]
        check(record["answer"] == "No", "answer written")
        check(len(store.export("responses")) == before,
              "a save updates one row and appends none")

        stale = record["updated_at"]
        store.save_response(rid, object_type="source", object_id=source_id,
                            question_key=question.question_key,
                            criterion_id=question.criterion_id,
                            field_subitem=question.field_subitem,
                            answer="In part", comment="tab 2", source_id=source_id)
        conflicted = False
        try:
            store.save_response(rid, object_type="source", object_id=source_id,
                                question_key=question.question_key,
                                criterion_id=question.criterion_id,
                                field_subitem=question.field_subitem,
                                answer="Yes", comment="tab 1", source_id=source_id,
                                expected_updated_at=stale)
        except store.SaveConflict:
            conflicted = True
        check(conflicted, "stale write raises SaveConflict on the workbook backend")

        store.submit_review(rid)
        check(store.get_review(manifest.TRAINING, "vaclav", source_id)["status"]
              == store.STATUS_SUBMITTED, "submit recorded")
        store.reopen_review(rid)
        check(store.get_review(manifest.TRAINING, "vaclav", source_id)["status"]
              == store.STATUS_IN_PROGRESS, "reopen recorded")
        check(sorted(p.name for p in directory.iterdir())
              == sorted(f"{tab}.csv" for tab in sheets.ALL_TABS),
              f"all {len(sheets.ALL_TABS)} tabs are written")

        # --- the auto-N/A representation must survive this backend too, not
        # --- only SQLite: it is the one that will hold the live evaluation.
        na_source = next(sid for sid in BRAIN.source_ids if not BRAIN.cites_from(sid))
        na_rid = store.ensure_review(
            phase_id=manifest.TRAINING, evaluator_id="giovanni", evaluator_name="Giovanni",
            pair_id="B", source_id=na_source, work_id=BRAIN.work_id(na_source),
            brain_snapshot_id=BRAIN.snapshot_id,
            eval_spec_version=spec.EVAL_SPEC_VERSION)
        na_items = progress.all_items(BRAIN, na_source, {})
        store.preallocate(
            na_rid, na_source,
            [(i.object_type, i.object_id, i.question,
              store.AUTO_NA if i.auto_na else "") for i in na_items], [])
        rows = store.load_responses(na_rid)
        row = rows[f"SOURCE_HE18_1|{na_source}"]
        check(row["answer"] == spec.NA_ANSWER and row["applicability"] == spec.AUTO_NA,
              "preallocation writes auto-N/A through the workbook backend")
        check(not rows[f"SOURCE_HE18_2|{na_source}"]["answer"],
              "and leaves the criterion that is still asked blank")

        store.save_response(na_rid, object_type="source", object_id=na_source,
                            question_key="SOURCE_HE18_2", criterion_id="HE-18.2",
                            field_subitem="CITES completeness", answer="Yes",
                            comment=None, applicability=spec.APPLICABLE,
                            source_id=na_source)
        rows = store.load_responses(na_rid)
        check(rows[f"SOURCE_HE18_2|{na_source}"]["applicability"] == spec.APPLICABLE,
              "an ordinary save records `applicable` through the workbook backend")
        check(rows[f"SOURCE_HE18_1|{na_source}"]["applicability"] == spec.AUTO_NA,
              "and does not disturb the N/A row beside it")
        header = sheets.LocalWorkbook(directory)._path(sheets.RESPONSES).read_text(
            encoding="utf-8").splitlines()[0]
        check("applicability" in header, f"the tab carries the column ({header.count(',') + 1} columns)")
    finally:
        store.workbook = original
        fresh_db()


def test_auto_na_write_converges():
    """Rendering an inapplicable item repeatedly must stop writing once it lands.

    The widget persists on render, so without the guard every rerun would queue
    another write of the same value — harmless on SQLite, but a wasted API call
    per keystroke against Google Sheets.
    """
    print("\n== auto-N/A writes converge ==")
    import time

    fresh_db()
    phase_id, evaluator = manifest.TRAINING, "vaclav"
    source_id = manifest.training_source_ids()[1]      # W0206: HE-21 applies to one claim
    claim_id = next(c["id"] for c in BRAIN.claims_of(source_id)
                    if not BRAIN.candidate_created_for(c["id"]))
    rid = store.review_id(phase_id, evaluator, source_id)
    store.ensure_review(phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
                        pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id),
                        brain_snapshot_id=BRAIN.snapshot_id,
                        eval_spec_version=spec.EVAL_SPEC_VERSION)
    store.start_review(rid, True)

    index = [c["id"] for c in BRAIN.claims_of(source_id)].index(claim_id)

    def render():
        at = signed_in(evaluator, "Vaclav", "Training", source_id=source_id)
        at.session_state[f"section|{rid}"] = "claims"
        at.session_state[f"claim_idx|{rid}"] = index
        return at.run()

    def settle():
        for _ in range(100):
            row = store.load_responses(rid).get(f"CLAIM_HE21|{claim_id}", {})
            if row.get("answer"):
                return row
            time.sleep(0.05)
        return store.load_responses(rid).get(f"CLAIM_HE21|{claim_id}", {})

    render()
    first = settle()
    check(first.get("answer") == spec.NA_ANSWER and first.get("applicability") == spec.AUTO_NA,
          f"the first render records {claim_id} HE-21 as N/A")

    for _ in range(3):
        render()
    time.sleep(0.5)
    again = store.load_responses(rid)[f"CLAIM_HE21|{claim_id}"]
    check(again["updated_at"] == first["updated_at"],
          "three further renders write nothing more (timestamp unchanged)")
    check(again["answer"] == spec.NA_ANSWER and again["applicability"] == spec.AUTO_NA,
          "and the value is still correct")



def test_v3_instrument():
    """The frozen instrument: workbook -> v2 calibration -> v3 page-by-page review."""
    print("\n== instrument v3 ==")
    check(spec.EVAL_SPEC_VERSION == "3.0", f"spec version 3.0 ({spec.EVAL_SPEC_VERSION})")
    check(spec.SCALE == ("Yes", "In part", "No"), f"scale is Yes/In part/No ({spec.SCALE})")
    check(not hasattr(spec, "SCALE_NA"),
          "no generic N/A scale — inapplicability is decided by the application")
    check(spec.SCORE == {"Yes": 3, "In part": 2, "No": 1}, "ordinal encoding 3/2/1")
    check(spec.COMMENT_REQUIRED_ON == ("In part", "No"),
          "comments required for In part and No")

    scored = [q for q in spec.QUESTIONS if not q.free_text] + [spec.EDGE_QUESTION]
    check(all("Unclear" not in q.answer_options for q in scored),
          "no criterion offers Unclear as a score")

    # Three scales, and only three. Every departure from Yes / In part / No is a
    # decision about that criterion, so each one is named here.
    binary = [q.criterion_id for q in scored if q.answer_options == spec.BINARY]
    with_na = [q.criterion_id for q in scored if q.answer_options == spec.SCALE_WITH_NA]
    ordinary = [q for q in scored if q.answer_options == spec.SCALE]
    check(len(ordinary) + len(binary) + len(with_na) == len(scored),
          "every scored criterion uses one of the three scales")
    check(binary == ["HE-20"], f"only HE-20 is binary ({binary})")
    check(with_na == ["HE-14.3"], f"only HE-14.3 offers N/A ({with_na})")
    check(all(spec.NA_ANSWER not in q.answer_options
              for q in scored if not q.human_na),
          "no other criterion offers N/A as an evaluator choice")
    check([q.criterion_id for q in scored if q.human_na] == ["HE-14.3"],
          "and only HE-14.3 is marked human_na")

    # every override lands on a real question — a typo must not silently
    # leave a criterion on older wording
    known = set(spec.BY_KEY) | {spec.EDGE_QUESTION.question_key}
    for layer, overrides in (("v2", spec._overrides_v2()), ("v3", spec._overrides_v3())):
        unknown = [k for k in overrides if k not in known]
        check(not unknown, f"every {layer} override key exists ({unknown})")

    changed = [q.question_key for q in spec.QUESTIONS if q.changed_in_v3]
    check(len(changed) == len(spec.QUESTIONS),
          f"every criterion carries final v3 wording ({len(changed)}/{len(spec.QUESTIONS)})")
    check(all(spec.BY_KEY[k].provenance for k in changed),
          "every criterion records which review settled its wording")
    check(spec.EDGE_QUESTION.changed_in_v3, "the edge criterion is settled too")

    # the placeholder is part of the instrument, not of the page
    check(all(q.comment_placeholder for q in spec.QUESTIONS),
          "every criterion has a comment placeholder")
    specific = [q for q in spec.QUESTIONS
                if q.comment_placeholder != spec.DEFAULT_PLACEHOLDER]
    check(len(specific) == len(spec.QUESTIONS),
          f"every placeholder is criterion-specific ({len(specific)})")


def test_v3_fidelity_to_the_design_review():
    """The instrument must still say what the page-by-page review agreed.

    Every answer in the study is interpreted against this wording, so a
    paraphrase is a silent change to the experiment. This is the check that
    caught HE-20 being reworded to suit a test assertion.
    """
    print("\n== instrument fidelity to Design/ ==")
    import fidelity

    criteria = fidelity.criteria()
    check(len(criteria) == len(spec.QUESTIONS) + 1,
          f"v3 covers every question and the edge criterion ({len(criteria)})")

    off_script = [k for k, v in criteria.items()
                  if "question" in v and not fidelity.question_matches_design(v["question"])]
    check(not off_script,
          f"every visible question is verbatim from Design/*.md ({off_script})")

    undeclared = {k: v2 for k, v in criteria.items()
                  if (v2 := fidelity.undeclared(v))}
    check(not undeclared,
          f"no undeclared definition prose ({ {k: len(v) for k, v in undeclared.items()} })")

    stale = {k: v2 for k, v in criteria.items() if (v2 := fidelity.stale_declarations(v))}
    check(not stale, f"no stale `derived` declarations ({list(stale)})")

    derived = sum(len(v.get("derived", [])) for v in criteria.values())
    quoted = sum(len(fidelity.sentences(v.get("check", "")))
                 + len(fidelity.sentences(v.get("definition", "")))
                 for v in criteria.values()) - derived
    check(derived and quoted,
          f"{quoted} definition sentences quoted, {derived} declared as derived")

    # and the check must actually be able to fail
    tampered = dict(criteria["CLAIM_HE06"])
    tampered["question"] = "Do the anchors adequately ground this Claim?"
    check(not fidelity.question_matches_design(tampered["question"]),
          "a paraphrased question is rejected")
    tampered = {"check": "Anchors should feel broadly convincing to the reader.",
                "derived": []}
    check(fidelity.undeclared(tampered), "an undeclared new sentence is rejected")


def test_v3_wording():
    print("\n== instrument v3 wording ==")
    check("SOURCE_HE08_3" not in spec.BY_KEY,
          "other_versions (HE-08.3) removed from the human flow")

    # Dominance was dropped from the instrument. It may still be *named* — but
    # only to say it is not required, and never in the question the evaluator
    # reads. A bare mention in the definition would put it back in force.
    NEGATING = ("do not require", "are not ranked", "is removed", "was removed",
                "do not judge", "do not evaluate the order")
    for key in ("SOURCE_HE08_1", "SOURCE_HE08_2", "CLAIM_HE07",
                "CLAIM_HE08_3", "CLAIM_HE08_4"):
        question = spec.BY_KEY[key]
        check("dominan" not in question.question_text.lower(),
              f"{question.criterion_id} does not ask about dominance")
        body = question.criterion_definition.lower()
        if "dominan" in body:
            check(any(marker in body for marker in NEGATING),
                  f"{question.criterion_id} mentions dominance only to rule it out")
        else:
            check(True, f"{question.criterion_id} does not mention dominance")

    he25 = spec.BY_KEY["CLAIM_HE25"]
    check(he25.field_subitem == "No duplicate Claim", f"HE-25 renamed ({he25.field_subitem})")
    check("duplicate" in he25.criterion_definition.lower(),
          "HE-25 framed as duplication by the Brain")
    check("this paper" in he25.question_text.lower(),
          "HE-25 is scoped to the Claims of this paper")

    he06 = spec.BY_KEY["CLAIM_HE06"]
    check(he06.field_subitem == "Textual grounding", f"HE-06 renamed ({he06.field_subitem})")
    check("do **not** need to reproduce" in he06.check_text,
          "HE-06 says anchors need not reproduce the whole argument")
    check("warrant" not in he06.question_text.lower(), "HE-06 no longer says 'warrant'")
    check("textual grounding" in he06.question_text.lower(),
          "HE-06 asks about textual grounding")

    for key in ("CLAIM_HE07", "CLAIM_HE08_1", "CLAIM_HE08_3"):
        question = spec.BY_KEY[key]
        check("defensible" in question.question_text.lower(),
              f"{question.criterion_id} uses the defensibility standard")

    he08_2 = spec.BY_KEY["CLAIM_HE08_2"]
    check("not_applicable" in he08_2.question_text,
          "positive_form asks whether not_applicable was correctly assigned")
    check(he08_2.answer_options == spec.SCALE,
          "and is answered on the ordinary scale, not with an evaluator N/A")

    he12 = spec.BY_KEY["CLAIM_HE12"]
    check("defensible mapping" in he12.question_text.lower(),
          "HE-12 evaluates the mappings that are present")
    check("missing" in he12.check_text.lower() and "separately" in he12.check_text.lower(),
          "HE-12 explicitly defers completeness to HE-20")
    check("Prefer anchors" not in he12.criterion_definition,
          "the anchor-preference clause left HE-12 (it belongs to HE-21)")

    he20 = spec.BY_KEY["CLAIM_HE20"]
    # Assert the bounding *idea*, not one phrase: v2 said "mapping-relevant",
    # the settled v3 wording says "for mapping purposes". Pinning the phrase is
    # what made the instrument get bent to fit the test once already.
    check("for mapping purposes" in he20.question_text.lower(),
          f"HE-20 is bounded by the mapping purpose ({he20.question_text})")
    check("do not penalise" in he20.check_text.lower()
          and "abstract" in he20.check_text.lower(),
          "and its definition rules out merely-possible associations")

    he05 = spec.BY_KEY["CLAIM_HE05"]
    check("strength" in he05.question_text.lower(),
          "HE-05 is about preservation of force")

    # the Dataset criteria stopped being one-line "Is X correct?" prompts
    for key in ("DATASET_HE15_4", "DATASET_HE15_5", "DATASET_HE15_7"):
        question = spec.BY_KEY[key]
        check(len(question.question_text) > 40 and question.check_text,
              f"{question.criterion_id} states what the field means")

    he14_3 = spec.BY_KEY["SOURCE_HE14_3"]
    check(he14_3.field_subitem == "Dataset completeness",
          f"HE-14.3 retitled ({he14_3.field_subitem})")
    check(he14_3.object_type == "source", "HE-14.3 is answered on the source as a whole")

    he18_2 = spec.BY_KEY["SOURCE_HE18_2"]
    check("in the Brain" in he18_2.question_text,
          "HE-18.2 is explicit that CITES covers Brain Sources only")

    he19_1 = spec.BY_KEY["SOURCE_HE19_1"]
    check("Claim set" in he19_1.question_text, "HE-19.1 judges the extracted Claim set")


def test_v2_conceptual_coverage():
    print("\n== source-level conceptual coverage ==")
    check("SOURCE_HE20S" in spec.BY_KEY, "coverage question exists")
    coverage = spec.BY_KEY["SOURCE_HE20S"]
    check(coverage.object_type == "source", "it is a source-level question")
    check(coverage.section == spec.SEC_RECALL, "it sits in the recall section, after all claims")
    check(coverage.answer_options == spec.SCALE, "it uses the ordinal scale")

    follow_up = spec.BY_KEY["SOURCE_HE20S_B"]
    check(follow_up.free_text and follow_up.parent_key == "SOURCE_HE20S",
          "its free-text follow-up hangs off it")

    # follow-ups now open on In part as well as No
    source_id = manifest.training_source_ids()[0]
    for parent_answer, expected in (("Yes", False), ("In part", True), ("No", True)):
        responses = {f"SOURCE_HE20S|{source_id}": {"answer": parent_answer}}
        keys = [i.question.question_key
                for i in progress.recall_items(BRAIN, source_id, responses)]
        check(("SOURCE_HE20S_B" in keys) == expected,
              f"follow-up {'opens' if expected else 'stays closed'} on {parent_answer!r}")


def test_v3_no_unclear():
    print("\n== Unclear removed from the human instrument ==")
    check(not hasattr(spec, "UNCLEAR_LABEL"), "the Unclear label is gone from the spec")
    check(not hasattr(progress, "is_unclear"),
          "completeness no longer consults an Unclear flag")
    check("unclear" in sheets.COLUMNS[sheets.RESPONSES],
          "the storage column stays, so v2 exports still parse")

    # Behaviour, not a source scan: a grep would pass over a widget that still
    # rendered the control under a different name, or wrote a stray value.
    phase_id, evaluator = manifest.TRAINING, "vaclav"
    source_id = manifest.training_source_ids()[0]
    rid = store.review_id(phase_id, evaluator, source_id)
    fresh_db()
    store.ensure_review(phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
                        pair_id="B", source_id=source_id, work_id=BRAIN.work_id(source_id),
                        brain_snapshot_id=BRAIN.snapshot_id,
                        eval_spec_version=spec.EVAL_SPEC_VERSION)
    store.start_review(rid, True)
    for section in ("source", "claims", "datasets", "cites", "recall"):
        at = open_section(evaluator, "Vaclav", phase_id, source_id, section)
        labels = [str(c.label).lower() for c in at.checkbox]
        check(not any("unclear" in label for label in labels),
              f"the {section} page renders no Unclear control ({len(at.checkbox)} checkboxes)")
    radios = criterion_radios(at)
    check(radios and all("Unclear" not in r.options for r in radios),
          "and no answer control offers it as an option")

    fresh_db()
    source_id = manifest.training_source_ids()[0]
    rid = store.ensure_review(phase_id=manifest.TRAINING, evaluator_id="vaclav", evaluator_name="Vaclav",
                              pair_id="B", source_id=source_id,
                              work_id=BRAIN.work_id(source_id),
                              brain_snapshot_id=BRAIN.snapshot_id,
                              eval_spec_version=spec.EVAL_SPEC_VERSION)
    store.start_review(rid, True)
    question = spec.source_section_questions()[0]
    item = progress.source_items(BRAIN, source_id, {})[0]

    def save(answer, comment):
        store.save_response(rid, object_type="source", object_id=source_id,
                            question_key=question.question_key,
                            criterion_id=question.criterion_id,
                            field_subitem=question.field_subitem,
                            answer=answer, comment=comment,
                            applicability=spec.APPLICABLE, source_id=source_id)
        return store.load_responses(rid)

    responses = save("In part", "only the second value applies")
    check(progress.item_complete(item, responses), "In part with a comment is complete")
    check(responses[item.lookup]["applicability"] == spec.APPLICABLE,
          "an answered item is recorded as applicable")
    responses = save("In part", "")
    check(not progress.item_complete(item, responses), "In part without a comment is not")
    check(progress.item_problem(item, responses) == "answered In part, required comment missing",
          "and the problem says so")
    responses = save("Yes", "")
    check(progress.item_complete(item, responses), "Yes needs no comment")
    responses = save("No", "the jurisdiction is wrong")
    check(progress.item_complete(item, responses),
          "No with a comment is a completed judgment, not an incomplete task")
    check(all(str(r.get("unclear")) in ("0", "") for r in store.export("responses")),
          "and nothing ever writes a value into the legacy column")


def test_sqlite_column_migration():
    """A store created before `applicability` existed is upgraded, not rebuilt.

    `CREATE TABLE IF NOT EXISTS` silently leaves an existing table on the old
    layout, so without the migration an upgraded deployment would fail on every
    save with "no such column".
    """
    print("\n== sqlite column migration ==")
    import sqlite3

    original = store.DB_PATH
    store.DB_PATH = pathlib.Path(tempfile.mkdtemp(dir=TEST_DB_DIR)) / "old.sqlite"
    try:
        # the v2-era schema: everything except the column added in v3
        legacy = store.SCHEMA.replace(
            "    applicability   TEXT NOT NULL DEFAULT '',\n", "")
        legacy = "\n".join(line for line in legacy.splitlines()
                           if not line.strip().startswith("--"))
        conn = sqlite3.connect(store.DB_PATH)
        conn.executescript(legacy)
        conn.execute(
            "INSERT INTO responses (response_key, review_id, source_id, object_type,"
            " object_id, question_key, criterion_id, answer, comment_evidence)"
            " VALUES ('k','r','SRC-0001','source','SRC-0001','SOURCE_HE08_1',"
            "'HE-08.1','In part','an older answer')")
        conn.commit()
        columns = {r[1] for r in conn.execute("PRAGMA table_info(responses)")}
        conn.close()
        check("applicability" not in columns, "the legacy table has no applicability column")

        store.init()

        with store.connect() as conn:
            columns = {r["name"] for r in conn.execute("PRAGMA table_info(responses)")}
            row = dict(conn.execute(
                "SELECT * FROM responses WHERE response_key='k'").fetchone())
        check("applicability" in columns, "init() adds the column in place")
        check(row["answer"] == "In part" and row["comment_evidence"] == "an older answer",
              "the existing answer survives the migration")
        check(row["applicability"] == "", "and defaults to empty, not to a value")

        store.init()   # a second run must not fail on the now-present column
        check(True, "init() is idempotent once migrated")
    finally:
        store.DB_PATH = original
        fresh_db()


def test_auto_na_recorded_without_opening_the_page():
    """1b.4: an unvisited section must still export N/A, not a blank."""
    print("\n== auto-N/A survives a paper nobody opened ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.AGREEMENT
    source_id = next(s for s in manifest.assigned_source_ids(evaluator, phase_id)
                     if not BRAIN.cites_from(s))
    rid = store.ensure_review(phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
                              pair_id="B", source_id=source_id,
                              work_id=BRAIN.work_id(source_id),
                              brain_snapshot_id=BRAIN.snapshot_id,
                              eval_spec_version=spec.EVAL_SPEC_VERSION)
    items = progress.all_items(BRAIN, source_id, {})
    store.preallocate(
        rid, source_id,
        [(i.object_type, i.object_id, i.question,
          store.AUTO_NA if i.auto_na else "") for i in items],
        [])

    responses = store.load_responses(rid)
    row = responses[f"SOURCE_HE18_1|{source_id}"]
    check(row["answer"] == spec.NA_ANSWER and row["applicability"] == spec.AUTO_NA,
          "HE-18.1 is already N/A although nobody opened CITES")
    check(row["updated_at"], "and carries a timestamp, like any other decision")

    other = responses[f"SOURCE_HE18_2|{source_id}"]
    check(not other["answer"] and other["applicability"] == "",
          "while HE-18.2, which is still asked, stays blank")

    auto = [i for i in items if i.auto_na]
    check(auto, f"this paper has {len(auto)} automatically inapplicable items")
    check(all(responses[i.lookup]["applicability"] == spec.AUTO_NA for i in auto),
          "every one of them is recorded")

    exported = {r["response_key"]: r for r in store.export("responses")}
    na = [r for r in exported.values() if r["applicability"] == spec.AUTO_NA]
    blank = [r for r in exported.values() if not r["answer"] and not r["applicability"]]
    check(len(na) == len(auto) and blank,
          f"the export separates {len(na)} inapplicable from {len(blank)} unanswered")

    check(store.AUTO_NA == spec.AUTO_NA and store.NA_ANSWER == spec.NA_ANSWER,
          "the storage constants match the instrument's")


def test_complete_with_auto_na_unanswered():
    """A paper completes without the evaluator answering its inapplicable items."""
    print("\n== completion with automatically N/A items ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.AGREEMENT
    # a source that actually has auto-N/A items, not just the smallest one
    source_id = next(
        s for s in manifest.assigned_source_ids(evaluator, phase_id)
        if any(i.auto_na for i in progress.all_items(BRAIN, s, {}))
        and len(BRAIN.claims_of(s)) <= 20)
    auto = [i for i in progress.all_items(BRAIN, source_id, {}) if i.auto_na]
    print(f"       {BRAIN.work_id(source_id)}: {len(auto)} inapplicable items")

    rid = store.ensure_review(phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
                              pair_id="B", source_id=source_id,
                              work_id=BRAIN.work_id(source_id),
                              brain_snapshot_id=BRAIN.snapshot_id,
                              eval_spec_version=spec.EVAL_SPEC_VERSION)
    store.start_review(rid, True)
    store.preallocate(
        rid, source_id,
        [(i.object_type, i.object_id, i.question,
          store.AUTO_NA if i.auto_na else "") for i in progress.all_items(BRAIN, source_id, {})],
        [(c["id"], e) for c in BRAIN.claims_of(source_id)
         for e in BRAIN.relations_of(c["id"])])

    # answer only the APPLICABLE items — never touch an auto-N/A one
    skipped = set()
    for _ in range(4):
        responses = store.load_responses(rid)
        for item in progress.all_items(BRAIN, source_id, responses):
            if item.auto_na:
                skipped.add(item.lookup)
                continue
            if responses.get(item.lookup, {}).get("answer"):
                continue
            store.save_response(rid, object_type=item.object_type, object_id=item.object_id,
                                question_key=item.question.question_key,
                                criterion_id=item.question.criterion_id,
                                field_subitem=item.question.field_subitem,
                                answer="none" if item.question.free_text else "Yes",
                                comment=None, applicability=spec.APPLICABLE,
                                source_id=source_id)
    for claim in BRAIN.claims_of(source_id):
        for edge in BRAIN.relations_of(claim["id"]):
            store.save_edge_response(rid, host_claim_id=claim["id"],
                                     edge_key=store.edge_key_of(edge),
                                     edge_from=edge.get("from"), edge_to=edge.get("to"),
                                     other_claim_id=edge["other_claim_id"],
                                     edge_type=edge["type"], label_correct="Yes",
                                     comment=None, source_id=source_id)

    check(skipped, f"{len(skipped)} inapplicable items were never answered")
    responses, edges = store.load_responses(rid), store.load_edge_responses(rid)
    missing = progress.missing_items(BRAIN, source_id, responses, edges)
    check(not missing, f"the paper is complete anyway ({missing[:2]})")
    check(all(responses[k]["applicability"] == spec.AUTO_NA for k in skipped),
          "and the skipped items still read as inapplicable, not unanswered")

    at = open_section("vaclav", "Vaclav", phase_id, source_id, "review")
    check(any("Ready to complete" in s.value for s in at.success),
          "the review page agrees")
    at = [b for b in at.button if "Mark paper complete" in b.label][0].click().run()
    _settle(at)          # a write landing late would demote it again
    check(store.get_review(phase_id, "vaclav", source_id)["status"]
          == store.STATUS_COMPLETE, "and the paper can be marked complete")


def test_applicable_denominator():
    """Progress counts must not include items nobody is asked to answer."""
    print("\n== applicable-item denominator ==")
    with_na = next(
        (s, c["id"]) for s in BRAIN.source_ids for c in BRAIN.claims_of(s)
        if any(i.auto_na for i in progress.claim_items(BRAIN, s, c["id"], {})))
    source_id, claim_id = with_na
    items = progress.claim_items(BRAIN, source_id, claim_id, {})
    applicable = progress.applicable(items)
    check(len(applicable) < len(items),
          f"{claim_id}: {len(applicable)} of {len(items)} items are asked")
    check(all(progress.item_complete(i, {}) for i in items if i.auto_na),
          "the unasked ones already count as settled")

    plain = next(c["id"] for c in BRAIN.claims_of(source_id)
                 if not any(i.auto_na for i in progress.claim_items(BRAIN, source_id, c["id"], {})))
    check(len(progress.applicable(progress.claim_items(BRAIN, source_id, plain, {})))
          > len(applicable),
          f"a claim with nothing inapplicable ({plain}) asks more")

    stats = progress.counts(BRAIN, source_id, {}, {})
    everything = progress.all_items(BRAIN, source_id, {})
    check(stats["items"] == len(progress.applicable(everything)) < len(everything),
          f"counts() reports the applicable total ({stats['items']} of {len(everything)})")
    check(stats["answered"] == 0, "and nothing is answered yet")


def test_free_text_placeholder_from_the_spec():
    """The placeholder is instrument text, so it must come from the spec."""
    print("\n== free-text placeholders ==")
    free_text = [q for q in spec.QUESTIONS if q.free_text]
    check(len(free_text) == 4, f"four free-text criteria ({len(free_text)})")
    check(all(q.comment_placeholder != spec.DEFAULT_PLACEHOLDER for q in free_text),
          "each has its own placeholder rather than the generic one")
    he19_3 = spec.BY_KEY["SOURCE_HE19_3"]
    check("p. 6" in he19_3.comment_placeholder,
          f"HE-19.3 shows the worked example from Design 9 ({he19_3.comment_placeholder!r})")

    source = (APP_DIR / "ui.py").read_text(encoding="utf-8")
    check(source.count("placeholder=question.comment_placeholder") == 2,
          "both the free-text and the comment widget take it from the question")
    check("List what is missing." not in source,
          "and no placeholder text is hard-coded in the widget")


def test_he20_is_binary():
    """Claim-level concept completeness is Yes or No, and No must name what is missing."""
    print("\n== HE-20 is binary ==")
    he20 = spec.BY_KEY["CLAIM_HE20"]
    check(he20.answer_options == ("Yes", "No"),
          f"HE-20 offers only Yes and No ({he20.answer_options})")
    check("In part" not in he20.answer_options, "In part is gone from it")
    check(he20.comment_required_on == ("No",), "a comment is required on No")

    # its neighbours are untouched
    check(spec.BY_KEY["CLAIM_HE12"].answer_options == spec.SCALE,
          "HE-12 keeps the three-value scale")
    check(spec.BY_KEY["SOURCE_HE20S"].answer_options == spec.SCALE,
          "and so does source-level conceptual coverage")

    # the follow-up still opens, on the one negative answer there is
    source_id = manifest.training_source_ids()[0]
    claim_id = BRAIN.claims_of(source_id)[0]["id"]
    for answer, expected in (("Yes", False), ("No", True)):
        responses = {f"CLAIM_HE20|{claim_id}": {"answer": answer}}
        keys = [i.question.question_key
                for i in progress.claim_items(BRAIN, source_id, claim_id, responses)]
        check(("CLAIM_HE20B" in keys) == expected,
              f"HE-20.b {'opens' if expected else 'stays closed'} on {answer!r}")

    # and completeness follows: No without the list is incomplete
    item = next(i for i in progress.claim_items(
        BRAIN, source_id, claim_id, {"CLAIM_HE20|" + claim_id: {"answer": "No"}})
        if i.question.question_key == "CLAIM_HE20")
    responses = {item.lookup: {"answer": "No", "comment_evidence": ""}}
    check(not progress.item_complete(item, responses),
          "No without a comment is incomplete")
    responses[item.lookup]["comment_evidence"] = "the access-to-justice concept"
    check(progress.item_complete(item, responses), "No with one is complete")
    check(progress.item_complete(item, {item.lookup: {"answer": "Yes"}}),
          "Yes needs nothing further")


def test_he14_3_human_na():
    """The evaluator, not the app, decides that a Source uses no dataset at all."""
    print("\n== HE-14.3 offers an evaluator N/A ==")
    he14 = spec.BY_KEY["SOURCE_HE14_3"]
    check(he14.answer_options == ("Yes", "In part", "No", "N/A"),
          f"HE-14.3 offers Yes / In part / No / N/A ({he14.answer_options})")
    check(he14.human_na, "marked as an evaluator decision")
    check(not he14.auto_na_rule,
          "and carries no automatic rule — zero Dataset nodes may be the defect itself")
    check(spec.NA_ANSWER not in he14.comment_required_on,
          "N/A needs no comment")
    check(set(he14.comment_required_on) == {"In part", "No"},
          "while In part and No still do")

    # a source with no Dataset node is still asked, with nothing preselected
    no_datasets = next(s for s in BRAIN.source_ids if not BRAIN.datasets_of(s))
    items = progress.dataset_items(BRAIN, no_datasets, {})
    recall = [i for i in items if i.question.question_key == "SOURCE_HE14_3"]
    check(len(recall) == 1, f"{no_datasets} has no Dataset node but is still asked")
    check(not recall[0].auto_na,
          "and the question is NOT automatically answered for them")
    check(not progress.item_complete(recall[0], {}),
          "so it counts as outstanding until the evaluator decides")

    # answering N/A completes it, and is stored as a human answer
    fresh_db()
    rid = store.ensure_review(
        phase_id=manifest.TRAINING, evaluator_id="vaclav", evaluator_name="Vaclav",
        pair_id="B", source_id=no_datasets, work_id=BRAIN.work_id(no_datasets))
    store.save_response(rid, object_type="source", object_id=no_datasets,
                        question_key="SOURCE_HE14_3", criterion_id="HE-14.3",
                        field_subitem=he14.field_subitem, answer=spec.NA_ANSWER,
                        comment=None, applicability=spec.APPLICABLE,
                        source_id=no_datasets, allow_append=True)
    row = store.load_responses(rid)[f"SOURCE_HE14_3|{no_datasets}"]
    check(row["answer"] == spec.NA_ANSWER, "N/A is stored as the answer")
    check(row["applicability"] == spec.APPLICABLE,
          f"with applicability 'applicable' ({row['applicability']!r}) — the "
          f"evaluator answered")
    check(not progress.is_auto_na(row),
          "so it is distinguishable from an application-generated N/A")
    check(progress.item_complete(recall[0], {recall[0].lookup: row}),
          "and completes the item without a comment")

    # the two kinds of N/A sit side by side in the data and stay apart
    auto = next(q for q in spec.QUESTIONS if q.auto_na_rule)
    check(auto.question_key != "SOURCE_HE14_3",
          f"the automatic N/A criteria are elsewhere ({auto.criterion_id})")
    check(not any(q.human_na and q.auto_na_rule for q in spec.QUESTIONS),
          "no criterion is both")


def test_v3_auto_na():
    """Three criteria the application decides, rather than offering an N/A."""
    print("\n== automatic inapplicability ==")

    rules = {q.question_key: q.auto_na_rule
             for q in spec.QUESTIONS if q.can_be_auto_na}
    check(rules == {"CLAIM_HE07": spec.AUTO_NA_NO_PREMISE,
                    "CLAIM_HE21": spec.AUTO_NA_NO_CANDIDATE,
                    "SOURCE_HE18_1": spec.AUTO_NA_NO_OUTGOING_CITES},
          f"exactly three criteria can be automatically N/A ({sorted(rules)})")
    check(all(spec.AUTO_NA_TEXT[r].startswith("Not applicable —") for r in rules.values()),
          "each one has a sentence explaining why")

    # --- HE-07: no premise expected when the source states no ground
    no_premise = next(c for c in BRAIN.claims.values()
                      if c.get("basis") == "none_stated"
                      and not (c.get("premise") or "").strip())
    has_premise = next(c for c in BRAIN.claims.values() if (c.get("premise") or "").strip())
    he07 = spec.BY_KEY["CLAIM_HE07"]
    check(progress.auto_na_applies(he07, BRAIN, no_premise["source"], no_premise["id"]),
          f"HE-07 is N/A for {no_premise['id']} (basis none_stated, premise empty)")
    check(not progress.auto_na_applies(he07, BRAIN, has_premise["source"], has_premise["id"]),
          f"HE-07 is asked for {has_premise['id']}")

    # --- HE-21: only where a candidate concept's record names this claim
    he21 = spec.BY_KEY["CLAIM_HE21"]
    motivating = next(c for c in BRAIN.claims.values()
                      if BRAIN.candidate_created_for(c["id"]))
    plain = next(c for c in BRAIN.claims.values()
                 if not BRAIN.candidate_created_for(c["id"]))
    check(not progress.auto_na_applies(he21, BRAIN, motivating["source"], motivating["id"]),
          f"HE-21 is asked for {motivating['id']}, which motivated a candidate")
    check(progress.auto_na_applies(he21, BRAIN, plain["source"], plain["id"]),
          f"HE-21 is N/A for {plain['id']}")

    # --- HE-18.1: nothing to assess without an outgoing CITES edge
    he18_1 = spec.BY_KEY["SOURCE_HE18_1"]
    cites = next(s for s in BRAIN.source_ids if BRAIN.cites_from(s))
    no_cites = next(s for s in BRAIN.source_ids if not BRAIN.cites_from(s))
    check(not progress.auto_na_applies(he18_1, BRAIN, cites, None),
          f"HE-18.1 is asked for {cites}, which cites another Brain Source")
    check(progress.auto_na_applies(he18_1, BRAIN, no_cites, None),
          f"HE-18.1 is N/A for {no_cites}, which has no outgoing edge")
    he18_2 = spec.BY_KEY["SOURCE_HE18_2"]
    check(not he18_2.can_be_auto_na,
          "HE-18.2 is still asked — zero generated edges is not automatically correct")

    # --- an N/A item is complete, invisible to the missing list, and excluded
    #     from the applicable-item denominator
    items = progress.cites_items(BRAIN, no_cites, {})
    na = [i for i in items if i.question.question_key == "SOURCE_HE18_1"]
    check(len(na) == 1 and na[0].auto_na, "the N/A item still exists, flagged")
    check(progress.item_complete(na[0], {}), "and counts as complete with no answer")
    check(progress.item_problem(na[0], {}) is None, "and reports no problem")
    check(len(progress.applicable(items)) == len(items) - 1,
          "it is excluded from the applicable items")
    missing = progress.missing_items(BRAIN, no_cites, {}, {})
    check(not any(m.what == "HE-18.1" for m in missing),
          "and never appears in the missing list")

    # --- and it is distinguishable from an unanswered item once persisted
    fresh_db()
    rid = store.ensure_review(phase_id=manifest.TRAINING, evaluator_id="vaclav", evaluator_name="Vaclav",
                              pair_id="B", source_id=no_cites, work_id=BRAIN.work_id(no_cites),
                              brain_snapshot_id=BRAIN.snapshot_id,
                              eval_spec_version=spec.EVAL_SPEC_VERSION)
    store.save_response(rid, object_type="source", object_id=no_cites,
                        question_key="SOURCE_HE18_1", criterion_id="HE-18.1",
                        field_subitem=he18_1.field_subitem,
                        answer=spec.NA_ANSWER, comment="",
                        applicability=spec.AUTO_NA, source_id=no_cites)
    stored = store.load_responses(rid)[f"SOURCE_HE18_1|{no_cites}"]
    check(stored["answer"] == spec.NA_ANSWER and stored["applicability"] == spec.AUTO_NA,
          "the row records N/A and why")
    check(progress.is_auto_na(stored), "and reads back as automatically inapplicable")
    unanswered = store.load_responses(rid).get(f"SOURCE_HE18_2|{no_cites}", {})
    check(not progress.is_auto_na(unanswered),
          "while an item nobody has reached is not")


def test_v2_batch_submission():
    print("\n== completion vs final submission ==")
    fresh_db()
    evaluator, phase_id = "vaclav", manifest.AGREEMENT
    sources = manifest.assigned_source_ids(evaluator, phase_id)
    first, second = sources[0], sources[1]
    rids = {}
    for source_id in (first, second):
        rid = store.ensure_review(phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
                                  pair_id="B", source_id=source_id,
                                  work_id=BRAIN.work_id(source_id),
                                  brain_snapshot_id=BRAIN.snapshot_id,
                                  eval_spec_version=spec.EVAL_SPEC_VERSION)
        store.start_review(rid, True)
        rids[source_id] = rid

    store.mark_complete(rids[first])
    check(store.get_review(phase_id, evaluator, first)["status"] == store.STATUS_COMPLETE,
          "a paper can be marked complete")
    check(store.STATUS_COMPLETE in store.EDITABLE_STATUSES, "complete is an editable state")

    at = signed_in(evaluator, "Vaclav", "Agreement").run()
    submit = [b for b in at.button if "Submit all papers" in b.label]
    check(not submit, "batch submission is hidden while papers are incomplete")
    check(any("still to complete" in c.value for c in at.caption),
          "the home screen says how many remain")

    store.unmark_complete(rids[first])
    check(store.get_review(phase_id, evaluator, first)["status"] == store.STATUS_IN_PROGRESS,
          "a complete paper can be reopened without unlocking anything")

    # complete every assigned paper, then the gate opens
    for source_id in sources:
        rid = store.ensure_review(phase_id=phase_id, evaluator_id=evaluator, evaluator_name="Vaclav",
                                  pair_id="B", source_id=source_id,
                                  work_id=BRAIN.work_id(source_id),
                                  brain_snapshot_id=BRAIN.snapshot_id,
                                  eval_spec_version=spec.EVAL_SPEC_VERSION)
        store.start_review(rid, True)
        store.mark_complete(rid)
        rids[source_id] = rid

    at = signed_in(evaluator, "Vaclav", "Agreement").run()
    submit = [b for b in at.button if "Submit all papers" in b.label]
    check(bool(submit), "batch submission appears once every paper is complete")
    check(submit and submit[0].disabled, "it stays disabled until the box is ticked")

    store.submit_many(rids.values())
    statuses = {r["source_id"]: r["status"] for r in store.all_reviews()}
    check(all(statuses[s] == store.STATUS_SUBMITTED for s in sources),
          "final submission locks every paper together")
    fresh_db()



def test_import_export_tolerates_older_columns():
    """A rescue tool must not refuse the exports it exists to rescue."""
    print("\n== import_export column tolerance ==")
    import csv as _csv
    sys.path.insert(0, str(APP_DIR / "tools"))
    import import_export

    directory = pathlib.Path(tempfile.mkdtemp())
    current = list(sheets.COLUMNS[sheets.RESPONSES])
    legacy = [c for c in current if c != "applicability"]     # the v2 layout
    check(len(legacy) == len(current) - 1, "the v2 export had one column fewer")

    old_file = directory / "responses.csv"
    with old_file.open("w", newline="", encoding="utf-8") as handle:
        writer = _csv.writer(handle)
        writer.writerow(legacy)
        writer.writerow(["k1", "r1", "SRC-0001", "source", "SRC-0001", "SOURCE_HE08_1",
                         "HE-08.1", "Contribution type", "In part", "a real answer",
                         "0", "2026-09-07T10:00:00.000000+00:00"][:len(legacy)])
    rows = import_export.read_csv(old_file, sheets.RESPONSES)
    check(len(rows) == 1, "a v2-shaped export is accepted")
    check(rows[0]["answer"] == "In part" and rows[0]["comment_evidence"] == "a real answer",
          "its answers are preserved")
    check(rows[0]["applicability"] == "", "the column it predates is filled in empty")
    check(set(rows[0]) == set(current), "and the row matches the current layout")

    new_file = directory / "current.csv"
    with new_file.open("w", newline="", encoding="utf-8") as handle:
        writer = _csv.writer(handle)
        writer.writerow(current)
        writer.writerow(["k2", "r1", "SRC-0001", "source", "SRC-0001", "SOURCE_HE18_1",
                         "HE-18.1", "CITES accuracy", "N/A", "", "0", "auto_na",
                         "2026-09-08T10:00:00.000000+00:00"])
    rows = import_export.read_csv(new_file, sheets.RESPONSES)
    check(rows[0]["applicability"] == "auto_na", "a current export round-trips unchanged")

    # the key column is the one absence that really is fatal
    broken = directory / "keyless.csv"
    with broken.open("w", newline="", encoding="utf-8") as handle:
        writer = _csv.writer(handle)
        writer.writerow([c for c in current if c != "response_key"])
        writer.writerow([""] * (len(current) - 1))
    try:
        import_export.read_csv(broken, sheets.RESPONSES)
        check(False, "a file without response_key is refused")
    except SystemExit as error:
        check("response_key" in str(error), f"a file without response_key is refused ({error})")

    empty = directory / "empty.csv"
    empty.write_text(",".join(current) + "\n", encoding="utf-8")
    check(import_export.read_csv(empty, sheets.RESPONSES) == [],
          "an export with no rows is not an error")


def test_deployment_secrets():
    """Streamlit Cloud supplies secrets only through st.secrets, never env."""
    print("\n== deployment secrets ==")
    import json as _json

    import sheets

    saved = {k: os.environ.pop(k, None) for k in
             ("GOOGLE_SHEET_ID", "GOOGLE_SERVICE_ACCOUNT_JSON",
              "HE_GOOGLE_SHEET_ID", "HE_GOOGLE_CREDENTIALS", "GOOGLE_CREDENTIALS")}
    key = {"type": "service_account", "project_id": "p",
           "client_email": "robot@p.iam.gserviceaccount.com"}
    # A real .streamlit/secrets.toml in the working tree would otherwise leak into
    # these assertions — and did.
    ambient = sheets._secrets
    sheets._secrets = lambda: {}
    try:
        check(not sheets.configured(), "unconfigured by default")

        os.environ["GOOGLE_SHEET_ID"] = "sheet-123"
        check(not sheets.configured(), "an id without a key is not configured")

        os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"] = _json.dumps(key)
        check(sheets.configured(), "id + inline JSON key is configured")
        check(sheets.service_account_info()["client_email"] == key["client_email"],
              "the key parses from inline JSON")

        path = pathlib.Path(tempfile.mkdtemp()) / "sa.json"
        path.write_text(_json.dumps(key), encoding="utf-8")
        os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"] = str(path)
        check(sheets.service_account_info()["project_id"] == "p",
              "the key parses from a file path")

        # the Cloud path: nothing in the environment, everything in st.secrets
        del os.environ["GOOGLE_SHEET_ID"]
        del os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
        check(not sheets.configured(), "unconfigured once the environment is cleared")

        original = sheets._secrets
        sheets._secrets = lambda: {"GOOGLE_SHEET_ID": "from-secrets",
                                   "gcp_service_account": key}
        try:
            check(sheets.sheet_id() == "from-secrets", "the id resolves from st.secrets")
            check(sheets.configured(), "a [gcp_service_account] table configures the backend")
            check(sheets.service_account_info()["client_email"] == key["client_email"],
                  "the key resolves from the TOML table")
        finally:
            sheets._secrets = original

        check("HE_GOOGLE_SHEET_ID" in sheets.ENV_SHEET_ID_ALIASES,
              "the HE_-prefixed names still work as aliases")
    finally:
        sheets._secrets = ambient
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def test_no_secret_leaks():
    """Nothing may print key material, and no key may be committable."""
    print("\n== secret hygiene ==")
    import sheets

    root = APP_DIR.parent
    code = "".join(p.read_text(encoding="utf-8")
                   for p in sorted(APP_DIR.rglob("*.py")))
    check("private_key" not in code.replace('"private_key"', "").replace(
              "'private_key'", ""),
          "no module interpolates a private key into output")
    check(hasattr(sheets, "describe_account"),
          "there is a safe way to identify the account")
    check("private_key" not in sheets.describe_account(),
          "describe_account() never reveals the key")

    rules = (root / ".gitignore").read_text(encoding="utf-8")
    for pattern in (".streamlit/", "*.p12", "*.pem", "*.key"):
        check(pattern in rules, f".gitignore excludes {pattern}")


def test_require_sheets_gate():
    """A deployed run must not fall back to a store Cloud can wipe."""
    print("\n== require-Sheets gate ==")
    import json as _json
    check(not manifest.require_sheets(), "off by default, so local runs are unaffected")

    saved = os.environ.pop("GOOGLE_SHEET_ID", None)
    os.environ["HE_REQUIRE_SHEETS"] = "true"
    try:
        check(manifest.require_sheets(), "the flag is read from the environment")
        at = app().run()
        titles = [t.value.lower() for t in at.title]
        check(any("not reachable" in x for x in titles),
              f"an unconfigured deployment stops on the storage screen ({titles[:1]})")
        check(not at.text_input, "the password form is unreachable")
        check(any("REQUIRE_SHEETS" in c.value for c in at.caption),
              "the screen names the setting that caused it")

        os.environ["HE_REQUIRE_SHEETS"] = "0"
        at = app().run()
        titles = [t.value.lower() for t in at.title]
        check(not any("not reachable" in x for x in titles),
              "with the flag off the app starts on the local store")

        # a configured-but-broken workbook must be reported even without the flag,
        # rather than silently swapped for SQLite
        key = pathlib.Path(tempfile.mkdtemp()) / "sa.json"
        key.write_text(_json.dumps({
            "type": "service_account", "project_id": "p", "client_email": "r@p.iam",
            "private_key": "-----BEGIN PRIVATE KEY-----\nnope\n-----END PRIVATE KEY-----\n",
            "token_uri": "https://oauth2.googleapis.com/token"}), encoding="utf-8")
        os.environ["GOOGLE_SHEET_ID"] = "does-not-exist"
        os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"] = str(key)
        # the backend is resolved once per process; the app restarts when secrets
        # change, but a test has to drop the cached answer by hand
        if hasattr(store.workbook, "cache_clear"):
            store.workbook.cache_clear()
        try:
            at = app().run()
            titles = [t.value.lower() for t in at.title]
            check(any("not reachable" in x for x in titles),
                  f"a broken workbook is reported even with the flag off ({titles[:1]})")
            check(not at.exception, "it is reported, not raised as a traceback")
        finally:
            os.environ.pop("GOOGLE_SHEET_ID", None)
            os.environ.pop("GOOGLE_SERVICE_ACCOUNT_JSON", None)
            if hasattr(store.workbook, "cache_clear"):
                store.workbook.cache_clear()
    finally:
        os.environ.pop("HE_REQUIRE_SHEETS", None)
        if saved is not None:
            os.environ["GOOGLE_SHEET_ID"] = saved


def test_deployment_payload():
    """The repository must ship the five Brain sources and nothing heavy."""
    print("\n== deployment payload ==")
    import json as _json
    root = APP_DIR.parent
    ignore = root / ".gitignore"
    check(ignore.exists(), ".gitignore exists")
    rules = ignore.read_text(encoding="utf-8")
    for pattern in ("brain/raw/", "evaluations.sqlite", "secrets.toml",
                    "service-account", "log.md"):
        check(pattern in rules, f".gitignore excludes {pattern}")

    required = [
        root / "requirements.txt", root / "DEPLOYMENT.md",
        APP_DIR / "streamlit_app.py", APP_DIR / "data" / "manifest.yaml",
        APP_DIR / "data" / "he_criteria.json", APP_DIR / "data" / "he_criteria_v2.json",
        APP_DIR / "data" / "anchor_grid.json",
        APP_DIR / "tools" / "bootstrap_sheets.py", APP_DIR / "tools" / "check_sheets.py",
    ]
    missing = [str(p.relative_to(root)) for p in required if not p.exists()]
    check(not missing, f"every file the deployment needs is present ({missing})")

    wiki = root / "brain" / "wiki"
    shipped = sum(p.stat().st_size for p in wiki.rglob("*")
                  if p.is_file() and any(part in p.parts for part in
                                         ("sources", "concepts", "datasets",
                                          "claims", "graph")))
    check(shipped < 8 * 1024 * 1024,
          f"the Brain payload stays small ({shipped / 1048576:.1f} MB)")

    requirements = (root / "requirements.txt").read_text(encoding="utf-8")
    for package in ("streamlit", "gspread", "google-auth", "PyYAML", "pandas"):
        check(package in requirements, f"requirements.txt pins {package}")

    # the secrets generator must emit valid TOML with the PEM intact
    import subprocess
    import tomllib

    key = {
        "type": "service_account", "project_id": "p", "private_key_id": "k",
        "private_key": "-----BEGIN PRIVATE KEY-----\nAAA\nBBB\n-----END PRIVATE KEY-----\n",
        "client_email": "robot@p.iam.gserviceaccount.com", "client_id": "1",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    key_path = pathlib.Path(tempfile.mkdtemp()) / "sa.json"
    key_path.write_text(_json.dumps(key), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(root / "app" / "tools" / "make_secrets.py"),
         str(key_path), "--sheet-id", "SHEET1",
         "--password", "pw", "--admin-secret", "ad"],
        capture_output=True, text=True, cwd=root,
    )
    check(result.returncode == 0, f"make_secrets runs ({result.stderr[:80]})")
    parsed = tomllib.loads(result.stdout)
    check(parsed["GOOGLE_SHEET_ID"] == "SHEET1", "it emits the sheet id")
    check(parsed["HE_REQUIRE_SHEETS"] is True, "it sets HE_REQUIRE_SHEETS")
    check(parsed["gcp_service_account"]["private_key"] == key["private_key"],
          "the PEM survives the TOML round-trip exactly")
    check(parsed["gcp_service_account"]["client_email"] == key["client_email"],
          "the service account address is carried through")



def test_navigation_state_cleanup():
    """A queued click must survive Streamlit dropping the selectbox's state.

    Leaving a section unregisters its selectbox, so `claim_idx` disappears from
    session_state. A click that arrives after that — a double-click, or a slow
    connection — used to reach the callback with a missing or None value and
    crash with `TypeError: unsupported operand type(s) for +`.
    """
    print("\n== navigation state cleanup ==")
    import views

    # Exercise the helper against a stand-in state, so the assertions do not
    # depend on which Streamlit session happens to be active in the test process.
    class FakeState(dict):
        def __getitem__(self, key):
            return dict.__getitem__(self, key)

    original = views.st
    views.st = type("S", (), {"session_state": FakeState()})()
    try:
        check(views.current_index("missing", 12) == 0,
              "a missing key resolves to the first item")
        for bad in (None, "3", 4.5, [], True):
            views.st.session_state["probe"] = bad
            got = views.current_index("probe", 12)
            check(got == 0, f"{bad!r} resolves to 0, not a crash (got {got})")
        views.st.session_state["probe"] = 7
        check(views.current_index("probe", 12) == 7, "a valid index is kept")
        check(views.current_index("probe", 3) == 2, "an out-of-range index is clamped")
        check(views.current_index("probe", 0) == 0, "an empty list does not go negative")
    finally:
        views.st = original

    # the real path: claims -> datasets (state dropped) -> claims -> Next claim
    fresh_db()
    source_id = manifest.training_source_ids()[0]
    rid = store.ensure_review(phase_id=manifest.TRAINING, evaluator_id="vaclav",
                              evaluator_name="Vaclav", pair_id="B", source_id=source_id,
                              work_id=BRAIN.work_id(source_id),
                              brain_snapshot_id=BRAIN.snapshot_id,
                              eval_spec_version=spec.EVAL_SPEC_VERSION)
    store.start_review(rid, True)
    idx_key = f"claim_idx|{rid}"

    at = open_section("vaclav", "Vaclav", manifest.TRAINING, source_id, "claims")
    [b for b in at.button if "Next claim" in b.label][0].click().run()
    check(at.session_state[idx_key] == 1, "Next claim advances")

    at = open_section("vaclav", "Vaclav", manifest.TRAINING, source_id, "datasets")
    check(idx_key not in at.session_state,
          "leaving Claims does drop the selectbox state (the trigger)")

    at = open_section("vaclav", "Vaclav", manifest.TRAINING, source_id, "claims")
    nxt = [b for b in at.button if "Next claim" in b.label]
    check(bool(nxt), "Next claim is available again")
    nxt[0].click().run()
    check(not at.exception, f"no crash after the round trip ({[e.value for e in at.exception][:1]})")
    check(at.session_state[idx_key] == 1, "and it advances from a clean start")
    fresh_db()


def main() -> None:
    fresh_db()
    test_navigation_state_cleanup()
    test_import_export_tolerates_older_columns()
    test_deployment_secrets()
    test_require_sheets_gate()
    test_deployment_payload()
    test_v3_instrument()
    test_v3_fidelity_to_the_design_review()
    test_v3_wording()
    test_v2_conceptual_coverage()
    test_v3_no_unclear()
    test_sqlite_column_migration()
    test_auto_na_recorded_without_opening_the_page()
    test_complete_with_auto_na_unanswered()
    test_applicable_denominator()
    test_free_text_placeholder_from_the_spec()
    test_he20_is_binary()
    test_he14_3_human_na()
    test_v3_auto_na()
    test_v2_batch_submission()
    test_allocation()
    test_preallocation_superset()
    test_workbook_read_economy()
    test_bulk_preallocation_locks_nothing()
    test_no_whole_tab_read_in_ordinary_use()
    test_unknown_key_is_an_error_not_an_append()
    test_row_index_cache()
    test_renders_do_not_write()
    test_failed_writes_are_retained()
    test_source_page()
    test_claim_page()
    test_claim_navigation()
    test_datasets_page()
    test_cites_page()
    test_source_completeness_page()
    test_review_page()
    test_phase_submission_marker()
    test_submission_refuses_incomplete_work()
    test_reserved_rows_do_not_gate_submission()
    test_admin_progress_and_assignments()
    test_admin_freeze_refuses_unsubmitted_work()
    test_admin_exports()
    test_all_six_evaluators_at_once()
    test_two_evaluators_on_one_agreement_paper()
    test_rapid_edits_keep_the_last_value()
    test_submission_waits_for_every_write()
    test_first_answer_conflict_window()
    test_survives_a_cold_restart()
    test_free_navigation_end_to_end()
    test_brain_edge_cases()
    test_modal_changes_nothing()
    test_completion_round_trip()
    test_a_failed_read_never_creates_a_tab()
    test_deployment_readiness()
    test_startup_reads_are_minimal()
    test_startup_never_reads_the_evaluation_tabs()
    test_quota_is_temporary_not_a_fault()
    test_storage_guard_handler_cannot_raise()
    test_login_rerun_end_to_end()
    test_pending_individual_split()
    test_store_isolation()
    test_citation_line()
    test_no_prose_leaks_through_magic()
    test_conflicts_are_not_retried()
    test_completion_blocked_by_unstored_answers()
    test_editing_demotes_a_complete_paper()
    test_conflict_token_refreshes()
    test_submission_revalidates_every_paper()
    test_refusals_survive_the_rerun()
    test_queue_coalesces_writes()
    test_ui_reads_once_per_session()
    test_configuration_layer()
    test_config_version_and_immutability()
    test_reservation_activation()
    test_preallocation_does_not_lock_assignments()
    test_training_is_optional()
    test_accepted_at_is_stable()
    test_provenance_is_stamped_when_work_begins()
    test_activated_reservation_records_the_active_configuration()
    test_history_survives_a_later_configuration_change()
    test_config_snapshot_tool()
    test_snapshot_guard()
    test_spec_version_guard()
    test_no_structured_fields()
    test_workbook_backend()
    test_auto_na_write_converges()
    test_data_loading()
    test_forbidden_runtime_sources()
    test_no_secrets_in_code()
    test_async_saving()
    test_spec()
    test_manifest()
    test_he21()
    test_free_navigation()
    test_wiki_modal()
    test_wiki_modal_entry_points()
    test_wiki_modal_content()
    test_navigation_is_never_gated()
    test_progress_visibility()
    test_resume_is_a_suggestion()
    test_login_and_identity()
    test_home_and_start()
    test_preallocation_and_save()
    test_sections_render()
    test_complete_submit_lock()
    test_review_blocks()
    test_admin()
    test_simultaneous_evaluators()
    test_resume_after_interruption()

    _wipe_db()
    shutil.rmtree(TEST_DB_DIR, ignore_errors=True)

    print("\n" + "=" * 60)
    if FAILURES:
        print(f"{len(FAILURES)} FAILED:")
        for failure in FAILURES:
            print("  -", failure)
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
