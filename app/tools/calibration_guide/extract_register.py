"""Build the normalised calibration decision register from the annotated Training report.

    python app/tools/calibration_guide/extract_register.py OUT_DIR

Reads (never writes) Calibration/TRAINING_AGREEMENT_REPORT.docx and
Calibration/CALIBRATION_DECISIONS_SUMMARY.docx. Writes OUT_DIR/register.json,
which holds evaluators' answers and comments verbatim; keep it out of the
repository (see training_report/README.md). The CSV registers are written by
``write_csv`` into Calibration/.

What the register adds to the report's Appendix B
-------------------------------------------------
* Each Final is kept verbatim and normalised into a category (CONFIRMED,
  REPLACEMENT, UNRESOLVED, NOT_APPLICABLE, EMPTY, SET_VALUED, PAPER_LEVEL).
  A replacement value (``Other`` for an assigned ``law``) is separated from
  the evaluation of the assigned value (No).
* Item status (AGREED / PROVISIONAL / OPEN) follows the rules in
  ``policies.STATUS_RULES``: a Final is a proposal unless a meeting recorded the
  case outcome; ``??``, ``No?``, "To be discussed", a truncated or
  self-contradicting Final, and a Final cell marked yellow are OPEN.
* The 4.1 gating is applied when answers are read, as the application does
  (app/spec.py GATES): an evaluator whose own Q02 or Relation type answer is No
  has no applicable answer for the gated questions. Those stored answers are
  shown, but never compared with a Final.
* ``differs`` is computed only against a CONFIRMED or REPLACEMENT Final of an
  item that is not OPEN.
"""
from __future__ import annotations

import collections
import csv
import json
import pathlib
import re
import sys
import zipfile

from lxml import etree

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

from policies import policies_for  # noqa: E402
from report_docx import EVALUATORS, W, _text, read_report, squash  # noqa: E402

REP = ROOT / "Calibration" / "TRAINING_AGREEMENT_REPORT.docx"
SUM = ROOT / "Calibration" / "CALIBRATION_DECISIONS_SUMMARY.docx"
CONCEPT_DIR = ROOT.parent / "SLiM_Brain" / "wiki" / "concepts"

QID = {
    "Central thesis or hypothesis": "Q02", "Strength and modality": "Q03",
    "Understood on its own": "Q04", "Textual grounding": "Q05", "Claim object": "Q06",
    "Claim type": "Q07", "Basis": "Q08", "Claim jurisdiction": "Q09",
    "Legal reference": "Q10", "Temporal reference": "Q11", "Concept assignment": "Q12",
    "Candidate Concept necessary": "Q13", "Missing Concepts (Q14)": "Q14",
    "Relation type": "REL_TYPE", "Grounding": "REL_GROUNDING", "Direction": "REL_DIRECTION",
    "Claim recall": "RECALL", "Restatements": "RESTATEMENTS", "Missing Claims (text)": "MISSING_CLAIMS",
}
CLAIM_GATED = {"Q03", "Q04", "Q05", "Q06", "Q07", "Q08", "Q09", "Q10", "Q11"}   # app/spec.py:409-416
RELATION_GATED = {"REL_GROUNDING", "REL_DIRECTION"}                             # app/spec.py:415
FIELD_VALUES = {
    "Q06": ["law", "technology", "other"],
    "Q07": ["descriptive", "interpretative", "prescriptive", "predictive"],
    "Q08": ["factual", "legal", "literature", "abstract"],
}
ANSWERS = {"yes": "Yes", "no": "No", "in part": "In part"}

