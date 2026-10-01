"""The evaluation specification, version 4.1.

Declarative: every question fixes its storage unit, its agreed wording, its
answer options, which Brain definitions are shown beside it, what follow-up it
requires, and — separately — what its answers *mean*. Nothing downstream infers
meaning from the literal text of an answer: the semantics are declared per
question and read from here by progress, Review and analysis.

Definitions come from `data/definitions_v4.json`, frozen from the Brain's schema
and skills by `tools/freeze_definitions.py`. The wording is reproduced verbatim;
only backtick markup is dropped when it is displayed.

Calibration guidance (`CALIBRATION`) is a different kind of text: practical
rules agreed at the calibration meeting for instrument 4.1. It is not schema or
skill text, is never written into the frozen definitions file and does not
enter `definitions_id`; the instrument version records it.

4.1 changes from 4.0: the per-Claim restatement question (formerly Question 1)
is replaced by Source-level restatement groups in Claim recall, and Relations
gain an independent Direction judgment for SUPPORTS and ATTACKS. The remaining
question keys keep their numbers.

Version 3.0 (the HE-xx instrument) is not interpreted by this module. Its
criteria are archived in `data/archive/v3/` and its answers remain in the round
workbook they were given in.
"""
from __future__ import annotations

import dataclasses
import functools
import json
import pathlib
import re

EVAL_SPEC_VERSION = "4.1"

DEFINITIONS_PATH = pathlib.Path(__file__).resolve().parent / "data" / "definitions_v4.json"

# ------------------------------------------------------------------ answers
YES, IN_PART, NO = "Yes", "In part", "No"
BINARY = (YES, NO)
TERNARY = (YES, IN_PART, NO)

RECALL_NONE = "None are represented"
RECALL_SOME = "Some are represented"
RECALL_MOST = "Most are represented"
RECALL_ALL = "All are represented"
RECALL_LEVELS = (RECALL_NONE, RECALL_SOME, RECALL_MOST, RECALL_ALL)

#: Question 14 state, stored on its RESPONSES row. An empty selection cannot
#: mean both "not evaluated" and "nothing missing", so the second is explicit.
Q14_NOT_EVALUATED = ""
Q14_NONE_MISSING = "none_missing"
Q14_MISSING = "missing"
Q14_STATES = (Q14_NOT_EVALUATED, Q14_NONE_MISSING, Q14_MISSING)

#: Restatements state, stored on its RESPONSES row as a code; the evaluator sees
#: No / Yes. The groups themselves live in the RESTATEMENTS tab. Neither value is
#: ever inferred from the rows there.
RESTATEMENTS_NONE = "none"
RESTATEMENTS_PRESENT = "present"
RESTATEMENT_CODES = (RESTATEMENTS_NONE, RESTATEMENTS_PRESENT)
RESTATEMENT_LABEL = {RESTATEMENTS_NONE: NO, RESTATEMENTS_PRESENT: YES}

# ---------------------------------------------------------------- semantics
CORRECTNESS_BINARY = "correctness_binary"     # Yes = correct, No = defect
CORRECTNESS_TERNARY = "correctness_ternary"   # ordered Yes > In part > No
SET_VALUED = "set_valued"                     # Question 14
ORDINAL4 = "ordinal4"                         # Claim recall
QUALITATIVE = "qualitative"                   # Missing Claims
RESTATEMENT_GROUPS = "restatement_groups"     # present = defect; groups exported raw

# -------------------------------------------------------------------- units
UNIT_CLAIM = "claim"
UNIT_CLAIM_CONCEPT = "claim_concept"          # Question 12
UNIT_CLAIM_CANDIDATE = "claim_candidate"      # Question 13
UNIT_RELATION = "relation"
UNIT_DATASET = "dataset"
UNIT_SOURCE = "source"

# Where a unit's answers are stored.
TAB_RESPONSES = "RESPONSES"
TAB_CONCEPT_RESPONSES = "CONCEPT_RESPONSES"
TAB_RELATION_RESPONSES = "RELATION_RESPONSES"

# ------------------------------------------------------ parts of the pages
PART_CLAIM = "Claim evaluation"
PART_FIELDS = "Schema fields"
PART_CONCEPTS = "Concepts"
PART_RELATIONS = "Relations"
CLAIM_PARTS = (PART_CLAIM, PART_FIELDS, PART_CONCEPTS, PART_RELATIONS)
PART_DATASET = "Dataset"
PART_RECALL = "Claim recall"

