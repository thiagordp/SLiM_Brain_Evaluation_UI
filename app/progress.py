"""Section/claim state machine and completeness.

Two state models:

    paper   NOT STARTED -> IN PROGRESS -> COMPLETE (not submitted) -> SUBMITTED
    section AVAILABLE -> INCOMPLETE -> COMPLETE

**Navigation is free.** Every section and every claim is reachable at any time:
evaluators asked to move between claims, datasets and CITES as they work, rather
than being marched through in order. The section badges still show what is
outstanding, so nothing is hidden — it is simply not blocked.

Completeness is enforced where it matters instead: a paper cannot be marked
complete while anything is missing, and the final batch submission cannot run
until every assigned paper is complete. What counts as missing is defined
narrowly, on the existing evaluation design only: an unanswered applicable
question, a missing comment required for a partial or negative answer, an
applicable conditional field left empty, or an unanswered edge. No new mandatory
fields are invented.

Three kinds of item are **not** missing when they carry no evaluator answer:

* a conditional follow-up whose parent is not negative — it is not shown at all;
* an item the application determined inapplicable from the Brain record — HE-07
  with no premise expected, HE-21 with no candidate concept, HE-18.1 with no
  outgoing CITES edge. These are stored as ``answer = N/A`` with
  ``applicability = auto_na``, so an inapplicable item never looks unanswered;
* an item answered ``No`` — a defect found is a completed judgment, not an
  incomplete task.
"""
from __future__ import annotations

import dataclasses

import spec

LOCKED, AVAILABLE, INCOMPLETE, COMPLETE = "locked", "available", "incomplete", "complete"

SECTIONS = [
    ("source", "1 · Source"),
    ("claims", "2 · Claims"),
    ("datasets", "3 · Datasets"),
    ("cites", "4 · CITES"),
    ("recall", "5 · Source-level completeness"),
    ("review", "6 · Review"),
]
SECTION_IDS = [s for s, _ in SECTIONS]
SECTION_LABEL = dict(SECTIONS)

#: The section bar puts six buttons across the page, so a name that fits the
#: Review page's status list is cut off there. The bar gets a short form; the
#: page still calls itself by its full name, and so does everywhere with room.
SECTION_TAB = dict(SECTION_LABEL, recall="5 · Completeness")


@dataclasses.dataclass(frozen=True)
class Item:
    """One expected answer: an applicable question about one object.

    ``auto_na`` marks an item the application itself determined inapplicable
    from the Brain record. It is still an item — it is rendered, and it owns a
    stored row — but it needs no evaluator answer and is excluded from the
    applicable-item counts the progress indicators show.
    """
    section: str
    object_type: str
    object_id: str
    question: spec.Question
    claim_id: str | None = None      # which claim page it lives on
    auto_na: bool = False

    @property
    def lookup(self) -> str:
        return f"{self.question.question_key}|{self.object_id}"


def auto_na_applies(question: spec.Question, brain, source_id: str,
                    claim_id: str | None) -> bool:
    """Whether the Brain record makes this criterion inapplicable.

    Decided here rather than offered to the evaluator: each rule is a fact about
    the record, and an N/A option invites the opposite error — choosing it where
    the criterion does apply.
    """
    rule = question.auto_na_rule
    if not rule:
        return False
    if rule == spec.AUTO_NA_NO_PREMISE:
        claim = brain.claims.get(claim_id, {}) if claim_id else {}
        return (claim.get("basis") == "none_stated"
                and not (claim.get("premise") or "").strip())
    if rule == spec.AUTO_NA_NO_CANDIDATE:
        return not (claim_id and brain.candidate_created_for(claim_id))
    if rule == spec.AUTO_NA_NO_OUTGOING_CITES:
        return not brain.cites_from(source_id)
    return False


def is_auto_na(record: dict) -> bool:
    """True for a stored row the application marked inapplicable."""
    return (record.get("applicability") or "") == spec.AUTO_NA


def _answered(record: dict, question: spec.Question) -> bool:
    if question.free_text:
        return bool((record.get("answer") or "").strip())
    return bool(record.get("answer"))


def _comment_ok(record: dict, question: spec.Question) -> bool:
    if record.get("answer") in question.comment_required_on:
        return bool((record.get("comment_evidence") or "").strip())
    return True


def item_complete(item: Item, responses: dict) -> bool:
    if item.auto_na:
        return True
    record = responses.get(item.lookup, {})
    return _answered(record, item.question) and _comment_ok(record, item.question)


def item_problem(item: Item, responses: dict) -> str | None:
    if item.auto_na:
        return None
    record = responses.get(item.lookup, {})
    if not _answered(record, item.question):
        return "unanswered"
    if not _comment_ok(record, item.question):
        return f"answered {record.get('answer')}, required comment missing"
    return None