# ---------------------------------------------------------------- hand-checked cases
# Keyed by (claim, question, assigned). Each entry records why the generic rules
# are overridden; nothing here changes a Final's verbatim text.
FINAL_OVERRIDES = {
    ("CLM-0009-004", "Relation type", "SUPPORTS → CLM-0016-004 (inferred)"): dict(
        category="UNRESOLVED", value="No", flags=["TRUNCATED"],
        reason="The Final text breaks off mid-word (“No. Considering our rea”); its justification cannot be read."),
    ("CLM-0009-006", "Direction", "ATTACKS → CLM-0008-009 (inferred)"): dict(
        category="UNRESOLVED", value=None, flags=["CONTRADICTION"],
        reason="The Final reads “N/A”, but the reviewer comment on the same cell says “This should also be ‘no’”. "
               "Under the implemented gating, Direction is not asked once Relation type is No."),
}
# Case outcomes that a meeting recorded explicitly (two or more participants).
AGREED_CASES = {
    ("CLM-0006-001", "Candidate Concept necessary", "Pseudolaw"):
        "M07 9:10–10:02: Alessandro withdraws his No (“then I agree that, yes, that it was necessary”).",
    ("CLM-0006-001", "Missing Concepts (Q14)", "selected / proposed"):
        "M07 20:45–23:22: Legal literacy agreed as missing (Vaclav, Francesca); legal argumentation judged tangential.",
    ("CLM-0006-002", "Direction", "SUPPORTS → CLM-0024-014 (inferred)"):
        "M07 24:22 (Francesca: “it's clearly the opposite … we also agreed when we did it all together”), referring to M28 1:54:52.",
    ("CLM-0006-015", "Textual grounding", ""):
        "M07 54:23–1:00:04: ‘true law’ is quoted in the Claim but in no anchor; Vaclav and Francesca settle on In part.",
}


def concept_vocabulary() -> list[str]:
    """Concept display names, derived from the ids as app/brain.py does."""
    sys.path.insert(0, str(ROOT / "app"))
    from brain import concept_label  # noqa: E402
    names = {concept_label(p.stem) for p in CONCEPT_DIR.glob("CPT-*.md")}
    return sorted(names, key=len, reverse=True)


def split_concepts(cell: str, vocab: list[str]) -> tuple[list[str], bool]:
    """Split a Q14 cell whose line breaks were lost, by longest known label.

    The report generator joined Concepts with a newline inside one run, which
    renders as a space. Returns the parts and whether the split is exact.
    """
    text = cell.strip()
    if text.lower() in ("none", ""):
        return [], True
    if text.startswith("NEW: "):
        return [text], True
    parts, rest = [], text
    while rest:
        for v in vocab:
            if rest.lower().startswith(v.lower()) and (len(rest) == len(v) or rest[len(v)] == " "):
                parts.append(rest[: len(v)])
                rest = rest[len(v):].lstrip()
                break
        else:
            parts.append(rest)
            return parts, False
    return parts, True


def norm_answer(a: str) -> str:
    return ANSWERS.get(a.strip().lower(), a.strip())


def parse_final(row: dict) -> dict:
    """Normalise one Final. The verbatim text is kept by the caller."""
    q, f = row["qid"], row["final"].strip()
    key = (row["id"], row["question"], row["assigned"])
    if key in FINAL_OVERRIDES:
        o = FINAL_OVERRIDES[key]
        return dict(category=o["category"], value=o["value"], replacement=None, note="", flags=list(o["flags"]), reason=o["reason"])
    out = dict(category=None, value=None, replacement=None, note="", flags=[], reason="")
    if row["paper_level"]:
        out["category"] = "PAPER_LEVEL"
        return out
    if q == "Q14":
        out["category"] = "SET_VALUED"
        return out
    if not f:
        out.update(category="EMPTY", reason="No Final was entered.")
        return out
    low = f.lower()
    if "??" in f or re.match(r"^\s*(yes|no|in part)\?", low) or "to be discussed" in low:
        m = re.match(r"^\s*(yes|no|in part)\?", low)
        out.update(category="UNRESOLVED", value=ANSWERS[m.group(1)] if m else None, flags=["TENTATIVE"],
                   reason="Marked as uncertain in the Final (“??”, “No?” or “To be discussed”).")
        return out
    if re.match(r"^n/?a\b", low):
        out["category"] = "NOT_APPLICABLE"
        out["reason"] = "Relation type judged No in the Final, so Direction is not asked (gating)."
        return out
    m = re.match(r"^(yes|no|in part)\b[.,]?\s*(.*)$", f, re.I | re.S)
    if m:
        out["category"], out["value"] = "CONFIRMED", ANSWERS[m.group(1).lower()]
        rest = m.group(2).strip()
        if m.group(1) != out["value"] and m.group(1).lower() == out["value"].lower():
            out["flags"].append("CASE_NORMALISED")
        values = FIELD_VALUES.get(q, [])
        first = re.match(r"^([A-Za-z]+)", rest)
        if out["value"] == "No" and first and first.group(1).lower() in values:
            out["replacement"] = first.group(1).lower()
            out["category"] = "REPLACEMENT"
        out["note"] = rest
        return out
    if f.lower().strip(". ") in FIELD_VALUES.get(q, []):
        out.update(category="REPLACEMENT", value="No", replacement=f.lower().strip(". "),
                   reason="The Final gives a replacement value; the evaluation of the assigned value is therefore No.")
        return out
    out.update(category="UNRESOLVED", flags=["UNPARSED"], reason="The Final is not a recognisable answer.")
    return out


