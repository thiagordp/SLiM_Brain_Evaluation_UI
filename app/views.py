"""The evaluation screens.

Order of objects, not of questions:

    Source -> Claim -> Concepts -> Relations -> Dataset -> CITES -> Recall -> Review

Every screen shows the structured value from the canonical record; the wiki is
context in the modal, never the thing parsed for an answer.
"""
from __future__ import annotations

import functools
import html

import streamlit as st

import progress
import spec
import store
import ui
from ui import Ctx


# ------------------------------------------------------------- 1. Source
LANGUAGES = {"en": "English", "fr": "French", "de": "German", "it": "Italian",
             "es": "Spanish", "pt": "Portuguese", "nl": "Dutch", "cs": "Czech"}


def _context_metadata(src: dict) -> list[tuple[str, str]]:
    """The bibliographic context, in the words a reader uses.

    Deliberately not the whole record. `file`, `conversion_tool`,
    `ingest_position`, `extraction_model` and `run_id` describe how the Brain
    was built, not what the paper is, and the raw paths in `file` and
    `other_versions` are of no evaluative use — the Design is explicit that they
    must not reach the evaluator. Other versions is therefore reported as a
    count. Everything omitted here remains in the Source wiki.
    """
    language = str(src.get("language") or "")
    others = src.get("other_versions") or []
    return [
        ("Title", src.get("title") or ""),
        ("Authors", "; ".join(src.get("authors") or [])),
        ("Year", str(src.get("year") or "")),
        ("Venue", src.get("venue") or ""),
        ("Venue type", str(src.get("venue_type") or "").replace("_", " ")),
        ("Length", src.get("pages_or_length") or ""),
        # Plain prose: monospace is reserved for the schema values under
        # judgment, and a language tag is context, not one of them.
        ("Language", f"{LANGUAGES[language]} ({language})"
                     if language in LANGUAGES else language),
        ("Other versions", f"{len(others)} additional version"
                           f"{'s' if len(others) != 1 else ''}" if others else ""),
        ("Claims extracted", str(src.get("claims_extracted") or "")),
    ]


def source_section(ctx: Ctx) -> None:
    src = ctx.brain.source(ctx.source_id)
    ui.reset_wiki(f"{ctx.source_id}|source")

    heading, count = st.columns([3, 1], vertical_alignment="bottom")
    heading.subheader("Source attributes")
    # Reserved now, written at the end of the section. An answer given on this
    # run reaches the response cache while the questions render — below this
    # point — so a count computed here would show the evaluator the state they
    # were in before they answered, and stay one interaction behind for ever.
    tally = count.empty()
    st.caption("Evaluate the Source-level classifications produced by the Brain.")

    with st.container(border=True):
        title, wiki = st.columns([3, 1], vertical_alignment="top")
        title.markdown("**Brain values**")
        with wiki:
            ui.wiki_button("Open Source wiki", ui.SOURCE, ctx.source_id,
                           key="wiki_src_section", width="stretch",
                           help="Context only — it changes nothing you have answered")

        # Only the two values under judgment. `other_versions` stopped being a
        # human question on 2026-09-07, so it belongs below with the context
        # rather than among the values someone is being asked about.
        ui.schema_values("Contribution type", src.get("contribution_type"))
        ui.schema_values("Source jurisdiction", src.get("source_jurisdiction"))

        with st.expander("Additional source metadata — context only"):
            ui.definition_list(_context_metadata(src))

    ui.scale_note(spec.RESPONSE_SCALE_NOTE)

    for question in spec.source_section_questions():
        with st.container(border=True):
            ui.question_widget(ctx, question, ctx.source_id)

    items = progress.applicable(
        progress.source_items(ctx.brain, ctx.source_id, ctx.responses))
    done = sum(1 for item in items if progress.item_complete(item, ctx.responses))
    tally.markdown(
        f"<div style='text-align:right'><strong>{done} of {len(items)}</strong>"
        f" questions complete</div>", unsafe_allow_html=True)


# ------------------------------------------------------------- 2. Claims
BADGE = {progress.COMPLETE: "✓", progress.INCOMPLETE: "●", progress.AVAILABLE: "○"}

#: C · Attributes shows the Brain's values once, in the reader's words. The
#: schema names stay in the questions, which are about those fields by name.
CLAIM_ATTRIBUTES = (
    ("Claim type", "claim_type"),
    ("Positive form", "positive_form"),
    ("Basis", "basis"),
    ("Basis qualifier", "basis_qualifier"),
    ("Claim jurisdiction", "claim_jurisdiction"),
    ("Jurisdiction relation", "jurisdiction_relation"),
    ("Jurisdiction inferred", "jurisdiction_inferred"),
    ("Temporal reference", "temporal_reference"),
)

RELATION_MEANINGS = {
    "SUPPORTS": "explicit source-grounded support",
    "ATTACKS": "explicit source-grounded opposition",
    "COMPATIBLE_WITH": "inferred reinforcement without citation grounding",
    "IN_TENSION_WITH": "inferred tension without citation grounding",
    "SAME_AS": "same proposition, claim type and jurisdiction",
}


def _statement_card(claim: dict) -> None:
    """The Claim itself, given the room it deserves — everything else judges it."""
    st.markdown(
        f'<div style="border-left:4px solid rgba(128,128,128,0.5);'
        f'background:rgba(128,128,128,0.08);border-radius:0 6px 6px 0;'
        f'padding:0.7rem 1rem;margin:0.2rem 0 0.9rem">'
        f'<div style="font-size:0.78rem;letter-spacing:0.06em;text-transform:uppercase;'
        f'opacity:0.65;margin-bottom:0.25rem">Claim statement</div>'
        f'<div style="font-size:1.05rem;line-height:1.5">'
        f'{html.escape(claim.get("statement", ""))}</div></div>',
        unsafe_allow_html=True,
    )


def _quotation(text: str, location: str) -> None:
    """An anchor as a reader sees it: the passage, then where it came from."""
    st.markdown(
        f'<blockquote style="border-left:3px solid rgba(128,128,128,0.4);'
        f'margin:0 0 0.6rem;padding:0.15rem 0 0.15rem 0.85rem">'
        f'<div style="line-height:1.5">“{html.escape(text)}”</div>'
        f'<div style="font-size:0.82rem;opacity:0.7;margin-top:0.2rem">'
        f'{html.escape(location) or "location not recorded"}</div></blockquote>',
        unsafe_allow_html=True,
    )


def _anchors(claim: dict) -> None:
    """The Claim's anchors, as quotation cards. One rendering, two places.

    They belong in B, where HE-06 asks whether they ground the Claim at all, and
    again beside HE-05, which asks whether the Claim keeps the force of what
    they say — a comparison nobody should have to make from memory.
    """
    quotes = claim.get("quotes") or []
    if not quotes:
        st.caption("No anchor was recorded for this claim.")
    for quote in quotes:
        _quotation(quote.get("quote", ""), quote.get("location", ""))


