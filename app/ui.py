"""Shared UI machinery: inspector stack, scroll-to-top, autosaving widgets."""
from __future__ import annotations

import dataclasses
import html
import re

import streamlit as st
import streamlit.components.v1 as components

import progress
import savequeue
import spec
import store

SAVE_IDLE, SAVE_SAVING = savequeue.IDLE, savequeue.SAVING
SAVE_SAVED, SAVE_FAILED = savequeue.SAVED, savequeue.FAILED
SAVE_RETRYING, SAVE_CONFLICT = savequeue.RETRYING, savequeue.CONFLICT


def _batchable(function, args, kwargs):
    """An ordinary answer save, expressed as a record `save_responses` accepts.

    Conflict-checked saves travel with the rest: the batch's rows lie inside one
    review's block, so their stored timestamps come back in a single range read.
    """
    if function is not store.save_response or len(args) != 1:
        return None
    return {"rid": args[0],
            "expected_updated_at": kwargs.get("expected_updated_at"),
            **{name: kwargs.get(name) for name in
               ("object_type", "object_id", "question_key", "criterion_id",
                "field_subitem", "answer", "comment", "applicability", "source_id")}}


def queue() -> savequeue.SaveQueue:
    """One queue per Streamlit session."""
    if "_save_queue" not in st.session_state:
        queue = savequeue.SaveQueue()
        queue.set_batch_writer(_batchable, store.save_responses)
        queue.set_fatal(store.SaveConflict)
        st.session_state["_save_queue"] = queue
    return st.session_state["_save_queue"]


# ------------------------------------------------------------ response cache
#: One read per review per session, not one per rerun.
#:
#: Streamlit reruns the whole script on every interaction, so rebuilding the
#: context from storage each time meant a storage read per radio click. The
#: cache is write-through: a queued save updates the cached dict immediately, so
#: what the evaluator sees is what will be persisted, and the two cannot drift.
#:
#: It is deliberately not a TTL cache. Nobody else writes these rows — each
#: evaluator owns their own — so the only thing that can invalidate it is this
#: session's own write, which updates it directly. `refresh()` forces a real
#: re-read where correctness demands one: before marking a paper complete and
#: before final submission.
CACHE = "_response_cache"


def _cache() -> dict:
    return st.session_state.setdefault(CACHE, {})


def cached_responses(review_id: str) -> tuple[dict, dict]:
    entry = _cache().get(review_id)
    if entry is None:
        entry = (store.load_responses(review_id),
                 store.load_edge_responses(review_id))
        _cache()[review_id] = entry
    return entry


def forget_responses(review_id: str | None = None) -> None:
    if review_id is None:
        st.session_state[CACHE] = {}
    else:
        _cache().pop(review_id, None)


# ------------------------------------------------------------------ context
@dataclasses.dataclass
class Ctx:
    brain: object
    phase_id: str
    evaluator_id: str
    evaluator_name: str
    pair_id: str | None
    source_id: str
    review_id: str
    responses: dict
    edge_responses: dict
    locked: bool

    def response(self, question_key: str, object_id: str) -> dict:
        return self.responses.get(f"{question_key}|{object_id}", {})

    def refresh(self) -> None:
        """Re-read from storage, bypassing the cache.

        Used where a stale view would be a correctness problem rather than a
        cosmetic one: verifying that nothing is missing before a paper is marked
        complete, and before a phase is finally submitted.
        """
        forget_responses(self.review_id)
        self.responses, self.edge_responses = cached_responses(self.review_id)


# --------------------------------------------------------------- scrolling
def scroll_to_top() -> None:
    """Pressing Next must open the next page at the top."""
    components.html(
        "<script>window.parent.document"
        ".querySelector('section.main, .stMain, [data-testid=\"stMain\"]')"
        "?.scrollTo({top:0});window.parent.scrollTo({top:0});</script>",
        height=0,
    )


def request_scroll() -> None:
    st.session_state["_scroll_top"] = True


def consume_scroll() -> None:
    if st.session_state.pop("_scroll_top", False):
        scroll_to_top()


# ------------------------------------------------------------------- wiki
#: One modal, every piece of supporting material. A wiki opened beside the
#: evaluation competed with it for width and, worse, its state leaked into the
#: page: whether a panel was open changed what the evaluation area looked like.
#: A modal is unambiguously context — it sits over the work, and closing it
#: leaves the work exactly as it was.
WIKI = "wiki_stack"

