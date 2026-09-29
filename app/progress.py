"""What is asked of a review, and how much of it is done.

Items are generated from the Brain record, never from a fixed count:

    per Claim     Questions 2–11, one Question 12 per assigned Concept, one
                  Question 13 per assigned candidate Concept, one Question 14,
                  and per Relation whose From Claim this is: Grounding, Direction
                  (SUPPORTS and ATTACKS only) and Relation type
    per Dataset   six questions, for the Datasets the Source's Claims rest on
    per Source    Claim recall, Missing Claims when recall is not "All", and
                  Restatements

There is no Source evaluation, no CITES, no Dataset recall and no Source-level
Concept completeness. A Source with no Datasets asks no Dataset question; a
Source with no Claims still asks Claim recall.

Completion is criterion-specific (see `item_problem`). Required follow-up data —
the Question 14 selection, the Description comment, the Missing Claims text,
the restatement groups — blocks completion; an optional comment never does.

Two page-state models, as before:

    paper    NOT STARTED -> IN PROGRESS -> COMPLETE -> SUBMITTED
    section  AVAILABLE -> INCOMPLETE -> COMPLETE      (never locked)
"""
from __future__ import annotations

import dataclasses

import spec
import store

AVAILABLE, INCOMPLETE, COMPLETE, INFO = "available", "incomplete", "complete", "info"

SECTIONS = [
    ("source", "Source"),
    ("claims", "Claims"),
    ("datasets", "Datasets"),
    ("recall", "Claim recall"),
    ("review", "Review"),
]
SECTION_IDS = [s for s, _ in SECTIONS]
SECTION_LABEL = dict(SECTIONS)


@dataclasses.dataclass(frozen=True)
class Item:
    """One expected judgment."""
    question: spec.Question
    source_id: str
    object_id: str            # claim, dataset or source id; concept id; relation key
    claim_id: str = ""
    #: Restatements only: the Source's Claim ids, against which groups are checked.
    source_claims: tuple[str, ...] = ()

    @property
    def section(self) -> str:
        unit = self.question.unit
        if unit == spec.UNIT_DATASET:
            return "datasets"
        if unit == spec.UNIT_SOURCE:
            return "recall"
        return "claims"

    @property
    def part(self) -> str:
        return self.question.part


# ------------------------------------------------------------- generation
def claim_items(brain, source_id: str, claim_id: str) -> list[Item]:
    items = [Item(q, source_id, claim_id, claim_id)
             for q in spec.claim_scalar_questions() if q is not spec.Q14]
    items += [Item(spec.Q12, source_id, concept_id, claim_id)
              for concept_id in brain.concepts_of_claim(claim_id)]
    items += [Item(spec.Q13, source_id, concept_id, claim_id)
              for concept_id in brain.candidates_of_claim(claim_id)]
    items.append(Item(spec.Q14, source_id, claim_id, claim_id))
    for relation in brain.relations_from_claim(claim_id):
        items += [Item(q, source_id, relation["key"], claim_id)
                  for q in spec.relation_questions(relation)]
    return items


def dataset_items(brain, source_id: str, dataset_id: str | None = None) -> list[Item]:
    ids = [dataset_id] if dataset_id else brain.dataset_ids_of(source_id)
    return [Item(q, source_id, did) for did in ids for q in spec.dataset_questions()]


def recall_items(brain, source_id: str, data=None, everything: bool = False) -> list[Item]:
    items = [Item(spec.RECALL, source_id, source_id)]
    if everything or (data is not None and spec.child_visible(
            spec.MISSING_CLAIMS, answer_of(items[0], data))):
        items.append(Item(spec.MISSING_CLAIMS, source_id, source_id))
    items.append(Item(spec.RESTATEMENTS, source_id, source_id,
                      source_claims=tuple(c["id"] for c in brain.claims_of(source_id))))
    return items


def all_items(brain, source_id: str, data, everything: bool = False) -> list[Item]:
    items: list[Item] = []
    for claim in brain.claims_of(source_id):
        items += claim_items(brain, source_id, claim["id"])
    items += dataset_items(brain, source_id)
    items += recall_items(brain, source_id, data, everything)
    return items