def _modality_evidence(claim: dict) -> None:
    """The anchors again, under HE-05, where the force is judged."""
    quotes = claim.get("quotes") or []
    st.caption(f"The Source's own words ({len(quotes)}), repeated from "
               f"B · Grounding so the comparison is here."
               if quotes else "The Source's own words")
    _anchors(claim)


def grounding_panel(ctx: Ctx, claim: dict) -> None:
    """What HE-06 and HE-07 are about: the anchors, and the premise beside them.

    Kept apart on purpose. HE-06 asks whether the quoted passages ground the
    Claim in the source; HE-07 asks whether the premise is a defensible
    reconstruction of the ground the source gives. Showing them as one block
    invites the evaluator to answer both from the same reading.
    """
    with st.container(border=True):
        quotes = claim.get("quotes") or []
        st.markdown(f"**Anchors** ({len(quotes)})" if quotes else "**Anchors**")
        _anchors(claim)

    with st.container(border=True):
        st.markdown("**Premise**")
        premise = (claim.get("premise") or "").strip()
        st.markdown(premise if premise else "_No premise recorded._")
        st.caption(f"Recorded basis: `{claim.get('basis') or '—'}`"
                   + (f" · qualifier: `{claim['basis_qualifier']}`"
                      if claim.get("basis_qualifier") else ""))


def attributes_panel(ctx: Ctx, claim: dict) -> None:
    """Every attribute under judgment in this section, once, in one place."""
    with st.container(border=True):
        st.markdown("**Brain values**")
        ui.definition_list([
            (label, ui.value_markup(claim.get(field)))
            for label, field in CLAIM_ATTRIBUTES
        ], skip_empty=False)
        if claim.get("dataset"):
            ui.wiki_button("Open Dataset wiki", ui.DATASET, claim["dataset"],
                           key=f"wiki_dst|{claim['id']}",
                           help="The dataset this claim rests on — evaluated in its "
                                "own section, shown here for context")


def concept_panel(ctx: Ctx, claim: dict) -> None:
    """Concepts grouped by family, with lifecycle status and a registry."""
    families = ctx.brain.concepts_by_family(claim.get("concepts"))
    with st.container(border=True):
        head, browse = st.columns([3, 1], vertical_alignment="top")
        head.markdown("**Mapped concepts, by family**")
        with browse:
            # The anchor grid and the full registry used to sit here as two
            # expanders, which pushed the questions off the screen on every
            # claim. They are the same material, one keystroke away instead of
            # permanently underfoot.
            ui.wiki_button("Browse Concept registry", ui.CONCEPT_REGISTRY,
                           key=f"wiki_reg|{claim['id']}", width="stretch",
                           help="Every concept in the Brain, with the anchor grid, "
                                "searchable")
        any_mapped = False
        for family in spec.CONCEPT_FAMILIES:
            concepts = families.get(family) or []
            st.markdown(f"<div style='font-weight:600;margin:0.5rem 0 0.1rem'>{family}"
                        f"</div>", unsafe_allow_html=True)
            if not concepts:
                st.caption("None mapped")
                continue
            any_mapped = True
            for concept in concepts:
                cid = concept.get("id", "")
                text, wiki = st.columns([5, 1], vertical_alignment="center")
                text.markdown(
                    f"<div style='line-height:1.4'><strong>"
                    f"{html.escape(concept.get('label', ''))}</strong> "
                    f"<code>{html.escape(concept.get('status', '?'))}</code><br>"
                    f"<span style='opacity:0.75;font-size:0.88rem'>"
                    f"{html.escape(concept.get('definition', ''))}</span></div>",
                    unsafe_allow_html=True)
                with wiki:
                    ui.wiki_button("Open wiki", ui.CONCEPT, cid, width="stretch",
                                   key=f"wiki_cpt|{claim['id']}|{cid}")
        if not any_mapped:
            st.caption("No concept is mapped to this claim.")


def relations_panel(ctx: Ctx, claim: dict) -> None:
    """HE-16: one judgment per edge; the claim-level value is derived.

    The methodology is the workbook's, unchanged: the 7 September meeting ended
    before the relation criteria were discussed, so only the presentation is new.
    """
    relations = ctx.brain.relations_of(claim["id"])
    if not relations:
        st.caption("No cross-source edge touches this claim. Nothing to evaluate here.")
        return

    summary = progress.he16_for_claim(ctx.brain, claim["id"], ctx.edge_responses)
    st.caption(f"HE-16 is derived from the judgments below, as in the workbook — "
               f"currently **{summary or '—'}**")

    question = spec.EDGE_QUESTION
    with st.expander("Criterion definition"):
        st.markdown(question.check_text)
        st.caption(question.definition_text)
        st.markdown("\n".join(f"- `{name}` — {meaning}"
                              for name, meaning in RELATION_MEANINGS.items()))
        st.caption("Extracted and inferred relations are different forms of evidence "
                   "and must not be treated interchangeably.")

    for relation in relations:
        _relation_card(ctx, claim, relation, question)


