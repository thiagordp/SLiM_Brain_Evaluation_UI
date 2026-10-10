"""Extract the Training-phase answers and agreement statistics into one JSON file.

Read-only: reads the round workbook through the application's own storage and
progress functions, and the Brain snapshot for Claims, anchors, Concepts and
relations. Nothing is written to the workbook.

    python app/tools/training_report/extract.py OUT.json

Uses the configured workbook (GOOGLE_SHEET_ID and the service account).
The report is rendered from OUT.json by build_report.js (see README.md).
"""
from __future__ import annotations

import collections
import datetime as dt
import itertools
import json
import pathlib
import sys

APP = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(APP))

import analysis  # noqa: E402
import coefficients  # noqa: E402
import progress  # noqa: E402
import spec  # noqa: E402
import store  # noqa: E402
from brain import concept_label, family_label, load_brain  # noqa: E402

PAPERS = ("SRC-0006", "SRC-0009")
PHASE = "training"
SET_VALUED = ("CLAIM_Q14_MISSING_CONCEPTS", "SOURCE_MISSING_CLAIMS", "SOURCE_RESTATEMENTS")
SECTION = {spec.PART_CLAIM: "Claim evaluation", spec.PART_FIELDS: "Schema fields",
           spec.PART_CONCEPTS: "Concepts", spec.PART_RELATIONS: "Relations",
           spec.PART_DATASET: "Dataset", spec.PART_RECALL: "Source-level"}
SHOWN = {"none": "No", "present": "Yes"}


def split_label(counts: collections.Counter) -> tuple[str, int]:
    """('4–3', minority) etc.; minority = number of answers outside the largest group."""
    values = sorted(counts.values(), reverse=True)
    return "–".join(str(v) for v in values), sum(values) - values[0]