SOURCE, CONCEPT, DATASET, CLAIM = "source", "concept", "dataset", "claim"
CONCEPT_REGISTRY = "concept_registry"
SOURCE_REGISTRY = "source_registry"
SOURCE_CLAIMS = "source_claims"

#: Ids the Brain's own prose refers to. Markdown links cannot call back into
#: Python, so the modal offers these as buttons instead of pretending the links
#: work.
REFERENCE = re.compile(r"\b(SRC-\d{4}|DST-\d{4}|CPT-[a-z0-9-]+|CLM-\d{4}-\d{3})\b")

KIND_OF_PREFIX = {"SRC": SOURCE, "DST": DATASET, "CPT": CONCEPT, "CLM": CLAIM}


def wiki_stack() -> list[tuple[str, str]]:
    return st.session_state.setdefault(WIKI, [])


def open_wiki(kind: str, object_id: str = "") -> None:
    """Open a fresh modal. Every entry point starts its own history.

    A dismissal — the X, Esc, a click outside — cannot be distinguished from
    never having opened it, so each entry point clears what came before rather
    than letting a stale trail accumulate behind it.
    """
    st.session_state[WIKI] = [(kind, object_id)]


def follow_wiki(kind: str, object_id: str = "") -> None:
    """Follow a link from inside the modal, keeping the way back."""
    stack = wiki_stack()
    if not stack or stack[-1] != (kind, object_id):
        stack.append((kind, object_id))


def wiki_back() -> None:
    stack = wiki_stack()
    if len(stack) > 1:
        stack.pop()


def close_wiki() -> None:
    st.session_state[WIKI] = []


def wiki_is_open() -> bool:
    return bool(wiki_stack())


def reset_wiki(context_key: str) -> None:
    """Close the modal when the evaluation context changes.

    Moving to another claim, dataset or section means the material on screen is
    no longer about what the evaluator is looking at.
    """
    if st.session_state.get("_wiki_context") != context_key:
        st.session_state["_wiki_context"] = context_key
        close_wiki()


# Kept as aliases so nothing outside this module had to change name mid-step.
INSPECTOR = WIKI
inspector_stack = wiki_stack
reset_inspector = reset_wiki
open_inspector = open_wiki


MODAL_CSS = """
<style>
/* Roughly three quarters of the viewport, with the content scrolling inside it
   rather than the page behind. */
div[data-testid="stDialog"] div[role="dialog"] {
    width: 75vw;
    max-width: 1200px;
    height: 82vh;
}
div[data-testid="stDialog"] div[role="dialog"] > div:nth-child(2) {
    overflow-y: auto;
}
</style>
"""


def wiki_button(label: str, kind: str, object_id: str = "", *, key: str,
                help: str | None = None, follow: bool = False,
                width: str = "content") -> None:
    """A control that opens the modal. Never touches an answer or the page."""
    st.button(label, key=key, help=help, width=width,
              on_click=follow_wiki if follow else open_wiki,
              args=(kind, object_id))


# the old name, so existing call sites keep working unchanged
def inspector_button(label: str, kind: str, object_id: str, key: str) -> None:
    wiki_button(label, kind, object_id, key=key,
                help=f"Open {object_id} — this does not change your answers")


def render_wiki_modal(ctx) -> None:
    """Show the modal when something is on the stack.

    Built each run so its title matches its contents. Dismissing it clears the
    stack, so it does not reopen behind the user's back on the next rerun.
    """
    stack = wiki_stack()
    if not stack:
        return
    st.markdown(MODAL_CSS, unsafe_allow_html=True)
    kind, object_id = stack[-1]
    dialog = st.dialog(_wiki_title(ctx, kind, object_id), width="large",
                       on_dismiss=close_wiki)(lambda: _wiki_body(ctx))
    dialog()


def _wiki_title(ctx, kind: str, object_id: str) -> str:
    brain = ctx.brain
    if kind == SOURCE:
        return f"Source wiki · {object_id}"
    if kind == CONCEPT:
        return f"Concept wiki · {brain.concept(object_id).get('label', object_id)}"
    if kind == DATASET:
        return f"Dataset wiki · {brain.dataset(object_id).get('name', object_id)}"
    if kind == CLAIM:
        return f"Claim · {object_id}"
    if kind == CONCEPT_REGISTRY:
        return "Concept registry"
    if kind == SOURCE_REGISTRY:
        return "Sources in the Brain"
    if kind == SOURCE_CLAIMS:
        return f"All claims from {brain.work_id(object_id) or object_id}"
    return "Brain"