COMMENT_LABEL = "Comment"
CORRECTION_LABEL = "Correction or comment"
OPTIONAL = "Optional."


@dataclasses.dataclass(frozen=True)
class Question:
    key: str                     # internal, never shown
    unit: str
    part: str
    title: str                   # short name for Review and headings
    text: str                    # the agreed wording, verbatim
    options: tuple[str, ...]
    semantics: str
    table: str = TAB_RESPONSES
    field: str = ""              # Brain field whose value is under judgment
    definitions: tuple[str, ...] = ()
    optional_comment_on: tuple[str, ...] = ()
    required_comment_on: tuple[str, ...] = ()
    calibration: tuple[str, ...] = ()        # keys of CALIBRATION
    relation_types: tuple[str, ...] = ()     # Relations: asked only for these types
    comment_label: str = CORRECTION_LABEL
    comment_help: str = ""
    parent: str = ""             # shown only for some answers of the parent
    shown_when_parent_in: tuple[str, ...] = ()
    column: str = ""             # RELATION_RESPONSES: which judgment column pair

    @property
    def free_text(self) -> bool:
        return self.semantics == QUALITATIVE


    def applies_to(self, relation: dict) -> bool:
        """Whether a Relation question is asked for this relation."""
        return not self.relation_types or relation.get("type") in self.relation_types


def _q(**kwargs) -> Question:
    return Question(**kwargs)


CLAIM_FIELD_QUESTIONS = (
    ("CLAIM_Q06_CLAIM_OBJECT", "claim_object", "Claim object"),
    ("CLAIM_Q07_CLAIM_TYPE", "claim_type", "Claim type"),
    ("CLAIM_Q08_BASIS", "basis", "Basis"),
    ("CLAIM_Q09_CLAIM_JURISDICTION", "claim_jurisdiction", "Claim jurisdiction"),
    ("CLAIM_Q10_LEGAL_REFERENCE", "legal_reference", "Legal reference"),
    ("CLAIM_Q11_TEMPORAL_REFERENCE", "temporal_reference", "Temporal reference"),
)

DATASET_FIELD_QUESTIONS = (
    ("DATASET_INTRODUCED_BY", "introduced_by", "Introduced by", ("dataset.introduced_by",)),
    ("DATASET_LANGUAGE", "language", "Language", ("dataset.language",)),
    ("DATASET_JURISDICTION", "jurisdiction", "Jurisdiction",
     ("dataset.jurisdiction", "claim.claim_jurisdiction")),
)

DESCRIPTION_HELP = (
    "If you selected In part or No, describe what is missing or incorrect. Where "
    "possible, provide the corrected information and indicate where it appears "
    "in the Source."
)

#: Explanatory interface text shown above the Grounding question. It is NOT a
#: definition and does not replace the frozen create-edges rule, which stays
#: available verbatim under Instructions.
GROUNDING_QUICK_GUIDE = (
    ("Extracted", "the two papers are linked by a citation on the specific point "
                  "represented by this relation."),
    ("Inferred", "there is no such citation grounding for this relation."),
)

#: Calibration-meeting guidance (instrument 4.1). NOT schema or skill text: it
#: is shown under its own "Calibration" heading, apart from the frozen
#: passages, and is kept out of `definitions_v4.json` and `definitions_id`.
#: Each entry is a tuple of lines, shown as separate paragraphs.
CALIBRATION_SOURCE = "calibration meeting (spec 4.1)"
CALIBRATION: dict[str, tuple[str, ...]] = {
    "claim.general": (
        "Evaluate this Claim from its statement and anchors.",
        "Judge the Claim fields from what the anchors support.",
        "Restatements are assessed in Claim recall.",
    ),
    "claim_object": (
        "Classify what the Claim asserts, not what it merely mentions.",
        "Law: the Claim is about law or legal/regulatory practice. This includes law "
        "regulating technology and the impact of technology on legal or regulatory "
        "practice.",
        "Technology: the Claim is about a technology, system or model. This includes "
        "how a technology behaves when applied to a legal task.",
        "Other: the Claim is substantively about both Law and Technology, or about Law "
        "or Technology together with another object that prevents either category from "
        "describing the Claim on its own.",
    ),
    "basis": (
        "Abstract means abstract or conceptual considerations. It does not mean the "
        "Abstract section of the paper.",
        "Literature means that the Claim and its anchors present the point as coming "
        "from prior literature.",
        "Judge the Basis from the anchors attached to this Claim.",
    ),
    "claim_jurisdiction": (
        "General: the Claim is explicitly jurisdiction-independent or concerns law in "
        "general.",
        "Undetermined: the jurisdiction is not stated and the context does not settle "
        "it.",
        "Do not choose General only because a technology Claim sounds broadly "
        "applicable.",
    ),
    "relation.direction": (
        "Judge whether the arrow runs from the Claim doing the supporting or "
        "attacking to the Claim being supported or attacked.",
    ),
}