# ---------------------------------------------------------------- answers
def record_of(item: Item, data) -> dict:
    question = item.question
    if question.table == spec.TAB_CONCEPT_RESPONSES:
        return data.concept(question.key, item.claim_id, item.object_id)
    if question.table == spec.TAB_RELATION_RESPONSES:
        return data.relation(item.object_id)
    return data.response(question.key, item.object_id)


def answer_of(item: Item, data) -> str:
    record = record_of(item, data)
    if item.question.table == spec.TAB_RELATION_RESPONSES:
        return str(record.get(f"{item.question.column}_answer") or "")
    return str(record.get("answer") or "")


def comment_of(item: Item, data) -> str:
    record = record_of(item, data)
    if item.question.table == spec.TAB_RELATION_RESPONSES:
        return str(record.get(f"{item.question.column}_comment") or "")
    return str(record.get("comment") or "")


def q14_selection(data, claim_id: str) -> tuple[list[dict], list[dict]]:
    return data.active_missing(claim_id), data.active_proposals(claim_id)


# ------------------------------------------------------------ restatements
def validate_restatement_group(brain, source_id: str, data, claim_ids,
                               replacing: str = "") -> tuple[list[str], str | None]:
    """(normalised member ids, why the group may not be written or None).

    The rule at the data boundary, whatever control proposed the group: members
    are this Source's Claims, duplicates are dropped, at least two distinct
    Claims remain, and none is already in another active group of this review.
    ``replacing`` names a group being rewritten, whose own members do not count
    as taken.
    """
    ids = sorted({str(c).strip() for c in claim_ids or () if str(c).strip()})
    mine = {c["id"] for c in brain.claims_of(source_id)}
    if not mine:
        return ids, f"{source_id} has no Claims."
    foreign = [c for c in ids if c not in mine]
    if foreign:
        return ids, f"{', '.join(foreign)} is not a Claim of {source_id}."
    if len(ids) < 2:
        return ids, "A restatement group needs at least two different Claims."
    taken = {cid: gid for gid, members in data.active_restatement_groups().items()
             if gid != replacing for cid in members}
    for cid in ids:
        if cid in taken and taken[cid] != store.restatement_group_id(ids):
            return ids, f"{cid} is already assigned to another restatement group."
        if cid in taken:
            return ids, "These Claims already form a restatement group."
    return ids, None


def restatement_groups(source_claims, data) -> tuple[dict[str, list[str]], list[str]]:
    """(valid active groups, problems with the rest), as loaded.

    A stored group counts only if its members are two or more distinct Claims of
    this Source, its id is the one those members derive, and no member is also
    in another active group. Anything else is left out and reported.
    """
    stored = data.active_restatement_groups()
    mine = set(source_claims)
    seen: dict[str, list[str]] = {}
    for gid, members in stored.items():
        for cid in members:
            seen.setdefault(cid, []).append(gid)
    valid, problems = {}, []
    for gid, members in sorted(stored.items(), key=lambda kv: kv[1]):
        if len(members) < 2:
            problems.append(f"group {', '.join(members)} has fewer than two Claims")
        elif any(c not in mine for c in members):
            problems.append(f"group {', '.join(members)} names a Claim of another Source")
        elif store.restatement_group_id(members) != gid:
            problems.append(f"group {', '.join(members)} is incomplete")
        elif any(len(seen[c]) > 1 for c in members):
            problems.append(f"group {', '.join(members)} shares a Claim with another group")
        else:
            valid[gid] = members
    return valid, problems


def _restatements_problem(item: Item, data) -> str | None:
    answer = answer_of(item, data)
    groups, problems = restatement_groups(item.source_claims, data)
    stored = data.active_restatement_groups()
    if answer == spec.RESTATEMENTS_NONE:
        return "answered No, but restatement groups exist" if stored else None
    if answer == spec.RESTATEMENTS_PRESENT:
        if problems:
            return "invalid restatement group: " + "; ".join(problems)
        return None if groups else "answered Yes, no restatement group added"
    return "unanswered"