def main() -> int:
    out_path = pathlib.Path(sys.argv[1])
    brain = load_brain()
    raw = analysis.read_raw()
    raters = [e["evaluator_id"] for e in raw["EVALUATORS"]]
    name = {e["evaluator_id"]: e["name"] for e in raw["EVALUATORS"]}
    status = {(r["source_id"], r["evaluator_id"]): r["status"] for r in raw["REVIEWS"]
              if r["phase_id"] == PHASE}
    out = {"snapshot": dt.datetime.now(dt.timezone(dt.timedelta(hours=2))).strftime("%Y-%m-%d %H:%M CEST"),
           "raters": [name[r] for r in raters], "papers": {}}

    for source in PAPERS:
        reviews = {r["evaluator_id"]: r for r in raw["REVIEWS"]
                   if r["source_id"] == source and r["phase_id"] == PHASE}
        data = {e: store.review_data(reviews[e]["review_id"], raw) for e in raters}
        claims = brain.claims_of(source)
        every = progress.all_items(brain, source, store.ReviewData(), everything=True)

        # ---- structure
        relations = [r for c in claims for r in brain.relations_from_claim(c["id"])]
        counts = {
            "claims": len(claims),
            "assigned_concepts": sum(len(brain.concepts_of_claim(c["id"])) for c in claims),
            "candidate_concepts": sum(len(brain.candidates_of_claim(c["id"])) for c in claims),
            "relations": dict(collections.Counter(r["type"] for r in relations)),
            "datasets": len(brain.dataset_ids_of(source)),
            "status": {name[e]: status.get((source, e), "") for e in raters},
        }

        # ---- single-label items
        items, missing, not_asked = [], 0, 0
        for item in every:
            q = item.question
            if q.key in SET_VALUED or q.free_text:
                continue
            answers = {name[e]: progress.answer_of(item, data[e]) for e in raters}
            comments = {name[e]: progress.comment_of(item, data[e]).strip() for e in raters}
            missing += sum(1 for v in answers.values() if not v)
            obj = {"kind": q.unit}
            if q.unit == spec.UNIT_CLAIM and q.field:
                obj["assigned"] = brain.claim(item.claim_id).get(q.field)
            elif q.unit in (spec.UNIT_CLAIM_CONCEPT, spec.UNIT_CLAIM_CANDIDATE):
                c = brain.concept(item.object_id)
                obj.update(concept_id=item.object_id, concept=concept_label(item.object_id),
                           family=family_label(c.get("concept_type", "")), status=c.get("status", ""))
            elif q.unit == spec.UNIT_RELATION:
                rel = next(r for r in brain.relations_from_claim(item.claim_id) if r["key"] == item.object_id)
                obj.update(type=rel["type"], source=rel["from"], target=rel["to"],
                           grounding=rel.get("grounding", ""), note=rel.get("note", ""),
                           target_statement=brain.claim(rel["to"]).get("statement", ""),
                           target_source=rel.get("to_source", ""))
            elif q.unit == spec.UNIT_DATASET:
                obj.update(dataset=item.object_id, assigned=brain.dataset(item.object_id).get(q.field) if q.field else None)
            given = collections.Counter(v for v in answers.values() if v)
            split, minority = split_label(given)
            items.append({
                "key": q.key, "title": q.title, "text": q.text, "section": SECTION[q.part],
                "claim": item.claim_id or "", "object_id": item.object_id, "object": obj,
                "answers": answers, "comments": {k: v for k, v in comments.items() if v},
                "flags": {k: spec.problem(q, v) for k, v in answers.items() if v},
                "distribution": dict(given.most_common()), "split": split, "minority": minority,
                "values": len(given), "unanimous": len(given) == 1,
            })
        # structurally not asked: Direction on SAME_AS
        not_asked += sum(1 for r in relations if not spec.DIRECTION.applies_to(r)) * len(raters)

        # ---- pairwise agreement
        pairs = []
        for a, b in itertools.combinations([name[e] for e in raters], 2):
            p = [(i["answers"][a], i["answers"][b]) for i in items if i["answers"][a] and i["answers"][b]]
            pairs.append({"a": a, "b": b, "n": len(p), "agree": sum(x == y for x, y in p),
                          "pct": round(100 * sum(x == y for x, y in p) / len(p), 1),
                          "both_yes_share": round(sum(1 for x, y in p if x == y and x in (spec.YES,)) /
                                                  max(1, sum(x == y for x, y in p)), 3)})

        # ---- per question unanimity
        per_q = []
        for q in spec.QUESTIONS:
            qi = [i for i in items if i["key"] == q.key]
            if qi:
                per_q.append({"key": q.key, "title": q.title, "section": SECTION[q.part], "n": len(qi),
                              "unanimous": sum(i["unanimous"] for i in qi),
                              "flags": {r: sum(1 for i in qi if i["flags"].get(r)) for r in out["raters"]}})

        # ---- chance-corrected, defect vs ok
        bin_units = [[i["flags"][r] for r in out["raters"] if r in i["flags"]] for i in items]
        pa, na = coefficients.specific_agreement(bin_units)
        alpha = coefficients.alpha([["d" if f else "o" for f in u] for u in bin_units])

        # ---- set-valued and Source-level answers
        q14 = {}
        for c in claims:
            q14[c["id"]] = {name[e]: {
                "state": data[e].response(spec.Q14.key, c["id"]).get("answer", ""),
                "selected": [{"id": r["concept_id"], "name": concept_label(r["concept_id"]),
                              "family": family_label(r.get("concept_family", ""))}
                             for r in data[e].active_missing(c["id"])],
                "proposed": [{"name": r["name"], "family": family_label(r.get("family", "")),
                              "explanation": r.get("explanation", "")}
                             for r in data[e].active_proposals(c["id"])]} for e in raters}
        source_level = {name[e]: {
            "recall": data[e].response(spec.RECALL.key, source).get("answer", ""),
            "missing_claims": data[e].response(spec.MISSING_CLAIMS.key, source).get("answer", ""),
            "restatements": SHOWN.get(data[e].response(spec.RESTATEMENTS.key, source).get("answer", ""), ""),
            "groups": sorted(data[e].active_restatement_groups().values()),
        } for e in raters}
        for r in source_level.values():
            if r["recall"] == spec.RECALL_ALL:
                not_asked += 1                              # Missing Claims not shown

        out["papers"][source] = {
            "counts": counts, "items": items, "pairs": pairs, "per_question": per_q,
            "missing_answers": missing, "not_asked": not_asked,
            "alpha_defect": alpha, "pos_agreement": pa, "neg_agreement": na,
            "q14": q14, "source_level": source_level,
            "claims": [{"id": c["id"], "statement": c.get("statement", ""),
                        "anchors": [{"quote": a.get("quote", ""), "location": a.get("location", "")}
                                    for a in (c.get("anchors") or [])],
                        "fields": {f: c.get(f) for f in ("claim_object", "claim_type", "basis",
                                                         "claim_jurisdiction", "legal_reference",
                                                         "temporal_reference")}} for c in claims],
        }

    out["coefficients"] = coefficients.compute(out)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for s, p in out["papers"].items():
        print(s, len(p["items"]), "items,", sum(1 for i in p["items"] if not i["unanimous"]), "contested,",
              "missing", p["missing_answers"], "not asked", p["not_asked"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
