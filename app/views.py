"""The evaluation screens: Source, Claims, Datasets, Claim recall, Review.

Each value under judgment is shown next to its question, with the Brain's own
definition directly below the question. Schema names and values are shown in
normal typography.
"""
from __future__ import annotations

import html
import re

import streamlit as st

import conceptsearch
import progress
import sheets
import spec
import store
import ui
from brain import CONCEPT_FAMILIES, concept_label, family_label
from ui import Ctx

MARK = {progress.COMPLETE: "✓", progress.INCOMPLETE: "●", progress.AVAILABLE: "○",
        progress.INFO: "·"}
MARK_LEGEND = "○ not started · ● in progress · ✓ complete"

#: Interface headings for a question's definition passages, where the frozen
#: entry's own label would not say which passage is which. Rendered apart from
#: the passages, never joined into them.
DEFINITION_HEADINGS = {
    "DATASET_JURISDICTION": {
        "dataset.jurisdiction": "Dataset jurisdiction",
        "claim.claim_jurisdiction": "Referenced jurisdiction definition",
    },
}


# -------------------------------------------------------------- navigation
def _section_key(ctx: Ctx) -> str:
    return f"section|{ctx.review_id}"


def go_to_section(ctx: Ctx, section: str, claim_index: int | None = None,
                  dataset_index: int | None = None) -> None:
    st.session_state[_section_key(ctx)] = section
    if claim_index is not None:
        st.session_state[f"claim_idx|{ctx.review_id}"] = claim_index
    if dataset_index is not None:
        st.session_state[f"ds_idx|{ctx.review_id}"] = dataset_index
    ui.close_wiki()
    ui.request_scroll()


def _index(key: str, total: int) -> int:
    value = st.session_state.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < total:
        value = 0
    st.session_state[key] = value
    return value


def _move(key: str, delta: int, total: int) -> None:
    st.session_state[key] = max(0, min(total - 1, st.session_state.get(key, 0) + delta))
    ui.close_wiki()
    ui.request_scroll()


def _live(ctx: Ctx) -> Ctx:
    """The context with the session's current review data (for callbacks)."""
    ctx.data = ui.cached_review(ctx.review_id)
    return ctx


# ------------------------------------------------------------ answer controls
def _answer_changed(ctx: Ctx, question: spec.Question, object_id: str, key: str) -> None:
    ctx = _live(ctx)
    answer = st.session_state.get(key) or ""
    changes = {"answer": answer}
    if question.related_claim_on and answer not in question.related_claim_on:
        changes["related_claim_id"] = ""
    ui.save_response(ctx, question, object_id, **changes)


def _text_changed(ctx: Ctx, question: spec.Question, object_id: str, key: str,
                  field: str) -> None:
    ui.save_response(_live(ctx), question, object_id,
                     **{field: st.session_state.get(key) or ""})


def _concept_changed(ctx: Ctx, question: spec.Question, claim_id: str,
                     concept_id: str, key: str, field: str) -> None:
    ui.save_concept(_live(ctx), question, claim_id, concept_id,
                    **{field: st.session_state.get(key) or ""})


def _relation_changed(ctx: Ctx, relation_key: str, key: str, field: str) -> None:
    ui.save_relation(_live(ctx), relation_key, **{field: st.session_state.get(key) or ""})


def _radio(ctx: Ctx, options, stored: str, key: str, on_change, args,
           horizontal: bool = True):
    options = list(options)
    return st.radio("Answer", options,
                    index=options.index(stored) if stored in options else None,
                    key=key, horizontal=horizontal, label_visibility="collapsed",
                    disabled=ctx.locked, on_change=on_change, args=args)


def _comment_box(ctx: Ctx, question: spec.Question, answer: str, stored: str,
                 key: str, on_change, args) -> None:
    if not spec.comment_visible(question, answer):
        return
    required = spec.comment_required(question, answer)
    label = question.comment_label + ("" if required else f" ({spec.OPTIONAL.lower()[:-1]})")
    st.text_area(label, value=stored, key=key, height=80, disabled=ctx.locked,
                 on_change=on_change, args=args,
                 help=question.comment_help or None)
    if question.comment_help:
        st.caption(question.comment_help)
    if required and not (st.session_state.get(key, stored) or "").strip():
        st.warning("A comment is required for this answer.")


def scalar_question(ctx: Ctx, question: spec.Question, object_id: str, *,
                    before=None, show_text: bool = True) -> str:
    """A RESPONSES question: wording, definitions, answer, comment. Autosaves."""
    record = ctx.data.response(question.key, object_id)
    if show_text:
        st.markdown(f"**{question.text}**")
    if question.definitions and not question.field:
        ui.definitions(question.definitions)
    if before is not None:
        before()
    key = ui.wkey(ctx, question.key, object_id)
    answer = _radio(ctx, question.options, record.get("answer", ""), key + "|a",
                    _answer_changed, (ctx, question, object_id, key + "|a"))
    _comment_box(ctx, question, answer or "", record.get("comment", ""), key + "|c",
                 _text_changed, (ctx, question, object_id, key + "|c", "comment"))
    return answer or ""


