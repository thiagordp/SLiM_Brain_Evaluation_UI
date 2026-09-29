"""Shared UI machinery: review cache, autosaving controls, wiki modal, definitions.

Every control saves through an ``on_change`` callback. Streamlit runs callbacks
before it re-runs the script, so the cached review data is updated first and
everything drawn afterwards — part counts, section marks, the Review page —
already reflects the answer just given. The write itself is queued and sent in
the background; navigation never waits for storage.
"""
from __future__ import annotations

import dataclasses
import html
import re

import streamlit as st
import streamlit.components.v1 as components

import savequeue
import sheets
import spec
import store
from brain import concept_label, family_label

SAVE_SAVING, SAVE_SAVED = savequeue.SAVING, savequeue.SAVED
SAVE_FAILED, SAVE_RETRYING = savequeue.FAILED, savequeue.RETRYING


# ------------------------------------------------------------- save queue
def _batchable(function, args, kwargs):
    """A row write expressed as a record `store.save_many` accepts."""
    if function is not store.write:
        return None
    return {"tab": args[0], "key": args[1], "values": args[2], **kwargs}


def queue() -> savequeue.SaveQueue:
    """One queue per Streamlit session."""
    if "_save_queue" not in st.session_state:
        q = savequeue.SaveQueue()
        q.set_batch_writer(_batchable, store.save_many)
        q.set_fatal(store.SaveConflict)
        st.session_state["_save_queue"] = q
    return st.session_state["_save_queue"]


def _own_stamps(key: str) -> set:
    """Stamps this session wrote to a row: never a conflict with itself."""
    return st.session_state.setdefault("_own_stamps", {}).setdefault(key, set())


# ------------------------------------------------------------ review cache
#: One read per review per session, not one per rerun. Write-through: every
#: save updates the cached rows before it is queued, so what the evaluator sees
#: is what will be stored. `Ctx.refresh()` re-reads where correctness demands it.
CACHE = "_review_cache"


def cached_review(rid: str) -> store.ReviewData:
    cache = st.session_state.setdefault(CACHE, {})
    if rid not in cache:
        cache[rid] = store.load_review(rid)
    return cache[rid]


def forget_review(rid: str | None = None) -> None:
    cache = st.session_state.setdefault(CACHE, {})
    targets = list(cache) if rid is None else [rid]
    for target in targets:
        cache.pop(target, None)
        # Widgets keep their own state; drop it so they show what storage holds.
        for key in [k for k in st.session_state.keys()
                    if isinstance(k, str) and k.startswith(f"w|{target}|")]:
            del st.session_state[key]


@dataclasses.dataclass
class Ctx:
    brain: object
    round_id: str
    phase_id: str
    evaluator_id: str
    source_id: str
    review_id: str
    data: store.ReviewData
    locked: bool

    def refresh(self) -> None:
        """Re-read from storage, bypassing the cache (before completion/submission)."""
        forget_review(self.review_id)
        self.data = cached_review(self.review_id)


def wkey(ctx: Ctx, *parts: str) -> str:
    """Session key of one control. Namespaced by review so a reload can clear it."""
    return "|".join(("w", ctx.review_id, *parts))


# ------------------------------------------------------------------ saving
def _queue_row(ctx: Ctx, tab: str, key: str, row: dict) -> None:
    expected = row.get("updated_at") or ""
    accept = _own_stamps(key)

    def written(stamp, target=row):
        accept.add(stamp)
        target["updated_at"] = stamp

    queue().submit(key, store.write, tab, key, dict(row), rid=ctx.review_id,
                   expected_updated_at=expected, also_accept=accept,
                   on_success=written)


def save_response(ctx: Ctx, question: spec.Question, object_id: str,
                  **changes) -> None:
    """RESPONSES: change the answer and/or comment of one row."""
    lookup = store.response_lookup(question.key, object_id)
    row = ctx.data.responses.get(lookup)
    if row is None:
        raise store.StorageIntegrityError(
            f"no stored row for {question.key} on {object_id}")
    if all((row.get(k) or "") == (v or "") for k, v in changes.items()):
        return
    row.update({k: v or "" for k, v in changes.items()})
    _queue_row(ctx, sheets.RESPONSES, row["response_key"], row)