def _relation_card(ctx: Ctx, claim: dict, relation: dict, question) -> None:
    other = ctx.brain.claims.get(relation["other_claim_id"], {})
    other_source = other.get("source", "")
    edge_key = store.edge_key_of(relation)
    stored = ctx.edge_responses.get(edge_key, {})
    base = ui.widget_base(ctx, claim["id"], edge_key)

    with st.container(border=True):
        left, middle, right = st.columns([4, 2, 4], vertical_alignment="top")
        with left:
            st.caption(f"THIS CLAIM · {claim['id']} · "
                       f"{ctx.brain.work_id(ctx.source_id)}")
            st.markdown(claim.get("statement", ""))
        with middle:
            arrow = "→" if relation["direction"] == "outgoing" else "←"
            st.markdown(
                f"<div style='text-align:center'>"
                f"<div style='font-size:1.6rem;line-height:1'>{arrow}</div>"
                f"<div style='font-weight:600;margin-top:0.2rem'>"
                f"<code>{html.escape(relation['type'])}</code></div>"
                f"<div style='font-size:0.82rem;opacity:0.72;margin-top:0.3rem'>"
                f"{html.escape(str(relation.get('grounding') or '—'))}<br>"
                f"plausibility: {html.escape(str(relation.get('plausibility') or '—'))}"
                f"</div></div>", unsafe_allow_html=True)
        with right:
            st.caption(f"RELATED CLAIM · {other.get('id', '?')} · "
                       f"{ctx.brain.work_id(other_source)}")
            st.markdown(other.get("statement", ""))
            claim_col, source_col = st.columns(2)
            with claim_col:
                ui.wiki_button("Open claim", ui.CLAIM, other.get("id", ""),
                               key=f"wiki_other|{base}", width="stretch")
            with source_col:
                ui.wiki_button("Open Source wiki", ui.SOURCE, other_source,
                               key=f"wiki_other_src|{base}", width="stretch")
        if relation.get("note"):
            st.caption(f"**Why the Brain linked them** — {relation['note']}")

        st.markdown(f"**{question.criterion_id}** · {question.question_text}")
        options = list(question.answer_options)
        current = stored.get("label_correct")
        answer = st.radio(
            "Label correct?", options,
            index=options.index(current) if current in options else None,
            key=base + "|a", horizontal=True, disabled=ctx.locked,
            label_visibility="collapsed",
        )
        required = answer in question.comment_required_on
        st.markdown(f"**{spec.COMMENT_LABEL}**")
        note = spec.comment_required_note(question)
        st.caption(note if required else f"{note} Optional here.")
        comment = st.text_area(
            "Comment / correct label", value=stored.get("comment_correct_label") or "",
            key=base + "|c", disabled=ctx.locked, height=80,
            label_visibility="collapsed",
            placeholder=question.comment_placeholder,
        )
        if required and not (comment or "").strip():
            st.warning(f"{question.criterion_id}: a comment is required when the "
                       f"label is not correct.")

        if not ctx.locked:
            changed = (answer != stored.get("label_correct")
                       or (comment or "") != (stored.get("comment_correct_label") or ""))
            if changed:
                row = {**stored, "label_correct": answer,
                       "comment_correct_label": comment}
                ctx.edge_responses[edge_key] = row

                def written(stamp, row=row):
                    if stamp:
                        row["updated_at"] = stamp

                ui.queue().submit(
                    store.edge_response_key(ctx.review_id, claim["id"], edge_key),
                    store.save_edge_response,
                    ctx.review_id, host_claim_id=claim["id"], edge_key=edge_key,
                    edge_from=relation.get("from"), edge_to=relation.get("to"),
                    other_claim_id=relation.get("other_claim_id"),
                    edge_type=relation.get("type"), label_correct=answer,
                    comment=comment, source_id=ctx.source_id,
                    on_success=written,
                )


def _questions_of(ctx: Ctx, claim: dict, subsection: str) -> None:
    """The criteria of one subsection, in the instrument's order and wording."""
    created = ctx.brain.candidate_created_for(claim["id"])
    for question in spec.questions_for(subsection):
        # A conditional follow-up appears only once its parent has been answered
        # negatively. HE-20 is binary, so HE-20.b appears exactly on "No".
        if question.applicability == spec.IF_PARENT_IS_NEGATIVE:
            parent = ctx.response(question.parent_key, claim["id"])
            if parent.get("answer") not in spec.NEGATIVE:
                continue
        note = ""
        if question.question_key == "CLAIM_HE21" and created:
            note = "Candidate created for this claim: " + ", ".join(
                f"`{c['id']}` {c.get('label', '')}" for c in created)
        # HE-05 asks whether the Claim preserves the modality of the Source, so
        # the Source's words are shown with the question rather than a
        # subsection away.
        evidence = (functools.partial(_modality_evidence, claim)
                    if question.question_key == "CLAIM_HE05" else None)
        with st.container(border=True):
            ui.question_widget(ctx, question, claim["id"], note=note,
                               evidence=evidence)
            if question.question_key == "CLAIM_HE25":
                ui.wiki_button("Compare claims from this paper", ui.SOURCE_CLAIMS,
                               ctx.source_id, key=f"wiki_dup|{claim['id']}",
                               help="Every claim the Brain extracted from this "
                                    "source, to check whether this one repeats another")


#: What each subsection puts in front of the evaluator before its questions.
SUBSECTION_PANEL = {
    spec.SUB_GROUNDING: grounding_panel,
    spec.SUB_ATTRIBUTES: attributes_panel,
    spec.SUB_CONCEPTS: concept_panel,
}


def claims_section(ctx: Ctx) -> None:
    claims = ctx.brain.claims_of(ctx.source_id)
    if not claims:
        st.warning("This source has no claims in the Brain.")
        return

    idx_key = f"claim_idx|{ctx.review_id}"
    st.session_state[idx_key] = current_index(idx_key, len(claims))

    # Every claim is directly selectable, in any order. The marker says how each
    # one stands; it never restricts which can be opened.
    # Everything on this page is drawn from what the widgets hold now, not from
    # what was cached before the evaluator's last click. `question_widget`
    # mirrors a change into `ctx.responses` as it renders, so anything computed
    # from the cache above the widgets is one interaction behind.
    claim_at = current_index(idx_key, len(claims))
    live_items = progress.applicable(progress.claim_items(
        ctx.brain, ctx.source_id, claims[claim_at]["id"], ctx.responses))
    answers, changed = ui.live_answers(ctx, live_items)
    edges, touched_edge = ui.live_edges(
        ctx, claims[claim_at]["id"],
        ctx.brain.relations_of(claims[claim_at]["id"]))
    touched = {item.question.section for item in changed}
    if touched_edge:
        touched.add(spec.SUB_RELATIONS)

    states = progress.claim_states(ctx.brain, ctx.source_id, answers, edges)
    index = st.selectbox(
        "Go to claim", list(range(len(claims))),
        format_func=lambda i: (
            f"{BADGE[states[claims[i]['id']]]} {i+1}. {claims[i]['id']} "
            f"— {claims[i]['statement'][:64]}…"
        ),
        key=idx_key,
    )
    claim = claims[index]
    ui.reset_wiki(f"{ctx.source_id}|claim|{claim['id']}")

    completed = sum(1 for state in states.values() if state == progress.COMPLETE)

    heading, tally = st.columns([3, 2], vertical_alignment="bottom")
    heading.subheader(f"Claim {index + 1} of {len(claims)} · {claim['id']}")
    # Reserved and written after the questions: an answer given on this run
    # reaches the response cache below this point, so a count taken here would
    # show the evaluator where they stood before they answered.
    claim_tally = tally.empty()

    context = st.columns([1, 1, 3])
    with context[0]:
        ui.wiki_button("Open Source wiki", ui.SOURCE, ctx.source_id,
                       key=f"wiki_claim_src|{claim['id']}", width="stretch")
    with context[1]:
        ui.wiki_button("View all claims from this paper", ui.SOURCE_CLAIMS,
                       ctx.source_id, key=f"wiki_claim_all|{claim['id']}",
                       width="stretch",
                       help="For judging whether this claim duplicates another")

    _statement_card(claim)
    _resume_hint(ctx, claims, index, idx_key)
    st.progress(completed / len(claims))
    st.caption(f"{completed} of {len(claims)} claims complete in this paper")
    ui.scale_note(spec.RESPONSE_SCALE_NOTE)

    parts = progress.claim_subsection_progress(
        ctx.brain, ctx.source_id, claim["id"], answers, edges)
    open_label = _open_subsection(
        f"claim_open|{ctx.review_id}|{claim['id']}", parts, touched)
    for label, done, total, state in parts:
        count = f"{done}/{total}" if total else "none applicable"
        with st.expander(f"{BADGE[state] if total else '—'}  {label} · {count}",
                         expanded=label == open_label):
            panel = SUBSECTION_PANEL.get(label)
            if panel:
                panel(ctx, claim)
            if label == spec.SUB_RELATIONS:
                relations_panel(ctx, claim)
            else:
                _questions_of(ctx, claim, label)

    done, total = progress.claim_progress(ctx.brain, ctx.source_id, claim["id"],
                                          answers, edges)
    claim_tally.markdown(
        f"<div style='text-align:right'><strong>{done}/{total}</strong>"
        f" applicable items complete</div>", unsafe_allow_html=True)

    _claim_nav(ctx, claims, index, idx_key, done, total)