def field_question(ctx: Ctx, question: spec.Question, object_id: str,
                   value, shown_value: str) -> None:
    """Schema-field pattern: name, assigned value, full definition, question."""
    with st.container(border=True):
        st.markdown(f"##### {question.title}")
        ui.value_line("Assigned value", shown_value)
        ui.definitions(question.definitions, headings=DEFINITION_HEADINGS.get(question.key))
        scalar_question(ctx, question, object_id)


# ------------------------------------------------------------------ Source
def source_section(ctx: Ctx) -> None:
    ui.reset_wiki(f"{ctx.source_id}|source")
    brain, source = ctx.brain, ctx.brain.source(ctx.source_id)
    st.subheader("Source")
    st.caption("Context for the evaluation. Nothing on this page is evaluated.")
    rows = [("Title", source.get("title")), ("Authors", source.get("authors")),
            ("Year", source.get("year")), ("Venue", source.get("venue")),
            ("Venue type", source.get("venue_type")),
            ("Language", source.get("language")), ("DOI", source.get("doi")),
            ("Publication date", source.get("publication_date")),
            ("Paper file", brain.pdf_name(ctx.source_id))]
    with st.container(border=True):
        for label, value in rows:
            if label == "Authors":
                shown = "; ".join(value or []) or "None recorded"
            elif label in ("Venue type", "Language"):
                shown = ui.display_value("language" if label == "Language" else "venue_type",
                                         value)
            else:
                shown = str(value) if value not in (None, "") else "None recorded"
            ui.value_line(label, shown)
    st.markdown("#### Source wiki")
    with st.container(border=True):
        st.markdown(ui.wiki_markdown(brain.source_body(ctx.source_id)))
    st.button("Continue to Claims →", type="primary", key="source_to_claims",
              on_click=go_to_section, args=(ctx, "claims"))


# ------------------------------------------------------------------ Claims
def claims_section(ctx: Ctx) -> None:
    brain = ctx.brain
    claims = brain.claims_of(ctx.source_id)
    if not claims:
        ui.reset_wiki(f"{ctx.source_id}|claims|none")
        st.subheader("Claims")
        st.info("No Claims were extracted from this Source. There is nothing to "
                "evaluate here; the Source is still evaluated under Claim recall.")
        st.button("Continue to Datasets →", key="claims_empty_next",
                  on_click=go_to_section, args=(ctx, "datasets"))
        return

    idx_key = f"claim_idx|{ctx.review_id}"
    index = _index(idx_key, len(claims))
    claim = claims[index]
    cid = claim["id"]
    ui.reset_wiki(f"{ctx.source_id}|claim|{cid}")
    states = progress.claim_states(brain, ctx.source_id, ctx.data)

    head, pick = st.columns([2, 3])
    head.subheader(f"Claim {index + 1} of {len(claims)}")
    head.caption(cid)
    with pick:
        st.selectbox(
            "Go to Claim", range(len(claims)), key=idx_key,
            format_func=lambda i: (f"{MARK[states[claims[i]['id']]]} {i + 1}. "
                                   f"{claims[i]['id']} — "
                                   f"{claims[i].get('statement', '')[:70]}…"),
            on_change=lambda: (ui.close_wiki(), ui.request_scroll()))
    ui.statement_card("Claim statement", claim.get("statement", ""))
    parts = progress.claim_parts(brain, ctx.source_id, cid, ctx.data)
    st.caption("  ·  ".join(f"{MARK[state]} {part} {done}/{total}"
                            for part, done, total, state in parts if total)
               + f"   —   {MARK_LEGEND}")
    counts = {part: (done, total) for part, done, total, _ in parts}

    _part_heading(spec.PART_CLAIM, counts)
    claim_evaluation(ctx, claim, claims)
    _part_heading(spec.PART_FIELDS, counts)
    schema_fields(ctx, claim)
    _part_heading(spec.PART_CONCEPTS, counts)
    concepts_part(ctx, claim)
    _part_heading(spec.PART_RELATIONS, counts)
    relations_part(ctx, claim)

    st.divider()
    cols = st.columns([1, 1, 3])
    cols[0].button("← Previous Claim", key="prev_claim", disabled=index == 0,
                   width="stretch", on_click=_move, args=(idx_key, -1, len(claims)))
    if index + 1 < len(claims):
        cols[1].button("Next Claim →", key="next_claim", width="stretch",
                       on_click=_move, args=(idx_key, 1, len(claims)))
    else:
        cols[1].button("Datasets →", key="claims_to_datasets", width="stretch",
                       on_click=go_to_section, args=(ctx, "datasets"))


def _part_heading(part: str, counts: dict) -> None:
    done, total = counts.get(part, (0, 0))
    st.markdown(f"### {part}")
    if total:
        st.caption(f"{done} of {total} complete")