def _wiki_body(ctx) -> None:
    stack = wiki_stack()
    if not stack:
        return
    kind, object_id = stack[-1]

    controls = st.columns([1, 1, 6])
    with controls[0]:
        st.button("← Back", key=f"wiki_back|{len(stack)}", disabled=len(stack) < 2,
                  on_click=wiki_back)
    with controls[1]:
        if st.button("✕ Close", key=f"wiki_close|{len(stack)}"):
            close_wiki()
            st.rerun()
    if len(stack) > 1:
        st.caption(" › ".join(oid or kind for kind, oid in stack))
    st.divider()

    if kind == SOURCE:
        _source_body(ctx, object_id)
    elif kind == CONCEPT:
        _concept_body(ctx, object_id)
    elif kind == DATASET:
        _dataset_body(ctx, object_id)
    elif kind == CLAIM:
        _claim_body(ctx, object_id)
    elif kind == CONCEPT_REGISTRY:
        _concept_registry_body(ctx)
    elif kind == SOURCE_REGISTRY:
        _source_registry_body(ctx)
    elif kind == SOURCE_CLAIMS:
        _source_claims_body(ctx, object_id)


def _references(ctx, text: str, exclude: str, key: str) -> None:
    """Offer the ids this page names as buttons, since its links cannot work."""
    found = []
    for match in REFERENCE.findall(text or ""):
        kind = KIND_OF_PREFIX.get(match[:3])
        if kind and match != exclude and match not in found:
            found.append(match)
    if not found:
        return
    with st.expander(f"Referenced here ({len(found)})"):
        st.caption("Opens in this window; ← Back returns.")
        for row in range(0, len(found[:24]), 4):
            for col, ident in zip(st.columns(4), found[row:row + 4]):
                with col:
                    wiki_button(ident, KIND_OF_PREFIX[ident[:3]], ident,
                                key=f"{key}|ref|{ident}", follow=True)


def _source_body(ctx, source_id: str) -> None:
    source = ctx.brain.source(source_id)
    st.markdown(f"### {source.get('title', source_id)}")
    st.caption(f"{', '.join(source.get('authors') or [])} · {source.get('year', '')} · "
               f"{source.get('venue', '')}")
    body = ctx.brain.source_body(source_id)
    _references(ctx, body, source_id, f"src|{source_id}")
    st.markdown(body)


def _concept_body(ctx, concept_id: str) -> None:
    concept = ctx.brain.concept(concept_id)
    st.markdown(f"### {concept.get('label', concept_id)}")
    st.caption(f"`{concept_id}` · {concept.get('status', '')} · "
               f"{concept.get('concept_type', '')}")
    body = ctx.brain.concept_body(concept_id)
    _references(ctx, body, concept_id, f"cpt|{concept_id}")
    st.markdown(body)


def _dataset_body(ctx, dataset_id: str) -> None:
    dataset = ctx.brain.dataset(dataset_id)
    st.markdown(f"### {dataset.get('name', dataset_id)}")
    st.caption(f"`{dataset_id}`")
    body = ctx.brain.dataset_body(dataset_id)
    _references(ctx, body, dataset_id, f"dst|{dataset_id}")
    st.markdown(body)


def claim_detail(brain, claim: dict) -> None:
    """A claim has no wiki page, so this card is generated from claims.jsonl."""
    st.markdown("**Statement**")
    st.markdown(f"> {claim.get('statement','')}")
    if claim.get("premise"):
        st.markdown("**Premise**")
        st.markdown(f"> {claim['premise']}")
    st.markdown("**Anchors**")
    for quote in claim.get("quotes") or []:
        st.markdown(f"> “{quote.get('quote','')}”")
        st.caption(quote.get("location", ""))
    st.markdown("**Attributes**")
    for key in ("claim_type", "positive_form", "basis", "basis_qualifier",
                "claim_jurisdiction", "jurisdiction_relation", "jurisdiction_inferred",
                "temporal_reference", "dataset"):
        if claim.get(key) not in (None, "", []):
            st.markdown(f"- **{key}** — `{claim[key]}`")
    if claim.get("concepts"):
        st.markdown("**Concepts**")
        for cid in claim["concepts"]:
            st.markdown(f"- `{cid}` {brain.concept(cid).get('label','')}")


def _claim_body(ctx, claim_id: str) -> None:
    claim = ctx.brain.claims.get(claim_id, {})
    st.caption("Claims have no wiki page; this view is generated from claims.jsonl.")
    claim_detail(ctx.brain, claim)