def _open_subsection(key: str, parts, touched) -> str:
    """Which subsection is open — decided by where the evaluator is working.

    It used to be pinned when the claim was first opened and never moved, so
    answering inside C closed C and reopened A on every single answer.

    Now an interaction makes that subsection the active one and it stays open
    while anything in it is still missing: a ``No`` waiting for its comment, or
    a parent that has just revealed a conditional follow-up. Once it is
    genuinely complete the next incomplete one opens instead, which is the part
    of the old behaviour the evaluator asked to keep.
    """
    if touched:
        st.session_state[key] = sorted(touched)[0] if len(touched) > 1 \
            else next(iter(touched))
    state_of = {label: (total, state) for label, _, total, state in parts}
    active = st.session_state.get(key)
    if active in state_of:
        total, state = state_of[active]
        if total and state != progress.COMPLETE:
            return active
    unfinished = [label for label, _, total, state in parts
                  if total and state != progress.COMPLETE]
    return unfinished[0] if unfinished else parts[0][0]


def _claim_nav(ctx: Ctx, claims, index: int, idx_key: str, done: int, total: int) -> None:
    """Previous and next. Neither is ever a gate.

    An incomplete claim says so and lets the evaluator go; the paper cannot be
    marked complete while anything is missing, which is where completeness is
    enforced. On the last claim the forward control names where it actually
    leads rather than pretending there is another claim.
    """
    st.divider()
    last = index >= len(claims) - 1
    nav = st.columns([2, 2, 3])
    with nav[0]:
        st.button("← Previous claim", disabled=index == 0, width="stretch",
                  on_click=_move_claim(idx_key, -1, len(claims)), key="prev_claim")
    with nav[1]:
        if last:
            st.button(f"{progress.SECTION_TAB['datasets']} →", width="stretch",
                      key="claims_to_datasets",
                      on_click=_go_to_section(ctx, "datasets"))
        else:
            st.button("Next claim →", width="stretch", key="next_claim",
                      on_click=_move_claim(idx_key, +1, len(claims)))
    with nav[2]:
        st.caption(f"Claim {index + 1} of {len(claims)}")

    outstanding = total - done
    if outstanding:
        st.caption(f"This claim still has {outstanding} item(s) to answer. That does "
                   f"not block you — move on and come back; the paper can only be "
                   f"marked complete once nothing is missing.")


def _go_to_section(ctx: Ctx, section: str):
    def callback():
        st.session_state[f"section|{ctx.review_id}"] = section
        ui.close_wiki()
        ui.request_scroll()
    return callback


def _resume_hint(ctx: Ctx, claims, index: int, idx_key: str) -> None:
    """Offer the place work was left off. A shortcut, never a redirect.

    The evaluator stays wherever they are unless they press it.
    """
    first = progress.first_incomplete_claim(ctx.brain, ctx.source_id, ctx.responses,
                                            ctx.edge_responses)
    if first == index:
        return
    target = claims[first]
    if progress.claim_complete(ctx.brain, ctx.source_id, target["id"],
                               ctx.responses, ctx.edge_responses):
        return
    st.button(
        f"Resume at claim {first + 1} ({target['id']})",
        key=f"resume|{ctx.review_id}",
        help="The first claim still needing work. You are free to stay here.",
        on_click=_go_to_claim(idx_key, first),
    )


def _go_to_claim(idx_key: str, index: int):
    def callback():
        st.session_state[idx_key] = index
        ui.request_scroll()
    return callback


def current_index(idx_key: str, total: int) -> int:
    """The selected index, tolerating Streamlit's widget-state cleanup.

    The key belongs to a selectbox. When the evaluator leaves the section, that
    widget is no longer rendered and Streamlit drops its state, so the key can be
    missing — or present but None — by the time a click is processed. That is
    reachable in normal use: leave Claims for Datasets, or click twice on a slow
    connection, and a queued click can arrive after the cleanup.
    """
    try:
        value = st.session_state[idx_key]
    except (KeyError, AttributeError):
        return 0
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return max(0, min(value, max(total - 1, 0)))


def _move_claim(idx_key: str, delta: int, total: int):
    def callback():
        current = current_index(idx_key, total)
        st.session_state[idx_key] = max(0, min(current + delta, max(total - 1, 0)))
        ui.close_wiki()
        ui.request_scroll()
    return callback


# ----------------------------------------------------------- 3. Datasets
SUB_DATASET_NODE = "A · Dataset node"
SUB_DATASET_ATTRIBUTES = "B · Dataset attributes"

#: The Dataset record as a reader sees it. `run_id` says which extraction run
#: produced the node, which is build provenance and not something anyone here is
#: asked about; it stays in the Dataset wiki.
DATASET_FIELDS = (
    ("Introduced by", "introduced_by"),
    ("Used by", "used_by"),
    ("Language", "language"),
    ("Jurisdiction", "jurisdiction"),
    ("Document types", "document_types"),
    ("Size", "size"),
    ("Annotation", "annotation"),
    ("Agreement reported", "agreement_reported"),
    ("Availability", "availability"),
)


def _tally(column, done: int, total: int, noun: str = "questions"):
    """The local count, right-aligned beside a heading."""
    column.markdown(
        f"<div style='text-align:right'><strong>{done} of {total}</strong>"
        f" {noun} complete</div>", unsafe_allow_html=True)


def _subsection_parts(ctx: Ctx, groups, object_id: str, answers) -> list:
    """Each Dataset subsection's count and state, from the live answers."""
    parts = []
    for label, questions in groups:
        wanted = {q.criterion_id for q in questions}
        items = [i for i in progress.applicable(
            progress.dataset_items(ctx.brain, ctx.source_id, answers))
            if i.object_id == object_id and i.question.criterion_id in wanted]
        done = sum(1 for i in items if progress.item_complete(i, answers))
        state = (progress.COMPLETE if items and done == len(items)
                 else progress.INCOMPLETE if done else progress.AVAILABLE)
        parts.append((label, done, len(items), state))
    return parts


