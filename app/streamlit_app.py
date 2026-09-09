"""HE Evaluation Interface.

    shared password -> select evaluator -> confirm (identity locked)
        -> Training | Agreement | Individual -> home -> paper -> sections
        -> review -> phase submission

Forward movement is controlled, backward movement is free, answers autosave,
and submission happens only after a complete validation pass.

The app reads the Brain read-only, reads the splitter's manifest read-only, and
carries its own versioned evaluation specification. It never shows automatic
structural (SC-) results and never shows another evaluator's answers.

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

import manifest
import progress
import sheets
import spec
import store
import ui
import views
from brain import load_brain

#: Resolved once, here, from the module `store` itself imported — not looked up
#: on a module name inside an `except` clause. Two things went wrong at once on
#: the first deployment: an older copy of this project was earlier on
#: `sys.path`, so `import sheets` inside the guard bound a `sheets` module with
#: neither `check_ready` nor `QuotaExceeded`. `store.init()` raised
#: AttributeError for the first, and evaluating `except sheets.QuotaExceeded`
#: raised AttributeError for the second — which replaced the original and hid
#: what had actually gone wrong. Binding the class at import time means a
#: mismatch is reported when the app starts, by the check below, instead of at
#: the worst possible moment.
QuotaExceeded = store.sheets.QuotaExceeded
StorageError = store.sheets.StorageError

if sheets is not store.sheets:                          # pragma: no cover
    raise ImportError(
        f"Two different `sheets` modules are loaded: {sheets.__file__} and "
        f"{store.sheets.__file__}. Another copy of this project is earlier on "
        f"sys.path; remove it before starting the app."
    )

st.set_page_config(page_title="HE Evaluation — SLiM Brain",
                   page_icon="📋", layout="wide")


@st.cache_resource
def brain():
    return load_brain()


# ------------------------------------------------------------------ login
#: A single password field does not need the whole viewport. Everything before
#: an evaluator is identified sits in one narrow centred column.
def _centred(width: int = 2):
    """A centred column roughly 500px wide on a normal screen."""
    return st.columns([1, width, 1])[1]


def gate_password() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
    with _centred():
        st.title("SLiM Brain — Human Evaluation")
        st.caption("Restricted access for evaluators.")
        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

        missing = manifest.missing_secrets()
        if missing:
            st.error(
                "The application is not configured: "
                + ", ".join(f"`{name}`" for name in missing)
                + " must be set before anyone can sign in."
            )
            st.code("\n".join(f"export {name}='…'" for name in missing), language="bash")
            return False

        with st.container(border=True):
            st.markdown("#### Enter access password")
            st.caption("Enter the shared evaluator password to continue.")
            with st.form("login", border=False):
                entered = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Continue", type="primary",
                                                  width="stretch")
            if submitted:
                if entered and entered == manifest.password():
                    st.session_state["authenticated"] = True
                    st.rerun()
                # Inline and quiet: a mistyped password is an ordinary event,
                # not an incident.
                st.error("Incorrect password. Please try again.")
    return False


def gate_identity() -> bool:
    """Name is chosen once and then locked for the session."""
    if st.session_state.get("evaluator_id"):
        return True

    st.markdown("<div style='height:6vh'></div>", unsafe_allow_html=True)
    with _centred():
        st.title("Select evaluator")
        st.caption("Select your name. Your identity determines which papers are "
                   "assigned to you, and cannot be changed during this session.")
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            # Not inside a form: the assignment panel has to appear as soon as a
            # name is picked, which is the whole point of showing it. Choosing
            # the wrong name writes into someone else's records.
            name = st.selectbox("Evaluator", sorted(manifest.evaluator_names()),
                                index=None, placeholder="Select your name")
            entry = manifest.evaluator_by_name(name) if name else None

            if entry:
                splits = manifest.splits_of(entry["evaluator_id"])
                shown = " · ".join(f"{manifest.PHASE_LABEL[phase]}: {split}"
                                   for phase, split in splits.items() if split)
                st.markdown(f"**{entry['name']}**")
                st.caption(shown or "No evaluation split assigned yet.")
                st.caption("Please confirm that you selected your own name.")

            if st.button("Confirm and continue", type="primary", width="stretch",
                         disabled=entry is None):
                st.session_state["evaluator_id"] = entry["evaluator_id"]
                st.session_state["evaluator_name"] = entry["name"]
                st.rerun()
    return False


# ------------------------------------------------------------------- home
def review_of(phase_id: str, evaluator_id: str, source_id: str) -> dict:
    data = brain()
    manifest_row = {"pair_id": manifest.pair_of(evaluator_id)}
    # Identity only. Provenance is stamped when the evaluator starts the paper,
    # because a preallocated row may have been made under a configuration that is
    # not the one the evaluation ends up being performed under.
    rid = store.ensure_review(
        phase_id=phase_id, evaluator_id=evaluator_id,
        evaluator_name=st.session_state.get("evaluator_name", ""),
        pair_id=manifest_row["pair_id"], source_id=source_id,
        work_id=data.work_id(source_id),
    )
    return store.get_review(phase_id, evaluator_id, source_id) or {"review_id": rid}


PHASE_CAPTION = {
    manifest.TRAINING:
        "Optional practice on the same two papers for everyone, to calibrate before "
        "you evaluate. Training responses are stored separately from the evaluation "
        "data, and you may leave this phase unfinished — it does not gate anything.",
    manifest.AGREEMENT:
        "You and one other evaluator assess the same papers independently. Do not "
        "discuss them until the agreement round is submitted.",
    manifest.INDIVIDUAL:
        "These papers are yours alone.",
}

PAGE_TO_PHASE = {manifest.PHASE_LABEL[p]: p for p in manifest.PHASES}

WORKING_NOTE = ("You may complete the papers in any order. Your progress is saved "
                "automatically, and you may return to revise your responses until "
                "final submission.")


def home(phase_id: str, evaluator_id: str) -> None:
    data = brain()
    sources = manifest.assigned_source_ids(evaluator_id, phase_id)
    st.title(manifest.PHASE_LABEL[phase_id])
    st.caption(PHASE_CAPTION[phase_id])
    st.caption(WORKING_NOTE)

    if not manifest.phase_open(phase_id):
        st.warning(f"The {phase_id} phase is not open yet.")
        return
    if not sources:
        st.info("No papers are assigned to you in this phase.")
        return

    reviews = store.reviews_for(evaluator_id, phase_id)
    statuses = {s: reviews.get(s, {}).get("status", store.STATUS_NOT_STARTED) for s in sources}
    done = sum(1 for s in sources
               if statuses[s] in (store.STATUS_COMPLETE, store.STATUS_SUBMITTED))
    st.progress(done / len(sources))
    st.caption(f"**{done} of {len(sources)} papers complete**")
    st.divider()

    for source_id in sources:
        _paper_card(data, phase_id, source_id, reviews.get(source_id, {}))

    _batch_submission(phase_id, evaluator_id, sources, statuses, reviews)


#: What the button offers depends on where the paper stands, so the label says
#: what pressing it will do rather than leaving the evaluator to infer it.
PAPER_ACTION = {
    store.STATUS_NOT_STARTED: "Start",
    store.STATUS_IN_PROGRESS: "Continue",
    store.STATUS_COMPLETE: "Review",
    store.STATUS_SUBMITTED: "View",
}

PAPER_STATUS = {
    store.STATUS_NOT_STARTED: "Not started",
    store.STATUS_IN_PROGRESS: "In progress",
    store.STATUS_COMPLETE: "Complete",
    store.STATUS_SUBMITTED: "Submitted",
}


def _authors(source: dict) -> str:
    """Surnames only, in the form a reader scans rather than the form the Brain stores."""
    authors = source.get("authors") or []
    if not authors:
        return ""
    written = authors[0].split(",")[0]
    if len(authors) == 2:
        written += f" & {authors[1].split(',')[0]}"
    elif len(authors) > 2:
        written += " et al."
    return written


def _venue(source: dict) -> str:
    """The venue without the extraction notes the Brain records beside it.

    `venue` carries the DOI and remarks such as "conference volume not named in
    the text" — provenance about the extraction, not part of the citation. Those
    belong in the Source wiki; the heading identifies the paper and stops.
    """
    venue = (source.get("venue") or "").strip()
    if venue.lower().startswith("unknown"):
        return ""
    for cut in (" (doi:", "; conference volume", " (not printed"):
        head, sep, _ = venue.partition(cut)
        if sep:
            venue = head
    return venue.strip(" ;,")


def _citation(source: dict) -> str:
    """One line identifying the paper: who wrote it, when, and where it appeared."""
    parts = [p for p in (_authors(source), str(source.get("year") or "")) if p]
    line = " · ".join(parts)
    venue = _venue(source)
    return f"{line} · {venue}" if venue else line


def _paper_card(data, phase_id: str, source_id: str, review: dict) -> None:
    """One paper: what it is, where it stands, and the one thing to do next."""
    status = review.get("status", store.STATUS_NOT_STARTED)
    source = data.source(source_id)

    claims = len(data.claims_of(source_id))
    datasets = len(data.datasets_of(source_id))
    metadata = (f"{claims} claim{'s' if claims != 1 else ''} · "
                + (f"{datasets} dataset{'s' if datasets != 1 else ''}"
                   if datasets else "no datasets"))

    with st.container(border=True):
        head, action = st.columns([6, 1])
        with head:
            st.markdown(f"**{data.work_id(source_id)} — {source.get('title', '')}**")
            st.caption(f"{_authors(source)} · {source.get('year', '')}")
            line = f"{metadata} · {PAPER_STATUS[status]}"
            if status == store.STATUS_IN_PROGRESS and review.get("review_id"):
                rid = review["review_id"]
                complete = progress.claims_done(
                    data, source_id,
                    store.load_responses(rid), store.load_edge_responses(rid))
                line += f" — {complete} of {claims} claims complete"
            elif status == store.STATUS_COMPLETE:
                line += " · still editable"
            elif status == store.STATUS_SUBMITTED:
                line += " · read-only"
            st.caption(line)
        with action:
            if st.button(PAPER_ACTION[status], key=f"open|{phase_id}|{source_id}",
                         width="stretch",
                         type="primary" if status == store.STATUS_NOT_STARTED else "secondary"):
                st.session_state["source_id"] = source_id
                st.rerun()


def _unfinished(sources) -> list[tuple[str, int]]:
    """Papers that do not survive a fresh read of their stored answers.

    Returns (source_id, missing count). Deliberately re-reads rather than
    trusting the recorded status: an answer may have failed to store, another
    session may have edited it, or a conditional follow-up may have become
    required after the paper was marked complete.
    """
    data = brain()
    out = []
    for source_id in sources:
        rid = store.review_id(st.session_state["_phase_id"],
                              st.session_state["evaluator_id"], source_id)
        ui.forget_responses(rid)
        responses = store.load_responses(rid)
        edges = store.load_edge_responses(rid)
        missing = progress.missing_items(data, source_id, responses, edges)
        review = store.get_review(st.session_state["_phase_id"],
                                  st.session_state["evaluator_id"], source_id) or {}
        if missing or not review.get("pdf_read_confirmed"):
            out.append((source_id, len(missing)))
    return out


def _stamp(value) -> str:
    """An ISO timestamp as a date and time, or the raw value if it is not one."""
    text = str(value or "")
    try:
        return dt.datetime.fromisoformat(text).strftime("%d %b %Y, %H:%M UTC")
    except ValueError:
        return text or "an unrecorded date"


def _batch_submission(phase_id, evaluator_id, sources, statuses, reviews) -> None:
    """One final submission per phase.

    Submitting Training does not submit Agreement, and submitting Agreement does
    not submit Individual: each phase is its own irreversible step.

    Completion and submission are separate on purpose: an evaluator's reading
    steadies after several papers, so they must be able to go back and revise
    earlier ones before anything is locked.
    """
    st.session_state["_phase_id"] = phase_id
    ui.show_held()
    st.divider()
    st.subheader(f"Final submission — {manifest.PHASE_LABEL[phase_id]}")

    # The marker is what makes a phase submitted, not the state of the reviews.
    # They can all read `submitted` while the marker is absent — a submission
    # interrupted before its last write — and that phase is *not* submitted.
    marker = store.phase_submission(phase_id, evaluator_id)
    if marker and marker.get("status") == store.SUBMITTED:
        st.success(f"{manifest.PHASE_LABEL[phase_id]} was finally submitted on "
                   f"{_stamp(marker.get('submitted_at'))}.")
        st.caption("Only an administrator can reopen a paper from here. Doing so "
                   "withdraws this submission until you submit the phase again.")
        return

    outstanding = [s for s in sources if statuses[s] != store.STATUS_SUBMITTED]
    if marker and marker.get("status") == store.RETRACTED:
        st.warning("This phase was submitted and then reopened by the "
                   "administrator. Finish what was reopened and submit again.")
    elif not outstanding:
        # Every review says submitted and no marker exists: the last write of a
        # previous attempt did not land. Finishing it is one idempotent step.
        st.warning("Every paper in this phase is already locked, but the "
                   "submission was not recorded — the last step did not complete.")
        if st.button("Complete the submission", type="primary",
                     key=f"finish_submit|{phase_id}"):
            store.record_phase_submission(phase_id, evaluator_id,
                                          manifest.config_version())
            st.rerun()
        return

    ready = [s for s in outstanding if statuses[s] == store.STATUS_COMPLETE]
    if manifest.is_optional(phase_id):
        st.caption("This phase is optional. You may submit it, or simply leave it — "
                   "neither affects the other phases.")

    if len(ready) != len(outstanding):
        remaining = len(outstanding) - len(ready)
        st.caption(f"{remaining} paper(s) still to complete. Final submission unlocks when "
                   "every assigned paper is marked complete.")
        return

    st.warning(f"This locks all {len(ready)} {manifest.PHASE_LABEL[phase_id].lower()} "
               f"papers. After it, you cannot change any answer — only the "
               f"administrator can reopen a paper. Other phases are unaffected.")
    confirmed = st.checkbox("I have finished revising and want to submit everything.",
                            key=f"confirm_batch|{phase_id}|{evaluator_id}")
    if st.button("Submit all papers", type="primary", disabled=not confirmed):
        with st.spinner("Saving your last answers…"):
            settled, outstanding, detail = ui.settle()
        if not settled:
            st.error(
                f"{outstanding} answer(s) are not yet stored, so nothing was "
                f"submitted. They are kept and retried — nothing is lost. "
                + (f"Last error: {detail}" if detail else "Try again in a moment.")
            )
            return

        # `complete` was recorded when the paper was finished, possibly days ago.
        # Submission is irreversible, so it is checked against the stored answers
        # now rather than against that record.
        with st.spinner(f"Checking {len(ready)} papers…"):
            incomplete = _unfinished(ready)
        if incomplete:
            ui.hold(
                f"Nothing was submitted: {len(incomplete)} paper(s) are no longer "
                f"complete when their stored answers are re-read — "
                + ", ".join(f"{brain().work_id(s)} ({n} missing)"
                            for s, n in incomplete[:4])
                + ". They have been reopened; finish what is missing and submit again."
            )
            for source_id, _ in incomplete:
                store.unmark_complete(store.review_id(phase_id, evaluator_id, source_id))
            st.rerun()
            return

        # Reviews first, marker last. Each review submission is idempotent, so a
        # failure part-way through leaves no marker and the retry is harmless.
        store.submit_many(reviews[s]["review_id"] for s in ready)
        store.record_phase_submission(phase_id, evaluator_id,
                                      manifest.config_version())
        st.rerun()


# ------------------------------------------------------------ paper start
def _provenance(data, phase_id: str, evaluator_id: str, source_id: str) -> dict:
    """What this evaluation is being performed under, at the moment it begins.

    Recorded on the review so historical meaning survives later configuration
    changes: an export must not be able to reinterpret a finished evaluation by
    consulting a table that has moved on since.
    """
    key = manifest.assignment_key(phase_id, evaluator_id, source_id)
    row = next((a for a in manifest.assignments()
                if a.get("assignment_key") == key), {})
    return {
        "brain_snapshot_id": data.snapshot_id,
        "eval_spec_version": spec.EVAL_SPEC_VERSION,
        "config_version": manifest.config_version(),
        "split_id": str(row.get("split_id") or ""),
        "assignment_state": manifest.state_of(row) if row else "",
    }


def paper_start(phase_id: str, evaluator_id: str, source_id: str, review: dict) -> bool:
    """Read confirmation gates the evaluation. PDFs live outside this app."""
    data = brain()
    src = data.source(source_id)

    st.title(f"{data.work_id(source_id)} — {src.get('title', '')}")
    # Enough to identify the paper and no more. DOIs, conversion notes and file
    # paths belong in the Source wiki, not in the heading.
    st.caption(_citation(src))
    st.divider()

    st.markdown("#### Evaluation task")
    st.markdown(
        "**Assess whether the Brain faithfully represents what the source says.** "
        "Do not assess whether the paper itself is good, important, persuasive or "
        "legally correct."
    )
    st.markdown("#### How to evaluate")
    st.markdown(views.EVALUATION_STANDARD)

    ui.wiki_button("Open Source wiki", ui.SOURCE, source_id, key="start_src_wiki",
                   help="Context only — it changes nothing and does not block Start")
    st.divider()

    confirmed = st.checkbox(
        "**I confirm that I have read the full paper before starting this evaluation.**",
        value=bool(review.get("pdf_read_confirmed")),
        key=f"read|{review.get('review_id')}",
    )
    st.caption("The papers are distributed separately and are not available through "
               "this interface.")

    if st.button("Start evaluation", type="primary", disabled=not confirmed):
        store.start_review(review["review_id"], True, **_provenance(
            data, phase_id, evaluator_id, source_id))
        st.rerun()
    return False


# ---------------------------------------------------------------- sections
def paper_view(phase_id: str, evaluator_id: str, source_id: str) -> None:
    data = brain()
    review = review_of(phase_id, evaluator_id, source_id)
    rid = review["review_id"]

    if st.button("← All papers", key="back_to_papers"):
        st.session_state.pop("source_id", None)
        ui.close_wiki()
        st.rerun()

    if review.get("status") == store.STATUS_NOT_STARTED:
        paper_start(phase_id, evaluator_id, source_id, review)
        ui.render_wiki_modal(_ctx(data, phase_id, evaluator_id, source_id, rid, False))
        return

    locked = review.get("status") == store.STATUS_SUBMITTED
    ctx = _ctx(data, phase_id, evaluator_id, source_id, rid, locked)

    # Rows are normally created in bulk by tools/preallocate.py before anyone
    # starts, so this is only a fallback for a local run where nobody did.
    if not st.session_state.get(f"prealloc|{rid}"):
        st.session_state[f"prealloc|{rid}"] = True
        if not store.is_preallocated(rid):
            items = progress.all_possible_items(data, source_id)
            edges = [(c["id"], e) for c in data.claims_of(source_id)
                     for e in data.relations_of(c["id"])]
            store.preallocate(
                rid, source_id,
                [(i.object_type, i.object_id, i.question,
                  store.AUTO_NA if i.auto_na else "") for i in items],
                edges)
            ctx.refresh()

    st.title(data.label(source_id))
    if locked:
        st.info("This paper has been submitted. Answers are read-only.")

    states = progress.section_states(data, source_id, ctx.responses, ctx.edge_responses)
    section_key = f"section|{rid}"
    current = st.session_state.get(section_key)
    open_sections = progress.unlocked_sections(states) if not locked else progress.SECTION_IDS
    if current not in open_sections:
        current = progress.next_open_section(states) if not locked else progress.SECTION_IDS[0]
        st.session_state[section_key] = current

    _section_bar(states, open_sections, current, section_key, ctx)
    st.caption(BADGE_LEGEND + " · every section is reachable at any time")
    st.divider()

    # The evaluation keeps the full width. Supporting material opens over it in a
    # modal, so nothing about the page changes according to whether it is open.
    views.RENDERERS[current](ctx)
    _section_nav(states, open_sections, current, section_key, ctx)
    ui.render_wiki_modal(ctx)

    ui.consume_scroll()


def _ctx(data, phase_id, evaluator_id, source_id, rid, locked) -> ui.Ctx:
    # From the session cache: Streamlit reruns this on every interaction, and a
    # storage read per radio click is what made the workbook backend unusable.
    responses, edges = ui.cached_responses(rid)
    return ui.Ctx(
        brain=data, phase_id=phase_id, evaluator_id=evaluator_id,
        evaluator_name=st.session_state.get("evaluator_name", ""),
        pair_id=manifest.pair_of(evaluator_id), source_id=source_id,
        review_id=rid, responses=responses,
        edge_responses=edges, locked=locked,
    )


#: One glyph per state, used for sections, claims and claim sub-sections alike,
#: so the same mark always means the same thing wherever it appears.
BADGE = {progress.COMPLETE: "✓", progress.INCOMPLETE: "●",
         progress.AVAILABLE: "○", progress.LOCKED: "○"}

BADGE_LEGEND = "○ untouched · ● in progress · ✓ complete"


def _section_bar(states, open_sections, current, section_key, ctx) -> None:
    cols = st.columns(len(progress.SECTION_IDS))
    for col, section in zip(cols, progress.SECTION_IDS):
        state = states[section]
        label = progress.SECTION_TAB[section]
        if section == "claims":
            done = progress.claims_done(ctx.brain, ctx.source_id,
                                        ctx.responses, ctx.edge_responses)
            label = f"{label} {done}/{len(ctx.brain.claims_of(ctx.source_id))}"
        with col:
            # Every section is reachable; only the one already open is inert.
            st.button(
                f"{BADGE[state]} {label}",
                key=f"nav|{section}",
                disabled=section == current,
                width="stretch",
                on_click=_go(section_key, section),
            )


def _go(section_key: str, section: str):
    def callback():
        st.session_state[section_key] = section
        ui.request_scroll()
    return callback


PAPER_OVERVIEW = "Paper overview"


def _section_nav(states, open_sections, current, section_key, ctx) -> None:
    st.divider()
    ui.render_save_status()
    index = progress.SECTION_IDS.index(current)
    previous = progress.SECTION_IDS[index - 1] if index else None
    following = progress.SECTION_IDS[index + 1] if index + 1 < len(progress.SECTION_IDS) else None

    # Back and Next are a convenience path through the sections, never a gate:
    # they are disabled only at the two ends. What is outstanding is shown by the
    # section bar above, so repeating it here would only add noise.
    # Named, not generic: "← Back" beside a modal that also says Back, and beside
    # "← All papers", tells the evaluator nothing about where it goes. At the
    # first section the name of what lies above is the paper overview — the
    # title, citation and section bar at the top of this page. At the last there
    # is no next section, and the forward control is dropped rather than left
    # standing as a disabled "Next" pointing nowhere: Review carries its own
    # ending, which is marking the paper complete.
    cols = st.columns([2, 2, 3])
    with cols[0]:
        st.button(f"← {progress.SECTION_TAB[previous]}" if previous
                  else f"← {PAPER_OVERVIEW}",
                  disabled=previous is None, width="stretch", key="sec_back",
                  on_click=_go(section_key, previous) if previous else None)
    if following:
        with cols[1]:
            st.button(f"{progress.SECTION_LABEL[following]} →",
                      width="stretch", key="sec_next",
                      on_click=_go(section_key, following))


# ------------------------------------------------------------------ admin
def _reservations(locked: set[str]) -> None:
    """Activate one reservation per paper, or hand a paper back.

    Both possible allocations of an undivided pool are preallocated, so settling
    the division is a one-field edit rather than a round of row creation — and
    reversible until somebody starts work.
    """
    held = manifest.reserved()
    if not held:
        return
    papers = manifest.reserved_sources()
    st.info(
        f"{len(held)} reserved rows over {len(papers)} papers. A reservation is "
        f"preallocated storage, not an assignment: it is invisible to the "
        f"evaluator and counts toward nothing. Activate **one** evaluator per "
        f"paper — activating both would make the pool a second agreement set."
    )
    data = brain()
    for source_id in papers:
        options = manifest.reservations_for(source_id)
        live = [a for a in manifest.assignments()
                if a["source_id"] == source_id and a["phase_id"] == manifest.INDIVIDUAL
                and manifest.state_of(a) == manifest.ASSIGNED]
        with st.container(border=True):
            st.markdown(f"**{data.label(source_id)}**")
            if live:
                holder = manifest.evaluator(live[0]["evaluator_id"]) or {}
                st.success(f"Assigned to {holder.get('name', live[0]['evaluator_id'])}")
            cols = st.columns(len(options) + 1)
            for col, row in zip(cols, options):
                name = (manifest.evaluator(row["evaluator_id"]) or {}).get(
                    "name", row["evaluator_id"])
                is_locked = row["assignment_key"] in locked
                with col:
                    st.button(
                        f"Assign to {name}", key=f"activate|{row['assignment_key']}",
                        disabled=bool(live) or is_locked,
                        help="locked: work has already started" if is_locked else None,
                        on_click=_set_state, args=(row["assignment_key"],
                                                   manifest.ASSIGNED))
            if live:
                with cols[-1]:
                    st.button("Return to reserved", key=f"release|{source_id}",
                              disabled=live[0]["assignment_key"] in locked,
                              help="locked: work has already started"
                              if live[0]["assignment_key"] in locked else None,
                              on_click=_set_state, args=(live[0]["assignment_key"],
                                                         manifest.RESERVED))


def _set_state(key: str, state: str):
    manifest.set_assignment_state(key, state)


def _phase_outstanding(phase_id: str) -> list[dict]:
    """What stands between this phase and being finished, evaluator by evaluator.

    A phase is finished when every evaluator who holds assignments in it has a
    valid submission marker. Reserved rows are not assignments: a paper nobody
    has been asked to read cannot make a phase unfinished.
    """
    out = []
    for entry in manifest.evaluators():
        evaluator_id = entry["evaluator_id"]
        sources = manifest.assigned_source_ids(evaluator_id, phase_id)
        if not sources:
            continue
        reviews = store.reviews_for(evaluator_id, phase_id)
        unsubmitted = [s for s in sources
                       if reviews.get(s, {}).get("status") != store.STATUS_SUBMITTED]
        submitted = store.phase_submitted(phase_id, evaluator_id)
        if submitted and not unsubmitted:
            continue
        out.append({
            "evaluator": entry["name"], "evaluator_id": evaluator_id,
            "papers": len(sources), "not submitted": len(unsubmitted),
            "phase submission": _submission_state(phase_id, evaluator_id),
        })
    return out


def _submission_state(phase_id: str, evaluator_id: str) -> str:
    row = store.phase_submission(phase_id, evaluator_id)
    if row is None:
        return "not submitted"
    if row.get("status") == store.SUBMITTED:
        return f"submitted {_stamp(row.get('submitted_at'))}"
    return "reopened by admin"


def _admin_progress(data) -> None:
    st.caption("Completion status only — substantive answers stay hidden during "
               "independent evaluation.")
    # The split a paper belongs to is a property of the assignment, so it is
    # read from there. The review row carries a copy, but only for rows created
    # after that column existed, which left the column blank for some papers and
    # filled for others in the same phase.
    split_of = {(a["evaluator_id"], a["phase_id"], a["source_id"]): a.get("split_id", "")
                for a in manifest.assignments()}
    rows = []
    for review in store.all_reviews():
        rid = review["review_id"]
        responses = store.load_responses(rid)
        edges = store.load_edge_responses(rid)
        stats = progress.counts(data, review["source_id"], responses, edges)
        rows.append({
            "evaluator": review["evaluator_name"],
            "phase": review["phase_id"],
            "split": split_of.get((review["evaluator_id"], review["phase_id"],
                                   review["source_id"]),
                                  review.get("split_id") or ""),
            "paper": review["work_id"],
            "progress": f"{stats['answered']}/{stats['items']}",
            "claims": f"{stats['claims_done']}/{stats['claims']}",
            "paper status": review["status"],
            "phase submission": _submission_state(review["phase_id"],
                                                  review["evaluator_id"]),
        })
    if not rows:
        st.info("No reviews yet.")
        return
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption("`progress` counts applicable items answered, not answers of any "
               "particular kind. Nothing here says what anybody decided.")


def _admin_assignments(locked: set[str]) -> None:
    st.caption(
        f"Configuration source: **{manifest.source_name()}** · "
        f"version `{manifest.config_version()}`"
    )
    if locked:
        st.caption(
            f"{len(locked)} assignments are locked: somebody has started work "
            f"against them. Adding a row, or naming the evaluator on a pending "
            f"one, is always safe; removing or reassigning a locked row would "
            f"strand the answers already given."
        )
    _reservations(locked)
    rows = [{**a, "locked": a.get("assignment_key") in locked}
            for a in manifest.assignments()]
    assigned = [r for r in rows if manifest.state_of(r) == manifest.ASSIGNED]
    reserved = [r for r in rows if manifest.state_of(r) == manifest.RESERVED]
    st.markdown(f"**Assigned ({len(assigned)})**")
    st.dataframe(pd.DataFrame(assigned), width="stretch", hide_index=True)
    st.markdown(f"**Reserved ({len(reserved)})** — held for a division not yet "
                f"settled. Visible here only; the evaluators who might receive "
                f"them see nothing.")
    st.dataframe(pd.DataFrame(reserved), width="stretch", hide_index=True)
    st.markdown("**Evaluators**")
    st.dataframe(pd.DataFrame(manifest.evaluators()), width="stretch",
                 hide_index=True)


PAUSE_VS_FREEZE = """
Closing a phase is one of two different acts, and they must not be confused.