def _concept_registry_body(ctx) -> None:
    st.caption("Every concept in the Brain. Anchors are given in advance and define "
               "the field; a candidate is created only when no anchor captures a "
               "claim without distortion.")
    query = st.text_input("Search", key="wiki_concept_search",
                          placeholder="label, id or family")
    rows = ctx.brain.concept_registry()
    if query:
        needle = query.lower()
        rows = [r for r in rows
                if needle in r["id"].lower() or needle in r["label"].lower()
                or needle in (r["concept_type"] or "").lower()]
    st.caption(f"{len(rows)} concepts")
    for row in rows[:80]:
        cols = st.columns([5, 1])
        cols[0].markdown(
            f"**{row['label']}** · `{row['id']}` — *{row['status']} / "
            f"{row['concept_type']}*  \n{row['definition']}")
        with cols[1]:
            wiki_button("wiki", CONCEPT, row["id"], key=f"reg_cpt|{row['id']}",
                        follow=True)


def _source_registry_body(ctx) -> None:
    st.caption("The publications the Brain holds. A citation becomes a CITES edge "
               "only when the cited work is one of these.")
    query = st.text_input("Search", key="wiki_source_search",
                          placeholder="title, author, year or id")
    rows = ctx.brain.source_registry()
    if query:
        needle = query.lower()
        rows = [r for r in rows
                if needle in r["title"].lower() or needle in r["id"].lower()
                or needle in r["work_id"].lower() or needle in r["year"]
                or any(needle in a.lower() for a in r["authors"])]
    st.caption(f"{len(rows)} of {len(ctx.brain.source_ids)} sources")
    for row in rows:
        cols = st.columns([5, 1])
        cols[0].markdown(
            f"**{row['work_id']} — {row['title']}**  \n"
            f"{', '.join(row['authors'])} · {row['year']} · `{row['id']}`")
        with cols[1]:
            wiki_button("wiki", SOURCE, row["id"], key=f"reg_src|{row['id']}",
                        follow=True)


def _source_claims_body(ctx, source_id: str) -> None:
    claims = ctx.brain.claims_of(source_id)
    st.caption(f"{len(claims)} claims were extracted from this paper. Shown so a "
               f"claim can be compared with the rest of the set.")
    for index, claim in enumerate(claims, start=1):
        cols = st.columns([6, 1])
        cols[0].markdown(f"**{index}. `{claim['id']}`** — {claim.get('statement', '')}")
        with cols[1]:
            wiki_button("detail", CLAIM, claim["id"],
                        key=f"srcclaims|{claim['id']}", follow=True)


# ------------------------------------------------------------ save status
def render_save_status() -> None:
    """What storage is doing, in one line.

    A failed write is retained and retried, so this says "not saved yet" rather
    than "lost". Completion and submission refuse while anything is unresolved,
    which is what makes that honest.
    """
    state, detail, unresolved = queue().state
    conflicts = queue().conflicts
    if conflicts:
        st.warning(
            f"**{len(conflicts)} change(s) were not applied.** Those answers had "
            f"already been changed somewhere else — most likely this paper is open "
            f"in another tab. What is stored has been kept; reload to see it."
        )
        if st.button("Reload this paper", key="reload_after_conflict"):
            queue().clear_conflicts()
            forget_responses()
            st.rerun()
    if state == SAVE_FAILED:
        st.warning(
            f"**Save failed — {unresolved} answer{'s' if unresolved != 1 else ''} "
            f"not yet stored.** They are kept and retried; nothing you have "
            f"typed is lost, and this paper cannot be marked complete until they "
            f"land. {detail}"
        )
        if st.button("Retry now", key="retry_saves"):
            queue().retry_now()
            st.rerun()
    elif state == SAVE_RETRYING:
        st.caption(f"Retrying… ({unresolved} outstanding)")
    elif state == SAVE_SAVING or unresolved:
        st.caption(f"Saving… ({unresolved} outstanding)")
    elif state == SAVE_SAVED:
        st.caption("✓ Saved")


NOTICE = "_notice"


def hold(message: str) -> None:
    """Keep a message across the rerun that follows it.

    `st.error` writes into the page being rendered, so an error raised just
    before `st.rerun()` is discarded before anyone sees it — which is exactly
    where the important refusals happen: the rerun is there to show the freshly
    re-read state, and the message explains why it changed.
    """
    st.session_state[NOTICE] = message