def save_concept(ctx: Ctx, question: spec.Question, claim_id: str, concept_id: str,
                 **changes) -> None:
    lookup = store.concept_lookup(question.key, claim_id, concept_id)
    row = ctx.data.concepts.get(lookup)
    if row is None:
        raise store.StorageIntegrityError(
            f"no stored row for {question.key} on {claim_id} / {concept_id}")
    if all((row.get(k) or "") == (v or "") for k, v in changes.items()):
        return
    row.update({k: v or "" for k, v in changes.items()})
    _queue_row(ctx, sheets.CONCEPT_RESPONSES, row["response_key"], row)


def save_relation(ctx: Ctx, relation_key: str, **changes) -> None:
    row = ctx.data.relations.get(relation_key)
    if row is None:
        raise store.StorageIntegrityError(f"no stored row for relation {relation_key}")
    if all((row.get(k) or "") == (v or "") for k, v in changes.items()):
        return
    row.update({k: v or "" for k, v in changes.items()})
    _queue_row(ctx, sheets.RELATION_RESPONSES, row["response_key"], row)


def save_selection(ctx: Ctx, tab: str, key: str, lookup: str, row: dict) -> None:
    """MISSING_CONCEPTS / PROPOSED_CONCEPTS: idempotent upsert, queued."""
    target = ctx.data.missing if tab == sheets.MISSING_CONCEPTS else ctx.data.proposals
    target[lookup] = row
    queue().submit(key, store.upsert_selection, tab, key, dict(row), rid=ctx.review_id)


def save_restatement_group(ctx: Ctx, claim_ids, active: bool) -> str | None:
    """Add (``active``) or remove one restatement group. Returns why it was
    refused, or None when it was queued.

    Adding is validated at this boundary whatever control asked for it (see
    `progress.validate_restatement_group`); a refused group writes nothing.
    Removing marks the group's own rows inactive. All member rows travel in one
    queued upsert, keyed by the group, so a later add or remove of the same
    group supersedes an earlier one still pending.
    """
    import progress

    if active:
        ids, problem = progress.validate_restatement_group(
            ctx.brain, ctx.source_id, ctx.data, claim_ids)
        if problem:
            return problem
    else:
        ids = sorted({str(c) for c in claim_ids})
    gid = store.restatement_group_id(ids)
    rows = {}
    for cid in ids:
        key = store.restatement_key(ctx.review_id, gid, cid)
        row = {"restatement_key": key, "review_id": ctx.review_id,
               "source_id": ctx.source_id, "group_id": gid, "claim_id": cid,
               "active": store.TRUE if active else store.FALSE}
        ctx.data.restatements[store.pair_lookup(gid, cid)] = row
        rows[key] = dict(row)
    queue().submit(f"{ctx.review_id}|{gid}", store.upsert_selections,
                   sheets.RESTATEMENTS, rows, rid=ctx.review_id)
    return None


# --------------------------------------------------------------- scrolling
SCROLL_SCRIPT = ("<script>window.parent.document"
                 ".querySelector('section.main, .stMain, [data-testid=\"stMain\"]')"
                 "?.scrollTo({top:0});window.parent.scrollTo({top:0});</script>")


def scroll_to_top() -> None:
    """A fixed, app-authored script: `st.iframe` where available, else the
    older `components.html` it replaces."""
    if hasattr(st, "iframe"):
        st.iframe(SCROLL_SCRIPT, height=1)
    else:                                               # older Streamlit
        components.html(SCROLL_SCRIPT, height=0)


def request_scroll() -> None:
    st.session_state["_scroll_top"] = True


def consume_scroll() -> None:
    if st.session_state.pop("_scroll_top", False):
        scroll_to_top()


# ------------------------------------------------------------ wiki modal
#: One modal carries every piece of context. It sits over the evaluation and
#: leaves it exactly as it was: opening or closing it touches no answer.
WIKI = "wiki_stack"
SOURCE, CONCEPT, DATASET, CLAIM, SOURCE_CLAIMS = (
    "source", "concept", "dataset", "claim", "source_claims")
REFERENCE = re.compile(r"\b(SRC-\d{4}|DST-\d{4}|CPT-[a-z0-9-]+|CLM-\d{4}-\d{3})\b")
KIND_OF_PREFIX = {"SRC": SOURCE, "DST": DATASET, "CPT": CONCEPT, "CLM": CLAIM}


def wiki_stack() -> list[tuple[str, str]]:
    return st.session_state.setdefault(WIKI, [])


