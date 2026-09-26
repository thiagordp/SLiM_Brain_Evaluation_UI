"""SLiM Brain — human evaluation, instrument 4.0.

    storage, round and preflight checks -> shared password -> evaluator
        -> Training | Agreement | Individual -> paper list -> paper
        -> Source · Claims · Datasets · Claim recall · Review -> phase submission

The app reads the Brain read-only and stores every answer in the round's Google
Sheets workbook. There is no other store: without a reachable, correctly
initialised workbook for the configured round, nothing starts.

Run:  streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import datetime as dt
import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import pandas as pd
import streamlit as st

import analysis
import manifest
import preflight
import progress
import sheets
import spec
import store
import ui
import views
from brain import load_brain

st.set_page_config(page_title="SLiM Brain — Human Evaluation", page_icon="📋",
                   layout="wide")


@st.cache_resource
def brain():
    return load_brain()


@st.cache_resource
def preflight_report(snapshot_id: str):
    return preflight.check(brain())


def _centred(width: int = 2):
    return st.columns([1, width, 1])[1]


# ------------------------------------------------------------------ guards
def guard_storage() -> bool:
    """The round workbook must be configured, reachable and initialised."""
    problem, transient = "", False
    try:
        store.check_ready()        # raises StorageNotConfigured without a workbook
    except Exception as error:     # shown, never swallowed or worked around
        problem = str(error) or repr(error)
        transient = isinstance(error, sheets.QuotaExceeded)
    if not problem:
        return True
    if transient:
        st.title("Google Sheets is busy")
        st.warning(problem)
        if st.button("Try again", type="primary"):
            store.forget_ready()
            st.rerun()
        return False
    st.title("The evaluation store is not available")
    st.error(problem)
    st.caption("Answers are stored only in the round's Google Sheets workbook, so the "
               "application does not start without it. See DEPLOYMENT.md: create a new "
               "workbook, set GOOGLE_SHEET_ID and the service account, and run "
               "`python app/tools/bootstrap_round.py`.")
    return False


def guard_round() -> bool:
    """The workbook must hold the configured round, instrument and Brain."""
    data = brain()
    meta = store.round_metadata()
    expected = {
        "round_id": manifest.round_id(),
        "eval_spec_version": spec.EVAL_SPEC_VERSION,
        "definitions_id": spec.definitions_id(),
        "brain_snapshot_id": data.snapshot_id,
    }
    wrong = {k: (meta.get(k, ""), v) for k, v in expected.items() if meta.get(k, "") != v}
    if not wrong:
        return True
    st.title("This workbook does not belong to this deployment")
    st.error("The workbook was initialised for a different round, instrument, "
             "definitions or Brain snapshot, so no evaluation can start against it.")
    for key, (stored, running) in wrong.items():
        st.markdown(f"- {key.replace('_', ' ')}: workbook **{stored or '(none)'}**, "
                    f"application **{running}**")
    st.caption("Point GOOGLE_SHEET_ID at this round's workbook, or bootstrap a new "
               "workbook for a new round. A workbook is never reused across rounds.")
    return False


def guard_preflight() -> bool:
    data = brain()
    report = preflight_report(data.snapshot_id)
    if report.ok:
        return True
    st.title("The evaluation is not available")
    st.error("The Brain snapshot did not pass validation, so evaluation cannot "
             "begin. Please contact the administrator.")
    with st.expander("Administrator diagnostic"):
        secret = st.text_input("Admin secret", type="password", key="preflight_admin")
        if secret and secret == manifest.admin_secret():
            for error in report.errors:
                st.markdown(f"- {error}")
            st.caption("Run `python app/tools/preflight.py` for the full report.")
    return False


# ------------------------------------------------------------------ login
def gate_password() -> bool:
    if st.session_state.get("authenticated"):
        return True
    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
    with _centred():
        st.title("SLiM Brain — Human Evaluation")
        st.caption("Restricted access for evaluators.")
        missing = manifest.missing_secrets()
        if missing:
            st.error("The application is not configured: " + ", ".join(missing)
                     + " must be set before anyone can sign in.")
            return False
        with st.container(border=True):
            with st.form("login", border=False):
                entered = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Continue", type="primary",
                                                  width="stretch")
            if submitted:
                if entered and entered == manifest.password():
                    st.session_state["authenticated"] = True
                    st.rerun()
                st.error("Incorrect password.")
    return False


def gate_identity() -> bool:
    if st.session_state.get("evaluator_id"):
        return True
    st.markdown("<div style='height:6vh'></div>", unsafe_allow_html=True)
    with _centred():
        st.title("Select evaluator")
        st.caption("Your identity determines which papers are assigned to you and "
                   "cannot be changed during this session.")
        with st.container(border=True):
            name = st.selectbox("Evaluator", sorted(manifest.evaluator_names()),
                                index=None, placeholder="Select your name")
            entry = manifest.evaluator_by_name(name) if name else None
            if entry:
                splits = manifest.splits_of(entry["evaluator_id"])
                st.markdown(f"**{entry['name']}**")
                st.caption(" · ".join(f"{manifest.PHASE_LABEL[p]}: {s}"
                                      for p, s in splits.items() if s)
                           or "No split assigned.")
            if st.button("Confirm and continue", type="primary", width="stretch",
                         disabled=entry is None):
                st.session_state["evaluator_id"] = entry["evaluator_id"]
                st.session_state["evaluator_name"] = entry["name"]
                st.rerun()
    return False


# -------------------------------------------------------------------- home
PHASE_CAPTION = {
    manifest.TRAINING: "Optional practice on the same papers for every evaluator. "
                       "It does not gate anything.",
    manifest.AGREEMENT: "You and one other evaluator assess the same papers "
                        "independently. Do not discuss them until the agreement round "
                        "is submitted.",
    manifest.INDIVIDUAL: "These papers are yours alone.",
}
PAGE_TO_PHASE = {manifest.PHASE_LABEL[p]: p for p in manifest.PHASES}
PAPER_ACTION = {store.STATUS_NOT_STARTED: "Start", store.STATUS_IN_PROGRESS: "Continue",
                store.STATUS_COMPLETE: "Review", store.STATUS_SUBMITTED: "View"}
PAPER_STATUS = {store.STATUS_NOT_STARTED: "Not started",
                store.STATUS_IN_PROGRESS: "In progress",
                store.STATUS_COMPLETE: "Complete", store.STATUS_SUBMITTED: "Submitted"}


def _rid(phase_id: str, evaluator_id: str, source_id: str) -> str:
    return store.review_id(manifest.round_id(), phase_id, evaluator_id, source_id)


def _authors(source: dict) -> str:
    authors = source.get("authors") or []
    if not authors:
        return ""
    written = authors[0]
    if len(authors) == 2:
        written += f" & {authors[1]}"
    elif len(authors) > 2:
        written += " et al."
    return written


def _stamp(value) -> str:
    try:
        return dt.datetime.fromisoformat(str(value)).strftime("%d %b %Y, %H:%M UTC")
    except ValueError:
        return str(value or "an unrecorded date")


def home(phase_id: str, evaluator_id: str) -> None:
    data = brain()
    sources = manifest.assigned_source_ids(evaluator_id, phase_id)
    st.title(manifest.PHASE_LABEL[phase_id])
    st.caption(PHASE_CAPTION[phase_id])
    if not manifest.phase_open(phase_id):
        st.warning(f"The {phase_id} phase is not open.")
        return
    if not sources:
        st.info("No papers are assigned to you in this phase.")
        return
    reviews = store.reviews_for(manifest.round_id(), evaluator_id, phase_id)
    statuses = {s: reviews.get(s, {}).get("status", store.STATUS_NOT_STARTED)
                for s in sources}
    done = sum(1 for s in sources
               if statuses[s] in (store.STATUS_COMPLETE, store.STATUS_SUBMITTED))
    st.progress(done / len(sources))
    st.caption(f"{done} of {len(sources)} papers complete. You may work in any order; "
               f"answers are saved as you go and can be revised until final submission.")
    for source_id in sources:
        source = data.source(source_id)
        status = statuses[source_id]
        claims = len(data.claims_of(source_id))
        datasets = len(data.dataset_ids_of(source_id))
        with st.container(border=True):
            head, action = st.columns([6, 1])
            head.markdown(f"**{data.label(source_id)}**")
            head.caption(f"{_authors(source)} · {source.get('year', '')} · "
                         f"paper file {data.pdf_name(source_id)}")
            head.caption(f"{claims} Claims · {datasets or 'no'} Dataset"
                         f"{'s' if datasets != 1 else ''} · {PAPER_STATUS[status]}")
            if action.button(PAPER_ACTION[status], key=f"open|{phase_id}|{source_id}",
                             width="stretch",
                             type="primary" if status == store.STATUS_NOT_STARTED
                             else "secondary"):
                st.session_state["source_id"] = source_id
                st.rerun()
    _phase_submission(phase_id, evaluator_id, sources, statuses, reviews)


def _unfinished(phase_id: str, evaluator_id: str, sources) -> list[tuple[str, int]]:
    """Papers that do not survive a fresh read of their stored answers."""
    data = brain()
    out = []
    for source_id in sources:
        rid = _rid(phase_id, evaluator_id, source_id)
        ui.forget_review(rid)
        stored = store.load_review(rid)
        missing = progress.missing_items(data, source_id, stored)
        review = store.get_review(rid) or {}
        if missing or str(review.get("pdf_read_confirmed")) not in ("1", "True", "true"):
            out.append((source_id, len(missing)))
    return out


def _phase_submission(phase_id, evaluator_id, sources, statuses, reviews) -> None:
    ui.show_held()
    st.divider()
    st.subheader(f"Final submission — {manifest.PHASE_LABEL[phase_id]}")
    round_id = manifest.round_id()
    marker = store.phase_submission(round_id, phase_id, evaluator_id)
    if marker and marker.get("status") == store.SUBMITTED:
        st.success(f"Submitted on {_stamp(marker.get('submitted_at'))}. Only the "
                   f"administrator can reopen a paper.")
        return
    outstanding = [s for s in sources if statuses[s] != store.STATUS_SUBMITTED]
    if marker and marker.get("status") == store.RETRACTED:
        st.warning("This phase was reopened by the administrator. Finish what was "
                   "reopened and submit again.")
    elif not outstanding:
        st.warning("Every paper is locked, but the submission was not recorded.")
        if st.button("Complete the submission", type="primary"):
            store.record_phase_submission(round_id, phase_id, evaluator_id,
                                          manifest.config_version())
            st.rerun()
        return
    ready = [s for s in outstanding if statuses[s] == store.STATUS_COMPLETE]
    if manifest.is_optional(phase_id):
        st.caption("This phase is optional. Submitting it, or not, affects no other "
                   "phase.")
    if len(ready) != len(outstanding):
        st.caption(f"{len(outstanding) - len(ready)} paper(s) still to complete. Final "
                   f"submission becomes available when every paper is complete.")
        return
    st.warning(f"This locks all {len(ready)} papers of this phase. After it, no answer "
               f"can be changed.")
    confirmed = st.checkbox("I have finished revising and want to submit everything.",
                            key=f"confirm_batch|{phase_id}")
    if st.button("Submit all papers", type="primary", disabled=not confirmed):
        with st.spinner("Saving your last answers…"):
            ok, pending, detail = ui.settle()
        if not ok:
            st.error(f"{pending} answer(s) are not yet stored, so nothing was "
                     f"submitted. {detail}")
            return
        with st.spinner("Checking the stored answers…"):
            incomplete = _unfinished(phase_id, evaluator_id, ready)
        if incomplete:
            ui.hold("Nothing was submitted: " + ", ".join(
                f"{s} ({n} missing)" for s, n in incomplete[:4])
                + " no longer complete when re-read. They have been reopened.")
            for source_id, _ in incomplete:
                store.unmark_complete(_rid(phase_id, evaluator_id, source_id))
            st.rerun()
        store.submit_many(reviews[s]["review_id"] for s in ready)
        store.record_phase_submission(round_id, phase_id, evaluator_id,
                                      manifest.config_version())
        st.rerun()


# ------------------------------------------------------------ paper start
TASK = """
**Assess whether the Brain faithfully represents what the Source says.** Do not
assess whether the paper itself is good, important, persuasive or legally correct.

