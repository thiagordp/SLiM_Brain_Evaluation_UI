"""Checks for the evaluation application, instrument 4.0.

    python app/tests/test_app.py            # everything
    python app/tests/test_app.py adapter    # only tests whose name contains "adapter"

Storage is an in-memory Google Sheets workbook (`tests/fakes.py`); nothing here
touches a real workbook. The UI checks run the real Streamlit script headlessly
with `streamlit.testing.v1.AppTest`.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile
import traceback

APP = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(APP), str(APP / "tests"), str(APP / "tools")]
os.environ["HE_APP_PASSWORD"] = "test-password"
os.environ["HE_ADMIN_SECRET"] = "test-admin"
for name in ("GOOGLE_SHEET_ID", "HE_GOOGLE_SHEET_ID", "GOOGLE_SERVICE_ACCOUNT_JSON",
             "HE_GOOGLE_CREDENTIALS", "GOOGLE_CREDENTIALS", "HE_ROUND_ID", "HE_BRAIN_DIR"):
    os.environ.pop(name, None)

import allocation  # noqa: E402
import analysis  # noqa: E402
import bootstrap_round  # noqa: E402
import brain as brain_module  # noqa: E402
import conceptsearch  # noqa: E402
import fakes  # noqa: E402
import freeze_definitions  # noqa: E402
import manifest  # noqa: E402
import preflight  # noqa: E402
import progress  # noqa: E402
import sheets  # noqa: E402
import spec  # noqa: E402
import store  # noqa: E402

ROUND = manifest.round_id()
BRAIN = brain_module.load_brain()
FAILURES: list[str] = []
CHECKS = 0


def check(condition, message: str) -> None:
    global CHECKS
    CHECKS += 1
    if not condition:
        FAILURES.append(message)
        print(f"  FAIL  {message}")


def fresh_round() -> fakes.FakeWorkbook:
    """A fake workbook bootstrapped exactly as a real round would be."""
    book = fakes.FakeWorkbook()
    store.use_workbook(book)
    manifest.invalidate()
    sys.argv = ["bootstrap_round.py"]
    with contextlib.redirect_stdout(io.StringIO()):
        code = bootstrap_round.main()
    assert code == 0, "bootstrap failed"
    store.forget_all()
    return book


def rid(phase: str, evaluator: str, source: str) -> str:
    return store.review_id(ROUND, phase, evaluator, source)


def start(review_id: str) -> None:
    store.start_review(review_id, True, eval_spec_version=spec.EVAL_SPEC_VERSION)


def answer_everything(review_id: str, source_id: str, *, recall=spec.RECALL_ALL) -> None:
    """Complete one review directly through the store, as fast as a test can."""
    data = store.load_review(review_id)
    records = []
    for row in data.responses.values():
        question = spec.BY_KEY[row["question_key"]]
        if question is spec.Q14:
            answer = spec.Q14_NONE_MISSING
        elif question is spec.RECALL:
            answer = recall
        elif question is spec.MISSING_CLAIMS:
            answer = "" if recall == spec.RECALL_ALL else "A missing thesis (p. 3)."
        elif question is spec.Q1:
            answer = spec.NO
        else:
            answer = spec.YES
        records.append({"tab": sheets.RESPONSES, "key": row["response_key"],
                        "values": {**row, "answer": answer}, "rid": review_id})
    for row in data.concepts.values():
        records.append({"tab": sheets.CONCEPT_RESPONSES, "key": row["response_key"],
                        "values": {**row, "answer": spec.YES}, "rid": review_id})
    for row in data.relations.values():
        records.append({"tab": sheets.RELATION_RESPONSES, "key": row["response_key"],
                        "values": {**row, "grounding_answer": spec.YES,
                                   "type_answer": spec.YES}, "rid": review_id})
    store.save_many(records)


def brain_copy() -> pathlib.Path:
    target = pathlib.Path(tempfile.mkdtemp(prefix="he-brain-"))
    shutil.copytree(BRAIN.root / "wiki", target / "wiki")
    shutil.copytree(BRAIN.root / "schema", target / "schema")
    return target


# =================================================================== adapter
def test_adapter_reads_current_schema():
    check(len(BRAIN.sources) == 25 and len(BRAIN.claims) == 374,
          "adapter: 25 Sources and 374 Claims")
    check(len(BRAIN.datasets) == 25 and not BRAIN.load_problems,
          "adapter: every Dataset page is read, including those YAML would reject")
    check(":" in BRAIN.dataset("DST-0004")["description"],
          "adapter: a description containing a colon is read whole")
    check(BRAIN.dataset_ids_of("SRC-0011") == ["DST-0008", "DST-0009", "DST-0010"],
          "adapter: Datasets come from the plural Claim field")
    check(BRAIN.dataset_ids_of("SRC-0003") == [], "adapter: SRC-0003 has no Dataset")
    relations = BRAIN.claim_relations()
    hosted = sum(len(BRAIN.relations_hosted(s)) for s in BRAIN.source_ids)
    check(hosted == len(relations) == 265,
          "adapter: every Claim Relation is hosted by exactly one Source")
    check(all(r["type"] in ("SUPPORTS", "ATTACKS", "SAME_AS") for r in relations),
          "adapter: only current Claim-to-Claim relation types")
    check(brain_module.concept_label("CPT-irac-analysis") == "IRAC analysis"
          and brain_module.concept_label("CPT-access-to-justice") == "Access to justice",
          "adapter: Concept names are derived deterministically from ids")
    vocabulary = BRAIN.vocabulary(spec.concept_grid())
    grid_only = [v for v in vocabulary if not v["has_page"]]
    check(len(grid_only) == 11 and all(v["definition"] == "" for v in grid_only),
          "adapter: grid-only anchors are in the vocabulary, with no invented definition")
    check(BRAIN.canonical_schema_version == "0.1.0", "adapter: canonical schema version")
    parsed = brain_module.parse_frontmatter(
        "---\nid: X\nlist: [a, b]\njson: [\"c, d\"]\nblock:\n  - e\n  - f\nnote: a: b\n---\n")
    check(parsed == {"id": "X", "list": ["a", "b"], "json": ["c, d"],
                     "block": ["e", "f"], "note": "a: b"},
          "adapter: frontmatter is read the way the Brain's own tools read it")


# =============================================================== definitions
def test_definitions_are_frozen_verbatim():
    skills = freeze_definitions.DEFAULT_SKILLS
    if skills.exists():
        rebuilt = freeze_definitions.build(BRAIN.root / "schema", skills)
        check(rebuilt == spec.definitions(),
              "definitions: the frozen file matches the schema and skills on disk")
    for key, entry in spec.definitions()["entries"].items():
        path = (BRAIN.root / entry["source"]) if entry["source"].startswith("schema/") \
            else skills.parent.parent / entry["source"]
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        check(entry["text"] in text, f"definitions: {key} text is verbatim")
        for item in entry.get("items", []):
            if item.get("text"):
                check(item["text"] in text, f"definitions: {key} / {item.get('value')} verbatim")
            for sub in item.get("sub", []):
                check(sub in text, f"definitions: {key} sub-item verbatim")
    grounding = spec.definition("edge.grounding")
    check(grounding["source"] == ".claude/skills/create-edges/SKILL.md"
          and grounding["items"][1]["text"] == "otherwise.",
          "definitions: Grounding comes word for word from the create-edges skill")
    check(spec.plain("one of `public` | `on_request`") == "one of public | on_request",
          "definitions: display drops only the code markup")


# ====================================================================== spec
AGREED = {
    "CLAIM_Q01_RESTATEMENT": "Is this Claim a restatement of another Claim already "
                             "extracted from this Source?",
    "CLAIM_Q02_CENTRAL_THESIS": "Does this statement represent a central thesis or "
                                "hypothesis that the paper advances as part of its "
                                "contribution?",
    "CLAIM_Q03_MODALITY": "Does the Claim preserve the strength and modality of the source?",
    "CLAIM_Q04_STANDALONE": "Can this Claim be understood on its own, without missing "
                            "context from the paper?",
    "CLAIM_Q05_GROUNDING": "Do the anchors provide sufficient textual grounding for this "
                           "Claim in the source?",
    "CLAIM_Q06_CLAIM_OBJECT": "Is Claim object correctly assigned according to the schema "
                              "definition?",
    "CLAIM_Q07_CLAIM_TYPE": "Is Claim type correctly assigned according to the schema "
                            "definition?",
    "CLAIM_Q08_BASIS": "Is Basis correctly assigned according to the schema definition?",
    "CLAIM_Q09_CLAIM_JURISDICTION": "Is Claim jurisdiction correctly assigned according "
                                    "to the schema definition?",
    "CLAIM_Q10_LEGAL_REFERENCE": "Is Legal reference correctly assigned according to the "
                                 "schema definition?",
    "CLAIM_Q11_TEMPORAL_REFERENCE": "Is Temporal reference correctly assigned according "
                                    "to the schema definition?",
    "CLAIM_Q12_CONCEPT": "Is this Concept correctly assigned to the Claim?",
    "CLAIM_Q13_CANDIDATE": "Is this candidate Concept necessary for representing this "
                           "Claim, given the existing Concept vocabulary?",
    "CLAIM_Q14_MISSING_CONCEPTS": "Are any mapping-relevant Concepts missing from this Claim?",
    "REL_GROUNDING": "Is the Grounding value correctly assigned according to the schema "
                     "definition?",
    "REL_TYPE": "Is the Relation type correct for the relationship between these two Claims?",
    "DATASET_NODE": "Does this record represent a dataset, benchmark or corpus that a "
                    "Claim in this Source actually rests on?",
    "DATASET_INTRODUCED_BY": "Is Introduced by correctly assigned according to the schema "
                             "definition?",
    "DATASET_LANGUAGE": "Is Language correctly assigned according to the schema definition?",
    "DATASET_JURISDICTION": "Is Jurisdiction correctly assigned according to the schema "
                            "definition?",
    "DATASET_DESCRIPTION": "Does the Dataset description correctly and sufficiently "
                           "represent the Dataset characteristics reported by the Source?",
    "DATASET_AVAILABILITY": "Is Availability correctly assigned according to the schema "
                            "definition?",
    "SOURCE_CLAIM_RECALL": "How completely does the current set of extracted Claims "
                           "represent the central theses or hypotheses that this Source "
                           "advances as part of its contribution?",
    "SOURCE_MISSING_CLAIMS": "Which central Claims are missing from the extracted set?",
}


def test_spec_wording_and_semantics():
    check(set(AGREED) == set(spec.BY_KEY), "spec: exactly the agreed questions exist")
    for key, text in AGREED.items():
        check(spec.BY_KEY[key].text == text, f"spec: {key} uses the agreed wording")
    check(spec.Q1.options == (spec.YES, spec.NO) and spec.problem(spec.Q1, spec.YES)
          and not spec.problem(spec.Q1, spec.NO),
          "spec: Question 1 Yes flags a restatement")
    q6 = spec.BY_KEY["CLAIM_Q06_CLAIM_OBJECT"]
    check(not spec.problem(q6, spec.YES) and spec.problem(q6, spec.NO),
          "spec: Questions 6–11 Yes means correct")
    check(spec.BY_KEY["CLAIM_Q05_GROUNDING"].options == spec.TERNARY,
          "spec: Question 5 is Yes / In part / No")
    check(spec.RECALL.options == spec.RECALL_LEVELS and len(spec.RECALL_LEVELS) == 4,
          "spec: Claim recall has four ordered levels")
    check(spec.ordinal(spec.RECALL, spec.RECALL_NONE) == 0
          and spec.ordinal(spec.RECALL, spec.RECALL_ALL) == 3, "spec: recall order")
    description = spec.BY_KEY["DATASET_DESCRIPTION"]
    check(spec.comment_required(description, spec.IN_PART)
          and spec.comment_required(description, spec.NO)
          and not spec.comment_required(q6, spec.NO),
          "spec: only the Description comment is required")
    everything = json.dumps([dataclass_text(q) for q in spec.QUESTIONS])
    check(not re.search(r"HE-\d", everything), "spec: no HE identifier is exposed")
    check("`" not in everything, "spec: no code typography in question wording")


def dataclass_text(question):
    return [question.text, question.title, question.comment_help, question.comment_label]


# ================================================================ allocation
def test_allocation_rules():
    data = allocation.load(manifest.allocation_path())
    check(allocation.validate(data, BRAIN) == [], "allocation: the dev file is valid")
    evaluators, rows = allocation.expand(data, BRAIN)
    phases = {p: [r for r in rows if r["phase_id"] == p] for p in allocation.PHASES}
    check(len(phases["training"]) == 12 and {r["source_id"] for r in phases["training"]}
          == {"SRC-0006", "SRC-0009"}, "allocation: 2 Training papers for all six")
    check(len(phases["agreement"]) == 12 and len({r["source_id"] for r in phases["agreement"]}) == 6,
          "allocation: 6 Agreement papers, each for both members of a pair")
    check(len(phases["individual"]) == 17, "allocation: 17 Individual papers")
    per = sorted(sum(1 for r in phases["individual"] if r["evaluator_id"] == e["evaluator_id"])
                 for e in evaluators)
    check(per == [2, 3, 3, 3, 3, 3], "allocation: Individual papers as even as possible")
    pairs = {e["evaluator_id"]: e["pair_id"] for e in evaluators}
    check(pairs["thiago"] == pairs["francesca"] == "A" and pairs["giuseppe"] == "B"
          and pairs["giovanni"] == pairs["alessandro"] == "C", "allocation: the three pairs")

    def broken(mutate):
        copy = json.loads(json.dumps(data))
        mutate(copy)
        return allocation.validate(copy, BRAIN)

    check(any("Training Source" in p for p in broken(
        lambda d: d["agreement"]["AGR-A"]["sources"].append("SRC-0006"))),
        "allocation: a Training Source used elsewhere is refused")
    check(any("more than once" in p for p in broken(
        lambda d: d["individual"]["IND-1"]["sources"].append("SRC-0001"))),
        "allocation: a Source placed twice is refused")
    check(any("not placed" in p for p in broken(
        lambda d: d["individual"]["IND-6"]["sources"].pop())),
        "allocation: an unplaced Source is refused")
    check(any("not in the current Brain" in p for p in broken(
        lambda d: d["training"].append("SRC-0999"))),
        "allocation: an unknown Source is refused")
    check(any("is titled" in p for p in broken(
        lambda d: d["training"].__setitem__(0, {"source": "SRC-0006", "title": "Wrong"}))),
        "allocation: a title that does not match the Brain is refused")
    check(any("exactly two" in p for p in broken(
        lambda d: d["pairs"]["A"].append("giuseppe"))),
        "allocation: a pair must have two evaluators")
    check(any("evaluator" in p for p in broken(
        lambda d: d["individual"]["IND-1"].__setitem__("evaluator", "nobody"))),
        "allocation: an Individual split needs a listed evaluator")


# ================================================================= preflight
def test_preflight():
    report = preflight.check(BRAIN)
    check(report.ok, f"preflight: the current snapshot passes ({report.errors[:2]})")
    root = brain_copy()
    try:
        claims = root / "wiki" / "claims" / "claims.jsonl"
        rows = [json.loads(line) for line in claims.read_text().splitlines() if line]
        rows[0]["claim_object"] = "politics"
        rows[1]["concepts"] = ["CPT-does-not-exist"]
        rows[2]["datasets"] = ["DST-9999"]
        rows[3].pop("anchors")
        claims.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        edges = root / "wiki" / "graph" / "edges.jsonl"
        erows = [json.loads(line) for line in edges.read_text().splitlines() if line]
        erows[0]["grounding"] = "plausible"
        erows[1]["to"] = "CLM-9999-999"
        erows[2]["type"] = "COMPATIBLE_WITH"
        edges.write_text("\n".join(json.dumps(r) for r in erows) + "\n")
        (root / "schema" / "claim.md").write_text("changed")
        text = "\n".join(preflight.check(brain_module.load_brain_from(root)).errors)
        for fragment, label in (("claim_object 'politics'", "an invalid Claim object"),
                                ("CPT-does-not-exist does not resolve", "an unresolved Concept"),
                                ("DST-9999 does not resolve", "an unresolved Dataset"),
                                ("`anchors` is missing", "missing anchors"),
                                ("grounding 'plausible'", "an invalid grounding"),
                                ("do not resolve to Claims", "an unresolved endpoint"),
                                ("unknown type", "an obsolete relation type"),
                                ("schema/claim.md differs", "a changed schema file")):
            check(fragment in text, f"preflight: rejects {label}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ================================================================= bootstrap
def test_bootstrap():
    book = fresh_round()
    meta = store.round_metadata()
    check(meta["round_id"] == ROUND and meta["eval_spec_version"] == "4.0"
          and meta["definitions_id"] == spec.definitions_id()
          and meta["brain_snapshot_id"] == BRAIN.snapshot_id
          and meta["brain_canonical_schema_version"] == "0.1.0",
          "bootstrap: ROUND records round, instrument, definitions and snapshot")
    check("RUN-2026-09-25-01" in meta["brain_runs"],
          "bootstrap: the runs and their schema versions are recorded")
    check(book.count(sheets.DEFINITIONS) == len(spec.definitions()["entries"]),
          "bootstrap: DEFINITIONS holds every definition shown to evaluators")
    check(book.count(sheets.REVIEWS) == 41 and book.count(sheets.ASSIGNMENTS) == 41,
          "bootstrap: one review per assignment")
    check(all(r["review_id"].startswith(ROUND + "|") for r in book.read_tab(sheets.REVIEWS)),
          "bootstrap: review ids carry the round namespace")
    check(bootstrap_round.verify_blocks(book, ROUND) == [],
          "bootstrap: every recorded block reads back at its rows")
    check(set(book.tab_titles()) == set(sheets.ALL_TABS), "bootstrap: exactly the round tabs")

    sys.argv = ["bootstrap_round.py"]
    with contextlib.redirect_stdout(io.StringIO()):
        check(bootstrap_round.main() == 1, "bootstrap: refuses a workbook holding a round")
    start(rid("agreement", "thiago", "SRC-0001"))
    sys.argv = ["bootstrap_round.py", "--overwrite-round", ROUND]
    with contextlib.redirect_stdout(io.StringIO()):
        check(bootstrap_round.main() == 1,
              "bootstrap: refuses to discard started evaluations without the flag")
    sys.argv += ["--discard-evaluations"]
    with contextlib.redirect_stdout(io.StringIO()):
        check(bootstrap_round.main() == 0, "bootstrap: an explicit overwrite replaces the round")

    other = fakes.FakeWorkbook()
    other.tabs["Notes"] = [["something"]]
    store.use_workbook(other)
    sys.argv = ["bootstrap_round.py"]
    with contextlib.redirect_stdout(io.StringIO()):
        check(bootstrap_round.main() == 1, "bootstrap: refuses a workbook with other content")


# ===================================================================== store
def test_store_roundtrip_and_conflicts():
    book = fresh_round()
    review = rid("individual", "thiago", "SRC-0008")
    start(review)
    store.get_review(review)            # the page has already read REVIEWS by now
    before = dict(book.requests)
    data = store.load_review(review)
    check(book.requests["read"] - before.get("read", 0) == 1,
          "store: a paper's answers load in one read request")
    row = data.response(spec.Q1.key, "CLM-0008-001")
    stamp = store.write(sheets.RESPONSES, row["response_key"], {**row, "answer": "No"},
                        rid=review, expected_updated_at="")
    check(store.load_review(review).response(spec.Q1.key, "CLM-0008-001")["answer"] == "No",
          "store: an answer round-trips")
    try:
        store.write(sheets.RESPONSES, row["response_key"], {**row, "answer": "Yes"},
                    rid=review, expected_updated_at="an older stamp")
        check(False, "store: a stale write is refused")
    except store.SaveConflict:
        check(True, "store: a stale write is refused")
    store.write(sheets.RESPONSES, row["response_key"], {**row, "answer": "Yes"},
                rid=review, expected_updated_at="an older stamp", also_accept={stamp})
    check(True, "store: the session's own earlier stamp is not a conflict")

    key = store.selection_key(review, "CLM-0008-001", "CPT-legal-drafting")
    values = {"review_id": review, "source_id": "SRC-0008", "claim_id": "CLM-0008-001",
              "concept_id": "CPT-legal-drafting", "active": store.TRUE}
    store.upsert_selection(sheets.MISSING_CONCEPTS, key, values, rid=review)
    store.upsert_selection(sheets.MISSING_CONCEPTS, key, values, rid=review)
    check(book.count(sheets.MISSING_CONCEPTS) == 1, "store: a repeated selection is one row")
    store.upsert_selection(sheets.MISSING_CONCEPTS, key, {**values, "active": store.FALSE},
                           rid=review)
    check(store.load_review(review).active_missing("CLM-0008-001") == [],
          "store: removal deactivates the same row")
    # Two sessions appending at the same instant: duplicated key in storage.
    book.append_rows(sheets.MISSING_CONCEPTS, [{**values, "selection_key": key,
                                                "active": store.TRUE,
                                                "updated_at": "9999-01-01"}])
    loaded = store.load_review(review)
    check(len(loaded.missing) == 1 and len(loaded.active_missing("CLM-0008-001")) == 1,
          "store: duplicate keys collapse to one effective selection")
    try:
        store.write(sheets.RESPONSES, "no such key", {}, rid=review)
        check(False, "store: an unknown row is refused")
    except store.StorageIntegrityError:
        check(True, "store: an unknown row is refused")


def test_store_requires_a_workbook():
    store.use_workbook(None)
    try:
        store.workbook()
        check(False, "store: without a workbook nothing is stored")
    except sheets.StorageNotConfigured:
        check(True, "store: without a workbook nothing is stored")


# ================================================================== progress
def test_progress_rules():
    fresh_round()
    source = "SRC-0001"
    review = rid("agreement", "thiago", source)
    start(review)
    answer_everything(review, source)
    data = store.load_review(review)
    check(progress.missing_items(BRAIN, source, data) == [],
          "progress: a fully answered paper has nothing missing")
    claim = BRAIN.claims_of(source)[0]["id"]

    def with_response(key, object_id, **changes):
        copy = data.copy()
        copy.responses[store.response_lookup(key, object_id)].update(changes)
        return copy

    reasons = lambda d: [m.reason for m in progress.missing_items(BRAIN, source, d)]
    check("restated Claim not selected" in reasons(
        with_response(spec.Q1.key, claim, answer="Yes")),
        "progress: Question 1 Yes requires the restated Claim")
    check(reasons(with_response(spec.Q1.key, claim, answer="Yes",
                                related_claim_id="CLM-0001-002")) == [],
          "progress: Question 1 Yes with a selected Claim is complete")
    check(reasons(with_response("CLAIM_Q02_CENTRAL_THESIS", claim, answer="No")) == [],
          "progress: an optional comment never blocks completion")
    check(reasons(with_response("CLAIM_Q05_GROUNDING", claim, answer="In part")) == [],
          "progress: Question 5 comment is optional")
    dataset = BRAIN.dataset_ids_of(source)[0]
    check(any("comment required" in r for r in reasons(
        with_response("DATASET_DESCRIPTION", dataset, answer="No"))),
        "progress: the Description comment is required for No")
    check(any("text required" in r for r in reasons(
        with_response(spec.RECALL.key, source, answer=spec.RECALL_MOST))),
        "progress: Missing Claims is required below All")
    check(any("not evaluated" in r for r in reasons(
        with_response(spec.Q14.key, claim, answer=""))),
        "progress: Question 14 unanswered is not complete")
    check(any("not evaluated" in r for r in reasons(
        with_response(spec.Q14.key, claim, answer=spec.Q14_MISSING))),
        "progress: 'missing' with nothing selected is not complete")

    # dynamic totals: per assigned Concept, per candidate, per hosted Relation
    items = progress.claim_items(BRAIN, source, claim)
    check(sum(1 for i in items if i.question is spec.Q12)
          == len(BRAIN.concepts_of_claim(claim)), "progress: one Q12 per assigned Concept")
    check(sum(1 for i in items if i.question is spec.Q13)
          == len(BRAIN.candidates_of_claim(claim)), "progress: one Q13 per candidate only")
    check(sum(1 for i in items if i.question.unit == spec.UNIT_RELATION)
          == 2 * len(BRAIN.relations_from_claim(claim)),
          "progress: two judgments per Relation starting from this Claim")
    check(progress.dataset_items(BRAIN, "SRC-0003") == [],
          "progress: no Dataset question for a Source without Datasets")
    empty = store.ReviewData()
    check(all(i.question.unit != spec.UNIT_RELATION or
              any(r["key"] == i.object_id for r in BRAIN.relations_hosted(source))
              for i in progress.all_items(BRAIN, source, empty)),
          "progress: a Relation is evaluated only in its From Source")


def test_zero_claim_source():
    root = brain_copy()
    try:
        claims = root / "wiki" / "claims" / "claims.jsonl"
        rows = [r for r in (json.loads(l) for l in claims.read_text().splitlines() if l)
                if r["source"] != "SRC-0010"]
        claims.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        edges = root / "wiki" / "graph" / "edges.jsonl"
        kept = [e for e in (json.loads(l) for l in edges.read_text().splitlines() if l)
                if not str(e.get("from", "")).startswith("CLM-0010")
                and not str(e.get("to", "")).startswith("CLM-0010")]
        edges.write_text("\n".join(json.dumps(e) for e in kept) + "\n")
        copy = brain_module.load_brain_from(root)
        items = progress.all_items(copy, "SRC-0010", store.ReviewData())
        check([i.question.key for i in items] == [spec.RECALL.key],
              "progress: a Source with no Claims is still evaluable by Claim recall")
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ==================================================================== search
def test_concept_search():
    vocabulary = BRAIN.vocabulary(spec.concept_grid())
    results = conceptsearch.search("machine learning", vocabulary)
    check(results and results[0]["id"] == "CPT-machine-learning",
          "search: the exact name ranks first")
    check(conceptsearch.search("machine learning", vocabulary) == results,
          "search: deterministic")
    partial = conceptsearch.search("privacy xyzzy", vocabulary)
    check(any(e["id"] == "CPT-privacy-and-data-protection" for e in partial),
          "search: not every word has to match")
    check(len(conceptsearch.search("", vocabulary)) == len(vocabulary),
          "search: an empty query lists everything")


# ================================================================== analysis
def test_agreement_metrics():
    pairs = [("Yes", "Yes"), ("No", "No"), ("Yes", "No"), ("Yes", "Yes")]
    kappa = analysis.cohen_kappa(pairs, ["Yes", "No"])
    check(abs(kappa - 0.5) < 1e-9, "analysis: Cohen's kappa on a known table")
    weighted = analysis.weighted_kappa([("No", "In part"), ("Yes", "Yes"), ("No", "No")],
                                       ["No", "In part", "Yes"])
    check(weighted is not None and 0 < weighted < 1, "analysis: linear-weighted kappa")
    book = fresh_round()
    for evaluator in ("thiago", "francesca"):
        review = rid("agreement", evaluator, "SRC-0001")
        start(review)
        answer_everything(review, "SRC-0001",
                          recall=spec.RECALL_ALL if evaluator == "thiago" else spec.RECALL_MOST)
    tables = analysis.export_tables()
    metrics = {m["question_key"]: m for m in tables["agreement_metrics"]}
    check(metrics["SOURCE_CLAIM_RECALL"]["metric"] == "linear_weighted_kappa"
          and metrics["CLAIM_Q05_GROUNDING"]["metric"] == "linear_weighted_kappa"
          and metrics["CLAIM_Q02_CENTRAL_THESIS"]["metric"] == "cohen_kappa",
          "analysis: the metric follows the question's scale")
    check("CLAIM_Q14_MISSING_CONCEPTS" not in metrics and "SOURCE_MISSING_CLAIMS" not in metrics,
          "analysis: structured and qualitative responses get no invented metric")
    check(all(r["eval_spec_version"] == "4.0" and r["round_id"] == ROUND
              for r in tables["claim_judgments"]),
          "analysis: every exported judgment names its round and instrument")
    check(len(tables["raw_responses"]) == book.count(sheets.RESPONSES),
          "analysis: the raw tabs are exported whole")


# ======================================================================== UI
def _app():
    from streamlit.testing.v1 import AppTest

    return AppTest.from_file(str(APP / "streamlit_app.py"), default_timeout=120)


def _login(at, name="Thiago"):
    at.run()
    at.text_input[0].input(os.environ["HE_APP_PASSWORD"])
    at.button[0].click()
    at.run()
    at.selectbox[0].select(name)
    at.run()
    at.button[0].click()
    at.run()


def _open(at, phase, source):
    at.sidebar.radio[0].set_value(manifest.PHASE_LABEL[phase])
    at.run()
    at.button(key=f"open|{phase}|{source}").click()
    at.run()


def _markdown(at) -> str:
    return "\n".join(m.value for m in at.markdown)


def _questions(at):
    """Answer controls on the page; the sidebar phase selector is not one."""
    return [r for r in at.radio if r.label != "Phase"]


def _flush(at):
    at.session_state["_save_queue"].flush(20)


def test_ui_guards():
    store.use_workbook(None)
    at = _app()
    at.run()
    check(at.title and "not available" in at.title[0].value,
          "ui: without a round workbook the app refuses to start")
    book = fresh_round()
    rows = book.tabs[sheets.ROUND]
    for row in rows:
        if row[0] == "round_id":
            row[1] = "ROUND-OTHER"
    store.forget_all()
    at = _app()
    at.run()
    check(at.title and "does not belong" in at.title[0].value,
          "ui: a workbook of another round is refused")


def test_ui_claim_flow():
    book = fresh_round()
    at = _app()
    _login(at)
    _open(at, "agreement", "SRC-0001")
    at.checkbox[0].check()
    at.run()
    [b for b in at.button if b.label == "Start evaluation"][0].click()
    at.run()
    page = _markdown(at)
    check("In tension with" not in page and "Attacked by" in page,
          "ui: the Source wiki shows current relation terminology")
    check(not _questions(at), "ui: the Source page asks nothing")
    at.button(key="nav|claims").click()
    at.run()
    check(not at.exception, f"ui: the Claim page renders ({[e.value for e in at.exception][:1]})")
    page = _markdown(at)
    check("<code>" not in page and "`" not in page,
          "ui: no schema name or value in code typography")
    check("Claim object" in page and "Law" in page and "Technology" in page,
          "ui: Claim object shows every category")
    check("Premise" not in page and "Positive form" not in page
          and "Plausibility" not in page and "Compatible with" not in page,
          "ui: removed fields and relation labels are absent")
    check("one per claim" in page, "ui: Question 2 shows the Statement definition")
    check("(this Claim)" in page and "From Claim" in page, "ui: Relation direction is shown")

    first = BRAIN.claims_of("SRC-0001")[0]["id"]
    base = f"w|{rid('agreement', 'thiago', 'SRC-0001')}"
    at.radio(key=f"{base}|{spec.Q1.key}|{first}|a").set_value("Yes")
    at.run()
    check(any(s.label == "Restatement of" for s in at.selectbox),
          "ui: Question 1 Yes asks which Claim is restated")

    # Question 14: search, add, clear search, add another; both persist.
    search_key = f"q14search|{rid('agreement', 'thiago', 'SRC-0001')}|{first}"
    at.text_input(key=search_key).input("machine learning")
    at.run()
    at.button(key=f"{base}|q14add|{first}|CPT-machine-learning").click()
    at.run()
    at.text_input(key=search_key).input("")
    at.run()
    at.text_input(key=search_key).input("privacy")
    at.run()
    at.button(key=f"{base}|q14add|{first}|CPT-privacy-and-data-protection").click()
    at.run()
    at.text_input(key=search_key).input("")
    at.run()
    labels = [b.label for b in at.button]
    check("Machine learning  ×" in labels and "Privacy and data protection  ×" in labels,
          "ui: selections persist when the search changes")
    check(f"{base}|q14add|{first}|CPT-machine-learning" not in [b.key for b in at.button],
          "ui: a selected Concept is no longer offered")
    at.button(key=f"{base}|q14rm|{first}|CPT-machine-learning").click()
    at.run()
    check("Machine learning  ×" not in [b.label for b in at.button],
          "ui: × removes a selected Concept")
    at.text_input(key=f"{base}|q14name|{first}").input("Legal chatbots")
    at.selectbox(key=f"{base}|q14family|{first}").select("technical_task")
    at.run()
    at.button(key=f"{base}|q14propose|{first}").click()
    at.run()
    check(any(label.startswith("Proposed · Legal chatbots") for label in
              [b.label for b in at.button]), "ui: a proposed Concept appears as selected")
    _flush(at)
    stored = store.load_review(rid("agreement", "thiago", "SRC-0001"))
    check(stored.response(spec.Q14.key, first)["answer"] == spec.Q14_MISSING
          and [r["concept_id"] for r in stored.active_missing(first)]
          == ["CPT-privacy-and-data-protection"]
          and [r["name"] for r in stored.active_proposals(first)] == ["Legal chatbots"],
          "ui: Question 14 is stored as state, selections and proposals")
    check(not any(r["concept_id"] == "CPT-legal-chatbots" for r in
                  stored.missing.values()) and "CPT-legal-chatbots" not in BRAIN.concepts,
          "ui: a proposal creates no Brain Concept")
    check(book.count(sheets.MISSING_CONCEPTS) == 2,
          "ui: selecting and removing keeps one row per Concept")


def test_ui_no_datasets_and_completion():
    fresh_round()
    source = "SRC-0010"
    review = rid("individual", "thiago", source)
    start(review)
    answer_everything(review, source)
    at = _app()
    _login(at)
    _open(at, "individual", source)
    at.button(key="nav|datasets").click()
    at.run()
    check(not _questions(at) and any("No Claim of this Source rests on a Dataset" in i.value
                               for i in at.info),
          "ui: no Dataset questions when the Source has no Dataset")
    at.button(key="nav|recall").click()
    at.run()
    check(not at.exception, "ui: Claim recall renders")
    at.button(key="nav|review").click()
    at.run()
    check(any("Every applicable item is answered" in s.value for s in at.success),
          "ui: Review reports a complete paper")
    page = _markdown(at)
    check("CITES" not in page and "Source attributes" not in page,
          "ui: Review holds only current evaluation items")
    [b for b in at.button if b.label == "Mark paper complete"][0].click()
    at.run()
    check(store.get_review(review)["status"] == store.STATUS_COMPLETE,
          "ui: a complete paper can be marked complete after a fresh re-read")


def test_ui_preflight_failure():
    fresh_round()
    root = brain_copy()
    try:
        claims = root / "wiki" / "claims" / "claims.jsonl"
        rows = [json.loads(line) for line in claims.read_text().splitlines() if line]
        rows[0]["concepts"] = ["CPT-nowhere"]
        claims.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        os.environ["HE_BRAIN_DIR"] = str(root)
        import streamlit as st
        st.cache_resource.clear()
        at = _app()
        at.run()
        check(at.title and at.title[0].value == "The evaluation is not available",
              "ui: an incompatible snapshot is rejected before evaluation begins")
        check(not at.text_input or at.text_input[0].label == "Admin secret",
              "ui: evaluators cannot sign in against an incompatible snapshot")
    finally:
        os.environ.pop("HE_BRAIN_DIR", None)
        import streamlit as st
        st.cache_resource.clear()
        shutil.rmtree(root, ignore_errors=True)


def test_ui_datasets_and_concepts():
    fresh_round()
    source = "SRC-0001"
    review = rid("agreement", "thiago", source)
    start(review)
    at = _app()
    _login(at)
    _open(at, "agreement", source)
    base = f"w|{review}"
    claim = BRAIN.claims_of(source)[0]["id"]
    at.button(key="nav|claims").click()
    at.run()
    first, second = BRAIN.concepts_of_claim(claim)[:2]
    at.radio(key=f"{base}|{spec.Q12.key}|{claim}|{first}|a").set_value("No")
    at.run()
    check(at.radio(key=f"{base}|{spec.Q12.key}|{claim}|{second}|a").value is None,
          "ui: each Concept judgment is independent")
    check(any(t.label.startswith("Comment") for t in at.text_area),
          "ui: a compact comment appears under a Concept answered No")

    at.button(key="nav|datasets").click()
    at.run()
    dataset = BRAIN.dataset_ids_of(source)[0]
    description = f"{base}|DATASET_DESCRIPTION|{dataset}|a"
    at.radio(key=description).set_value("In part")
    at.run()
    check(any("A comment is required" in w.value for w in at.warning),
          "ui: Description In part asks for the required comment")
    check(any("describe what is missing or incorrect" in c.value for c in at.caption),
          "ui: the Description comment carries the agreed instruction")
    page = _markdown(at)
    check("Document type" not in page and "Agreement reported" not in page
          and "Used by" not in page, "ui: removed Dataset fields are absent")
    check("<code>" not in page and "`" not in page,
          "ui: no code typography on the Dataset page")
    at.button(key=f"ds_wiki|{dataset}").click()
    at.run()
    check(at.session_state["wiki_stack"] == [("dataset", dataset)],
          "ui: the Dataset wiki opens in the modal")
    at.session_state["wiki_stack"] = []
    at.run()
    check(at.radio(key=description).value == "In part",
          "ui: closing the modal keeps the Dataset answers")
    _flush(at)
    check(store.load_review(review).response("DATASET_DESCRIPTION", dataset)["answer"]
          == "In part", "ui: the Dataset answer is stored")


def test_ui_submission_locks():
    fresh_round()
    for source in manifest.assigned_source_ids("thiago", "training"):
        review = rid("training", "thiago", source)
        start(review)
        answer_everything(review, source)
        store.mark_complete(review)
    at = _app()
    _login(at)
    at.sidebar.radio[0].set_value("Training")
    at.run()
    at.checkbox(key="confirm_batch|training").check()
    at.run()
    [b for b in at.button if b.label == "Submit all papers"][0].click()
    at.run()
    check(store.phase_submitted(ROUND, "training", "thiago"),
          "ui: a complete phase can be finally submitted")
    check(all(store.get_review(rid("training", "thiago", s))["status"] == "submitted"
              for s in ("SRC-0006", "SRC-0009")), "ui: submission locks every paper")
    _open(at, "training", "SRC-0006")
    at.button(key="nav|claims").click()
    at.run()
    check(all(r.disabled for r in _questions(at)), "ui: a submitted paper is read-only")


# ====================================================================== main
def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    tests = [(name, fn) for name, fn in globals().items()
             if name.startswith("test_") and callable(fn) and only in name]
    for name, fn in tests:
        print(name)
        try:
            fn()
        except Exception:
            FAILURES.append(f"{name} raised")
            traceback.print_exc()
    print(f"\n{CHECKS} checks, {len(FAILURES)} failed")
    for failure in FAILURES:
        print(f"  - {failure}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