def claim_evaluation(ctx: Ctx, claim: dict, claims: list[dict]) -> None:
    cid = claim["id"]
    anchors = claim.get("anchors") or []

    with st.container(border=True):
        q1 = spec.Q1
        answer = scalar_question(ctx, q1, cid)
        if answer in q1.related_claim_on:
            record = ctx.data.response(q1.key, cid)
            stored = record.get("related_claim_id", "")
            options = progress.evaluated_claims(ctx.brain, ctx.source_id, ctx.data,
                                                exclude=cid)
            if stored and stored not in options:
                options.append(stored)
            by_id = {c["id"]: c for c in claims}
            key = ui.wkey(ctx, q1.key, cid, "related")
            st.selectbox(
                "Restatement of", options,
                index=options.index(stored) if stored in options else None,
                placeholder="Select the Claim this one restates",
                format_func=lambda c: f"{c} — {by_id.get(c, {}).get('statement', '')[:110]}",
                key=key, disabled=ctx.locked, on_change=_text_changed,
                args=(ctx, q1, cid, key, "related_claim_id"))
            if not options:
                st.caption("No other Claim of this Source has been evaluated yet. "
                           "Evaluate the restated Claim first, then return here.")
            elif not stored:
                st.warning("Select the Claim this one restates.")

    for question in spec.claim_scalar_questions(spec.PART_CLAIM)[1:]:
        with st.container(border=True):
            if question.key == "CLAIM_Q03_MODALITY":
                scalar_question(ctx, question, cid, before=lambda: _anchors(anchors))
            elif question.key == "CLAIM_Q05_GROUNDING":
                scalar_question(ctx, question, cid, before=lambda: _anchors(anchors))
            else:
                scalar_question(ctx, question, cid)


def _anchors(anchors) -> None:
    st.caption(f"Anchors ({len(anchors)})")
    for anchor in anchors:
        ui.quotation(anchor.get("quote", ""), anchor.get("location", ""))


def schema_fields(ctx: Ctx, claim: dict) -> None:
    for question in spec.claim_scalar_questions(spec.PART_FIELDS):
        value = claim.get(question.field)
        field_question(ctx, question, claim["id"], value,
                       ui.display_value(question.field, value))


# ----------------------------------------------------------------- Concepts
def concepts_part(ctx: Ctx, claim: dict) -> None:
    brain, cid = ctx.brain, claim["id"]
    assigned = brain.concepts_of_claim(cid)

    with st.container(border=True):
        st.markdown(f"**{spec.Q12.text}**")
        st.caption("Each Concept assigned to this Claim is judged on its own.")
        for family, ids in brain.group_by_family(assigned).items():
            if not ids:
                continue
            st.markdown(
                f"<div style='border-top:1px solid rgba(128,128,128,0.3);"
                f"margin:0.6rem 0 0.2rem;padding-top:0.4rem;font-weight:700'>"
                f"{html.escape(family_label(family))}</div>", unsafe_allow_html=True)
            for concept_id in ids:
                _concept_judgment(ctx, spec.Q12, cid, concept_id)

    candidates = brain.candidates_of_claim(cid)
    if candidates:
        with st.container(border=True):
            st.markdown(f"**{spec.Q13.text}**")
            ui.definitions(spec.Q13.definitions)
            for concept_id in candidates:
                _concept_judgment(ctx, spec.Q13, cid, concept_id)

    with st.container(border=True):
        missing_concepts(ctx, claim)


def _concept_judgment(ctx: Ctx, question: spec.Question, cid: str, concept_id: str) -> None:
    concept = ctx.brain.concept(concept_id)
    record = ctx.data.concept(question.key, cid, concept_id)
    st.markdown(f"**{concept_label(concept_id)}**")
    st.caption(f"{spec.value_label(concept.get('status', ''))} · {concept_id}")
    ui.concept_definition(concept.get("definition", ""))
    key = ui.wkey(ctx, question.key, cid, concept_id)
    answer = _radio(ctx, question.options, record.get("answer", ""), key + "|a",
                    _concept_changed,
                    (ctx, question, cid, concept_id, key + "|a", "answer"))
    _comment_box(ctx, question, answer or "", record.get("comment", ""), key + "|c",
                 _concept_changed, (ctx, question, cid, concept_id, key + "|c", "comment"))
    st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)


# -------------------------------------------------------------- Question 14
def _q14_state(ctx: Ctx, cid: str) -> None:
    """Keep the stored Question 14 state consistent with the selection."""
    existing, proposed = progress.q14_selection(ctx.data, cid)
    current = ctx.data.response(spec.Q14.key, cid).get("answer", "")
    if existing or proposed:
        wanted = spec.Q14_MISSING
    else:
        wanted = current if current == spec.Q14_NONE_MISSING else spec.Q14_NOT_EVALUATED
    ui.save_response(ctx, spec.Q14, cid, answer=wanted)


def _select_concept(ctx: Ctx, cid: str, entry: dict, active: bool) -> None:
    ctx = _live(ctx)
    key = store.selection_key(ctx.review_id, cid, entry["id"])
    ui.save_selection(ctx, sheets.MISSING_CONCEPTS, key,
                      store.pair_lookup(cid, entry["id"]), {
                          "selection_key": key, "review_id": ctx.review_id,
                          "source_id": ctx.source_id, "claim_id": cid,
                          "concept_id": entry["id"], "concept_family": entry["family"],
                          "concept_status": entry["status"],
                          "active": store.TRUE if active else store.FALSE})
    _q14_state(ctx, cid)