The evaluation has five parts: the Source (context only), each Claim with its
schema fields, Concepts and Relations, each Dataset, Claim recall, and a final
Review. Answers are saved as you go.
"""


def paper_start(phase_id: str, evaluator_id: str, source_id: str, review: dict) -> None:
    data = brain()
    st.title(data.label(source_id))
    st.caption(f"{_authors(data.source(source_id))} · paper file "
               f"{data.pdf_name(source_id)}")
    st.divider()
    st.markdown(TASK)
    confirmed = st.checkbox("I confirm that I have read the full paper before starting "
                            "this evaluation.", key=f"read|{review['review_id']}")
    st.caption("The papers are distributed separately and are not available through "
               "this interface.")
    if st.button("Start evaluation", type="primary", disabled=not confirmed):
        row = manifest.assignment(phase_id, evaluator_id, source_id)
        store.start_review(
            review["review_id"], True,
            brain_snapshot_id=data.snapshot_id,
            eval_spec_version=spec.EVAL_SPEC_VERSION,
            definitions_id=spec.definitions_id(),
            config_version=manifest.config_version(),
            split_id=str(row.get("split_id") or ""),
            assignment_state=manifest.state_of(row) if row else "")
        st.rerun()


# ---------------------------------------------------------------- the paper
def paper_view(phase_id: str, evaluator_id: str, source_id: str) -> None:
    data = brain()
    rid = _rid(phase_id, evaluator_id, source_id)
    review = store.get_review(rid)
    if st.button("← All papers", key="back_to_papers"):
        st.session_state.pop("source_id", None)
        ui.close_wiki()
        st.rerun()
    if review is None:
        st.error(f"No stored review exists for {rid}. The round workbook was not "
                 f"bootstrapped with this assignment; the administrator can add it "
                 f"with `bootstrap_round.py --extend`.")
        return
    if review.get("status") == store.STATUS_NOT_STARTED:
        paper_start(phase_id, evaluator_id, source_id, review)
        return

    locked = review.get("status") == store.STATUS_SUBMITTED
    ctx = ui.Ctx(brain=data, round_id=manifest.round_id(), phase_id=phase_id,
                 evaluator_id=evaluator_id, source_id=source_id, review_id=rid,
                 data=ui.cached_review(rid), locked=locked)

    st.title(data.label(source_id))
    if locked:
        st.info("This paper has been submitted. Answers are read-only.")
    states = progress.section_states(data, source_id, ctx.data)
    key = f"section|{rid}"
    if st.session_state.get(key) not in progress.SECTION_IDS:
        st.session_state[key] = "source"
    current = st.session_state[key]

    cols = st.columns(len(progress.SECTION_IDS))
    for col, section in zip(cols, progress.SECTION_IDS):
        label = progress.SECTION_LABEL[section]
        if section == "claims":
            label += f" {progress.claims_done(data, source_id, ctx.data)}/" \
                     f"{len(data.claims_of(source_id))}"
        mark = views.MARK.get(states.get(section, ""), "")
        col.button(f"{mark} {label}".strip(), key=f"nav|{section}", width="stretch",
                   disabled=section == current,
                   on_click=views.go_to_section, args=(ctx, section))
    st.caption(views.MARK_LEGEND + " · every section can be opened at any time")
    st.divider()

    views.RENDERERS[current](ctx)
    st.divider()
    ui.render_save_status()
    ui.render_wiki_modal(ctx)
    ui.consume_scroll()


# ------------------------------------------------------------------- admin
def _set_state(key: str, state: str) -> None:
    manifest.set_assignment_state(key, state)


def _admin_progress() -> None:
    data = brain()
    st.caption("Completion only. Substantive answers are not shown during "
               "independent evaluation.")
    rows = []
    for review in store.all_reviews():
        if review.get("status") == store.STATUS_NOT_STARTED:
            rows.append({"evaluator": review["evaluator_name"],
                         "phase": review["phase_id"], "split": review["split_id"],
                         "paper": review["source_id"], "progress": "",
                         "status": review["status"]})
            continue
        stats = progress.counts(data, review["source_id"],
                                store.load_review(review["review_id"]))
        rows.append({"evaluator": review["evaluator_name"], "phase": review["phase_id"],
                     "split": review["split_id"], "paper": review["source_id"],
                     "progress": f"{stats['done']}/{stats['items']}",
                     "status": review["status"]})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def _admin_assignments() -> None:
    locked = manifest.active_assignment_keys(store.all_reviews())
    st.caption(f"Configuration version {manifest.config_version()} · "
               f"{len(locked)} assignment(s) locked by started work")
    for row in manifest.reserved():
        with st.container(border=True):
            st.markdown(f"Reserved: **{row['evaluator_id']}** · {row['phase_id']} · "
                        f"{row['source_id']}")
            st.button("Activate", key=f"activate|{row['assignment_key']}",
                      disabled=row["assignment_key"] in locked,
                      on_click=_set_state, args=(row["assignment_key"], manifest.ASSIGNED))
    rows = [{**a, "locked": a.get("assignment_key") in locked}
            for a in manifest.assignments()]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.dataframe(pd.DataFrame(manifest.evaluators()), width="stretch", hide_index=True)


def _admin_control() -> None:
    st.subheader("Phases")
    st.caption("All phases are open by default and none gates another. Closing a phase "
               "stops further work; it records nothing as submitted.")
    for phase_id in manifest.PHASES:
        is_open = manifest.phase_open(phase_id)
        row, action = st.columns([4, 1], vertical_alignment="center")
        row.markdown(f"**{manifest.PHASE_LABEL[phase_id]}** — "
                     f"{'open' if is_open else 'closed'}")
        if action.button("Close" if is_open else "Open", key=f"phase|{phase_id}"):
            manifest.set_phase(phase_id, not is_open)
            st.rerun()
    st.subheader("Reopen a submitted paper")
    submitted = [r for r in store.all_reviews() if r["status"] == store.STATUS_SUBMITTED]
    if not submitted:
        st.caption("Nothing submitted yet.")
    for review in submitted:
        row, action = st.columns([5, 1], vertical_alignment="center")
        row.write(f"{review['evaluator_name']} · {review['phase_id']} · "
                  f"{review['source_id']}")
        if action.button("Reopen", key=f"reopen|{review['review_id']}"):
            retracted = store.reopen_review(review["review_id"])
            ui.hold(f"{review['source_id']} is open again."
                    + (" The phase submission was withdrawn." if retracted else ""))
            st.rerun()


def _admin_exports() -> None:
    st.caption("Raw tabs exactly as stored, normalised tables joined with review "
               "provenance, and agreement for the agreement phase. Every table "
               "carries the round and the evaluation specification version.")
    if not st.button("Prepare exports"):
        return
    tables = analysis.export_tables()
    frames = {name: pd.DataFrame(rows) for name, rows in tables.items()}
    for name, frame in frames.items():
        st.download_button(f"{name}.csv — {len(frame)} rows",
                           frame.to_csv(index=False).encode("utf-8"),
                           file_name=f"{manifest.round_id()}_{name}.csv",
                           mime="text/csv", key=f"dl|{name}")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, frame in frames.items():
            frame.to_excel(writer, index=False, sheet_name=name[:31])
    st.download_button("All tables (XLSX)", buffer.getvalue(),
                       file_name=f"{manifest.round_id()}_evaluation_export.xlsx",
                       mime="application/vnd.openxmlformats-officedocument."
                            "spreadsheetml.sheet")


def _admin_system() -> None:
    data = brain()
    st.markdown("**Round**")
    for key, value in store.round_metadata().items():
        st.write(f"{key.replace('_', ' ')} — {value}")
    st.markdown("**Brain**")
    st.write(f"{len(data.sources)} Sources · {len(data.claims)} Claims · "
             f"{len(data.concepts)} Concepts · {len(data.datasets)} Datasets · "
             f"{len(data.claim_relations())} Claim Relations")
    report = preflight_report(data.snapshot_id)
    st.markdown("**Preflight**")
    st.write(f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    for warning in report.warnings:
        st.caption(f"• {warning}")
    st.markdown("**Configuration**")
    problems = manifest.validate(set(data.sources), reviews=store.all_reviews())
    if problems:
        for problem in problems:
            st.warning(problem)
    else:
        st.success("Configuration is consistent.")


def admin_page() -> None:
    st.title("Admin")
    if not st.session_state.get("admin_ok"):
        with st.form("admin"):
            secret = st.text_input("Admin secret", type="password")
            if st.form_submit_button("Unlock"):
                if secret and secret == manifest.admin_secret():
                    st.session_state["admin_ok"] = True
                    st.rerun()
                st.error("Wrong admin secret.")
        return
    ui.show_held()
    tabs = st.tabs(["Progress", "Assignments", "Control", "Exports", "System"])
    with tabs[0]:
        _admin_progress()
    with tabs[1]:
        _admin_assignments()
    with tabs[2]:
        _admin_control()
    with tabs[3]:
        _admin_exports()
    with tabs[4]:
        _admin_system()


# -------------------------------------------------------------------- main
def main() -> None:
    if not guard_storage():
        return
    # Preflight first: a Brain that changed on disk is reported with what is wrong
    # with it, not only as a snapshot that differs from the workbook's.
    if not guard_preflight():
        return
    if not guard_round():
        return
    if not gate_password():
        return
    if not gate_identity():
        return

    evaluator_id = st.session_state["evaluator_id"]
    st.sidebar.markdown(f"**{st.session_state['evaluator_name']}**")
    splits = manifest.splits_of(evaluator_id)
    st.sidebar.caption(" · ".join(f"{manifest.PHASE_LABEL[p]}: {s}"
                                  for p, s in splits.items() if s))
    st.sidebar.caption(f"Round {manifest.round_id()}")
    pages = [manifest.PHASE_LABEL[p] for p in manifest.PHASES]
    pages += ["Admin"] if manifest.is_admin(evaluator_id) else []
    page = st.sidebar.radio("Phase", pages, key="phase_choice")
    if st.session_state.get("_page") != page:
        st.session_state["_page"] = page
        st.session_state.pop("source_id", None)
        ui.close_wiki()
    if page == "Admin":
        admin_page()
        return
    phase_id = PAGE_TO_PHASE[page]
    source_id = st.session_state.get("source_id")
    if source_id and manifest.is_assigned(evaluator_id, phase_id, source_id):
        paper_view(phase_id, evaluator_id, source_id)
    else:
        st.session_state.pop("source_id", None)
        home(phase_id, evaluator_id)


if __name__ == "__main__":
    main()