def item_problem(item: Item, data) -> str | None:
    """Why this item is not complete, or None. Criterion-specific."""
    question = item.question
    answer = answer_of(item, data)
    if question is spec.RESTATEMENTS:
        return _restatements_problem(item, data)
    if question is spec.Q14:
        if answer == spec.Q14_NONE_MISSING:
            return None
        existing, proposed = q14_selection(data, item.claim_id)
        if answer == spec.Q14_MISSING and (existing or proposed):
            return None
        return "not evaluated"
    if question.free_text:
        return None if answer.strip() else "text required"
    if not answer:
        return "unanswered"
    if spec.comment_required(question, answer) and not comment_of(item, data).strip():
        return f"answered {answer}, comment required"
    return None


def item_complete(item: Item, data) -> bool:
    return item_problem(item, data) is None


def item_started(item: Item, data) -> bool:
    if item.question is spec.RESTATEMENTS:
        return bool(answer_of(item, data) or data.active_restatement_groups())
    if item.question is spec.Q14:
        existing, proposed = q14_selection(data, item.claim_id)
        return bool(answer_of(item, data) or existing or proposed)
    return bool(answer_of(item, data))


def _state(done: int, total: int, started: bool) -> str:
    if total and done == total:
        return COMPLETE
    return INCOMPLETE if started else AVAILABLE


# ------------------------------------------------------------------ claims
def claim_parts(brain, source_id: str, claim_id: str, data) -> list[tuple]:
    """(part, done, total, state) for the four parts of a Claim page."""
    items = claim_items(brain, source_id, claim_id)
    out = []
    for part in spec.CLAIM_PARTS:
        mine = [i for i in items if i.part == part]
        done = sum(1 for i in mine if item_complete(i, data))
        out.append((part, done, len(mine),
                    _state(done, len(mine), any(item_started(i, data) for i in mine))))
    return out


def claim_progress(brain, source_id: str, claim_id: str, data) -> tuple[int, int]:
    items = claim_items(brain, source_id, claim_id)
    return sum(1 for i in items if item_complete(i, data)), len(items)


def claim_complete(brain, source_id: str, claim_id: str, data) -> bool:
    done, total = claim_progress(brain, source_id, claim_id, data)
    return done == total


def claim_states(brain, source_id: str, data) -> dict[str, str]:
    states = {}
    for claim in brain.claims_of(source_id):
        items = claim_items(brain, source_id, claim["id"])
        done = sum(1 for i in items if item_complete(i, data))
        states[claim["id"]] = _state(done, len(items),
                                     any(item_started(i, data) for i in items))
    return states


def claims_done(brain, source_id: str, data) -> int:
    return sum(1 for state in claim_states(brain, source_id, data).values()
               if state == COMPLETE)


# ---------------------------------------------------------------- sections
def section_items(section: str, brain, source_id: str, data) -> list[Item]:
    if section == "claims":
        return [i for c in brain.claims_of(source_id)
                for i in claim_items(brain, source_id, c["id"])]
    if section == "datasets":
        return dataset_items(brain, source_id)
    if section == "recall":
        return recall_items(brain, source_id, data)
    return []


def section_states(brain, source_id: str, data) -> dict[str, str]:
    """The Source page is information only, so it has no state of its own."""
    states = {"source": INFO}
    for section in ("claims", "datasets", "recall"):
        items = section_items(section, brain, source_id, data)
        done = sum(1 for i in items if item_complete(i, data))
        if not items:
            states[section] = COMPLETE if section != "recall" else AVAILABLE
            if section in ("claims", "datasets"):
                states[section] = INFO
            continue
        states[section] = _state(done, len(items),
                                 any(item_started(i, data) for i in items))
    states["review"] = COMPLETE if not missing_items(brain, source_id, data) else AVAILABLE
    return states


def resume_point(brain, source_id: str, data) -> tuple[str, int]:
    """Where work was left: (section, claim index). A suggestion, never a route."""
    claims = brain.claims_of(source_id)
    for index, claim in enumerate(claims):
        if not claim_complete(brain, source_id, claim["id"], data):
            return "claims", index
    for section in ("datasets", "recall"):
        if any(not item_complete(i, data)
               for i in section_items(section, brain, source_id, data)):
            return section, 0
    return "review", 0