def _remove_proposal(ctx: Ctx, cid: str, row: dict) -> None:
    ctx = _live(ctx)
    ui.save_selection(ctx, sheets.PROPOSED_CONCEPTS, row["proposal_key"],
                      store.pair_lookup(cid, row["proposal_id"]),
                      {**row, "active": store.FALSE})
    _q14_state(ctx, cid)


def _none_missing(ctx: Ctx, cid: str, key: str) -> None:
    ctx = _live(ctx)
    checked = bool(st.session_state.get(key))
    ui.save_response(ctx, spec.Q14, cid,
                     answer=spec.Q14_NONE_MISSING if checked else spec.Q14_NOT_EVALUATED)


def proposal_id(name: str, family: str) -> str:
    return f"{re.sub(r'[^a-z0-9]+', '-', conceptsearch.normalise(name)).strip('-')}--{family}"


def _propose(ctx: Ctx, cid: str, name_key: str, family_key: str, why_key: str) -> None:
    ctx = _live(ctx)
    name = (st.session_state.get(name_key) or "").strip()
    family = st.session_state.get(family_key)
    if not name or not family:
        st.session_state[f"{name_key}|error"] = "Give a name and a Concept family."
        return
    pid = proposal_id(name, family)
    key = store.proposal_key(ctx.review_id, cid, pid)
    ui.save_selection(ctx, sheets.PROPOSED_CONCEPTS, key, store.pair_lookup(cid, pid), {
        "proposal_key": key, "review_id": ctx.review_id, "source_id": ctx.source_id,
        "claim_id": cid, "proposal_id": pid, "name": name, "family": family,
        "explanation": (st.session_state.get(why_key) or "").strip(),
        "active": store.TRUE})
    _q14_state(ctx, cid)
    for k in (name_key, why_key):
        st.session_state[k] = ""
    st.session_state[family_key] = None
    st.session_state.pop(f"{name_key}|error", None)


def missing_concepts(ctx: Ctx, claim: dict) -> None:
    brain, cid = ctx.brain, claim["id"]
    st.markdown(f"**{spec.Q14.text}**")
    vocabulary = brain.vocabulary(spec.concept_grid())
    existing, proposed = progress.q14_selection(ctx.data, cid)
    selected_ids = {r["concept_id"] for r in existing}
    excluded = set(brain.concepts_of_claim(cid)) | selected_ids
    eligible = [e for e in vocabulary if e["id"] not in excluded]
    by_id = {e["id"]: e for e in vocabulary}
    state = ctx.data.response(spec.Q14.key, cid).get("answer", "")

    # ---- selected: a separate, persistent area
    with st.container(border=True):
        st.markdown("**Selected missing Concepts**")
        if not existing and not proposed:
            st.caption("None selected." if state != spec.Q14_NONE_MISSING else
                       "You recorded that no additional Concepts are missing.")
        for row in existing:
            entry = by_id.get(row["concept_id"], {"label": concept_label(row["concept_id"])})
            name, remove = st.columns([8, 1], vertical_alignment="center")
            name.markdown(html.escape(entry["label"]))
            remove.button("×", key=ui.wkey(ctx, "q14rm", cid, row["concept_id"]),
                          disabled=ctx.locked, help=f"Remove {entry['label']}",
                          on_click=_select_concept,
                          args=(ctx, cid, {"id": row["concept_id"],
                                           "family": row.get("concept_family", ""),
                                           "status": row.get("concept_status", "")}, False))
        for row in proposed:
            name, remove = st.columns([8, 1], vertical_alignment="center")
            name.markdown(f"Proposed · {html.escape(row['name'])} "
                          f"({html.escape(family_label(row['family']))})")
            remove.button("×", key=ui.wkey(ctx, "q14rmp", cid, row["proposal_id"]),
                          disabled=ctx.locked, help=f"Remove the proposal {row['name']}",
                          on_click=_remove_proposal, args=(ctx, cid, row))
        none_key = ui.wkey(ctx, "q14none", cid)
        st.session_state[none_key] = state == spec.Q14_NONE_MISSING
        st.checkbox("No additional Concepts are missing", key=none_key,
                    disabled=ctx.locked or bool(existing or proposed),
                    on_change=_none_missing, args=(ctx, cid, none_key))

    # ---- search and browse: independent of the selection
    query = st.text_input("Search Concepts", key=f"q14search|{ctx.review_id}|{cid}",
                          placeholder="Type one or more words",
                          disabled=ctx.locked)
    results = conceptsearch.search(query, eligible)
    groups = {family: [] for family in CONCEPT_FAMILIES}
    for entry in results:
        groups.setdefault(entry["family"], []).append(entry)
    if query and not results:
        st.caption("No Concept matches. You can propose a new one below.")
    for family, entries in groups.items():
        if query and not entries:
            continue
        with st.expander(f"{family_label(family)} ({len(entries)})",
                         expanded=bool(query)):
            if not entries:
                st.caption("No further Concept in this family.")
            for entry in entries:
                text, definition, action = st.columns([6, 2, 1],
                                                      vertical_alignment="center")
                with text:
                    st.markdown(f"**{html.escape(entry['label'])}**")
                    st.caption(spec.value_label(entry["status"]))
                with definition:
                    if entry["definition"]:
                        with st.popover("Definition"):
                            st.markdown(html.escape(entry["definition"]))
                    else:
                        st.caption(ui.NO_CONCEPT_DEFINITION)
                with action:
                    st.button("Add", key=ui.wkey(ctx, "q14add", cid, entry["id"]),
                              disabled=ctx.locked, on_click=_select_concept,
                              args=(ctx, cid, entry, True))

    with st.expander("Propose new Concept"):
        name_key = ui.wkey(ctx, "q14name", cid)
        family_key = ui.wkey(ctx, "q14family", cid)
        why_key = ui.wkey(ctx, "q14why", cid)
        st.text_input("Proposed Concept name", key=name_key, disabled=ctx.locked)
        st.selectbox("Concept family", list(CONCEPT_FAMILIES), index=None,
                     format_func=family_label, key=family_key, disabled=ctx.locked,
                     placeholder="Select a family")
        st.text_area("Why the existing vocabulary is insufficient (optional)",
                     key=why_key, height=70, disabled=ctx.locked)
        st.button("Add proposal", key=ui.wkey(ctx, "q14propose", cid),
                  disabled=ctx.locked, on_click=_propose,
                  args=(ctx, cid, name_key, family_key, why_key))
        error = st.session_state.get(f"{name_key}|error")
        if error:
            st.warning(error)
        st.caption("A proposal is stored with this evaluation only. It does not "
                   "create or change a Concept in the Brain.")