def _subsection(ctx: Ctx, label: str, questions, object_id: str,
                done: int, total: int, state: str, expanded: bool) -> None:
    """One collapsible group of criteria, carrying its own state and count."""
    with st.expander(f"{BADGE[state]}  {label} · {done}/{total}",
                     expanded=expanded):
        for question in questions:
            with st.container(border=True):
                ui.question_widget(ctx, question, object_id)


def datasets_section(ctx: Ctx) -> None:
    datasets = ctx.brain.datasets_of(ctx.source_id)

    heading, tally = st.columns([3, 2], vertical_alignment="bottom")
    heading.subheader("Datasets")
    count = tally.empty()
    st.caption("Evaluate the Dataset records the Brain created for this Source. "
               "A Dataset node stands for a body of legal material the paper "
               "introduces or uses — not for every corpus the paper mentions.")

    if datasets:
        idx_key = f"ds_idx|{ctx.review_id}"
        st.session_state[idx_key] = current_index(idx_key, len(datasets))
        index = st.selectbox(
            "Go to dataset", range(len(datasets)),
            format_func=lambda i: f"{i+1}. {datasets[i]['id']} — {datasets[i].get('name','')}",
            key=idx_key,
        )
        dataset = datasets[index]
        did = dataset["id"]
        ui.reset_wiki(f"{ctx.source_id}|dataset|{did}")

        # As on the claim page: what the widgets hold now, so a count drawn
        # above them is not one interaction behind.
        live_items = [i for i in progress.applicable(
            progress.dataset_items(ctx.brain, ctx.source_id, ctx.responses))
            if i.object_id == did]
        answers, changed = ui.live_answers(ctx, live_items)

        st.markdown(f"##### Dataset {index + 1} of {len(datasets)} · `{did}`")
        with st.container(border=True):
            name, wiki = st.columns([3, 1], vertical_alignment="top")
            name.markdown(f"**{dataset.get('name', '')}**")
            with wiki:
                ui.wiki_button("Open Dataset wiki", ui.DATASET, did, width="stretch",
                               key=f"wiki_ds|{did}",
                               help="The generated record — context only")
            ui.definition_list(
                [(label, ui.value_markup(dataset.get(field)))
                 for label, field in DATASET_FIELDS], skip_empty=False)

            using = ctx.brain.claims_using_dataset(ctx.source_id, did)
            with st.expander(f"Claims resting on this Dataset ({len(using)})"):
                if not using:
                    st.caption("No claim from this source rests on this dataset.")
                for claim in using:
                    row, detail = st.columns([5, 1], vertical_alignment="center")
                    row.markdown(f"`{claim['id']}` {claim['statement']}")
                    with detail:
                        ui.wiki_button("View details", ui.CLAIM, claim["id"],
                                       width="stretch",
                                       key=f"wiki_ds_claim|{did}|{claim['id']}")

        ui.scale_note(spec.RESPONSE_SCALE_NOTE)

        questions = spec.dataset_questions()
        groups = [
            (SUB_DATASET_NODE,
             [q for q in questions if q.criterion_id.startswith("HE-14")]),
            (SUB_DATASET_ATTRIBUTES,
             [q for q in questions if q.criterion_id.startswith("HE-15")]),
        ]
        parts = _subsection_parts(ctx, groups, did, answers)
        # HE-14.3 is asked for the Source as a whole, below both groups, so an
        # edit to it belongs to neither and must not pull one of them open.
        of_group = {q.criterion_id: label for label, group in groups
                    for q in group}
        touched = {of_group[i.question.criterion_id] for i in changed
                   if i.question.criterion_id in of_group}
        open_label = _open_subsection(
            f"ds_open|{ctx.review_id}|{did}", parts, touched)
        for (label, group), (_, done, total, state) in zip(groups, parts):
            _subsection(ctx, label, group, did, done, total, state,
                        expanded=label == open_label)

        if len(datasets) > 1:
            nav = st.columns([2, 2, 3])
            nav[0].button("← Previous dataset", disabled=index == 0, width="stretch",
                          key="prev_ds", on_click=_move_claim(idx_key, -1, len(datasets)))
            nav[1].button("Next dataset →", disabled=index >= len(datasets) - 1,
                          width="stretch", key="next_ds",
                          on_click=_move_claim(idx_key, +1, len(datasets)))
            nav[2].caption(f"Dataset {index + 1} of {len(datasets)}")
    else:
        ui.reset_wiki(f"{ctx.source_id}|dataset|none")
        st.info("The Brain created no Dataset nodes for this Source.")
        st.caption("Nothing to evaluate node by node. The recall question below is "
                   "still asked: no node is not the same as nothing to record.")

    st.divider()
    st.markdown("##### Dataset recall — Source as a whole")
    st.caption("Asked once for the paper, not once per Dataset: whether the Brain "
               "created a Dataset node for every body of legal material this Source "
               "introduces or uses.")
    with st.container(border=True):
        ui.question_widget(ctx, spec.dataset_recall_question(), ctx.source_id)

    items = progress.applicable(
        progress.dataset_items(ctx.brain, ctx.source_id, ctx.responses))
    _tally(count, sum(1 for i in items if progress.item_complete(i, ctx.responses)),
           len(items))


# -------------------------------------------------------------- 4. CITES
def _citation_row(ctx: Ctx, source_id: str, key: str, arrow: str = "") -> None:
    """One cited or citing paper: what it is, and the way to read it."""
    source = ctx.brain.source(source_id)
    text, wiki = st.columns([5, 1], vertical_alignment="center")
    text.markdown(
        f"<div style='line-height:1.45'>"
        f"<code>{html.escape(source_id)}</code> · "
        f"<code>{html.escape(ctx.brain.work_id(source_id))}</code>"
        f"{'  ·  ' + html.escape(arrow) if arrow else ''}<br>"
        f"<strong>{html.escape(source.get('title', ''))}</strong><br>"
        f"<span style='opacity:0.75;font-size:0.88rem'>"
        f"{html.escape(_authors_short(source))} · {html.escape(str(source.get('year') or ''))}"
        f"</span></div>", unsafe_allow_html=True)
    with wiki:
        ui.wiki_button("Open Source wiki", ui.SOURCE, source_id, width="stretch",
                       key=key)


def _authors_short(source: dict) -> str:
    authors = source.get("authors") or []
    if not authors:
        return ""
    written = authors[0].split(",")[0]
    if len(authors) == 2:
        written += f" & {authors[1].split(',')[0]}"
    elif len(authors) > 2:
        written += " et al."
    return written