def q14_disposition(final: str, concept: str, claim: str) -> tuple[str, str]:
    """(disposition, basis) for one proposed Missing Concept. 'Reasonable' is never 'adopted'."""
    f = final.strip().lower()
    if claim == "CLM-0006-001":
        if "literacy" in concept.lower():
            return "AGREED_MISSING", "Final “Legal Literatcy”; agreed at M07 23:03–23:22."
        return "NOT_ADOPTED", "Judged tangential (M07 20:45–20:55; reviewer comment 7 Oct)."
    if claim == "CLM-0006-019":
        return "NOT_ADOPTED_OPEN_POLICY", "Final “None”, with a proposed policy to separate Administration from Access to justice (marked yellow)."
    if f.startswith("none") or f == "":
        return "NOT_ADOPTED", "Final “%s”." % final.strip()
    if "bert" in concept.lower() and "instead of bert" in f:
        return "REASONABLE_WITH_CHANGE", "Final: “They are reasonable. However, transformers would suffice instead of BERT.”"
    if "reasonable" in f or "acceptable" in f:
        return "CONSIDERED_REASONABLE", "Final “%s” (necessity not assessed)." % final.strip()
    return "UNCLEAR", "Final “%s”." % final.strip()


def split_label(answers: list[str]) -> str:
    c = collections.Counter(a for a in answers if a)
    order = {"Yes": 0, "In part": 1, "No": 2}
    return " / ".join(f"{k} {n}" for k, n in sorted(c.items(), key=lambda kv: (-kv[1], order.get(kv[0], 9), kv[0])))


def read_summary_appendix() -> list[dict]:
    z = zipfile.ZipFile(SUM)
    doc = etree.fromstring(z.read("word/document.xml"))
    for t in doc.iter(W + "tbl"):
        trs = t.findall(W + "tr")
        head = [_text(c) for c in trs[0].findall(W + "tc")]
        if head == ["Claim", "Question", "Assigned", "Split", "Final", "Differs"]:
            rows = []
            for tr in trs[1:]:
                cells = [" ".join(_text(p) for p in c.findall(".//" + W + "p")).strip() for c in tr.findall(W + "tc")]
                rows.append(dict(zip(head, cells)))
            return rows
    raise SystemExit("Appendix A table not found in the summary")