# ---------------------------------------------------------------- Relations
def relations_part(ctx: Ctx, claim: dict) -> None:
    brain, cid = ctx.brain, claim["id"]
    hosted = brain.relations_from_claim(cid)
    incoming = brain.relations_to_claim(cid)
    if not hosted:
        st.caption("No Relation starts from this Claim." + (
            " Relations that end at it are listed below as context." if incoming else ""))
    for n, relation in enumerate(hosted, 1):
        with st.container(border=True):
            _relation_card(ctx, relation, cid, n)
            record = ctx.data.relation(relation["key"])
            for question in spec.relation_questions():
                st.markdown(f"**{question.text}**")
                ui.definitions(question.definitions)
                key = ui.wkey(ctx, question.key, relation["key"])
                answer_field = f"{question.column}_answer"
                comment_field = f"{question.column}_comment"
                answer = _radio(ctx, question.options, record.get(answer_field, ""),
                                key + "|a", _relation_changed,
                                (ctx, relation["key"], key + "|a", answer_field))
                _comment_box(ctx, question, answer or "", record.get(comment_field, ""),
                             key + "|c", _relation_changed,
                             (ctx, relation["key"], key + "|c", comment_field))
    if incoming:
        with st.expander(f"Relations ending at this Claim, evaluated in another "
                         f"Source's review ({len(incoming)})"):
            for n, relation in enumerate(incoming, 1):
                _relation_card(ctx, relation, cid, f"in{n}")
                st.divider()


def _relation_card(ctx: Ctx, relation: dict, current: str, n) -> None:
    brain = ctx.brain
    left, middle, right = st.columns([5, 2, 5])
    for column, label, claim_id in ((left, "From Claim", relation["from"]),
                                    (right, "To Claim", relation["to"])):
        with column:
            marker = " (this Claim)" if claim_id == current else ""
            st.markdown(f"**{label}**{marker}")
            st.caption(f"{claim_id} · {brain.source_of_claim(claim_id)}")
            st.markdown(html.escape(brain.claim(claim_id).get("statement", "")))
            if claim_id != current:
                b1, b2 = st.columns(2)
                with b1:
                    ui.wiki_button("Open Claim", ui.CLAIM, claim_id,
                                   key=f"rel_clm|{relation['key']}|{n}")
                with b2:
                    ui.wiki_button("Open Source", ui.SOURCE, brain.source_of_claim(claim_id),
                                   key=f"rel_src|{relation['key']}|{n}")
    with middle:
        st.markdown("<div style='text-align:center;padding-top:1.6rem'>"
                    f"<div style='font-size:0.8rem;opacity:0.7'>Relation type</div>"
                    f"<div style='font-weight:600'>{html.escape(spec.value_label(relation['type']))}"
                    f"</div><div style='font-size:1.4rem'>→</div>"
                    f"<div style='font-size:0.8rem;opacity:0.7'>Grounding</div>"
                    f"<div>{html.escape(spec.value_label(relation.get('grounding', '')))}"
                    "</div></div>", unsafe_allow_html=True)
    st.markdown(f"**Relation Note:** {html.escape(relation.get('note', ''))}")