# ------------------------------------------------------------------ review
@dataclasses.dataclass(frozen=True)
class Missing:
    section: str
    where: str
    what: str
    reason: str
    claim_index: int | None = None
    dataset_index: int | None = None


def _where(brain, item: Item) -> str:
    unit = item.question.unit
    if unit in (spec.UNIT_CLAIM_CONCEPT, spec.UNIT_CLAIM_CANDIDATE):
        from brain import concept_label
        return f"{item.claim_id} · {concept_label(item.object_id)}"
    if unit == spec.UNIT_RELATION:
        relation = next((r for r in brain.relations_from_claim(item.claim_id)
                         if r["key"] == item.object_id), {})
        return (f"{item.claim_id} · {spec.value_label(relation.get('type', ''))} "
                f"→ {relation.get('to', '')}")
    if unit == spec.UNIT_DATASET:
        return f"Dataset {item.object_id}"
    if unit == spec.UNIT_SOURCE:
        return "Claim recall"
    return item.claim_id


def missing_items(brain, source_id: str, data) -> list[Missing]:
    claims = [c["id"] for c in brain.claims_of(source_id)]
    datasets = brain.dataset_ids_of(source_id)
    out = []
    for item in all_items(brain, source_id, data):
        problem = item_problem(item, data)
        if problem is None:
            continue
        out.append(Missing(
            item.section, _where(brain, item), item.question.title, problem,
            claims.index(item.claim_id) if item.claim_id in claims else None,
            datasets.index(item.object_id) if item.object_id in datasets else None))
    return out


def counts(brain, source_id: str, data) -> dict:
    items = all_items(brain, source_id, data)
    return {
        "items": len(items),
        "done": sum(1 for i in items if item_complete(i, data)),
        "claims": len(brain.claims_of(source_id)),
        "claims_done": claims_done(brain, source_id, data),
    }


# -------------------------------------------------------------- storage layout
def review_rows(brain, rid: str, source_id: str) -> dict[str, list[dict]]:
    """Every block row this review needs, conditional items included.

    What bootstrap preallocates. Missing Claims is created even though it is
    asked only once recall is below "All", so no row has to be appended in the
    middle of a live round. Question 14's selections are not here: they live in
    the two selection tabs, which grow by idempotent upserts.
    """
    responses, concepts, relations = [], [], []
    seen_relations = set()
    for item in all_items(brain, source_id, store.ReviewData(), everything=True):
        question = item.question
        if question.table == spec.TAB_RESPONSES:
            responses.append({
                "response_key": store.response_key(rid, question.unit, item.object_id,
                                                   question.key),
                "review_id": rid, "source_id": source_id,
                "object_type": question.unit, "object_id": item.object_id,
                "claim_id": item.claim_id, "question_key": question.key,
            })
        elif question.table == spec.TAB_CONCEPT_RESPONSES:
            concept = brain.concept(item.object_id)
            concepts.append({
                "response_key": store.concept_response_key(
                    rid, item.claim_id, item.object_id, question.key),
                "review_id": rid, "source_id": source_id,
                "claim_id": item.claim_id, "concept_id": item.object_id,
                "concept_status": concept.get("status", ""),
                "concept_family": concept.get("concept_type", ""),
                "question_key": question.key,
            })
        elif item.object_id not in seen_relations:
            seen_relations.add(item.object_id)
            relation = next(r for r in brain.relations_from_claim(item.claim_id)
                            if r["key"] == item.object_id)
            relations.append({
                "response_key": store.relation_response_key(rid, relation["key"]),
                "review_id": rid, "source_id": source_id,
                "relation_key": relation["key"], "relation_type": relation["type"],
                "from_claim": relation["from"], "to_claim": relation["to"],
                "from_source": relation["from_source"],
                "to_source": relation["to_source"],
                "grounding": relation.get("grounding", ""),
                "note": relation.get("note", ""),
            })
    return {"RESPONSES": responses, "CONCEPT_RESPONSES": concepts,
            "RELATION_RESPONSES": relations}