def build() -> dict:
    rep = read_report(str(REP))
    vocab = concept_vocabulary()
    rows = rep["rows"]
    for i, r in enumerate(rows):
        r["n"] = i + 1
        r["paper_level"] = r["id"].startswith("SRC-")
        r["paper"] = r["id"] if r["paper_level"] else "SRC-" + r["id"][4:8]
        r["qid"] = QID[r["question"]]
        r["answers"] = {e: norm_answer(v["answer"]) for e, v in r["evaluators"].items()}

    by_key = {(r["id"], r["qid"], r["assigned"]): r for r in rows}
    by_claim_q = {(r["id"], r["qid"]): r for r in rows}

    for r in rows:
        # --- gating, read as the application reads stored answers
        gated = []
        if r["qid"] in CLAIM_GATED and (r["id"], "Q02") in by_claim_q:
            gate = by_claim_q[(r["id"], "Q02")]["answers"]
            gated = [e for e in EVALUATORS if gate[e] == "No"]
            r["gate_row"] = "Q02"
        elif r["qid"] in RELATION_GATED and (r["id"], "REL_TYPE", r["assigned"]) in by_key:
            gate = by_key[(r["id"], "REL_TYPE", r["assigned"])]["answers"]
            gated = [e for e in EVALUATORS if gate[e] == "No"]
            r["gate_row"] = "REL_TYPE"
        r["gated"] = gated
        r["split_stored"] = split_label(list(r["answers"].values())) if not r["paper_level"] and r["qid"] != "Q14" else ""
        r["split_applicable"] = split_label([a for e, a in r["answers"].items() if e not in gated]) if gated else r["split_stored"]

        # --- Final
        fin = parse_final(r)
        r.update({f"final_{k}": v for k, v in fin.items()})
        final_yellow = "Final" in r["manual_yellow_cells"]
        if r["manual_yellow"] and not final_yellow:
            r["final_flags"].append("YELLOW_EVALUATOR_CELL")
        if final_yellow:
            r["final_flags"].append("YELLOW")

        key = (r["id"], r["question"], r["assigned"])
        if key in AGREED_CASES:
            r["status"], r["status_basis"] = "AGREED", AGREED_CASES[key]
        elif r["final_category"] in ("UNRESOLVED", "EMPTY") or final_yellow:
            r["status"] = "OPEN"
            r["status_basis"] = r["final_reason"] or ("Final cell marked yellow (open question)." if final_yellow else "")
            if final_yellow and not r["status_basis"].startswith("Final cell"):
                r["status_basis"] += " Final cell marked yellow."
        elif r["final_category"] == "PAPER_LEVEL":
            r["status"], r["status_basis"] = "OPEN", "No agreed procedure for paper-level recall items (see policy RC-1)."
        else:
            r["status"] = "PROVISIONAL"
            r["status_basis"] = ("Proposed Final entered by Vaclav (email of 9 Oct)." if r["paper"] == "SRC-0006"
                                 else "Proposed Final; author not recorded in the report (reviewer comments on SRC-0009 are by Thiago).")

        # --- differs
        r["differs"], r["differs_note"] = [], ""
        if r["status"] == "OPEN":
            r["differs_note"] = "Not compared: the Final is open."
        elif r["final_category"] in ("CONFIRMED", "REPLACEMENT"):
            target = r["final_value"]
            r["differs"] = [e for e in EVALUATORS if e not in gated and r["answers"][e] and r["answers"][e] != target]
            if gated:
                r["differs_note"] = "Gated (not compared): " + ", ".join(gated) + "."
        elif r["final_category"] == "NOT_APPLICABLE":
            r["differs_note"] = "Not compared: Direction is not applicable once Relation type is No."
        elif r["final_category"] == "SET_VALUED":
            r["differs_note"] = "Not compared: set-valued (see the Missing Concept proposals)."
        else:
            r["differs_note"] = "Not compared: paper-level item."

        r["policy_ids"] = policies_for(r["id"] if not r["paper_level"] else "*", r["qid"])

        # --- reviewer comments attached to this row
        r["reviewer_comments"] = [
            {**rep["comments"][cid], "cell": col} for col, ids in r["comment_ids"].items() for cid in ids
        ]

    # --- Missing Concept proposals, one row per (claim, evaluator, Concept)
    proposals = []
    for r in rows:
        if r["qid"] != "Q14":
            continue
        for e in EVALUATORS:
            parts, exact = split_concepts(r["evaluators"][e]["answer"], vocab)
            for p in parts:
                disp, basis = q14_disposition(r["final"], p, r["id"])
                proposals.append(dict(
                    claim=r["id"], evaluator=e, concept=p.removeprefix("NEW: "), new=p.startswith("NEW: "),
                    cell=r["evaluators"][e]["answer"], split_exact=exact, final=r["final"],
                    disposition=disp, basis=basis, status=r["status"]))

    # --- comparison with the summary's Appendix A (same order, paper-level rows omitted there)
    summary = read_summary_appendix()
    item_rows = [r for r in rows if not r["paper_level"]]
    compare = []
    for s, r in zip(summary, item_rows):
        if s["Claim"] != r["id"]:
            compare.append(dict(kind="ALIGNMENT", claim=r["id"], question=r["question"], detail=f'summary row {s["Claim"]}'))
            continue
        diffs = []
        if s["Split"] and s["Split"] != r["split_stored"]:
            diffs.append(f'Split: summary “{s["Split"]}”, recomputed “{r["split_stored"]}”')
        same_text = re.sub(r"\s+", "", squash(s["Final"])) == re.sub(r"\s+", "", squash(r["final"]))
        if not same_text and not (s["Final"] == "(no Final)" and not r["final"]):
            diffs.append(f'Final text: summary “{s["Final"]}”, report “{r["final"]}”')
        sd = {x.strip() for x in s["Differs"].split(",") if x.strip()}
        rd = set(r["differs"])
        if sd != rd:
            why = r["differs_note"] or ""
            diffs.append(f'Differs: summary [{", ".join(sorted(sd)) or "—"}], register [{", ".join(sorted(rd)) or "—"}]. {why}'.strip())
        for d in diffs:
            compare.append(dict(kind="DIFF", claim=r["id"], question=r["question"], assigned=r["assigned"], detail=d))
    if len(summary) != len(item_rows):
        compare.append(dict(kind="COUNT", claim="", question="", detail=f"summary rows {len(summary)}, report item rows {len(item_rows)}"))

    return dict(rows=rows, proposals=proposals, statements=rep["statements"], comments=rep["comments"],
                anchored=rep["anchored"], summary_compare=compare)