def cites_section(ctx: Ctx) -> None:
    ui.reset_wiki(f"{ctx.source_id}|cites")
    outgoing = ctx.brain.cites_from(ctx.source_id)
    incoming = ctx.brain.cites_to(ctx.source_id)
    here = ctx.brain.work_id(ctx.source_id)

    heading, tally = st.columns([3, 2], vertical_alignment="bottom")
    heading.subheader("Citations within the Brain")
    count = tally.empty()
    st.caption("This section evaluates citations between this paper and other "
               "Sources represented in the Brain. **It is not the paper's complete "
               "bibliography.** A citation becomes a CITES edge only when the cited "
               "publication is itself a Source in the Brain.")
    st.caption("References to publications outside the Brain, and citations to "
               "legislation, case law or other primary legal sources, are "
               "intentionally excluded.")

    ui.wiki_button("Browse Brain Sources", ui.SOURCE_REGISTRY, ctx.source_id,
                   key="wiki_src_registry",
                   help="Which publications the Brain holds — needed to judge "
                        "whether a citation should have become an edge")

    with st.container(border=True):
        st.markdown(f"**Citations from this paper — evaluate ({len(outgoing)})**")
        if not outgoing:
            st.caption("The Brain generated no outgoing CITES edges for this Source.")
        for edge in outgoing:
            _citation_row(ctx, edge["to"], f"wiki_cit|{edge['to']}",
                          arrow=f"{here} → {ctx.brain.work_id(edge['to'])}")

    with st.container(border=True):
        st.markdown(f"**Other Brain Sources citing this paper — context only "
                    f"({len(incoming)})**")
        st.caption("Shown for orientation only. These citations are not evaluated "
                   "on this page.")
        if not incoming:
            st.caption("No other Brain Source cites this paper.")
        for edge in incoming:
            _citation_row(ctx, edge["from"], f"wiki_cited_by|{edge['from']}",
                          arrow=f"{ctx.brain.work_id(edge['from'])} → {here}")

    ui.scale_note(spec.RESPONSE_SCALE_NOTE)

    for question in spec.cites_questions():
        if question.applicability == spec.IF_PARENT_IS_NEGATIVE:
            parents = (question.parent_key or "").split("|")
            if not any(ctx.response(p, ctx.source_id).get("answer") in spec.NEGATIVE
                       for p in parents):
                continue
        with st.container(border=True):
            ui.question_widget(ctx, question, ctx.source_id)

    items = progress.applicable(
        progress.cites_items(ctx.brain, ctx.source_id, ctx.responses))
    _tally(count, sum(1 for i in items if progress.item_complete(i, ctx.responses)),
           len(items))


# --------------------------------------------- 5. Source-level completeness
RECALL_DISTINCTION = (
    "**Claim recall and conceptual coverage test different failures.** Claim "
    "recall asks whether a central proposition is missing. Conceptual coverage "
    "asks whether the extracted and mapped Claims, taken together, represent the "
    "paper's mapping-relevant concepts."
)


def recall_section(ctx: Ctx) -> None:
    ui.reset_wiki(f"{ctx.source_id}|recall")
    claims = ctx.brain.claims_of(ctx.source_id)

    heading, tally = st.columns([3, 2], vertical_alignment="bottom")
    heading.subheader("Source-level completeness")
    count = tally.empty()
    st.caption("Now assess the paper as a whole, after reviewing all of its "
               "extracted Claims. Judge against the full paper you read, not "
               "against the wiki.")
    ui.scale_note(spec.RESPONSE_SCALE_NOTE)

    questions = {q.criterion_id: q for q in spec.recall_questions()}

    # ---- A · Claim recall
    st.markdown("##### A · Claim recall")
    with st.container(border=True):
        head, wiki = st.columns([3, 1], vertical_alignment="top")
        head.markdown(f"**Extracted Claims ({len(claims)})**")
        with wiki:
            ui.wiki_button("Open Source wiki", ui.SOURCE, ctx.source_id,
                           width="stretch", key="wiki_recall_src")
        for i, claim in enumerate(claims, 1):
            row, detail = st.columns([6, 1], vertical_alignment="center")
            row.markdown(
                f"<div style='line-height:1.45'><code>{html.escape(claim['id'])}</code>"
                f"<br>{html.escape(claim['statement'])}</div>",
                unsafe_allow_html=True)
            with detail:
                ui.wiki_button("View details", ui.CLAIM, claim["id"], width="stretch",
                               key=f"wiki_recall|{claim['id']}")

    _recall_question(ctx, questions["HE-19.1"])
    _recall_question(ctx, questions["HE-19.3"])

    # ---- B · Conceptual coverage
    st.markdown("##### B · Conceptual coverage")
    st.caption(RECALL_DISTINCTION)
    with st.container(border=True):
        head, browse = st.columns([3, 1], vertical_alignment="top")
        head.markdown("**Concepts represented across this Source**")
        with browse:
            ui.wiki_button("Browse Concept registry", ui.CONCEPT_REGISTRY,
                           width="stretch", key="wiki_recall_reg",
                           help="Every concept in the Brain, with the anchor grid")
        families = ctx.brain.concepts_of_source(ctx.source_id)
        for family in spec.CONCEPT_FAMILIES:
            concepts = families.get(family) or []
            st.markdown(f"<div style='font-weight:600;margin:0.5rem 0 0.1rem'>"
                        f"{family}</div>", unsafe_allow_html=True)
            if not concepts:
                st.caption("None mapped anywhere in this Source")
                continue
            for concept in concepts:
                row, wiki = st.columns([5, 1], vertical_alignment="center")
                row.markdown(
                    f"<div style='line-height:1.4'><strong>"
                    f"{html.escape(concept['label'])}</strong> "
                    f"<code>{html.escape(concept['status'])}</code> · "
                    f"<span style='opacity:0.75'>{concept['claims']} "
                    f"{'Claim' if concept['claims'] == 1 else 'Claims'}</span></div>",
                    unsafe_allow_html=True)
                with wiki:
                    ui.wiki_button("Open wiki", ui.CONCEPT, concept["id"],
                                   width="stretch",
                                   key=f"wiki_srccpt|{concept['id']}")

    _recall_question(ctx, questions["HE-20.S"])
    _recall_question(ctx, questions["HE-20.S.b"])

    items = progress.applicable(
        progress.recall_items(ctx.brain, ctx.source_id, ctx.responses))
    _tally(count, sum(1 for i in items if progress.item_complete(i, ctx.responses)),
           len(items))


def _recall_question(ctx: Ctx, question) -> None:
    """A source-level criterion, with its conditional follow-up honoured."""
    if question.applicability == spec.IF_PARENT_IS_NEGATIVE:
        parents = (question.parent_key or "").split("|")
        if not any(ctx.response(p, ctx.source_id).get("answer") in spec.NEGATIVE
                   for p in parents):
            return
    with st.container(border=True):
        ui.question_widget(ctx, question, ctx.source_id)


