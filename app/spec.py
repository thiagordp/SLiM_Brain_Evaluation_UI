"""Built-in evaluation specification.

The deployed app does not read HE_review_form.xlsx, the schema or the skills at
runtime. This module is the versioned internal specification: for every
existing evaluation question it fixes the question key, criterion id, object
type, wording, answer options, comment requirement and applicability rule.

Criterion wording and schema definitions are bundled verbatim in
data/he_criteria.json, extracted from the workbook by tools/extract_criteria.py.
No wording or answer type is redesigned here.

Two rules from the workbook that shape this file:

* ``question_key`` exists because criterion ids are not unique. HE-08.1 occurs
  at Source level (contribution_type) and at Claim level (claim_type); the same
  holds for HE-08.2 and HE-08.3. The evaluator never sees these keys.

* **HE-16 is not itself a Yes/No answer.** In the workbook its cell is a formula
  over the per-edge rows: correct / evaluated (%). The app therefore collects
  one judgment per edge and derives the HE-16 summary, exactly as Excel does.
  HE-16 has no entry in ``QUESTIONS``; see ``EDGE_QUESTION``.

Three layers, merged in order, so the workbook is never modified and each
change stays attributable:

    HE_review_form.xlsx
          |
    he_criteria.json      verbatim workbook extract
          |
    he_criteria_v2.json   the 2026-09-07 calibration meeting
          |
    he_criteria_v3.json   the page-by-page UI and instrument review, 2026-09-08

Version 3.0 fixes the final instrument. The scale is ``Yes / In part / No`` with
a comment required for the two negative values. There is no evaluator-facing
``Unclear`` flag and no generic evaluator-facing ``N/A``: the three criteria
that can be inapplicable are decided by the application from the Brain record
and stored explicitly, so an inapplicable item is never confused with an
unanswered one.
"""
from __future__ import annotations

import dataclasses
import functools
import json
import pathlib

EVAL_SPEC_VERSION = "3.0"

DATA = pathlib.Path(__file__).resolve().parent / "data" / "he_criteria.json"
DATA_V2 = pathlib.Path(__file__).resolve().parent / "data" / "he_criteria_v2.json"
DATA_V3 = pathlib.Path(__file__).resolve().parent / "data" / "he_criteria_v3.json"

# Qualitative criteria admit a middle value: many outputs are partly correct.
SCALE = ("Yes", "In part", "No")

#: Completeness at claim level is not a matter of degree. Either every
#: mapping-relevant concept this claim needs is present, or at least one is
#: missing and must be named. A middle value would only record how the evaluator
#: felt about a set they are about to enumerate anyway.
BINARY = ("Yes", "No")

FREE_TEXT: tuple[str, ...] = ()

#: Ordinal encoding for agreement analysis. N/A has no score.
SCORE = {"Yes": 3, "In part": 2, "No": 1}

NEGATIVE = ("In part", "No")
COMMENT_REQUIRED_ON = NEGATIVE

#: The stored answer for an inapplicable item.
#:
#: Two quite different things can produce it, and the pair must stay
#: distinguishable in the data:
#:
#: * the **application** decided, from the Brain record, that a criterion cannot
#:   apply — stored with ``applicability = auto_na``;
#: * the **evaluator** decided, from the paper, that it does not apply — stored
#:   with ``applicability = applicable``, because answering is exactly what they
#:   did.
#:
#: Only a criterion marked ``human_na`` may offer it as a choice.
NA_ANSWER = "N/A"

#: The only scale on which an evaluator may choose N/A: see HE-14.3.
SCALE_WITH_NA = ("Yes", "In part", "No", NA_ANSWER)

# Applicability rules
ALWAYS = "always"
# Follow-ups open on any negative answer, so a partly-correct parent still asks
# what is missing. These questions are not rendered at all while the parent is
# positive, and are not counted as missing.
IF_PARENT_IS_NEGATIVE = "if_parent_is_negative"   # HE-20.b, HE-18.3, HE-19.3, HE-20.S.b