def write_csv(reg: dict, out_dir: pathlib.Path) -> None:
    cols = ["n", "paper", "claim", "question_id", "question", "assigned", *EVALUATORS, "split_stored",
            "gated_evaluators", "split_applicable", "final_verbatim", "final_category", "final_evaluation",
            "proposed_replacement", "final_flags", "item_status", "status_basis", "differs_from_final",
            "differs_note", "policy_ids", "reviewer_comment_ids"]
    with open(out_dir / "CALIBRATION_DECISION_REGISTER.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in reg["rows"]:
            w.writerow([r["n"], r["paper"], r["id"], r["qid"], r["question"], r["assigned"],
                        *[r["evaluators"][e]["answer"] for e in EVALUATORS], r["split_stored"],
                        "; ".join(r["gated"]), r["split_applicable"], r["final"], r["final_category"],
                        r["final_value"] or "", r["final_replacement"] or "", "; ".join(r["final_flags"]),
                        r["status"], r["status_basis"], "; ".join(r["differs"]), r["differs_note"],
                        "; ".join(r.get("policy_ids", [])),
                        "; ".join(c["id"] for c in r["reviewer_comments"])])
    with open(out_dir / "CALIBRATION_MISSING_CONCEPTS.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["claim", "evaluator", "concept", "new_concept", "cell_verbatim", "split_exact",
                    "final_verbatim", "disposition", "basis", "item_status"])
        for p in reg["proposals"]:
            w.writerow([p["claim"], p["evaluator"], p["concept"], p["new"], p["cell"], p["split_exact"],
                        p["final"], p["disposition"], p["basis"], p["status"]])


if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    reg = build()
    (out / "register.json").write_text(json.dumps(reg, ensure_ascii=False, indent=1))
    c = collections.Counter(r["status"] for r in reg["rows"])
    print(f'{len(reg["rows"])} rows; status {dict(c)}; {len(reg["proposals"])} proposals; '
          f'{len(reg["summary_compare"])} differences with the summary')