def open_wiki(kind: str, object_id: str = "") -> None:
    st.session_state[WIKI] = [(kind, object_id)]


def follow_wiki(kind: str, object_id: str = "") -> None:
    stack = wiki_stack()
    if not stack or stack[-1] != (kind, object_id):
        stack.append((kind, object_id))


def wiki_back() -> None:
    stack = wiki_stack()
    if len(stack) > 1:
        stack.pop()


def close_wiki() -> None:
    st.session_state[WIKI] = []


def reset_wiki(context_key: str) -> None:
    """Close the modal when the evaluation context changes."""
    if st.session_state.get("_wiki_context") != context_key:
        st.session_state["_wiki_context"] = context_key
        close_wiki()


MODAL_CSS = """
<style>
div[data-testid="stDialog"] div[role="dialog"] {
    width: 75vw; max-width: 1200px; height: 82vh;
}
div[data-testid="stDialog"] div[role="dialog"] > div:nth-child(2) {
    overflow-y: auto;
}
</style>
"""


def wiki_button(label: str, kind: str, object_id: str = "", *, key: str,
                follow: bool = False, width: str = "content") -> None:
    st.button(label, key=key, width=width,
              on_click=follow_wiki if follow else open_wiki, args=(kind, object_id))


def render_wiki_modal(ctx: Ctx) -> None:
    stack = wiki_stack()
    if not stack:
        return
    st.markdown(MODAL_CSS, unsafe_allow_html=True)
    kind, object_id = stack[-1]
    st.dialog(_wiki_title(ctx, kind, object_id), width="large",
              on_dismiss=close_wiki)(lambda: _wiki_body(ctx))()


def _wiki_title(ctx: Ctx, kind: str, object_id: str) -> str:
    brain = ctx.brain
    return {
        SOURCE: f"Source wiki · {object_id}",
        CONCEPT: f"Concept wiki · {concept_label(object_id)}",
        DATASET: f"Dataset wiki · {brain.dataset(object_id).get('name', object_id)}",
        CLAIM: f"Claim · {object_id}",
        SOURCE_CLAIMS: f"Claims extracted from {object_id}",
    }.get(kind, "Brain")


def _wiki_body(ctx: Ctx) -> None:
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
        st.caption(" › ".join(oid or k for k, oid in stack))
    st.divider()
    if kind == SOURCE:
        source = ctx.brain.source(object_id)
        st.markdown(f"### {source.get('title', object_id)}")
        _references(ctx, ctx.brain.source_body(object_id), object_id, f"src|{object_id}")
        st.markdown(wiki_markdown(ctx.brain.source_body(object_id)))
        raw_markdown(ctx.brain.raw_page("source", object_id))
    elif kind == CONCEPT:
        concept = ctx.brain.concept(object_id)
        st.markdown(f"### {concept_label(object_id)}")
        st.caption(f"{object_id} · {spec.value_label(concept.get('status', ''))} · "
                   f"{family_label(concept.get('concept_type', ''))}")
        _references(ctx, ctx.brain.concept_body(object_id), object_id, f"cpt|{object_id}")
        st.markdown(wiki_markdown(ctx.brain.concept_body(object_id)))
        raw_markdown(ctx.brain.raw_page("concept", object_id))
    elif kind == DATASET:
        dataset = ctx.brain.dataset(object_id)
        st.markdown(f"### {dataset.get('name', object_id)}")
        st.caption(object_id)
        _references(ctx, ctx.brain.dataset_body(object_id), object_id, f"dst|{object_id}")
        st.markdown(wiki_markdown(ctx.brain.dataset_body(object_id)))
        raw_markdown(ctx.brain.raw_page("dataset", object_id))
    elif kind == CLAIM:
        st.caption("Claims have no wiki page; this view is generated from the Claim "
                   "record.")
        claim_detail(ctx.brain, ctx.brain.claim(object_id))
        wiki_button(f"Open Source wiki · {ctx.brain.source_of_claim(object_id)}",
                    SOURCE, ctx.brain.source_of_claim(object_id),
                    key=f"clm_src|{object_id}", follow=True)
    elif kind == SOURCE_CLAIMS:
        for index, claim in enumerate(ctx.brain.claims_of(object_id), start=1):
            cols = st.columns([6, 1])
            cols[0].markdown(f"**{index}. {claim['id']}** — "
                             f"{html.escape(claim.get('statement', ''))}")
            with cols[1]:
                wiki_button("Detail", CLAIM, claim["id"], key=f"srcclaims|{claim['id']}",
                            follow=True)