#: Shown directly above the new-Concept proposal form.
PROPOSAL_HINT = ("Propose a new Concept only when no existing Concept can represent "
                 "this Claim without bending it.")

MISSING_CLAIMS_HELP = (
    "Write each missing Claim as a short proposition and, where possible, "
    "indicate the page or section where the Source advances it."
)

QUESTIONS: tuple[Question, ...] = (
    # ------------------------------------------------ Claim evaluation
    _q(key="CLAIM_Q02_CENTRAL_THESIS", unit=UNIT_CLAIM, part=PART_CLAIM,
       title="Central thesis or hypothesis",
       text="Does this statement represent a central thesis or hypothesis that the "
            "paper advances as part of its contribution?",
       options=BINARY, semantics=CORRECTNESS_BINARY,
       definitions=("claim.node", "claim.statement"), optional_comment_on=(NO,),
       comment_label=COMMENT_LABEL),
    _q(key="CLAIM_Q03_MODALITY", unit=UNIT_CLAIM, part=PART_CLAIM,
       title="Strength and modality",
       text="Does the Claim preserve the strength and modality of the source?",
       options=BINARY, semantics=CORRECTNESS_BINARY,
       definitions=("skill.extract_claims.modality",), optional_comment_on=(NO,),
       comment_label=COMMENT_LABEL),
    _q(key="CLAIM_Q04_STANDALONE", unit=UNIT_CLAIM, part=PART_CLAIM,
       title="Understood on its own",
       text="Can this Claim be understood on its own, without missing context from "
            "the paper?",
       options=BINARY, semantics=CORRECTNESS_BINARY,
       definitions=("skill.extract_claims.standalone",), optional_comment_on=(NO,),
       comment_label=COMMENT_LABEL),
    _q(key="CLAIM_Q05_GROUNDING", unit=UNIT_CLAIM, part=PART_CLAIM,
       title="Textual grounding",
       text="Do the anchors provide sufficient textual grounding for this Claim in "
            "the source?",
       options=TERNARY, semantics=CORRECTNESS_TERNARY,
       definitions=("claim.anchors",), optional_comment_on=(IN_PART, NO),
       comment_label=COMMENT_LABEL),
    # ------------------------------------------------- Schema fields
    *(_q(key=key, unit=UNIT_CLAIM, part=PART_FIELDS, title=label,
         text=f"Is {label} correctly assigned according to the schema definition?",
         options=BINARY, semantics=CORRECTNESS_BINARY, field=field,
         definitions=(f"claim.{field}",), optional_comment_on=(NO,),
         calibration=(field,) if field in CALIBRATION else ())
      for key, field, label in CLAIM_FIELD_QUESTIONS),
    # ------------------------------------------------------- Concepts
    _q(key="CLAIM_Q12_CONCEPT", unit=UNIT_CLAIM_CONCEPT, part=PART_CONCEPTS,
       title="Concept assignment",
       text="Is this Concept correctly assigned to the Claim?",
       options=BINARY, semantics=CORRECTNESS_BINARY, table=TAB_CONCEPT_RESPONSES,
       optional_comment_on=(NO,), comment_label=COMMENT_LABEL),
    _q(key="CLAIM_Q13_CANDIDATE", unit=UNIT_CLAIM_CANDIDATE, part=PART_CONCEPTS,
       title="Candidate Concept necessary",
       text="Is this candidate Concept necessary for representing this Claim, given "
            "the existing Concept vocabulary?",
       options=BINARY, semantics=CORRECTNESS_BINARY, table=TAB_CONCEPT_RESPONSES,
       definitions=("concept.status",), optional_comment_on=(NO,),
       comment_label=COMMENT_LABEL),
    _q(key="CLAIM_Q14_MISSING_CONCEPTS", unit=UNIT_CLAIM, part=PART_CONCEPTS,
       title="Missing Concepts",
       text="Are any mapping-relevant Concepts missing from this Claim?",
       options=(), semantics=SET_VALUED),
    # ------------------------------------------------------ Relations
    _q(key="REL_GROUNDING", unit=UNIT_RELATION, part=PART_RELATIONS,
       title="Grounding",
       text="Is the Grounding value correctly assigned according to the schema "
            "definition?",
       options=BINARY, semantics=CORRECTNESS_BINARY, table=TAB_RELATION_RESPONSES,
       field="grounding", definitions=("edge.grounding",),
       optional_comment_on=(NO,), column="grounding"),
    _q(key="REL_DIRECTION", unit=UNIT_RELATION, part=PART_RELATIONS,
       title="Direction",
       text="Is the direction of this relation correct?",
       options=BINARY, semantics=CORRECTNESS_BINARY, table=TAB_RELATION_RESPONSES,
       definitions=("edge.from_to", "edge.relation_type"),
       calibration=("relation.direction",), optional_comment_on=(NO,),
       column="direction", relation_types=("SUPPORTS", "ATTACKS")),
    _q(key="REL_TYPE", unit=UNIT_RELATION, part=PART_RELATIONS,
       title="Relation type",
       text="Is the Relation type correct for the relationship between these two "
            "Claims?",
       options=BINARY, semantics=CORRECTNESS_BINARY, table=TAB_RELATION_RESPONSES,
       field="type", definitions=("edge.relation_type",),
       optional_comment_on=(NO,), column="type"),
    # ------------------------------------------------------- Datasets
    _q(key="DATASET_NODE", unit=UNIT_DATASET, part=PART_DATASET,
       title="Dataset node",
       text="Does this record represent a dataset, benchmark or corpus that a Claim "
            "in this Source actually rests on?",
       options=BINARY, semantics=CORRECTNESS_BINARY,
       definitions=("dataset.node",), optional_comment_on=(NO,),
       comment_label=COMMENT_LABEL),
    *(_q(key=key, unit=UNIT_DATASET, part=PART_DATASET, title=label,
         text=f"Is {label} correctly assigned according to the schema definition?",
         options=BINARY, semantics=CORRECTNESS_BINARY, field=field,
         definitions=definitions, optional_comment_on=(NO,))
      for key, field, label, definitions in DATASET_FIELD_QUESTIONS),
    _q(key="DATASET_DESCRIPTION", unit=UNIT_DATASET, part=PART_DATASET,
       title="Description",
       text="Does the Dataset description correctly and sufficiently represent the "
            "Dataset characteristics reported by the Source?",
       options=TERNARY, semantics=CORRECTNESS_TERNARY, field="description",
       definitions=("dataset.description",), required_comment_on=(IN_PART, NO),
       comment_label=COMMENT_LABEL, comment_help=DESCRIPTION_HELP),
    _q(key="DATASET_AVAILABILITY", unit=UNIT_DATASET, part=PART_DATASET,
       title="Availability",
       text="Is Availability correctly assigned according to the schema definition?",
       options=BINARY, semantics=CORRECTNESS_BINARY, field="availability",
       definitions=("dataset.availability",), optional_comment_on=(NO,)),
    # --------------------------------------------------- Claim recall
    _q(key="SOURCE_CLAIM_RECALL", unit=UNIT_SOURCE, part=PART_RECALL,
       title="Claim recall",
       text="How completely does the current set of extracted Claims represent the "
            "central theses or hypotheses that this Source advances as part of its "
            "contribution?",
       options=RECALL_LEVELS, semantics=ORDINAL4, definitions=("claim.node",)),
    _q(key="SOURCE_MISSING_CLAIMS", unit=UNIT_SOURCE, part=PART_RECALL,
       title="Missing Claims",
       text="Which central Claims are missing from the extracted set?",
       options=(), semantics=QUALITATIVE, parent="SOURCE_CLAIM_RECALL",
       shown_when_parent_in=(RECALL_NONE, RECALL_SOME, RECALL_MOST),
       comment_help=MISSING_CLAIMS_HELP),
    _q(key="SOURCE_RESTATEMENTS", unit=UNIT_SOURCE, part=PART_RECALL,
       title="Restatements",
       text="Are any extracted Claims restatements of the same proposition?",
       options=RESTATEMENT_CODES, semantics=RESTATEMENT_GROUPS),
)

