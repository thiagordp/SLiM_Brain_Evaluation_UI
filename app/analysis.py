"""Exports and inter-evaluator agreement, computed from the raw stored rows.

Storage is never reinterpreted: the raw tabs are exported as they are, and the
normalised tables below only join them with review provenance and spell out the
question each row answers.

Agreement is computed only where a metric is well defined for the unit:

    binary correctness items      observed agreement, Cohen's kappa
    ordered ternary items         observed agreement, linear-weighted kappa
      (Q5, Dataset Description)
    Claim recall (None…All)       observed agreement, linear-weighted kappa

Question 14 sets, proposed Concepts, Question 1's restated-Claim targets and
Missing Claims are exported raw; no comparison metric is invented for them.
The restatement answer itself (Yes/No) is binary and is compared as such.
"""
from __future__ import annotations

import collections

import sheets
import spec
import store

REVIEW_COLUMNS = ("round_id", "eval_spec_version", "definitions_id",
                  "brain_snapshot_id", "phase_id", "evaluator_id", "pair_id",
                  "split_id", "source_id", "status")


def _raw() -> dict[str, list[dict]]:
    book = store.workbook()
    return dict(zip(sheets.ALL_TABS, book.read_ranges(
        [(tab, None, None) for tab in sheets.ALL_TABS])))


def _with_review(row: dict, reviews: dict, round_meta: dict) -> dict:
    review = reviews.get(row.get("review_id"), {})
    out = {name: review.get(name, "") for name in REVIEW_COLUMNS}
    # A review nobody started has no recorded instrument; the round's applies.
    for name in ("round_id", "eval_spec_version", "definitions_id", "brain_snapshot_id"):
        out[name] = out[name] or round_meta.get(name, "")
    return {**out, **row}


def normalised(raw: dict[str, list[dict]]) -> dict[str, list[dict]]:
    reviews = {r["review_id"]: r for r in raw[sheets.REVIEWS]}
    meta = {r["key"]: r["value"] for r in raw[sheets.ROUND]}

    def question_columns(question: spec.Question, answer: str) -> dict:
        return {"question": question.title, "question_text": question.text,
                "semantics": question.semantics,
                "flags_problem": spec.problem(question, answer) if answer else ""}

    claim_rows, dataset_rows, recall_rows, q14_state = [], [], [], []
    for row in raw[sheets.RESPONSES]:
        question = spec.BY_KEY.get(row["question_key"])
        if question is None:
            continue
        full = {**_with_review(row, reviews, meta),
                **question_columns(question, row.get("answer", ""))}
        if question is spec.Q14:
            q14_state.append(full)
        elif question.unit == spec.UNIT_CLAIM:
            claim_rows.append(full)
        elif question.unit == spec.UNIT_DATASET:
            dataset_rows.append(full)
        else:
            recall_rows.append(full)

    concept_rows = []
    for row in raw[sheets.CONCEPT_RESPONSES]:
        question = spec.BY_KEY[row["question_key"]]
        concept_rows.append({**_with_review(row, reviews, meta),
                             **question_columns(question, row.get("answer", ""))})

    relation_rows = []
    for row in raw[sheets.RELATION_RESPONSES]:
        for question in spec.relation_questions():
            answer = row.get(f"{question.column}_answer", "")
            relation_rows.append({
                **_with_review({k: v for k, v in row.items()
                                if not k.startswith(("grounding_", "type_"))},
                               reviews, meta),
                **question_columns(question, answer),
                "answer": answer, "comment": row.get(f"{question.column}_comment", "")})

    missing = [_with_review(r, reviews, meta) for r in
               store.effective(raw[sheets.MISSING_CONCEPTS], "selection_key").values()]
    proposed = [_with_review(r, reviews, meta) for r in
                store.effective(raw[sheets.PROPOSED_CONCEPTS], "proposal_key").values()]
    return {
        "claim_judgments": claim_rows,
        "concept_judgments": concept_rows,
        "missing_concepts_state": q14_state,
        "missing_concepts": missing,
        "proposed_concepts": proposed,
        "relation_judgments": relation_rows,
        "dataset_judgments": dataset_rows,
        "claim_recall": recall_rows,
    }


# -------------------------------------------------------------- agreement
def cohen_kappa(pairs: list[tuple[str, str]], categories) -> float | None:
    """Unweighted Cohen's kappa. None where it is undefined (no variation)."""
    return weighted_kappa(pairs, categories, weighted=False)