def _references(ctx: Ctx, text: str, exclude: str, key: str) -> None:
    """The ids a page names, offered as buttons, since its links cannot work here."""
    found = []
    for match in REFERENCE.findall(text or ""):
        if match != exclude and match not in found and KIND_OF_PREFIX.get(match[:3]):
            found.append(match)
    if not found:
        return
    with st.expander(f"Referenced here ({len(found)})"):
        for row in range(0, len(found[:32]), 4):
            for col, ident in zip(st.columns(4), found[row:row + 4]):
                with col:
                    wiki_button(ident, KIND_OF_PREFIX[ident[:3]], ident,
                                key=f"{key}|ref|{ident}", follow=True)


# ------------------------------------------------------ wiki as evaluator context
#: Headings written by older wiki generators, and what the current schema calls
#: the same thing. The Source wiki is evaluator context, so it must not present
#: an obsolete relation vocabulary as if it were current.
OBSOLETE_HEADINGS = {
    "In tension with (attacks)": "Attacks",
    "In tension with (attacked by)": "Attacked by",
}
_LINK = re.compile(r"\[([^\]]+)\]\((?!https?://)[^)]*\)")


def wiki_markdown(body: str) -> str:
    """A wiki page as it may be shown to an evaluator.

    Local links become plain text (they point at files the app does not serve),
    and obsolete relation headings are given their current names. Nothing else
    in the page is altered.
    """
    text = _LINK.sub(r"\1", body or "")
    for old, new in OBSOLETE_HEADINGS.items():
        text = re.sub(rf"^(#+\s*){re.escape(old)}\s*$", rf"\g<1>{new}", text, flags=re.M)
    return text


# -------------------------------------------------------------- rendering
LANGUAGES = {"en": "English", "fr": "French", "de": "German", "it": "Italian",
             "es": "Spanish", "pt": "Portuguese", "nl": "Dutch", "cs": "Czech",
             "ru": "Russian", "zh": "Chinese", "ko": "Korean", "ar": "Arabic",
             "ms": "Malay", "tr": "Turkish", "ja": "Japanese", "pl": "Polish"}


def display_value(field: str, value) -> str:
    """A Brain value in normal typography. Empty values are said, not hidden."""
    values = value if isinstance(value, list) else ([value] if value not in (None, "") else [])
    if not values:
        return "None recorded"
    shown = []
    for item in values:
        text = str(item)
        if field in ("language",) and text in LANGUAGES:
            shown.append(f"{LANGUAGES[text]} ({text})")
        elif field in ("claim_jurisdiction", "jurisdiction", "legal_reference", "note",
                       "description", "name") or re.fullmatch(r"[A-Z]{2}", text):
            shown.append(text if text not in ("general", "undetermined")
                         else spec.value_label(text))
        else:
            shown.append(spec.value_label(text))
    return ", ".join(shown)


def _esc(text: str) -> str:
    return html.escape(spec.plain(text))


#: The one evaluator-facing label for closed guidance, whatever the frozen
#: material comes from (a schema file or a skill).
INSTRUCTIONS = "Instructions"
RAW_MARKDOWN = "Raw Markdown"


def _paragraphs_html(text: str) -> str:
    """A verbatim passage with its paragraphs and line breaks kept."""
    return "".join(
        "<p style='margin:0 0 0.5rem'>"
        + "<br>".join(_esc(line) for line in paragraph.split("\n")) + "</p>"
        for paragraph in text.split("\n\n") if paragraph.strip())


def definition_html(key: str) -> str:
    """One frozen passage, verbatim apart from the dropped code markup.

    Nothing is added to it: no heading, no marker for the assigned value (that
    value is shown outside, next to the question). For a categorical field each
    value's frozen text follows the value's name as a separate bold label.
    """
    entry = spec.definition(key)
    parts = []
    if entry.get("text"):
        parts.append(f"<div>{_esc(entry['text'])}</div>")
    items = entry.get("items") or []
    if items:
        rows = []
        for item in items:
            value = item.get("value", "")
            text = _esc(item.get("text", ""))
            if value:
                name = html.escape(spec.value_label(value))
                line = f"<strong>{name}</strong>" + (f" — {text}" if text else "")
            else:
                line = text
            subs = item.get("sub") or []
            if subs:
                line += "<ul style='margin:0.1rem 0 0'>" + "".join(
                    f"<li>{_esc(s)}</li>" for s in subs) + "</ul>"
            rows.append(f"<li>{line}</li>")
        parts.append("<ul style='margin:0.25rem 0 0;padding-left:1.2rem'>"
                     + "".join(rows) + "</ul>")
    return "".join(parts)