def show_held() -> None:
    message = st.session_state.pop(NOTICE, None)
    if message:
        st.error(message)


def unresolved_writes() -> int:
    return queue().unresolved


def settle(timeout: float = 30.0) -> tuple[bool, int, str]:
    """Flush before an irreversible step. Returns (ok, outstanding, detail)."""
    ok = queue().flush(timeout=timeout)
    failures = queue().failures
    detail = "; ".join(sorted(set(failures.values())))[:200]
    return ok, queue().unresolved, detail


# --------------------------------------------------------------- rendering
def fmt(value) -> str:
    if value is None or value == "" or value == []:
        return "_(empty)_"
    if isinstance(value, list):
        return ", ".join(f"`{v}`" for v in value)
    if isinstance(value, bool):
        return "`true`" if value else "`false`"
    return f"`{value}`"


def field_rows(pairs) -> None:
    for label, value in pairs:
        st.markdown(f"- **{label}** — {fmt(value)}")


def schema_values(label: str, values) -> None:
    """A Brain value under a plain-language label.

    Monospace is reserved for what it means: a literal value from the schema —
    `technical`, `CA-QC`. The label above it is ordinary prose, because
    "Contribution type" is not a value the evaluator has to match against
    anything.

    Label and values are one block rather than two `st.markdown` calls: two
    calls put a paragraph's worth of air between a heading and the thing it
    heads, which spread a panel of four short lines over half a screen.
    """
    if isinstance(values, str) or values is None:
        values = [values] if values else []
    shown = (" · ".join(f"<code>{html.escape(str(v))}</code>" for v in values)
             if values else "<em>none recorded</em>")
    st.markdown(
        f'<div style="margin:0 0 0.6rem">'
        f'<div style="font-weight:600;margin-bottom:0.1rem">{html.escape(label)}</div>'
        f'<div>{shown}</div></div>',
        unsafe_allow_html=True,
    )


_BOLD = re.compile(r"\*\*(.+?)\*\*")


def scale_note(text: str) -> None:
    """The response scale, stated once per section.

    A caption is too quiet for a rule the evaluator is meant to apply to every
    answer below it, and `st.info` is a banner three times the height of the
    sentence. This is body-weight text against a faint ground, one line tall.
    The grey is given in rgba so it reads on either theme without knowing which
    one is in force.
    """
    body = _BOLD.sub(r"<strong>\1</strong>", text)
    st.markdown(
        f'<div style="border-left:3px solid rgba(128,128,128,0.45);'
        f'background:rgba(128,128,128,0.09);border-radius:0 4px 4px 0;'
        f'padding:0.4rem 0.75rem;margin:0.35rem 0 0.9rem;line-height:1.45">'
        f'{body}</div>',
        unsafe_allow_html=True,
    )


def definition_list(pairs, *, skip_empty: bool = True) -> None:
    """Label and value in two columns — a reference table, not debug output.

    ``skip_empty`` decides what an absent value means. In a context block an
    empty field is simply nothing to say, so the row goes. Among the attributes
    under judgment it is a fact the evaluator is being asked about — that the
    Brain recorded no basis qualifier — so the row stays and shows a dash.
    """
    for label, value in pairs:
        if skip_empty and value in (None, "", []):
            continue
        left, right = st.columns([1, 3], gap="small")
        left.markdown(f"**{label}**")
        right.markdown(value if value not in (None, "", []) else "—")


def value_markup(value) -> str:
    """A Brain value as monospace, or a dash where the Brain recorded nothing."""
    if value is None or value == "" or value == []:
        return "—"
    if isinstance(value, bool):
        value = "true" if value else "false"
    if isinstance(value, list):
        return " · ".join(f"`{v}`" for v in value)
    return f"`{value}`"


def _persist(ctx: Ctx, question: spec.Question, object_id: str,
             answer, comment, applicability: str) -> None:
    """Queue the write; the UI does not wait for storage.

    The row's stored ``updated_at`` goes out as the expectation, so the same
    evaluator working in two tabs gets a conflict rather than a silent
    overwrite. On success the token is refreshed from the stamp the write
    returned — without that, the next legitimate edit in this session would
    compare against a timestamp storage has moved past, and every second edit
    would look like a conflict.
    """
    lookup = f"{question.question_key}|{object_id}"
    stored = ctx.responses.get(lookup, {})
    key = store.response_key(ctx.review_id, question.object_type, object_id,
                             question.question_key)

    def written(stamp):
        row = ctx.responses.get(lookup)
        if isinstance(row, dict) and stamp:
            row["updated_at"] = stamp

    queue().submit(
        key, store.save_response, ctx.review_id,
        object_type=question.object_type, object_id=object_id,
        question_key=question.question_key, criterion_id=question.criterion_id,
        field_subitem=question.field_subitem, answer=answer, comment=comment,
        applicability=applicability, source_id=ctx.source_id,
        expected_updated_at=stored.get("updated_at") or "",
        on_success=written,
    )