def weighted_kappa(pairs: list[tuple[str, str]], categories,
                   weighted: bool = True) -> float | None:
    """Cohen's kappa; with ``weighted``, linear weights over the given order."""
    categories = list(categories)
    k = len(categories)
    n = len(pairs)
    if not n or k < 2:
        return None
    index = {c: i for i, c in enumerate(categories)}

    def weight(i: int, j: int) -> float:
        if not weighted:
            return 1.0 if i == j else 0.0
        return 1.0 - abs(i - j) / (k - 1)

    joint = collections.Counter((index[a], index[b]) for a, b in pairs)
    left = collections.Counter(index[a] for a, _ in pairs)
    right = collections.Counter(index[b] for _, b in pairs)
    observed = sum(weight(i, j) * c for (i, j), c in joint.items()) / n
    expected = sum(weight(i, j) * left[i] * right[j]
                   for i in range(k) for j in range(k)) / (n * n)
    if expected >= 1.0:
        return None
    return (observed - expected) / (1.0 - expected)


def _metric_for(question: spec.Question):
    if question.semantics in (spec.CORRECTNESS_BINARY, spec.RESTATEMENT_FLAG):
        return "cohen_kappa", list(question.options), False
    if question.semantics == spec.CORRECTNESS_TERNARY:
        return "linear_weighted_kappa", [spec.NO, spec.IN_PART, spec.YES], True
    if question.semantics == spec.ORDINAL4:
        return "linear_weighted_kappa", list(spec.RECALL_LEVELS), True
    return None, None, None


def agreement(raw: dict[str, list[dict]]) -> tuple[list[dict], list[dict]]:
    """(paired units, per-question metrics) for the agreement phase."""
    reviews = {r["review_id"]: r for r in raw[sheets.REVIEWS]
               if r.get("phase_id") == "agreement"}
    units: dict[tuple, dict[str, str]] = collections.defaultdict(dict)

    def add(review_id: str, question_key: str, unit_id: str, answer: str):
        review = reviews.get(review_id)
        if review is None or not answer:
            return
        units[(review["pair_id"], review["source_id"], question_key, unit_id)][
            review["evaluator_id"]] = answer

    for row in raw[sheets.RESPONSES]:
        question = spec.BY_KEY.get(row["question_key"])
        if question and _metric_for(question)[0]:
            add(row["review_id"], question.key, row["object_id"], row.get("answer", ""))
    for row in raw[sheets.CONCEPT_RESPONSES]:
        add(row["review_id"], row["question_key"],
            f"{row['claim_id']}|{row['concept_id']}", row.get("answer", ""))
    for row in raw[sheets.RELATION_RESPONSES]:
        for question in spec.relation_questions():
            add(row["review_id"], question.key, row["relation_key"],
                row.get(f"{question.column}_answer", ""))

    paired, by_question = [], collections.defaultdict(list)
    for (pair_id, source_id, question_key, unit_id), answers in sorted(units.items()):
        if len(answers) != 2:
            continue
        (ev_a, ans_a), (ev_b, ans_b) = sorted(answers.items())
        paired.append({"pair_id": pair_id, "source_id": source_id,
                       "question_key": question_key,
                       "question": spec.BY_KEY[question_key].title,
                       "unit_id": unit_id, "evaluator_a": ev_a, "answer_a": ans_a,
                       "evaluator_b": ev_b, "answer_b": ans_b,
                       "agree": ans_a == ans_b})
        by_question[question_key].append((ans_a, ans_b))

    metrics = []
    for question_key, pairs in sorted(by_question.items()):
        question = spec.BY_KEY[question_key]
        name, categories, weighted = _metric_for(question)
        pairs = [(a, b) for a, b in pairs if a in categories and b in categories]
        if not pairs:
            continue
        value = weighted_kappa(pairs, categories, weighted=weighted)
        metrics.append({
            "question_key": question_key, "question": question.title,
            "semantics": question.semantics, "units": len(pairs),
            "observed_agreement": round(sum(a == b for a, b in pairs) / len(pairs), 4),
            "metric": name, "value": "" if value is None else round(value, 4),
        })
    return paired, metrics


def export_tables() -> dict[str, list[dict]]:
    """Everything the administrator downloads: raw tabs, normalised, agreement."""
    raw = _raw()
    tables = {f"raw_{tab.lower()}": rows for tab, rows in raw.items()}
    tables.update(normalised(raw))
    paired, metrics = agreement(raw)
    tables["agreement_pairs"] = paired
    tables["agreement_metrics"] = metrics
    return tables