def _render_passage(key: str) -> None:
    """Render one frozen entry. Presentation only: the stored text is untouched.

    * a skill passage with a stored ``verbatim`` block (Grounding) is shown as
      that block, the skill's own list structure included;
    * any other skill passage keeps its paragraphs and line breaks;
    * a schema entry shows its text and its values with their meanings.

    In every case the only transformation is dropping backtick code markup.
    """
    entry = spec.definition(key)
    if entry.get("verbatim"):
        st.markdown(spec.plain(entry["verbatim"]))
    elif entry["source"].startswith(".claude/skills/"):
        st.markdown(_paragraphs_html(entry["text"]), unsafe_allow_html=True)
    else:
        st.markdown(definition_html(key), unsafe_allow_html=True)


SCHEMA_SKILL = "Schema / skill"
CALIBRATION = "Calibration"


def _section_heading(text: str) -> None:
    st.markdown(f"<div style='font-size:0.8rem;letter-spacing:0.04em;"
                f"text-transform:uppercase;opacity:0.7;margin:0.3rem 0 0.2rem'>"
                f"{html.escape(text)}</div>", unsafe_allow_html=True)


def definitions(keys, headings: dict | None = None, calibration=()) -> None:
    """Guidance for a question, in a closed "Instructions" expander.

    Each frozen passage is preceded by a heading that is interface structure —
    the entry's label, or ``headings[key]`` — rendered as its own element and
    never joined into the passage.

    ``calibration`` names `spec.CALIBRATION` entries. When there are any, the
    frozen passages go under a "Schema / skill" heading and the calibration
    lines under a separate "Calibration" heading, so meeting decisions are
    never presented as schema text. Without calibration the block is unchanged.
    """
    if not keys and not calibration:
        return
    with st.expander(INSTRUCTIONS, expanded=False):
        if keys and calibration:
            _section_heading(SCHEMA_SKILL)
        for key in keys:
            heading = (headings or {}).get(key) or spec.definition(key)["label"]
            st.markdown(f"**{html.escape(heading)}**")
            _render_passage(key)
        if calibration:
            _section_heading(CALIBRATION)
            st.markdown("".join(
                f"<p style='margin:0 0 0.5rem'>{html.escape(line)}</p>"
                for name in calibration for line in spec.CALIBRATION[name]),
                unsafe_allow_html=True)


def raw_markdown(text: str) -> None:
    """The exact file text of a wiki page, read-only and copyable.

    Shown as it is on disk — frontmatter included, nothing rebuilt from the
    rendered page. Informational only: it reads nothing but the Brain file and
    writes nothing.
    """
    # `st.code` drops exactly one leading and one trailing newline of its body;
    # padding them back keeps the displayed and copied text identical to the file.
    body = ("\n" if text.startswith("\n") else "") + text + ("\n" if text.endswith("\n") else "")
    with st.expander(RAW_MARKDOWN, expanded=False):
        st.code(body, language="markdown", wrap_lines=True)


_DOI_PREFIX = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.I)
EXTERNAL_ICON = (
    "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' "
    "fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' "
    "stroke-linejoin='round' aria-hidden='true' style='vertical-align:-2px'>"
    "<path d='M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6'/>"
    "<polyline points='15 3 21 3 21 9'/><line x1='10' y1='14' x2='21' y2='3'/></svg>")


def doi_url(value) -> str:
    """https://doi.org/<doi> for a recorded DOI, or "" when there is none.

    Accepts a bare `10.x/...`, `doi:...` or an http(s) doi.org URL.
    """
    text = _DOI_PREFIX.sub("", str(value or "").strip()).strip()
    if not re.match(r"^10\.\d{4,9}/\S+$", text):
        return ""
    return "https://doi.org/" + text