- **Pause** — *operational.* Stops further work for now: an interruption, a
  deadline, a machine being replaced. It makes **no claim about completeness or
  submission**, changes no review and no submission record, and is lifted by
  reopening the phase. A paused phase is **not** finished and must not be
  analysed as though it were.
- **Freeze** — *methodological closure.* The phase is finished: every evaluator
  with assigned papers holds a valid final phase-submission marker. Available
  only then; if anybody is outstanding, freezing is refused and says who.
"""


def _admin_control() -> None:
    st.subheader("Phases")
    st.caption("All three are open by default and none gates another.")
    st.markdown(PAUSE_VS_FREEZE)
    for phase_id in manifest.PHASES:
        with st.container(border=True):
            is_open = manifest.phase_open(phase_id)
            head, action = st.columns([4, 1], vertical_alignment="center")
            head.markdown(f"**{manifest.PHASE_LABEL[phase_id]}** — "
                          f"{'open' if is_open else 'closed'}")
            held = manifest.reserved_sources(phase_id)
            if held:
                head.caption(f"{len(held)} papers reserved, not yet assigned "
                             f"(does not affect availability)")
            if not is_open:
                # A closed phase does not remember which act closed it, and it
                # must not be made to look as though it does. What can be said
                # truthfully is what its submissions say.
                short = len(_phase_outstanding(phase_id))
                head.caption(
                    "Closed. Every assigned evaluator has finally submitted it, "
                    "so this is a frozen phase." if not short else
                    f"Closed with {short} evaluator(s) not finally submitted, so "
                    f"this is a paused phase, not a frozen one. Its results are "
                    f"not complete.")
                with action:
                    if st.button("Reopen phase", key=f"phase_open|{phase_id}",
                                 width="stretch"):
                        manifest.set_phase(phase_id, True)
                        st.rerun()
                continue

            outstanding = _phase_outstanding(phase_id)
            label = manifest.PHASE_LABEL[phase_id]
            if not outstanding:
                head.success(
                    f"**Ready to freeze.** Every evaluator with assigned papers in "
                    f"{label} holds a valid final phase-submission marker. Freezing "
                    f"records the methodological closure of the phase.")
                with action:
                    if st.button(f"Freeze {label}", key=f"phase_close|{phase_id}",
                                 width="stretch", type="primary",
                                 help="Methodological closure: the phase is "
                                      "finished and its results may be analysed"):
                        manifest.set_phase(phase_id, False)
                        st.rerun()
                st.caption("Pausing is also available while a phase is open, but "
                           "there is nothing left to pause work on here.")
                continue

            # Refused, and said in the same breath what is outstanding. Closing a
            # phase changes nothing about anybody's reviews, so it must never be
            # allowed to read as though the work had been submitted.
            head.error(
                f"**Cannot freeze {label}.** Freezing means the phase is finished, "
                f"and the evaluators below have not finally submitted it. Freezing "
                f"would record nothing as submitted — it would only stop them "
                f"finishing.")
            st.dataframe(pd.DataFrame(outstanding), width="stretch",
                         hide_index=True)
            st.markdown(f"**Pause {label} instead?** Pausing is operational, not "
                        f"methodological: it stops further work for now, records "
                        f"no submission, changes no review, and can be lifted at "
                        f"any time by reopening the phase. It is **not** a frozen "
                        f"or completed phase, and nothing may be analysed as "
                        f"though it were.")
            paused = st.checkbox(
                f"I understand that pausing {label} stops work in an unfinished "
                f"state and claims nothing about completeness or submission.",
                key=f"pause_ok|{phase_id}")
            if st.button(f"Pause {label}", key=f"phase_pause|{phase_id}",
                         disabled=not paused,
                         help="Operational only: no claim about completeness"):
                manifest.set_phase(phase_id, False)
                st.rerun()

    st.subheader("Reopen a submitted paper")
    st.caption("Reopening withdraws that evaluator's submission of the phase the "
               "paper belongs to, and leaves the other phases alone. They submit "
               "the phase again once the paper is finished.")
    submitted = [r for r in store.all_reviews()
                 if r["status"] == store.STATUS_SUBMITTED]
    if not submitted:
        st.caption("Nothing submitted yet.")
    for review in submitted:
        row, action = st.columns([5, 1], vertical_alignment="center")
        row.write(f"{review['evaluator_name']} · "
                  f"{manifest.PHASE_LABEL.get(review['phase_id'], review['phase_id'])} · "
                  f"{review['work_id']} — phase "
                  f"{_submission_state(review['phase_id'], review['evaluator_id'])}")
        with action:
            if st.button("Reopen", key=f"reopen|{review['review_id']}",
                         width="stretch"):
                retracted = store.reopen_review(review["review_id"])
                ui.hold(
                    f"{review['work_id']} is open for editing again."
                    + (f" {review['evaluator_name']}'s "
                       f"{manifest.PHASE_LABEL[review['phase_id']].lower()} "
                       f"submission has been withdrawn until they submit again."
                       if retracted else "")
                )
                st.rerun()


def _admin_exports() -> None:
    frames = {
        "config": pd.DataFrame(sorted(manifest.config().items()),
                               columns=["key", "value"]),
        "evaluators": pd.DataFrame(manifest.evaluators()),
        "assignments": pd.DataFrame(manifest.assignments()),
        # `current_assignment_state` is added beside the state recorded on the
        # review, so an analysis can tell what a review was performed under from
        # what the configuration says today.
        "reviews": pd.DataFrame(
            manifest.with_current_state(store.export("reviews"))),
        "responses": pd.DataFrame(store.export("responses")),
        "edge_responses": pd.DataFrame(store.export("edge_responses")),
        "phase_submissions": pd.DataFrame(store.export("phase_submissions")),
        "provenance": pd.DataFrame(sorted(_provenance_metadata().items()),
                                   columns=["key", "value"]),
    }
    for name, frame in frames.items():
        st.download_button(f"{name}.csv — {len(frame)} rows",
                           frame.to_csv(index=False).encode("utf-8"),
                           file_name=f"{name}.csv", mime="text/csv", key=f"dl|{name}")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, frame in frames.items():
            frame.to_excel(writer, index=False, sheet_name=name[:31])
    st.download_button("Combined workbook (XLSX)", buffer.getvalue(),
                       file_name="he_evaluation_export.xlsx",
                       mime="application/vnd.openxmlformats-officedocument."
                            "spreadsheetml.sheet")

    st.divider()
    st.markdown("**Configuration snapshots**")
    st.caption("Written by `app/tools/snapshot_config.py` when a configuration is "
               "accepted, and committed. A snapshot that exists only on the "
               "machine that made it is not a record.")
    kept = sorted(p.name for p in SNAPSHOT_DIR.glob("*")
                  if p.is_dir()) if SNAPSHOT_DIR.exists() else []
    if kept:
        st.dataframe(pd.DataFrame({"snapshot": kept}), width="stretch",
                     hide_index=True)
    else:
        st.caption("No snapshot has been kept yet.")


def _provenance_metadata() -> dict[str, str]:
    """Everything an analysis needs to say what these answers were produced by."""
    data = brain()
    return {
        "brain_snapshot_id": data.snapshot_id,
        "eval_spec_version": spec.EVAL_SPEC_VERSION,
        "config_version": manifest.config_version(),
        "split_version": manifest.split_version(),
        "configuration_source": manifest.source_name(),
        "storage_backend": store.backend_name(),
        "exported_at": store.now(),
    }


def _admin_system(data) -> None:
    st.markdown("**Versions**")
    for label, value in _provenance_metadata().items():
        if label == "exported_at":
            continue      # says "now" on a screen; it belongs in the export file
        st.write(f"{label.replace('_', ' ').capitalize()} — `{value}`")
    st.write(f"Manifest snapshot — `{manifest.brain_snapshot_id()}`")
    st.write(f"Open phases — {', '.join(manifest.open_phases()) or 'none'}")

    st.markdown("**Brain**")
    st.write(f"{len(data.sources)} sources · {len(data.claims)} claims · "
             f"{len(data.concepts)} concepts · {len(data.datasets)} datasets · "
             f"{len(data.edges)} edges")

    st.markdown("**Storage**")
    reviews = store.all_reviews()
    started = [r for r in reviews if r.get("status") != store.STATUS_NOT_STARTED]
    preallocated = sum(1 for r in reviews
                       if str(r.get("responses_first_row") or "").strip())
    st.write(f"{len(reviews)} review rows · {len(started)} started · "
             f"{preallocated} with a recorded response block")
    st.write(f"{len(store.export('responses'))} response rows · "
             f"{len(store.export('edge_responses'))} edge rows · "
             f"{len(store.all_phase_submissions())} phase submissions")
    queue = ui.queue()
    state, detail, _ = queue.state
    st.write(f"Save queue — {state}"
             + (f" ({detail})" if detail else "")
             + f" · {queue.unresolved} unresolved")

    st.markdown("**Configuration**")
    problems = manifest.validate(set(data.sources), data.snapshot_id,
                                 reviews=reviews)
    if problems:
        for problem in problems:
            st.warning(problem)
    else:
        st.success("Configuration is consistent.")


SNAPSHOT_DIR = pathlib.Path(__file__).resolve().parent / "data" / "config_snapshots"


def admin_page() -> None:
    st.title("Admin")
    if not st.session_state.get("admin_ok"):
        with st.form("admin"):
            secret = st.text_input("Admin secret", type="password")
            if st.form_submit_button("Unlock"):
                if secret and secret == manifest.admin_secret():
                    st.session_state["admin_ok"] = True
                    st.rerun()
                else:
                    st.error("Wrong admin secret.")
        return

    data = brain()
    ui.show_held()
    tabs = st.tabs(["Progress", "Assignments", "Control", "Exports", "System"])
    with tabs[0]:
        _admin_progress(data)
    with tabs[1]:
        _admin_assignments(manifest.active_assignment_keys(store.all_reviews()))
    with tabs[2]:
        _admin_control()
    with tabs[3]:
        _admin_exports()
    with tabs[4]:
        _admin_system(data)


# ------------------------------------------------------------------- main
def guard_snapshot() -> bool:
    """Stop visibly if the Brain changed after the split was accepted.

    A moving target would silently invalidate answers already given, so this
    aborts rather than warning.
    """
    data = brain()
    if manifest.snapshot_matches(data.snapshot_id):
        return True
    st.title("Brain snapshot mismatch")
    st.error(
        "The Brain on disk is not the artifact this evaluation was configured "
        "against, so the evaluation cannot start."
    )
    st.markdown(
        f"- configured (from the accepted split): `{manifest.brain_snapshot_id()}`\n"
        f"- on disk: `{data.snapshot_id}`"
    )
    st.caption("Restore the frozen Brain, or re-run the Splitter against this one "
               "and re-import the split.")
    return False


def guard_spec_version() -> bool:
    """Stop visibly if the running instrument is not the configured one.

    The configuration names the evaluation specification the round was accepted
    against. Running a different one would mix answers given under two different
    instruments into one dataset, and nothing downstream could separate them —
    so this aborts rather than warning.
    """
    configured = manifest.eval_spec_version()
    if not configured or configured == spec.EVAL_SPEC_VERSION:
        return True
    st.title("Evaluation specification mismatch")
    st.error(
        "The running application does not carry the evaluation specification "
        "this configuration was accepted against, so the evaluation cannot start."
    )
    st.markdown(
        f"- configured: `{configured}`\n"
        f"- running: `{spec.EVAL_SPEC_VERSION}`"
    )
    st.caption("Deploy the matching version of the application, or update "
               "`eval_spec_version` in the configuration once the new instrument "
               "is the accepted one.")
    return False


def guard_storage() -> bool:
    """On a deployed run, refuse to start unless the live workbook is reachable.

    Falling back to SQLite on Streamlit Community Cloud would let evaluators
    work into a store that can disappear between restarts, and they would only
    find out once answers were already lost.
    """
    problem = None
    gap = ""
    transient = False
    if sheets.configured():
        # Configured, so a failure is always shown — never silently swapped for a
        # different store, which would split the run's answers across two places.
        #
        # One `except`, and the kind of failure decided afterwards. An `except`
        # clause that has to look a name up can itself raise, and when it does it
        # replaces the exception it was meant to report — which is how the first
        # deployment turned a plain "no attribute check_ready" into an
        # AttributeError about the handler.
        try:
            store.init()
        except Exception as error:
            problem = str(error) or repr(error)
            transient = isinstance(error, QuotaExceeded)
    else:
        # Half a configuration is a misconfiguration, not a request for SQLite.
        gap = sheets.configuration_gap()
        if gap:
            problem = gap
        elif manifest.require_sheets():
            problem = (
                f"`{sheets.ENV_SHEET_ID}` and a service account must both be set. "
                f"Provide the key as a `[{sheets.SECRETS_SERVICE_ACCOUNT}]` table in "
                f"Streamlit secrets, or as `{sheets.ENV_CREDENTIALS}`."
            )

    if problem is None:
        return True

    if transient:
        # Nothing is wrong with the workbook and nothing needs fixing, so the
        # page must not send anybody to the bootstrap tool. It says wait.
        st.title("Google Sheets is busy")
        st.warning(problem)
        st.caption(
            "This is a rate limit, not a fault: Google allows 60 read requests "
            "per minute per user across everybody using this workbook. No answer "
            "has been lost and nothing in the workbook was changed."
        )
        if st.button("Try again", type="primary"):
            store.forget_ready()
            st.rerun()
        return False

    st.title("Google Sheets is not configured" if gap
             else "Google Sheets is not reachable")
    st.error(problem)
    if gap:
        st.caption(
            "The app stops instead of falling back to the local store: it would "
            "accept every answer, report them saved, and leave the workbook empty. "
            "On Streamlit Community Cloud those files are not guaranteed to persist, "
            "so the answers could then be lost entirely."
        )
    elif manifest.require_sheets():
        st.caption(
            f"`{manifest.ENV_REQUIRE_SHEETS}` is set, so the app will not fall back to "
            "the local store: on Streamlit Community Cloud those files are not "
            "guaranteed to persist and answers written there could be lost."
        )
    else:
        st.caption(
            f"`{sheets.ENV_SHEET_ID}` is set, so the app will not quietly fall back to "
            "the local store — that would split this run's answers across two places. "
            f"To work locally on SQLite instead, unset `{sheets.ENV_SHEET_ID}`."
        )
    st.markdown(
        "Diagnose step by step with `python app/tools/check_sheets.py --write`, "
        "and create the tabs with `python app/tools/bootstrap_sheets.py`."
    )
    return False


def main() -> None:
    # `guard_storage` calls `store.init()` and reports what it finds, so calling
    # it again here only repeated the work on every rerun.
    if not guard_storage():
        return
    if not guard_snapshot():
        return
    if not guard_spec_version():
        return
    if not gate_password():
        return
    if not gate_identity():
        return

    data = brain()
    evaluator_id = st.session_state["evaluator_id"]
    name = st.session_state["evaluator_name"]

    st.sidebar.markdown(f"**{name}**")

    # The evaluator sees their own split ids, never a pair letter: the "Group
    # A/B/C" labels in circulation contradict the AGR names.
    splits = manifest.splits_of(evaluator_id)
    if any(splits.values()):
        st.sidebar.caption(" · ".join(
            f"{manifest.PHASE_LABEL[phase]}: {split}"
            for phase, split in splits.items() if split))

    pages = [manifest.PHASE_LABEL[p] for p in manifest.PHASES]
    pages += ["Admin"] if manifest.is_admin(evaluator_id) else []
    page = st.sidebar.radio("Phase", pages, key="phase_choice")

    if st.session_state.get("_page") != page:
        st.session_state["_page"] = page
        st.session_state.pop("source_id", None)
        ui.close_wiki()

    # Brain hash, spec version, graph counts and the backend name are system
    # diagnostics, not evaluator navigation. They live in Admin -> System.
    if manifest.is_admin(evaluator_id):
        problems = manifest.validate(set(data.sources), data.snapshot_id)
        if problems:
            st.sidebar.divider()
            with st.sidebar.expander(f"⚠ {len(problems)} configuration notes"):
                for problem in problems:
                    st.caption(f"• {problem}")

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