# ------------------------------------------------------- automatic N/A rules
# Three criteria can be inapplicable for a reason the application can read off
# the Brain record. Asking the evaluator to select N/A for them invites the
# opposite error — selecting it when the criterion does apply — so the app
# decides, shows a sentence instead of a control, and stores the outcome as
# `answer = N/A` with `applicability = auto_na`. That keeps an inapplicable item
# distinguishable from an unanswered one in the exported data.
AUTO_NA_NONE = ""
AUTO_NA_NO_PREMISE = "no_premise_expected"            # HE-07
AUTO_NA_NO_CANDIDATE = "no_candidate_concept"         # HE-21
AUTO_NA_NO_OUTGOING_CITES = "no_outgoing_cites"       # HE-18.1

#: Stored in RESPONSES.applicability.
APPLICABLE = "applicable"
AUTO_NA = "auto_na"

AUTO_NA_TEXT = {
    AUTO_NA_NO_PREMISE:
        "Not applicable — no premise is expected because the source states no ground.",
    AUTO_NA_NO_CANDIDATE:
        "Not applicable — no candidate Concept was created for this Claim.",
    AUTO_NA_NO_OUTGOING_CITES:
        "Not applicable — the Brain generated no outgoing CITES edges to assess.",
}

CONCEPT_FAMILIES = ("legal_task", "technique_class", "normative_concern", "other")

CONCEPT_FAMILY_DEFINITION = {
    "legal_task": "What is being done with legal material — the task.",
    "technique_class": "How it is done — the class of technique.",
    "normative_concern": "What is at stake — the value or risk engaged.",
    "other": "A candidate notion none of the three families fits.",
}

CONCEPT_STATUS_DEFINITION = {
    "anchor": "Given in advance; defines the field.",
    "candidate": "Created during extraction because no anchor captured a claim "
                 "without distortion.",
    "emergent": "A candidate promoted at batch close-out after reaching the "
                "independent-source threshold. Same origin as a candidate.",
}

#: Shown once at the top of each section instead of repeating the rule per card.
RESPONSE_SCALE_NOTE = (
    "**Response scale:** **Yes** = fully complies · **In part** = partly complies · "
    "**No** = does not comply. A comment is required for **In part** and **No**."
)

COMMENT_LABEL = "Comment / evidence"
COMMENT_REQUIRED_NOTE = "Required for In part or No."


def comment_required_note(question) -> str:
    """Which answers oblige a comment, in this question's own terms.

    Nearly every criterion is Yes / In part / No, so the constant above holds.
    HE-20 is binary, and telling its evaluator that a comment is "required for
    In part or No" names an answer the question does not offer.
    """
    triggers = [a for a in question.answer_options
                if a in question.comment_required_on]
    if not triggers:
        return COMMENT_REQUIRED_NOTE
    return f"Required for {' or '.join(triggers)}."
DEFAULT_PLACEHOLDER = (
    "Explain what is incorrect or missing and, where possible, give the corrected "
    "value and the relevant location in the source."
)

ANCHOR_GRID_PATH = pathlib.Path(__file__).resolve().parent / "data" / "anchor_grid.json"


@functools.lru_cache(maxsize=1)
def anchor_grid() -> dict[str, list[dict]]:
    """The predefined anchor concepts, shipped with the app.

    Built in rather than read from schema/ at runtime, so the instrument stays
    frozen for this experiment even if the Brain's schema files later evolve.
    """
    return json.loads(ANCHOR_GRID_PATH.read_text(encoding="utf-8"))