def doi_line(value) -> None:
    """The DOI as text, with a small external-link icon that opens it in a new
    tab. A plain link: no callback, no state, nothing written."""
    url = doi_url(value)
    shown = str(value).strip() if value not in (None, "") else "None recorded"
    link = (f" <a href='{html.escape(url, quote=True)}' target='_blank' "
            f"rel='noopener noreferrer' title='Open the DOI in a new tab' "
            f"aria-label='Open the DOI in a new tab' "
            f"style='text-decoration:none;color:inherit;opacity:0.75'>{EXTERNAL_ICON}</a>"
            if url else "")
    st.markdown(f"**DOI:** {html.escape(shown)}{link}", unsafe_allow_html=True)


def value_line(label: str, value: str) -> None:
    st.markdown(f"**{label}:** {html.escape(value)}", unsafe_allow_html=True)


def quotation(text: str, location: str) -> None:
    location = html.escape(location or "location not recorded")
    st.markdown(
        f'<div style="border-left:3px solid rgba(128,128,128,0.35);'
        f'padding:0.3rem 0.8rem;margin:0.25rem 0 0.5rem">'
        f'<div>“{html.escape(text or "")}”</div>'
        f'<div style="opacity:0.7;font-size:0.85rem;margin-top:0.2rem">{location}</div>'
        f'</div>', unsafe_allow_html=True)


def statement_card(label: str, statement: str) -> None:
    st.markdown(
        f'<div style="border:1px solid rgba(128,128,128,0.35);border-radius:6px;'
        f'padding:0.75rem 1rem;margin:0.3rem 0 0.8rem">'
        f'<div style="font-size:0.75rem;letter-spacing:0.05em;opacity:0.7;'
        f'text-transform:uppercase;margin-bottom:0.3rem">{html.escape(label)}</div>'
        f'<div style="font-size:1.07rem;line-height:1.5">{html.escape(statement or "")}'
        f'</div></div>', unsafe_allow_html=True)


def claim_detail(brain, claim: dict) -> None:
    """A Claim, generated from its record, in plain typography."""
    st.markdown("**Statement**")
    st.markdown(f"> {claim.get('statement', '')}")
    st.markdown("**Anchors**")
    for anchor in claim.get("anchors") or []:
        quotation(anchor.get("quote", ""), anchor.get("location", ""))
    for field, label in (("claim_object", "Claim object"), ("claim_type", "Claim type"),
                         ("basis", "Basis"), ("claim_jurisdiction", "Claim jurisdiction"),
                         ("legal_reference", "Legal reference"),
                         ("temporal_reference", "Temporal reference")):
        value_line(label, display_value(field, claim.get(field)))
    concepts = claim.get("concepts") or []
    if concepts:
        value_line("Concepts", ", ".join(concept_label(c) for c in concepts))
    datasets = claim.get("datasets") or []
    if datasets:
        value_line("Datasets", ", ".join(
            f"{brain.dataset(d).get('name', d)} ({d})" for d in datasets))


# ------------------------------------------------------------ save status
def render_save_status() -> None:
    state, detail, unresolved = queue().state
    conflicts = queue().conflicts
    if conflicts:
        st.warning(f"{len(conflicts)} change(s) were not applied: those answers had "
                   f"already been changed elsewhere, most likely in another browser "
                   f"tab. The stored answers were kept. Reload to see them.")
        if st.button("Reload this paper", key="reload_after_conflict"):
            queue().clear_conflicts()
            settle()                    # store what is pending before re-reading
            forget_review()
            st.rerun()
    if state == SAVE_FAILED:
        st.warning(f"Save failed: {unresolved} answer(s) not yet stored. They are kept "
                   f"and retried; the paper cannot be marked complete until they are "
                   f"stored. {detail}")
        if st.button("Retry now", key="retry_saves"):
            queue().retry_now()
            st.rerun()
    elif state == SAVE_RETRYING:
        st.caption(f"Retrying… ({unresolved} outstanding)")
    elif state == SAVE_SAVING or unresolved:
        st.caption(f"Saving… ({unresolved} outstanding)")
    elif state == SAVE_SAVED:
        st.caption("✓ Saved")


def hold(message: str) -> None:
    """Keep a message across the rerun that follows it."""
    st.session_state["_notice"] = message


def show_held() -> None:
    message = st.session_state.pop("_notice", None)
    if message:
        st.error(message)


def settle(timeout: float = 30.0) -> tuple[bool, int, str]:
    """Flush before an irreversible step. Returns (ok, outstanding, detail)."""
    ok = queue().flush(timeout=timeout)
    detail = "; ".join(sorted(set(queue().failures.values())))[:200]
    return ok, queue().unresolved, detail