def _remember(ctx: Ctx, question: spec.Question, object_id: str,
              answer, comment, applicability: str) -> None:
    """Mirror a queued write into the in-session view of the responses."""
    stored = ctx.response(question.question_key, object_id)
    ctx.responses[f"{question.question_key}|{object_id}"] = {
        **stored, "answer": answer, "comment_evidence": comment,
        "applicability": applicability,
    }


def _auto_na_for(ctx: Ctx, question: spec.Question, object_id: str) -> bool:
    """Whether the Brain record makes this criterion inapplicable here.

    The three rules are claim-level (HE-07, HE-21) or source-level (HE-18.1), so
    the object id is the claim or source they are keyed on.
    """
    claim_id = object_id if question.object_type == "claim" else None
    return progress.auto_na_applies(question, ctx.brain, ctx.source_id, claim_id)


def _criterion_header(question: spec.Question, note: str) -> None:
    st.markdown(f"**{question.criterion_id}** · {question.field_subitem}")
    st.markdown(question.question_text)
    if note:
        st.info(note)
    with st.expander("Criterion definition"):
        if question.check_text:
            st.markdown(question.check_text)
        if question.definition_text:
            st.caption(question.definition_text)


def question_widget(ctx: Ctx, question: spec.Question, object_id: str,
                    *, note: str = "") -> None:
    """One criterion: wording, definition, answer, comment. Autosaves on change.

    The workbook's free-text and comment fields are kept exactly as they are —
    no structured selector replaces or supplements them.

    A criterion the application has determined inapplicable shows a sentence
    instead of a control and records ``N/A`` once, so the stored row says
    "inapplicable" rather than looking unanswered.
    """
    stored = ctx.response(question.question_key, object_id)
    base = f"{ctx.review_id}|{object_id}|{question.question_key}"

    if _auto_na_for(ctx, question, object_id):
        _criterion_header(question, note)
        st.info(question.auto_na_text)
        already = (stored.get("applicability") == spec.AUTO_NA
                   and stored.get("answer") == spec.NA_ANSWER)
        if not ctx.locked and not already:
            _persist(ctx, question, object_id, spec.NA_ANSWER, "", spec.AUTO_NA)
            _remember(ctx, question, object_id, spec.NA_ANSWER, "", spec.AUTO_NA)
        return

    _criterion_header(question, note)

    answer = stored.get("answer")
    comment = stored.get("comment_evidence") or ""

    if question.free_text:
        answer = st.text_area(
            "Answer", value=answer or "", key=base + "|a",
            disabled=ctx.locked, height=110,
            placeholder=question.comment_placeholder,
        )
        new_comment = comment
    else:
        options = list(question.answer_options)
        index = options.index(answer) if answer in options else None
        answer = st.radio("Answer", options, index=index, key=base + "|a",
                          horizontal=True, disabled=ctx.locked,
                          label_visibility="collapsed")
        required = answer in question.comment_required_on
        st.markdown(f"**{spec.COMMENT_LABEL}**")
        note = spec.comment_required_note(question)
        st.caption(note if required else f"{note} Optional here.")
        new_comment = st.text_area(
            spec.COMMENT_LABEL, value=comment, key=base + "|c",
            disabled=ctx.locked, height=90,
            placeholder=question.comment_placeholder,
            label_visibility="collapsed",
        )
        if required and not (new_comment or "").strip():
            st.warning(f"{question.criterion_id}: a comment is required when the answer "
                       f"is {answer}.")

    if not ctx.locked:
        # None and "" are the same absence. An unanswered radio yields None while
        # a preallocated cell holds "", so comparing them raw made every render
        # of every unanswered question queue a write that changed nothing.
        changed = (
            (answer or "") != (stored.get("answer") or "")
            or (new_comment or "") != (stored.get("comment_evidence") or "")
        )
        if changed:
            _persist(ctx, question, object_id, answer, new_comment, spec.APPLICABLE)
            _remember(ctx, question, object_id, answer, new_comment, spec.APPLICABLE)