def applicable(items: list[Item]) -> list[Item]:
    """The items that actually ask the evaluator for something.

    The denominator of every "n of m complete" indicator, so an inapplicable
    criterion never makes a finished claim look unfinished.
    """
    return [i for i in items if not i.auto_na]


# --------------------------------------------------------------- expansion
def _applicable(question: spec.Question, brain, claim_id, responses,
                everything: bool = False) -> bool:
    """Whether this question is asked given the answers so far.

    ``everything`` ignores the answers and admits every conditional follow-up.
    Preallocation uses it: a row that appears only once its parent turns negative
    would otherwise have to be appended in the middle of a live round, by
    whichever evaluator happened to answer first.
    """
    if everything:
        return True
    if question.applicability == spec.IF_PARENT_IS_NEGATIVE:
        parents = (question.parent_key or "").split("|")
        for parent in parents:
            parent_question = spec.BY_KEY.get(parent)
            if parent_question is None:
                continue
            object_id = claim_id if parent_question.object_type == "claim" else None
            # source-level parents are keyed on the source id
            for lookup, record in responses.items():
                if lookup.startswith(parent + "|") and record.get("answer") in spec.NEGATIVE:
                    if object_id is None or lookup.endswith("|" + object_id):
                        return True
        return False
    return True


def claim_items(brain, source_id: str, claim_id: str, responses: dict,
                everything: bool = False) -> list[Item]:
    out = []
    for question in spec.claim_questions():
        if not _applicable(question, brain, claim_id, responses, everything):
            continue
        out.append(Item("claims", "claim", claim_id, question, claim_id,
                        auto_na=auto_na_applies(question, brain, source_id, claim_id)))
    return out


def source_items(brain, source_id: str, responses: dict,
                 everything: bool = False) -> list[Item]:
    return [Item("source", "source", source_id, q,
                 auto_na=auto_na_applies(q, brain, source_id, None))
            for q in spec.source_section_questions()]


def dataset_items(brain, source_id: str, responses: dict,
                  everything: bool = False) -> list[Item]:
    out = []
    for dataset in brain.datasets_of(source_id):
        for question in spec.dataset_questions():
            out.append(Item("datasets", "dataset", dataset["id"], question))
    # asked even when the source has no Dataset node
    out.append(Item("datasets", "source", source_id, spec.dataset_recall_question()))
    return out


def cites_items(brain, source_id: str, responses: dict,
                everything: bool = False) -> list[Item]:
    out = []
    for question in spec.cites_questions():
        if not _applicable(question, brain, None, responses, everything):
            continue
        out.append(Item("cites", "source", source_id, question,
                        auto_na=auto_na_applies(question, brain, source_id, None)))
    return out


def recall_items(brain, source_id: str, responses: dict,
                 everything: bool = False) -> list[Item]:
    out = []
    for question in spec.recall_questions():
        if not _applicable(question, brain, None, responses, everything):
            continue
        out.append(Item("recall", "source", source_id, question,
                        auto_na=auto_na_applies(question, brain, source_id, None)))
    return out


def all_items(brain, source_id: str, responses: dict,
              everything: bool = False) -> list[Item]:
    items = source_items(brain, source_id, responses, everything)
    for claim in brain.claims_of(source_id):
        items += claim_items(brain, source_id, claim["id"], responses, everything)
    items += dataset_items(brain, source_id, responses, everything)
    items += cites_items(brain, source_id, responses, everything)
    items += recall_items(brain, source_id, responses, everything)
    return items


def all_possible_items(brain, source_id: str) -> list[Item]:
    """Every row this review could ever need, conditionals included.

    What preallocation must create. HE-20.b, HE-18.3, HE-19.3 and HE-20.S.b are
    asked only once their parent answer turns negative; if their rows were not
    made in advance, the first evaluator to answer ``No`` would append a row into
    a workbook other evaluators are reading and writing at the same time.

    The auto-N/A flag is still computed per item, because it is a fact about the
    Brain record rather than about anyone's answers.
    """
    return all_items(brain, source_id, {}, everything=True)


# ------------------------------------------------------------------ edges
def edges_of_claim(brain, claim_id: str) -> list[dict]:
    return brain.relations_of(claim_id)


def claim_edges_complete(brain, claim_id: str, edge_responses: dict) -> bool:
    import store

    for edge in edges_of_claim(brain, claim_id):
        record = edge_responses.get(store.edge_key_of(edge), {})
        if not record.get("label_correct"):
            return False
        if record.get("label_correct") in spec.EDGE_QUESTION.comment_required_on:
            if not (record.get("comment_correct_label") or "").strip():
                return False
    return True