# ----------------------------------------------------------------- Datasets
def datasets_section(ctx: Ctx) -> None:
    brain = ctx.brain
    ids = brain.dataset_ids_of(ctx.source_id)
    st.subheader("Datasets")
    if not ids:
        ui.reset_wiki(f"{ctx.source_id}|dataset|none")
        st.info("No Claim of this Source rests on a Dataset, so there is no Dataset "
                "to evaluate.")
        st.button("Continue to Claim recall →", key="datasets_empty_next",
                  type="primary", on_click=go_to_section, args=(ctx, "recall"))
        return

    idx_key = f"ds_idx|{ctx.review_id}"
    index = _index(idx_key, len(ids))
    did = ids[index]
    dataset = brain.dataset(did)
    ui.reset_wiki(f"{ctx.source_id}|dataset|{did}")

    head, pick = st.columns([2, 3])
    head.markdown(f"#### Dataset {index + 1} of {len(ids)}")
    head.caption(did)
    if len(ids) > 1:
        pick.selectbox("Go to Dataset", range(len(ids)), key=idx_key,
                       format_func=lambda i: f"{i + 1}. {brain.dataset(ids[i]).get('name', ids[i])}",
                       on_change=lambda: (ui.close_wiki(), ui.request_scroll()))
    ui.statement_card("Dataset", dataset.get("name", did))
    ui.wiki_button("Open Dataset wiki", ui.DATASET, did, key=f"ds_wiki|{did}")
    resting = brain.claims_using_dataset(ctx.source_id, did)
    with st.expander(f"Claims resting on this Dataset ({len(resting)})", expanded=False):
        for claim in resting:
            st.markdown(f"**{claim['id']}** — {html.escape(claim.get('statement', ''))}")

    items = progress.dataset_items(brain, ctx.source_id, did)
    done = sum(1 for i in items if progress.item_complete(i, ctx.data))
    st.caption(f"{done} of {len(items)} complete")
    for question in spec.dataset_questions():
        if question.key == "DATASET_NODE":
            with st.container(border=True):
                scalar_question(ctx, question, did)
        elif question.key == "DATASET_DESCRIPTION":
            with st.container(border=True):
                st.markdown(f"##### {question.title}")
                ui.statement_card("Current Dataset description",
                                  dataset.get("description", "") or "None recorded")
                ui.definitions(question.definitions)
                scalar_question(ctx, question, did)
        else:
            value = dataset.get(question.field)
            field_question(ctx, question, did, value,
                           _dataset_value(ctx, question.field, value))

    st.divider()
    cols = st.columns([1, 1, 3])
    cols[0].button("← Previous Dataset", key="prev_ds", disabled=index == 0,
                   width="stretch", on_click=_move, args=(idx_key, -1, len(ids)))
    if index + 1 < len(ids):
        cols[1].button("Next Dataset →", key="next_ds", width="stretch",
                       on_click=_move, args=(idx_key, 1, len(ids)))
    else:
        cols[1].button("Claim recall →", key="ds_to_recall", width="stretch",
                       on_click=go_to_section, args=(ctx, "recall"))


def _dataset_value(ctx: Ctx, field: str, value) -> str:
    if field == "introduced_by" and value in ctx.brain.sources:
        return f"{value} — {ctx.brain.source(value).get('title', '')}"
    return ui.display_value(field, value)


# -------------------------------------------------------------- Claim recall
def recall_section(ctx: Ctx) -> None:
    ui.reset_wiki(f"{ctx.source_id}|recall")
    brain = ctx.brain
    claims = brain.claims_of(ctx.source_id)
    st.subheader("Claim recall")
    with st.container(border=True):
        st.markdown(f"**Extracted Claims ({len(claims)})**")
        if not claims:
            st.caption("No Claims were extracted from this Source.")
        for n, claim in enumerate(claims, 1):
            st.markdown(f"{n}. {html.escape(claim.get('statement', ''))}  \n"
                        f"<span style='opacity:0.65;font-size:0.85rem'>{claim['id']}</span>",
                        unsafe_allow_html=True)
        ui.wiki_button("Open Source wiki", ui.SOURCE, ctx.source_id, key="recall_src")

    question = spec.RECALL
    record = ctx.data.response(question.key, ctx.source_id)
    with st.container(border=True):
        st.markdown(f"**{question.text}**")
        ui.definitions(question.definitions)
        key = ui.wkey(ctx, question.key, ctx.source_id)
        answer = st.segmented_control(
            "Claim recall", list(question.options), selection_mode="single",
            default=record.get("answer") or None, key=key + "|a",
            label_visibility="collapsed", disabled=ctx.locked,
            on_change=_answer_changed, args=(ctx, question, ctx.source_id, key + "|a"))
        st.caption("Ordered from None to All.")

    child = spec.MISSING_CLAIMS
    if spec.child_visible(child, answer or ""):
        stored = ctx.data.response(child.key, ctx.source_id).get("answer", "")
        with st.container(border=True):
            st.markdown(f"**{child.text}**")
            st.caption(child.comment_help)
            key = ui.wkey(ctx, child.key, ctx.source_id)
            st.text_area("Missing Claims", value=stored, key=key, height=160,
                         label_visibility="collapsed", disabled=ctx.locked,
                         on_change=_text_changed,
                         args=(ctx, child, ctx.source_id, key, "answer"))
            if not (st.session_state.get(key, stored) or "").strip():
                st.warning("Required for this answer.")