@dataclasses.dataclass(frozen=True)
class Question:
    question_key: str          # SOURCE_HE08_1 — internal, never shown
    criterion_id: str          # HE-08.1 — shown
    object_type: str           # source | claim | dataset
    section: str               # which screen/sub-section it belongs to
    field_subitem: str         # visible criterion title
    question_text: str         # UI wording
    answer_options: tuple[str, ...]
    comment_required_on: tuple[str, ...] = COMMENT_REQUIRED_ON
    applicability: str = ALWAYS
    auto_na_rule: str = AUTO_NA_NONE   # the app decides, from the Brain record
    human_na: bool = False             # the evaluator may decide, from the paper
    parent_key: str | None = None      # for IF_PARENT_IS_NEGATIVE
    free_text: bool = False
    workbook_key: str = ""             # key into he_criteria.json

    def _text(self, field: str) -> str:
        """The newest layer that sets this field; workbook text otherwise."""
        override = override_for(self.question_key)
        if field in override:
            return override[field]
        return _workbook().get(self.workbook_key, {}).get(field, "")

    @property
    def criterion_definition(self) -> str:
        parts = [self.check_text, self.definition_text]
        return "\n\n".join(p for p in parts if p)

    @property
    def check_text(self) -> str:
        return self._text("check")

    @property
    def definition_text(self) -> str:
        return self._text("definition")

    @property
    def comment_placeholder(self) -> str:
        return self._text("placeholder") or DEFAULT_PLACEHOLDER

    @property
    def changed_in_v2(self) -> bool:
        return bool(_overrides_v2().get(self.question_key))

    @property
    def changed_in_v3(self) -> bool:
        return bool(_overrides_v3().get(self.question_key))

    @property
    def provenance(self) -> str:
        """Which review settled this criterion's current wording."""
        return override_for(self.question_key).get("_from", "")

    @property
    def scores(self) -> bool:
        """True when this question carries an ordinal judgment."""
        return not self.free_text

    @property
    def can_be_auto_na(self) -> bool:
        return bool(self.auto_na_rule)

    @property
    def auto_na_text(self) -> str:
        return AUTO_NA_TEXT.get(self.auto_na_rule, "")


@functools.lru_cache(maxsize=1)
def _workbook() -> dict:
    """The verbatim workbook extract (v1)."""
    return json.loads(DATA.read_text(encoding="utf-8"))