def edge_problems(brain, claim_id: str, edge_responses: dict) -> list[tuple[dict, str]]:
    import store

    out = []
    for edge in edges_of_claim(brain, claim_id):
        record = edge_responses.get(store.edge_key_of(edge), {})
        answer = record.get("label_correct")
        if not answer:
            out.append((edge, "unanswered"))
        elif (answer in spec.EDGE_QUESTION.comment_required_on
              and not (record.get("comment_correct_label") or "").strip()):
            out.append((edge, f"answered {answer}, required comment missing"))
    return out


def he16_for_claim(brain, claim_id: str, edge_responses: dict) -> str:
    import store

    answers = [
        edge_responses.get(store.edge_key_of(edge), {}).get("label_correct")
        for edge in edges_of_claim(brain, claim_id)
    ]
    return spec.he16_summary(answers)


# ------------------------------------------------------------- completion
def claim_complete(brain, source_id, claim_id, responses, edge_responses) -> bool:
    items = claim_items(brain, source_id, claim_id, responses)
    if not all(item_complete(i, responses) for i in items):
        return False
    return claim_edges_complete(brain, claim_id, edge_responses)


def claims_done(brain, source_id, responses, edge_responses) -> int:
    """How many claims are complete, in any order."""
    return sum(
        1 for claim in brain.claims_of(source_id)
        if claim_complete(brain, source_id, claim["id"], responses, edge_responses)
    )


def section_complete(section, brain, source_id, responses, edge_responses) -> bool:
    if section == "claims":
        claims = brain.claims_of(source_id)
        return all(
            claim_complete(brain, source_id, c["id"], responses, edge_responses)
            for c in claims
        )
    if section == "review":
        return not missing_items(brain, source_id, responses, edge_responses)
    getter = {
        "source": source_items, "datasets": dataset_items,
        "cites": cites_items, "recall": recall_items,
    }[section]
    return all(item_complete(i, responses) for i in getter(brain, source_id, responses))


def section_states(brain, source_id, responses, edge_responses) -> dict[str, str]:
    """AVAILABLE / INCOMPLETE / COMPLETE for every section.

    No section is ever LOCKED. Each is reported on its own contents so the badges
    show progress, but any of them can be opened at any time.
    """
    states: dict[str, str] = {}
    for section in SECTION_IDS:
        if section_complete(section, brain, source_id, responses, edge_responses):
            states[section] = COMPLETE
        elif _section_started(section, brain, source_id, responses, edge_responses):
            states[section] = INCOMPLETE
        else:
            states[section] = AVAILABLE
    return states


def _section_started(section, brain, source_id, responses, edge_responses) -> bool:
    if section == "claims":
        return claims_done(brain, source_id, responses, edge_responses) > 0 or any(
            responses.get(i.lookup, {}).get("answer")
            for c in brain.claims_of(source_id)
            for i in applicable(claim_items(brain, source_id, c["id"], responses))
        )
    if section == "review":
        return False
    getter = {
        "source": source_items, "datasets": dataset_items,
        "cites": cites_items, "recall": recall_items,
    }[section]
    return any(responses.get(i.lookup, {}).get("answer")
               for i in applicable(getter(brain, source_id, responses)))


def next_open_section(states: dict[str, str]) -> str:
    """The first section still needing work — where a resumed paper reopens."""
    for section in SECTION_IDS:
        if section != "review" and states.get(section) in (AVAILABLE, INCOMPLETE):
            return section
    return SECTION_IDS[0]


def first_incomplete_claim(brain, source_id, responses, edge_responses) -> int:
    """Index of the first claim still needing work, for resuming."""
    for index, claim in enumerate(brain.claims_of(source_id)):
        if not claim_complete(brain, source_id, claim["id"], responses, edge_responses):
            return index
    return 0


def unlocked_sections(states: dict[str, str]) -> list[str]:
    """Every section. Kept as a function so callers stay unchanged."""
    return list(SECTION_IDS)


def unlocked_claim_count(brain, source_id, responses, edge_responses) -> int:
    """Every claim is reachable; claims are not gated on the previous one."""
    return len(brain.claims_of(source_id))


# ------------------------------------------------- claim page sub-sections
#: The five parts of a claim page, in the order they appear. A–D are questions;
#: E is one judgement per cross-source edge, which is why it is counted apart.
CLAIM_SUBSECTIONS = (
    spec.SUB_VALIDITY, spec.SUB_GROUNDING, spec.SUB_ATTRIBUTES,
    spec.SUB_CONCEPTS, spec.SUB_RELATIONS,
)


def claim_subsection_items(brain, source_id, claim_id, responses, subsection):
    """The applicable, answerable items of one part of a claim page."""
    return [i for i in applicable(claim_items(brain, source_id, claim_id, responses))
            if i.question.section == subsection]