# ------------------------------------------------------------------ Review
def review_section(ctx: Ctx) -> None:
    ui.reset_wiki(f"{ctx.source_id}|review")
    brain, sid = ctx.brain, ctx.source_id
    st.subheader("Review")
    ui.show_held()
    missing = progress.missing_items(brain, sid, ctx.data)
    counts = progress.counts(brain, sid, ctx.data)
    states = progress.section_states(brain, sid, ctx.data)

    if missing:
        st.warning(f"Incomplete: {len(missing)} item(s) need an answer.")
    else:
        st.success("Every applicable item is answered.")
    if counts["items"]:
        st.progress(counts["done"] / counts["items"])
    st.caption(f"{counts['done']} of {counts['items']} items · "
               f"{counts['claims_done']} of {counts['claims']} Claims complete")

    for section in ("claims", "datasets", "recall"):
        items = progress.section_items(section, brain, sid, ctx.data)
        done = sum(1 for i in items if progress.item_complete(i, ctx.data))
        row, action = st.columns([5, 1], vertical_alignment="center")
        detail = (f"{done} of {len(items)} items" if items
                  else "nothing to evaluate in this Source")
        row.markdown(f"{MARK[states[section]]} **{progress.SECTION_LABEL[section]}** — {detail}")
        action.button("Open", key=f"open_sec|{section}", on_click=go_to_section,
                      args=(ctx, section))

    if missing:
        st.markdown("#### Items requiring an answer")
        _missing_groups(ctx, missing)

    st.markdown("#### Answers")
    st.caption("Answers that record a problem in the Brain output are marked "
               "“flagged”.")
    _review_claims(ctx)
    _review_datasets(ctx)
    _review_recall(ctx)
    _completion(ctx, missing)


def _missing_groups(ctx: Ctx, missing) -> None:
    """Missing items grouped by Claim and by Dataset, Claim recall apart.

    A paper can have hundreds of unanswered items; one row per Claim or Dataset
    keeps the page readable, and each group opens to its individual items.
    """
    claims = ctx.brain.claims_of(ctx.source_id)
    datasets = ctx.brain.dataset_ids_of(ctx.source_id)
    by_claim: dict[int, list] = {}
    by_dataset: dict[int, list] = {}
    recall = []
    for item in missing:
        if item.section == "claims" and item.claim_index is not None:
            by_claim.setdefault(item.claim_index, []).append(item)
        elif item.section == "datasets" and item.dataset_index is not None:
            by_dataset.setdefault(item.dataset_index, []).append(item)
        else:
            recall.append(item)

    def group(kind, label, index, items, open_args):
        row, action = st.columns([6, 1], vertical_alignment="top")
        with row:
            with st.expander(f"{label} — {len(items)} missing", expanded=False):
                for n, item in enumerate(items):
                    detail = item.where.split(" · ", 1)[1] if " · " in item.where else ""
                    line, go = st.columns([6, 1], vertical_alignment="center")
                    line.markdown(f"**{html.escape(item.what)}**"
                                  + (f" · {html.escape(detail)}" if detail else "")
                                  + f" — {html.escape(item.reason)}")
                    go.button("Go", key=f"goto|{kind}|{index}|{n}",
                              on_click=go_to_section, args=(ctx, *open_args))
        action.button("Open", key=f"open_missing|{kind}|{index}",
                      on_click=go_to_section, args=(ctx, *open_args))

    if by_claim:
        st.markdown("**Claims**")
        for index, items in sorted(by_claim.items()):
            group("claim", f"Claim {claims[index]['id']}", index, items,
                  ("claims", index, None))
    if by_dataset:
        st.markdown("**Datasets**")
        for index, items in sorted(by_dataset.items()):
            did = datasets[index]
            group("dataset", f"Dataset {did} · {ctx.brain.dataset(did).get('name', did)}",
                  index, items, ("datasets", None, index))
    if recall:
        st.markdown("**Claim recall**")
        for n, item in enumerate(recall):
            line, go = st.columns([6, 1], vertical_alignment="center")
            line.markdown(f"**{html.escape(item.what)}** — {html.escape(item.reason)}")
            go.button("Go", key=f"goto|recall|{n}", on_click=go_to_section,
                      args=(ctx, "recall"))


def _shown(question: spec.Question, answer: str) -> str:
    if not answer:
        return "_Not answered_"
    label = {spec.Q14_NONE_MISSING: "No additional Concepts are missing",
             spec.Q14_MISSING: "Missing Concepts recorded"}.get(answer, answer)
    return f"**{html.escape(label)}**" + (" — flagged" if spec.problem(question, answer) else "")


def _with_comment(text: str, comment: str) -> str:
    return text + (f"  \n{html.escape(comment)}" if (comment or "").strip() else "")