# ------------------------------------------------------------- 6. Review
#: Free-text findings the evaluator recorded. These are results, not gaps: a
#: paper with four missing Concepts listed is a *completed* evaluation that
#: found four missing Concepts. Keeping them apart from "items requiring
#: attention" is the whole point of the Review page.
RECORDED = (
    ("Missing Claims", "SOURCE_HE19_3", "HE-19.3"),
    ("Missing mapping-relevant Concepts (Source level)", "SOURCE_HE20S_B", "HE-20.S.b"),
    ("Missing or spurious CITES", "SOURCE_HE18_3", "HE-18.3"),
)

STATUS_MARK = {progress.COMPLETE: "✓", progress.INCOMPLETE: "●",
               progress.AVAILABLE: "○", progress.LOCKED: "○"}


def _criterion_titles() -> dict[str, str]:
    return {q.criterion_id: q.field_subitem for q in spec.QUESTIONS}


def review_section(ctx: Ctx) -> None:
    ui.reset_wiki(f"{ctx.source_id}|review")
    st.subheader("Review paper")
    st.caption("Check that the evaluation is complete before marking this paper "
               "complete. You may return to any section and revise your responses.")
    ui.show_held()

    missing = progress.missing_items(ctx.brain, ctx.source_id, ctx.responses,
                                     ctx.edge_responses)
    review = store.get_review(ctx.phase_id, ctx.evaluator_id, ctx.source_id) or {}

    _evaluation_status(ctx, missing)
    _items_requiring_attention(ctx, missing)
    _recorded_findings(ctx)
    _evaluation_overview(ctx)
    _completion(ctx, missing, review)


def _evaluation_status(ctx: Ctx, missing) -> None:
    st.markdown("#### Evaluation status")
    stats = progress.counts(ctx.brain, ctx.source_id, ctx.responses, ctx.edge_responses)
    if missing:
        st.warning(f"**Incomplete — {len(missing)} item"
                   f"{'s' if len(missing) != 1 else ''} require"
                   f"{'' if len(missing) != 1 else 's'} attention**")
    else:
        st.success("**Ready to complete** — all required evaluation fields are filled.")
    total = max(stats["items"], 1)
    st.progress(min(stats["answered"] / total, 1.0))

    states = progress.section_states(ctx.brain, ctx.source_id, ctx.responses,
                                     ctx.edge_responses)
    per_section: dict[str, int] = {}
    for item in missing:
        per_section[item.section] = per_section.get(item.section, 0) + 1

    for section in progress.SECTION_IDS:
        if section == "review":
            continue
        row, action = st.columns([5, 1], vertical_alignment="center")
        outstanding = per_section.get(section, 0)
        if section == "claims":
            detail = (f"{stats['claims_done']} of {stats['claims']} Claims complete")
        elif outstanding:
            detail = f"{outstanding} item{'s' if outstanding != 1 else ''} incomplete"
        else:
            detail = "Complete"
        row.markdown(f"{STATUS_MARK[states[section]]}  **"
                     f"{progress.SECTION_LABEL[section]}** — {detail}")
        with action:
            st.button("Open", key=f"open_sec|{section}", width="stretch",
                      on_click=_go_to_section(ctx, section))


ATTENTION_LIMIT = 25


def _items_requiring_attention(ctx: Ctx, missing) -> None:
    st.markdown("#### Items requiring attention")
    if not missing:
        st.caption("Nothing is missing. Every applicable criterion has an answer, "
                   "and every required comment and conditional field is filled.")
        return
    st.caption("Complete the following before this paper can be marked complete. "
               "A **No** answer is not listed here: it is a completed judgment.")
    titles = _criterion_titles()
    shown = missing[:ATTENTION_LIMIT]
    if len(missing) > len(shown):
        # A paper that has barely been started has every item outstanding, and a
        # list of two hundred identical cards is not a list anyone reads. The
        # section summary above already says where the work is; this list earns
        # its place as the paper nears completion, which is when it is short.
        st.info(f"Showing the first {len(shown)} of {len(missing)}. Work through "
                f"the sections above; as the paper nears completion this list "
                f"becomes the whole of what is left.")
    for i, item in enumerate(shown):
        with st.container(border=True):
            text, action = st.columns([5, 1], vertical_alignment="center")
            title = titles.get(item.what, "")
            text.markdown(
                f"<div style='line-height:1.45'>"
                f"<span style='opacity:0.72;font-size:0.85rem'>"
                f"{html.escape(item.where)}</span><br>"
                f"<strong>{html.escape(item.what)}</strong>"
                f"{' · ' + html.escape(title) if title else ''}<br>"
                f"<span style='opacity:0.8'>{html.escape(item.reason)}</span></div>",
                unsafe_allow_html=True)
            with action:
                st.button("Go to item", key=f"goto|{i}", width="stretch",
                          on_click=_go_to_item(ctx, item))


def _go_to_item(ctx: Ctx, item):
    def callback():
        st.session_state[f"section|{ctx.review_id}"] = item.section
        if item.claim_index is not None:
            st.session_state[f"claim_idx|{ctx.review_id}"] = item.claim_index
        ui.close_wiki()
        ui.request_scroll()
    return callback


def _recorded_findings(ctx: Ctx) -> None:
    """What the evaluator found, as opposed to what they have yet to do."""
    st.markdown("#### Recorded omissions and defects")
    st.caption("These are findings you recorded during the evaluation. They do not "
               "prevent completion.")

    def written(question_key: str, object_id: str) -> str:
        row = ctx.response(question_key, object_id)
        return (row.get("answer") or "").strip()

    groups: list[tuple[str, list[str]]] = []
    for label, question_key, _criterion in RECORDED:
        text = written(question_key, ctx.source_id)
        groups.append((label, [text] if text else []))

    # HE-20.b is per claim, so it is gathered rather than read from one row.
    per_claim = []
    for claim in ctx.brain.claims_of(ctx.source_id):
        text = written("CLAIM_HE20B", claim["id"])
        if text:
            per_claim.append(f"`{claim['id']}` — {text}")
    groups.insert(1, ("Missing Concepts (Claim level)", per_claim))

    # Dataset recall records what is missing in its comment, not in a field of
    # its own, so the finding is the comment beside a negative answer.
    recall = ctx.response("SOURCE_HE14_3", ctx.source_id)
    dataset_finding = []
    if (recall.get("answer") or "") in spec.NEGATIVE:
        dataset_finding = [(recall.get("comment_evidence") or "").strip()
                           or "_Recorded as incomplete, with no detail given._"]
    groups.insert(3, ("Missing Dataset nodes", dataset_finding))

    if not any(entries for _, entries in groups):
        st.caption("You have recorded no omissions or defects for this paper.")
        return
    for label, entries in groups:
        with st.expander(f"{label} ({len(entries)})"):
            if not entries:
                st.caption("None recorded.")
            for entry in entries:
                st.markdown(entry)