def claim_subsection_progress(brain, source_id, claim_id, responses, edge_responses):
    """(label, done, total, state) for each of A–E.

    The denominator is what is actually asked of this claim, so it moves: HE-07
    and HE-21 drop out where the Brain record settles them, a conditional
    follow-up appears once its parent turns negative, and the number of edges
    differs from claim to claim. A fixed total would report a finished claim as
    unfinished.
    """
    out = []
    for subsection in CLAIM_SUBSECTIONS:
        if subsection == spec.SUB_RELATIONS:
            edges = edges_of_claim(brain, claim_id)
            problems = edge_problems(brain, claim_id, edge_responses)
            total, done = len(edges), len(edges) - len(problems)
            started = done > 0
        else:
            items = claim_subsection_items(brain, source_id, claim_id, responses,
                                           subsection)
            total = len(items)
            done = sum(1 for i in items if item_complete(i, responses))
            started = any(responses.get(i.lookup, {}).get("answer") for i in items)
        if total and done == total:
            state = COMPLETE
        elif started:
            state = INCOMPLETE
        else:
            state = AVAILABLE
        out.append((subsection, done, total, state))
    return out


def claim_progress(brain, source_id, claim_id, responses, edge_responses):
    """(done, total) over everything this claim actually asks, edges included."""
    items = applicable(claim_items(brain, source_id, claim_id, responses))
    done = sum(1 for i in items if item_complete(i, responses))
    edges = edges_of_claim(brain, claim_id)
    done += len(edges) - len(edge_problems(brain, claim_id, edge_responses))
    return done, len(items) + len(edges)


def claim_states(brain, source_id, responses, edge_responses) -> dict[str, str]:
    """AVAILABLE / INCOMPLETE / COMPLETE for every claim of a source."""
    states = {}
    for claim in brain.claims_of(source_id):
        done, total = claim_progress(brain, source_id, claim["id"], responses,
                                     edge_responses)
        if total and done == total:
            states[claim["id"]] = COMPLETE
        elif done:
            states[claim["id"]] = INCOMPLETE
        else:
            states[claim["id"]] = AVAILABLE
    return states


def resume_point(brain, source_id, responses, edge_responses):
    """Where work was left off: (section, claim index) — a suggestion, not a route.

    Offered as a shortcut the evaluator may ignore. Navigation is free, so
    nothing here restricts where they can go; it only saves them finding the
    place again.
    """
    states = section_states(brain, source_id, responses, edge_responses)
    section = next_open_section(states)
    index = first_incomplete_claim(brain, source_id, responses, edge_responses)
    return section, index


# ------------------------------------------------------------ review page
@dataclasses.dataclass(frozen=True)
class Missing:
    section: str
    where: str            # human-readable location
    what: str             # criterion id
    reason: str
    claim_index: int | None = None


def missing_items(brain, source_id, responses, edge_responses) -> list[Missing]:
    out: list[Missing] = []
    claims = brain.claims_of(source_id)
    index_of = {c["id"]: i for i, c in enumerate(claims)}

    for item in source_items(brain, source_id, responses):
        problem = item_problem(item, responses)
        if problem:
            out.append(Missing("source", "Source attributes", item.question.criterion_id, problem))

    for claim in claims:
        cid = claim["id"]
        for item in claim_items(brain, source_id, cid, responses):
            problem = item_problem(item, responses)
            if problem:
                out.append(Missing("claims", cid, item.question.criterion_id,
                                   problem, index_of[cid]))
        for edge, problem in edge_problems(brain, cid, edge_responses):
            out.append(Missing("claims", f"{cid} · edge {edge['type']} → {edge['other_claim_id']}",
                               "HE-16", problem, index_of[cid]))

    for item in dataset_items(brain, source_id, responses):
        problem = item_problem(item, responses)
        if problem:
            where = ("Dataset " + item.object_id) if item.object_type == "dataset" else "Source"
            out.append(Missing("datasets", where, item.question.criterion_id, problem))

    for item in cites_items(brain, source_id, responses):
        problem = item_problem(item, responses)
        if problem:
            out.append(Missing("cites", "CITES", item.question.criterion_id, problem))

    for item in recall_items(brain, source_id, responses):
        problem = item_problem(item, responses)
        if problem:
            out.append(Missing("recall", "Claim recall", item.question.criterion_id, problem))

    return out


def counts(brain, source_id, responses, edge_responses) -> dict:
    items = applicable(all_items(brain, source_id, responses))
    answered = sum(1 for i in items if item_complete(i, responses))
    edges = [e for c in brain.claims_of(source_id) for e in edges_of_claim(brain, c["id"])]
    import store
    edges_done = sum(
        1 for e in edges
        if edge_responses.get(store.edge_key_of(e), {}).get("label_correct")
    )
    return {
        "items": len(items), "answered": answered,
        "edges": len(edges), "edges_done": edges_done,
        "claims": len(brain.claims_of(source_id)),
        "claims_done": sum(
            1 for c in brain.claims_of(source_id)
            if claim_complete(brain, source_id, c["id"], responses, edge_responses)
        ),
    }