def _review_claims(ctx: Ctx) -> None:
    brain, sid, data = ctx.brain, ctx.source_id, ctx.data
    claims = brain.claims_of(sid)
    states = progress.claim_states(brain, sid, data)
    for index, claim in enumerate(claims):
        cid = claim["id"]
        done, total = progress.claim_progress(brain, sid, cid, data)
        with st.expander(f"{MARK[states[cid]]} {index + 1}. {cid} · {done}/{total}"):
            st.caption(claim.get("statement", ""))
            for question in spec.claim_scalar_questions():
                if question is spec.Q14:
                    continue
                record = data.response(question.key, cid)
                text = _shown(question, record.get("answer", ""))
                if record.get("related_claim_id"):
                    text += f" · restates {record['related_claim_id']}"
                st.markdown(f"{question.title}: " + _with_comment(text, record.get("comment", "")))
            for question, ids in ((spec.Q12, brain.concepts_of_claim(cid)),
                                  (spec.Q13, brain.candidates_of_claim(cid))):
                for concept_id in ids:
                    record = data.concept(question.key, cid, concept_id)
                    st.markdown(f"{question.title} · {concept_label(concept_id)}: "
                                + _with_comment(_shown(question, record.get("answer", "")),
                                                record.get("comment", "")))
            state = data.response(spec.Q14.key, cid).get("answer", "")
            st.markdown(f"{spec.Q14.title}: {_shown(spec.Q14, state)}")
            existing, proposed = progress.q14_selection(data, cid)
            for row in existing:
                st.markdown(f"- Selected: {concept_label(row['concept_id'])} "
                            f"({family_label(row.get('concept_family', ''))})")
            for row in proposed:
                st.markdown(f"- Proposed: {html.escape(row['name'])} "
                            f"({family_label(row['family'])})"
                            + (f" — {html.escape(row['explanation'])}"
                               if row.get("explanation") else ""))
            for relation in brain.relations_from_claim(cid):
                record = data.relation(relation["key"])
                label = (f"{spec.value_label(relation['type'])} → {relation['to']} "
                         f"({spec.value_label(relation.get('grounding', ''))})")
                for question in spec.relation_questions():
                    st.markdown(
                        f"{question.title} · {label}: " + _with_comment(
                            _shown(question, record.get(f"{question.column}_answer", "")),
                            record.get(f"{question.column}_comment", "")))
            st.button("Open Claim", key=f"open_claim|{cid}", on_click=go_to_section,
                      args=(ctx, "claims", index))


def _review_datasets(ctx: Ctx) -> None:
    ids = ctx.brain.dataset_ids_of(ctx.source_id)
    for index, did in enumerate(ids):
        with st.expander(f"Dataset · {ctx.brain.dataset(did).get('name', did)}"):
            for question in spec.dataset_questions():
                record = ctx.data.response(question.key, did)
                st.markdown(f"{question.title}: " + _with_comment(
                    _shown(question, record.get("answer", "")), record.get("comment", "")))
            st.button("Open Dataset", key=f"open_ds|{did}", on_click=go_to_section,
                      args=(ctx, "datasets", None, index))


def _review_recall(ctx: Ctx) -> None:
    record = ctx.data.response(spec.RECALL.key, ctx.source_id)
    with st.expander("Claim recall", expanded=True):
        st.markdown(f"{spec.RECALL.title}: {_shown(spec.RECALL, record.get('answer', ''))}")
        if spec.child_visible(spec.MISSING_CLAIMS, record.get("answer", "")):
            text = ctx.data.response(spec.MISSING_CLAIMS.key, ctx.source_id).get("answer", "")
            st.markdown(f"{spec.MISSING_CLAIMS.title}:")
            st.markdown(html.escape(text) if text.strip() else "_Not answered_")


def _completion(ctx: Ctx, missing) -> None:
    st.divider()
    if ctx.locked:
        st.info("This paper has been submitted. Answers are read-only.")
        return
    review = store.get_review(ctx.review_id) or {}
    if review.get("status") == store.STATUS_COMPLETE:
        st.success("This paper is marked complete. It stays editable until you submit "
                   "the phase; any change returns it to in progress.")
        return
    if st.button("Mark paper complete", type="primary", disabled=bool(missing)):
        with st.spinner("Saving your last answers…"):
            ok, outstanding, detail = ui.settle()
        if not ok:
            ui.hold(f"{outstanding} answer(s) are not yet stored, so the paper was not "
                    f"marked complete. They are kept and retried. {detail}")
            st.rerun()
        ctx.refresh()
        remaining = progress.missing_items(ctx.brain, ctx.source_id, ctx.data)
        if remaining:
            ui.hold(f"After re-reading the stored answers, {len(remaining)} item(s) are "
                    f"still missing. Nothing was marked complete.")
        else:
            store.mark_complete(ctx.review_id)
        st.rerun()


RENDERERS = {
    "source": source_section,
    "claims": claims_section,
    "datasets": datasets_section,
    "recall": recall_section,
    "review": review_section,
}