def _evaluation_overview(ctx: Ctx) -> None:
    """The answers as recorded, collapsed. Not a second chance to change them."""
    st.markdown("#### Evaluation overview")
    st.caption("What you have recorded so far, section by section. Open a section "
               "to read it back; change anything from the section itself.")

    states = progress.section_states(ctx.brain, ctx.source_id, ctx.responses,
                                     ctx.edge_responses)
    gathered = {
        "source": progress.source_items(ctx.brain, ctx.source_id, ctx.responses),
        "datasets": progress.dataset_items(ctx.brain, ctx.source_id, ctx.responses),
        "cites": progress.cites_items(ctx.brain, ctx.source_id, ctx.responses),
        "recall": progress.recall_items(ctx.brain, ctx.source_id, ctx.responses),
    }
    # In the order the evaluator worked, which is the order of the section bar.
    for section in progress.SECTION_IDS:
        if section == "review":
            continue
        if section == "claims":
            _claims_overview(ctx, states)
            continue
        items = progress.applicable(gathered[section])
        done = sum(1 for i in items if progress.item_complete(i, ctx.responses))
        with st.expander(f"{STATUS_MARK[states[section]]}  "
                         f"{progress.SECTION_LABEL[section]} · {done}/{len(items)}"):
            _answer_table(ctx, items)


def _claims_overview(ctx: Ctx, states) -> None:
    """One row per claim, as the workbook's Summary tab does.

    Fifteen criteria for every claim would reproduce the whole evaluation, which
    is exactly what this page exists not to do.
    """
    claims = ctx.brain.claims_of(ctx.source_id)
    done = sum(1 for c in claims
               if progress.claim_complete(ctx.brain, ctx.source_id, c["id"],
                                          ctx.responses, ctx.edge_responses))
    with st.expander(f"{STATUS_MARK[states['claims']]}  "
                     f"{progress.SECTION_LABEL['claims']} · {done}/{len(claims)} "
                     f"Claims complete"):
        for index, claim in enumerate(claims):
            claim_done, claim_total = progress.claim_progress(
                ctx.brain, ctx.source_id, claim["id"], ctx.responses,
                ctx.edge_responses)
            state = (progress.COMPLETE if claim_done == claim_total
                     else progress.INCOMPLETE if claim_done else progress.AVAILABLE)
            row, action = st.columns([5, 1], vertical_alignment="center")
            row.markdown(f"{STATUS_MARK[state]}  `{claim['id']}` · "
                         f"{claim_done}/{claim_total} items")
            with action:
                st.button("Open", key=f"open_claim|{claim['id']}", width="stretch",
                          on_click=_go_to_claim_from_review(ctx, index))


def _go_to_claim_from_review(ctx: Ctx, index: int):
    def callback():
        st.session_state[f"section|{ctx.review_id}"] = "claims"
        st.session_state[f"claim_idx|{ctx.review_id}"] = index
        ui.close_wiki()
        ui.request_scroll()
    return callback


def _answer_table(ctx: Ctx, items) -> None:
    if not items:
        st.caption("Nothing applies in this section.")
        return
    for item in items:
        row = ctx.response(item.question.question_key, item.object_id)
        answer = (row.get("answer") or "").strip()
        if row.get("applicability") == spec.AUTO_NA:
            shown = "_Not applicable_"
        elif not answer:
            shown = "_Not answered_"
        elif item.question.free_text:
            shown = answer
        else:
            shown = f"**{answer}**"
        left, right = st.columns([1, 3], gap="small")
        left.markdown(f"`{item.question.criterion_id}`")
        right.markdown(shown)


def _completion(ctx: Ctx, missing, review: dict) -> None:
    st.divider()
    if ctx.locked:
        st.info("This paper has been finally submitted. It is read-only.")
        return

    read_confirmed = bool(review.get("pdf_read_confirmed"))
    if not read_confirmed:
        st.error("You have not confirmed reading the full paper.")

    st.markdown("#### Paper status")
    complete = review.get("status") == store.STATUS_COMPLETE
    if complete:
        st.success("**Complete.** You can still change any answer until the final "
                   "submission of this phase, which locks every paper together.")
        if st.button("Reopen for editing"):
            store.unmark_complete(ctx.review_id)
            st.rerun()
        return

    ready = not missing and read_confirmed
    if ready:
        st.markdown("**Ready to complete** — all required evaluation fields are "
                    "filled. You may still return to any section and revise your "
                    "responses before marking the paper complete.")
    else:
        st.markdown(f"**Incomplete** — {len(missing)} required item"
                    f"{'s' if len(missing) != 1 else ''} still need"
                    f"{'' if len(missing) != 1 else 's'} attention.")

    if st.button("Mark paper complete", type="primary", disabled=not ready):
        # The one place that waits for storage. Everything shown above came from
        # the session's cache; before recording a claim about the answers, get
        # them into storage and then read them back, because the claim is about
        # what is stored and not about what this browser remembers.
        with st.spinner("Saving your last answers…"):
            settled, outstanding, detail = ui.settle()
        if not settled:
            st.error(
                f"{outstanding} answer(s) are not yet stored, so the paper was not "
                f"marked complete. They are kept and retried — nothing is lost. "
                + (f"Last error: {detail}" if detail else "Try again in a moment.")
            )
        else:
            ctx.refresh()          # re-read: bypasses the session cache
            still_missing = progress.missing_items(
                ctx.brain, ctx.source_id, ctx.responses, ctx.edge_responses)
            if still_missing:
                ui.hold(
                    f"{len(still_missing)} item(s) are still missing once the stored "
                    f"answers are re-read, so the paper was not marked complete. "
                    f"The list above has been refreshed from storage."
                )
                st.rerun()
            else:
                store.mark_complete(ctx.review_id)
                st.rerun()
    st.caption("Marking a paper complete does not lock it. Final submission happens "
               "once, from the paper list, so you can revisit earlier papers as your "
               "judgment settles across the set.")


EVALUATION_STANDARD = (
    "**How to judge.** Ask whether the output is a *defensible* reconstruction or "
    "classification under the schema — not whether you would have coded it identically. "
    "Where another reading would also be plausible, a defensible choice is not a failure. "
    "Use **In part** when something is partly right, and say in the comment exactly what "
    "is wrong or missing."
)


RENDERERS = {
    "source": source_section,
    "claims": claims_section,
    "datasets": datasets_section,
    "cites": cites_section,
    "recall": recall_section,
    "review": review_section,
}