BY_KEY = {q.key: q for q in QUESTIONS}


def questions(*, unit: str | None = None, part: str | None = None) -> list[Question]:
    return [q for q in QUESTIONS
            if (unit is None or q.unit == unit) and (part is None or q.part == part)]


def claim_scalar_questions(part: str | None = None) -> list[Question]:
    """Questions 2–11 and the Question 14 state row: one row per Claim."""
    return [q for q in questions(unit=UNIT_CLAIM, part=part)]


def dataset_questions() -> list[Question]:
    return questions(unit=UNIT_DATASET)


def relation_questions(relation: dict | None = None) -> list[Question]:
    """The Relation questions; given a relation, only those asked for its type."""
    return [q for q in questions(unit=UNIT_RELATION)
            if relation is None or q.applies_to(relation)]


def recall_questions() -> list[Question]:
    return questions(unit=UNIT_SOURCE)


Q12 = BY_KEY["CLAIM_Q12_CONCEPT"]
Q13 = BY_KEY["CLAIM_Q13_CANDIDATE"]
Q14 = BY_KEY["CLAIM_Q14_MISSING_CONCEPTS"]
RECALL = BY_KEY["SOURCE_CLAIM_RECALL"]
MISSING_CLAIMS = BY_KEY["SOURCE_MISSING_CLAIMS"]
RESTATEMENTS = BY_KEY["SOURCE_RESTATEMENTS"]
DIRECTION = BY_KEY["REL_DIRECTION"]