def _load(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


@functools.lru_cache(maxsize=1)
def _overrides_v2() -> dict:
    """The 2026-09-07 calibration changes, keyed by question_key."""
    return _load(DATA_V2)


@functools.lru_cache(maxsize=1)
def _overrides_v3() -> dict:
    """The 2026-09-08 page-by-page review, keyed by question_key."""
    return _load(DATA_V3)


@functools.lru_cache(maxsize=1)
def _overrides() -> dict:
    """v2 and v3 merged field by field, with v3 winning."""
    merged: dict[str, dict] = {k: dict(v) for k, v in _overrides_v2().items()}
    for key, entry in _overrides_v3().items():
        merged.setdefault(key, {}).update(entry)
    return merged


def override_for(question_key: str) -> dict:
    return _overrides().get(question_key, {})


def _q(**kwargs) -> Question:
    """Build a question, applying the newest wording override for its key."""
    override = override_for(kwargs["question_key"])
    if "question" in override:
        kwargs["question_text"] = override["question"]
    if "field" in override:
        kwargs["field_subitem"] = override["field"]
    question = Question(**kwargs)
    if question.workbook_key and question.workbook_key not in _workbook():
        raise KeyError(f"{question.workbook_key} missing from the workbook extract")
    if NA_ANSWER in question.answer_options and not question.human_na:
        raise ValueError(
            f"{question.question_key} offers N/A as a choice without human_na. "
            f"Inapplicability is normally read off the Brain record, not asked "
            f"of the evaluator; set human_na only where the paper is the only "
            f"thing that can settle it."
        )
    if question.human_na and question.auto_na_rule:
        raise ValueError(
            f"{question.question_key} is both decided by the app and offered to "
            f"the evaluator"
        )
    return question


# ---------------------------------------------------------------- sections
SEC_SOURCE = "source"
SEC_CLAIMS = "claims"
SEC_DATASETS = "datasets"
SEC_CITES = "cites"
SEC_RECALL = "recall"

# claim sub-sections, in the order they appear on the claim page
SUB_VALIDITY = "A · Claim"
SUB_GROUNDING = "B · Grounding"
SUB_ATTRIBUTES = "C · Attributes"
SUB_CONCEPTS = "D · Concepts"
SUB_RELATIONS = "E · Relations"


# Every ``question_text`` and ``field_subitem`` below is the final v3 wording.
# It is repeated in he_criteria_v3.json, which also carries the criterion
# definition and the comment placeholder; keeping the two in step means the
# fallback can never contradict the instrument if a file fails to load.
QUESTIONS: tuple[Question, ...] = (
    # ---------------------------------------------------------- 1. Source
    _q(question_key="SOURCE_HE08_1", criterion_id="HE-08.1", object_type="source",
       section=SEC_SOURCE, field_subitem="Contribution type",
       question_text="Do the selected `contribution_type` values correctly and completely "
                     "represent the publication's contribution, including its most "
                     "pertinent type or types?",
       answer_options=SCALE, workbook_key="source:HE-08.1"),
    _q(question_key="SOURCE_HE08_2", criterion_id="HE-08.2", object_type="source",
       section=SEC_SOURCE, field_subitem="Source jurisdiction",
       question_text="Does `source_jurisdiction` correctly represent the legal system or "
                     "systems in which the publication is situated?",
       answer_options=SCALE, workbook_key="source:HE-08.2"),
    # HE-08.3 (other_versions) was removed from the human flow on 2026-09-07:
    # duplicate and version handling already happens during preprocessing, so
    # only the selected publication is ever ingested. The requirement moves to
    # automatic/ingest validation, not to a reviewer.

    # ------------------------------------------------ 2A. claim as an item
    _q(question_key="CLAIM_HE03", criterion_id="HE-03", object_type="claim",
       section=SUB_VALIDITY, field_subitem="Claim definition",
       question_text="Does this extracted item qualify as a single claim under the Brain's "
                     "claim definition?",
       answer_options=SCALE, workbook_key="claim:HE-03"),
    _q(question_key="CLAIM_HE25", criterion_id="HE-25", object_type="claim",
       section=SUB_VALIDITY, field_subitem="No duplicate Claim",
       question_text="Is this Claim distinct from every other Claim extracted from this paper?",
       answer_options=SCALE, workbook_key="claim:HE-25"),
    _q(question_key="CLAIM_HE04", criterion_id="HE-04", object_type="claim",
       section=SUB_VALIDITY, field_subitem="Independent intelligibility",
       question_text="Can this Claim be understood on its own, without missing context "
                     "from the paper?",
       answer_options=SCALE, workbook_key="claim:HE-04"),
    _q(question_key="CLAIM_HE05", criterion_id="HE-05", object_type="claim",
       section=SUB_VALIDITY, field_subitem="Modality preserved",
       question_text="Does the Claim preserve the strength and modality of the source?",
       answer_options=SCALE, workbook_key="claim:HE-05"),

    # --------------------------------------------------- 2B. anchoring
    _q(question_key="CLAIM_HE06", criterion_id="HE-06", object_type="claim",
       section=SUB_GROUNDING, field_subitem="Textual grounding",
       question_text="Do the anchors provide sufficient textual grounding for this Claim "
                     "in the source?",
       answer_options=SCALE, workbook_key="claim:HE-06"),
    # N/A when `basis` is none_stated and the premise is correctly empty. The
    # Brain record settles that, so the app decides it rather than the evaluator.
    _q(question_key="CLAIM_HE07", criterion_id="HE-07", object_type="claim",
       section=SUB_GROUNDING, field_subitem="Premise",
       question_text="Is the premise a defensible reconstruction of the ground the source "
                     "gives for this Claim?",
       answer_options=SCALE, auto_na_rule=AUTO_NA_NO_PREMISE,
       workbook_key="claim:HE-07"),

    # -------------------------------------------------- 2C. attributes
    _q(question_key="CLAIM_HE08_1", criterion_id="HE-08.1", object_type="claim",
       section=SUB_ATTRIBUTES, field_subitem="Claim type",
       question_text="Is `claim_type` a defensible classification of what this Claim does?",
       answer_options=SCALE, workbook_key="claim:HE-08.1"),
    # `not_applicable` is a value the Brain may assign; the evaluator judges
    # whether assigning it was right, so this is an ordinary Yes/In part/No.
    _q(question_key="CLAIM_HE08_2", criterion_id="HE-08.2", object_type="claim",
       section=SUB_ATTRIBUTES, field_subitem="Positive form",
       question_text="If this Claim describes legal practice, is `positive_form` correctly "
                     "assigned? Otherwise, is it correctly marked `not_applicable`?",
       answer_options=SCALE, workbook_key="claim:HE-08.2"),
    _q(question_key="CLAIM_HE08_3", criterion_id="HE-08.3", object_type="claim",
       section=SUB_ATTRIBUTES, field_subitem="Basis",
       question_text="Is `basis` a defensible classification of the ground the source gives "
                     "for this Claim, and is `basis_qualifier` correct where applicable?",
       answer_options=SCALE, workbook_key="claim:HE-08.3"),
    _q(question_key="CLAIM_HE08_4", criterion_id="HE-08.4", object_type="claim",
       section=SUB_ATTRIBUTES, field_subitem="Claim jurisdiction",
       question_text="Do the jurisdiction fields correctly represent the legal scope of this "
                     "Claim and how that scope was determined?",
       answer_options=SCALE, workbook_key="claim:HE-08.4"),
    _q(question_key="CLAIM_HE08_5", criterion_id="HE-08.5", object_type="claim",
       section=SUB_ATTRIBUTES, field_subitem="Temporal reference",
       question_text="Does `temporal_reference` correctly represent the time or period "
                     "described by this Claim?",
       answer_options=SCALE, workbook_key="claim:HE-08.5"),

    # ---------------------------------------------------- 2D. concepts
    _q(question_key="CLAIM_HE12", criterion_id="HE-12", object_type="claim",
       section=SUB_CONCEPTS, field_subitem="Concept correctness",
       question_text="Is every Concept currently mapped to this Claim a defensible mapping?",
       answer_options=SCALE, workbook_key="claim:HE-12"),
    # N/A unless a candidate concept's own record names this claim as motivating
    # its creation. Read from the Concept record, never from log.md.
    _q(question_key="CLAIM_HE21", criterion_id="HE-21", object_type="claim",
       section=SUB_CONCEPTS, field_subitem="Candidate concept necessary",
       question_text="Was creating this candidate Concept necessary because no existing "
                     "anchor or equivalent Concept captured the Claim without distortion?",
       answer_options=SCALE, auto_na_rule=AUTO_NA_NO_CANDIDATE,
       workbook_key="claim:HE-21"),
    # Binary. A partial answer here would say "something is missing" without
    # saying what, and HE-20.b asks for exactly that list — so `No` and the list
    # carry the whole judgment between them.
    _q(question_key="CLAIM_HE20", criterion_id="HE-20", object_type="claim",
       section=SUB_CONCEPTS, field_subitem="Concept completeness",
       question_text="Are all Concepts needed to represent what this Claim substantively "
                     "concerns for mapping purposes included in its mapping?",
       answer_options=BINARY, comment_required_on=("No",),
       workbook_key="claim:HE-20"),
    _q(question_key="CLAIM_HE20B", criterion_id="HE-20.b", object_type="claim",
       section=SUB_CONCEPTS, field_subitem="Missing Concepts",
       question_text="If the mapping is incomplete, list the missing Concept(s).",
       answer_options=FREE_TEXT, free_text=True,
       applicability=IF_PARENT_IS_NEGATIVE, parent_key="CLAIM_HE20",
       comment_required_on=(), workbook_key="claim:HE-20.b"),

    # ---------------------------------------------------- 3. Datasets
    _q(question_key="DATASET_HE14_1", criterion_id="HE-14.1", object_type="dataset",
       section=SEC_DATASETS, field_subitem="Warranted Dataset node",
       question_text="Does this Dataset node correspond to a dataset, benchmark, or corpus "
                     "that the Source actually uses or introduces?",
       answer_options=SCALE, workbook_key="dataset:HE-14.1"),
    _q(question_key="DATASET_HE14_2", criterion_id="HE-14.2", object_type="dataset",
       section=SEC_DATASETS, field_subitem="Introduced by / used by",
       question_text="Do `introduced_by` and `used_by` correctly represent how this Dataset "
                     "relates to the Sources in the Brain?",
       answer_options=SCALE, workbook_key="dataset:HE-14.2"),
    # The Brain's own value may be `not_applicable` or `not_stated`; the
    # evaluator judges whether that value is right, so no evaluator-level N/A.
    _q(question_key="DATASET_HE15_1", criterion_id="HE-15.1", object_type="dataset",
       section=SEC_DATASETS, field_subitem="Language",
       question_text="Does `language` correctly identify the language or languages of the "
                     "texts in this Dataset?",
       answer_options=SCALE, workbook_key="dataset:HE-15.1"),
    _q(question_key="DATASET_HE15_2", criterion_id="HE-15.2", object_type="dataset",
       section=SEC_DATASETS, field_subitem="Jurisdiction",
       question_text="Does `jurisdiction` correctly identify the legal system or systems "
                     "from which the Dataset's texts come?",
       answer_options=SCALE, workbook_key="dataset:HE-15.2"),
    _q(question_key="DATASET_HE15_3", criterion_id="HE-15.3", object_type="dataset",
       section=SEC_DATASETS, field_subitem="Document types",
       question_text="Does `document_types` correctly describe the kinds of documents "
                     "contained in the Dataset?",
       answer_options=SCALE, workbook_key="dataset:HE-15.3"),
    _q(question_key="DATASET_HE15_4", criterion_id="HE-15.4", object_type="dataset",
       section=SEC_DATASETS, field_subitem="Size",
       question_text="Does `size` correctly reproduce the Dataset size stated by the "
                     "Source, including its unit?",
       answer_options=SCALE, workbook_key="dataset:HE-15.4"),
    _q(question_key="DATASET_HE15_5", criterion_id="HE-15.5", object_type="dataset",
       section=SEC_DATASETS, field_subitem="Annotation",
       question_text="Does `annotation` correctly describe how the Dataset was annotated?",
       answer_options=SCALE, workbook_key="dataset:HE-15.5"),
    _q(question_key="DATASET_HE15_6", criterion_id="HE-15.6", object_type="dataset",
       section=SEC_DATASETS, field_subitem="Agreement reported",
       question_text="Does `agreement_reported` correctly indicate whether the Source "
                     "reports an inter-annotator agreement measure for this Dataset?",
       answer_options=SCALE, workbook_key="dataset:HE-15.6"),
    _q(question_key="DATASET_HE15_7", criterion_id="HE-15.7", object_type="dataset",
       section=SEC_DATASETS, field_subitem="Availability",
       question_text="Does `availability` correctly represent the Dataset's access status "
                     "as reported by the Source?",
       answer_options=SCALE, workbook_key="dataset:HE-15.7"),
    # HE-14.3 sits on the Dataset sheet but its own wording says "answer on the
    # source as a whole", so it is stored against the Source. It is asked even
    # when the Brain created no Dataset node: zero nodes is not automatically
    # correct.
    # The one criterion where the evaluator may answer N/A. A source that uses no
    # dataset at all is a real state of the world, and only the paper can settle
    # it. Deliberately NOT inferred from the Brain having produced no Dataset
    # node: zero nodes may itself be the recall failure this question is asking
    # about.
    _q(question_key="SOURCE_HE14_3", criterion_id="HE-14.3", object_type="source",
       section=SEC_DATASETS, field_subitem="Dataset completeness",
       question_text="Has the Brain created a Dataset node for every dataset, benchmark, or "
                     "corpus that this Source actually uses or introduces?",
       answer_options=SCALE_WITH_NA, human_na=True,
       workbook_key="dataset:HE-14.3"),

    # ------------------------------------------------------- 4. CITES
    # N/A when the Brain generated no outgoing CITES edge — there is nothing to
    # assess. HE-18.2 is still asked: zero edges is not automatically correct.
    _q(question_key="SOURCE_HE18_1", criterion_id="HE-18.1", object_type="source",
       section=SEC_CITES, field_subitem="CITES accuracy",
       question_text="Do all outgoing CITES edges shown above correspond to citations that "
                     "this paper actually makes to the indicated Brain Sources, with the "
                     "correct direction from this paper to the cited Source?",
       answer_options=SCALE, auto_na_rule=AUTO_NA_NO_OUTGOING_CITES,
       workbook_key="source:HE-18.1"),
    _q(question_key="SOURCE_HE18_2", criterion_id="HE-18.2", object_type="source",
       section=SEC_CITES, field_subitem="CITES completeness",
       question_text="Are all citations made by this paper to other Sources represented in "
                     "the Brain captured by outgoing CITES edges?",
       answer_options=SCALE, workbook_key="source:HE-18.2"),
    _q(question_key="SOURCE_HE18_3", criterion_id="HE-18.3", object_type="source",
       section=SEC_CITES, field_subitem="Missing or spurious CITES edges",
       question_text="List the CITES edges that are missing or spurious.",
       answer_options=FREE_TEXT, free_text=True,
       applicability=IF_PARENT_IS_NEGATIVE, parent_key="SOURCE_HE18_1|SOURCE_HE18_2",
       comment_required_on=(), workbook_key="source:HE-18.3"),

    # ------------------------------------- 5. Source-level completeness
    _q(question_key="SOURCE_HE19_1", criterion_id="HE-19.1", object_type="source",
       section=SEC_RECALL, field_subitem="Claim recall",
       question_text="Does the extracted Claim set capture all central theses or hypotheses "
                     "that the Source advances as part of its contribution?",
       answer_options=SCALE, workbook_key="source:HE-19.1"),
    _q(question_key="SOURCE_HE19_3", criterion_id="HE-19.3", object_type="source",
       section=SEC_RECALL, field_subitem="Missing Claims",
       question_text="List each central Claim that is missing from the Brain.",
       answer_options=FREE_TEXT, free_text=True,
       applicability=IF_PARENT_IS_NEGATIVE, parent_key="SOURCE_HE19_1",
       comment_required_on=(), workbook_key="source:HE-19.3"),

    # Added 2026-09-07, settled 2026-09-08. Claim-level concept recall cannot
    # see that a concept absent from one claim may be carried by another claim
    # of the same paper; this asks the complementary question across the whole
    # source. It has no workbook ancestor, so its text comes only from v2/v3.
    _q(question_key="SOURCE_HE20S", criterion_id="HE-20.S", object_type="source",
       section=SEC_RECALL, field_subitem="Source conceptual coverage",
       question_text="Taken across all extracted Claims, does the Concept mapping "
                     "adequately represent the concepts that this Source materially "
                     "engages for systematic mapping?",
       answer_options=SCALE),
    _q(question_key="SOURCE_HE20S_B", criterion_id="HE-20.S.b", object_type="source",
       section=SEC_RECALL, field_subitem="Missing mapping-relevant Concepts",
       question_text="List the Concept or Concepts needed to complete the Source-level "
                     "mapping.",
       answer_options=FREE_TEXT, free_text=True,
       applicability=IF_PARENT_IS_NEGATIVE, parent_key="SOURCE_HE20S",
       comment_required_on=()),
)

BY_KEY = {q.question_key: q for q in QUESTIONS}


# HE-16 is answered once per edge and its claim-level value is derived.
EDGE_QUESTION = _q(
    question_key="EDGE_HE16", criterion_id="HE-16", object_type="edge",
    section=SUB_RELATIONS, field_subitem="Relation label",
    question_text="Is the relation label correct for the relationship between these two "
                  "Claims?",
    answer_options=SCALE, workbook_key="claim:HE-16",
)


def questions_for(section: str) -> list[Question]:
    return [q for q in QUESTIONS if q.section == section]


def claim_questions() -> list[Question]:
    """Every claim-level question, in page order."""
    order = (SUB_VALIDITY, SUB_GROUNDING, SUB_ATTRIBUTES, SUB_CONCEPTS)
    return [q for section in order for q in questions_for(section)]


def source_section_questions() -> list[Question]:
    return questions_for(SEC_SOURCE)


def dataset_questions() -> list[Question]:
    """Per-dataset questions only (HE-14.3 is source-level, asked once)."""
    return [q for q in questions_for(SEC_DATASETS) if q.object_type == "dataset"]


def dataset_recall_question() -> Question:
    return BY_KEY["SOURCE_HE14_3"]


def cites_questions() -> list[Question]:
    return questions_for(SEC_CITES)


def recall_questions() -> list[Question]:
    return questions_for(SEC_RECALL)


def he16_summary(edge_answers: list[str | None]) -> str:
    """Reproduce the workbook formula: correct / evaluated (percentage)."""
    evaluated = [a for a in edge_answers if a]
    if not evaluated:
        return ""
    yes = sum(1 for a in evaluated if a == "Yes")
    return f"{yes}/{len(evaluated)} ({yes / len(evaluated) * 100:.0f}%)"