# ---------------------------------------------------------------- meaning
def problem(question: Question, answer: str) -> bool:
    """Whether this answer records a defect in the Brain output.

    Criterion-specific by construction: a problem is read from the question's
    declared semantics, never from the literal answer text.
    """
    if not answer:
        return False
    if question.semantics == RESTATEMENT_GROUPS:
        return answer == RESTATEMENTS_PRESENT
    if question.semantics in (CORRECTNESS_BINARY, CORRECTNESS_TERNARY):
        return answer in (NO, IN_PART)
    if question.semantics == ORDINAL4:
        return answer != RECALL_ALL
    if question.semantics == SET_VALUED:
        return answer == Q14_MISSING
    return False


def ordinal(question: Question, answer: str) -> int | None:
    """Position on an ordered scale, for weighted agreement. None elsewhere."""
    if question.semantics == CORRECTNESS_TERNARY and answer in TERNARY:
        return {NO: 0, IN_PART: 1, YES: 2}[answer]
    if question.semantics == ORDINAL4 and answer in RECALL_LEVELS:
        return RECALL_LEVELS.index(answer)
    return None


def comment_visible(question: Question, answer: str) -> bool:
    return bool(answer) and (answer in question.optional_comment_on
                             or answer in question.required_comment_on)


def comment_required(question: Question, answer: str) -> bool:
    return bool(answer) and answer in question.required_comment_on


def child_visible(question: Question, parent_answer: str) -> bool:
    return bool(parent_answer) and parent_answer in question.shown_when_parent_in


# ------------------------------------------------------------ definitions
@functools.lru_cache(maxsize=1)
def definitions() -> dict:
    return json.loads(DEFINITIONS_PATH.read_text(encoding="utf-8"))


def definitions_id() -> str:
    return definitions()["definitions_id"]


def canonical_schema_version() -> str:
    return definitions()["canonical_schema_version"]


def frozen_source_hashes() -> dict[str, str]:
    return dict(definitions()["source_hashes"])


def definition(key: str) -> dict:
    return definitions()["entries"][key]


def concept_grid() -> dict[str, list[str]]:
    """The anchor grid of the frozen schema, in the schema's family order."""
    grid = definitions()["concept_grid"]
    from brain import CONCEPT_FAMILIES

    return {family: list(grid.get(family, [])) for family in CONCEPT_FAMILIES}


_TICKS = re.compile(r"`([^`]*)`")


def plain(text: str) -> str:
    """Definition text for display: verbatim, with the code markup dropped."""
    return _TICKS.sub(r"\1", text or "")


def value_label(value) -> str:
    """A schema value as a reader names it: `on_request` -> `On request`.

    Codes that are identifiers rather than words — `EU`, `US`, `SUPPORTS` —
    keep their case; only snake_case words are turned into prose.
    """
    text = str(value if value is not None else "")
    if not text:
        return ""
    if re.fullmatch(r"[a-z]+(_[a-z]+)*", text):
        words = text.replace("_", " ")
        return words[:1].upper() + words[1:]
    if re.fullmatch(r"[A-Z]+(_[A-Z]+)+", text):          # SAME_AS
        return text.replace("_", " ")
    return text
