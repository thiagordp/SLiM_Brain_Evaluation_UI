"""Render the annex: the full calibration decision register and its evidence.

    python app/tools/calibration_guide/build_annex.py BUILD_DIR OUT.docx
"""
from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import docstyle as ds  # noqa: E402
import policies as pol  # noqa: E402
from docx.shared import Pt  # noqa: E402
from report_docx import EVALUATORS  # noqa: E402

TITLE = "SLiM Brain — Calibration Decision Register (Annex)"
W = 26.7                                     # A4 landscape text width at 1.5 cm margins (cm)
ABBR = dict(zip(EVALUATORS, ["Fr", "Tb", "Tg", "Al", "Gp", "Gv", "Vj"]))
SHORT_ANS = {"Yes": "Y", "No": "N", "In part": "P", "": "–", "none": "–"}
IDS = re.compile(r"\b((?:GEN|CL|GR|FD|CO|RE|RC|CC)-\d+)\b")
POL = pol.by_id()
CATEGORY_TEXT = {
    "CONFIRMED": "A plain Yes, No or In part, possibly followed by a note. Compared with the evaluators' answers.",
    "REPLACEMENT": "The Final gives another value for the field (e.g. Other for an assigned law, or “No. Abstract”). "
                   "The evaluation of the assigned value is No; the proposed value is shown separately.",
    "UNRESOLVED": "Marked “??”, “No?” or “To be discussed”, truncated, or contradicted by a comment on the "
                  "same cell. Treated as open; never compared.",
    "NOT_APPLICABLE": "“N/A”: the Final judges Relation type No, so Direction is not asked.",
    "EMPTY": "No Final was entered.",
    "SET_VALUED": "Missing Concepts (Q14): one row per proposal in Annex C.",
    "PAPER_LEVEL": "Claim recall, Restatements, Missing Claims: Annex D.",
}


def text(p, s, size=8, color=None, bold=None):
    for part in IDS.split(s):
        if not part:
            continue
        if IDS.fullmatch(part) and part in POL:
            ds.link(p, part, ds.bm_name(part), size=size, color=ds.BLUE, bold=bold)
        else:
            ds.rich(p, part, size=size, color=color, bold=bold)


def h1(doc, s, brk=True):
    if brk:
        ds.page_break(doc)
    return doc.add_paragraph(s, style="Heading 1")


def note(doc, s, size=8.4, after=3):
    p = ds.para(doc, "", after=after)
    text(p, s, size=size, color=ds.MUTED)
    return p


def normalised(r):
    c = r["final_category"]
    if c == "CONFIRMED":
        s = r["final_value"]
    elif c == "REPLACEMENT":
        s = f'No · proposed: {r["final_replacement"]}'
    elif c == "UNRESOLVED":
        s = "Unresolved" + (f' (tentative {r["final_value"]})' if r["final_value"] else "")
    elif c == "NOT_APPLICABLE":
        s = "Not applicable"
    elif c == "EMPTY":
        s = "No Final"
    else:
        s = c.replace("_", " ").title()
    flags = [f for f in r["final_flags"] if f not in ("TENTATIVE",)]
    if flags:
        s += "\n" + ", ".join(f.lower().replace("_", " ") for f in flags)
    return s


def answers_cell(r, e):
    a = r["answers"][e]
    if r["qid"] == "Q14":
        a = r["evaluators"][e]["answer"]
        return "–" if a.lower() in ("none", "") else "+"
    s = SHORT_ANS.get(a, a[:6])
    return s + ("†" if e in r["gated"] else "")


def build(reg, out):
    doc = ds.new_document(landscape=True, margins_cm=1.5)
    ds.header_footer(doc, "SLiM Brain · Calibration Decision Register (Annex)",
                     "Companion to the Calibration Policy and Open Decisions guide", "Human evaluation · Training phase · 14 October 2026")
    rows = reg["rows"]
    items = [r for r in rows if not r["paper_level"]]

    doc.add_paragraph(TITLE, style="Title")
    ds.para(doc, "Human evaluation · Training phase · 14 October 2026 · instrument 4.1 · SRC-0006 and SRC-0009",
            size=11, color=ds.BLUE, italic=True, after=4)
    p = ds.para(doc, "", after=6)
    text(p, f"This annex reproduces every contested item of Appendix B of the Training report ({len(rows)} rows: {len(items)} "
            f"item rows and {len(rows) - len(items)} paper-level rows), with the Final as written and its normalised reading, "
            f"and the evidence behind every rule of the guide. Generated from Calibration/TRAINING_AGREEMENT_REPORT.docx "
            f"(state of 14 October 2026) by app/tools/calibration_guide; the source files are unchanged.", size=9.5)

    # ---------------- A
    doc.add_paragraph("A  How to read this register", style="Heading 1")
    doc.add_paragraph("Item status", style="Heading 2")
    t = ds.table(doc, [3.0, W - 3.0], size=8.4)
    for st in (pol.AGREED, pol.PROVISIONAL, pol.OPEN):
        ds.add_row(t, [lambda c, st=st: ds.chip(c.paragraphs[0], st, size=7.5),
                       {"AGREED": "The case outcome was recorded at a meeting with the assent of at least two participants "
                                  "(CLM-0006-001 Pseudolaw and Legal literacy, CLM-0006-002 Direction, CLM-0006-015 Textual grounding).",
                        "PROVISIONAL": "A Final proposed by one reviewer: Vaclav for SRC-0006 (email of 9 October); not recorded "
                                       "for SRC-0009 (the reviewer comments there are by Thiago). A proposal, not a team decision.",
                        "OPEN": "The Final is tentative, missing, truncated, self-contradictory or in a cell marked yellow by a "
                                "reviewer (Vaclav: “There is few open question for me (highlighted in yellow)”, email of 9 "
                                "October). The proposed value is kept but not used for comparison."}[st]])
    doc.add_paragraph("Normalisation of the Final", style="Heading 2")
    t = ds.table(doc, [3.6, W - 3.6], header=["Category", "Meaning"], size=8.4)
    for k, v in CATEGORY_TEXT.items():
        ds.add_row(t, [k.replace("_", " ").title(), v])
    doc.add_paragraph("Differs and gating", style="Heading 2")
    for s in [
        "**Differs** lists the evaluators whose answer differs from a CONFIRMED or REPLACEMENT Final of an item that is not "
        "OPEN. It is empty, with the reason stated, for every other item. It is recomputed from the seven answers by "
        "validate.py.",
        "**Gating (†).** Training answers were stored before the 4.1 gates existed. As the application reads them, an "
        "evaluator who answered No to Q02 has no applicable answer for Q03–Q11 of that Claim, and an evaluator who "
        "answered No to Relation type has none for Grounding and Direction of that relation. Such answers are shown with "
        "† and never compared (GEN-5). Where the gate question is not listed (all seven answered the same), no gating "
        "is applied.",
        "**Answers.** Y = Yes, N = No, P = In part, – = none; for Missing Concepts, + = at least one Concept proposed. "
        "Evaluators: " + ", ".join(f"{v} {k}" for k, v in ABBR.items()) + ".",
        "**Yellow.** The report generator marks ties in pale yellow (FFF2CC) and minority answers in orange (FCE4D6). "
        "Bright yellow (FFFF00) and yellow highlighting are never produced by the generator: they are reviewers' marks.",
    ]:
        q = doc.add_paragraph(style="List Bullet")
        q.paragraph_format.space_after = Pt(1.5)
        text(q, s, size=8.6)
    doc.add_paragraph("Sources", style="Heading 2")
    t = ds.table(doc, [2.0, W - 2.0], size=8.2)
    for k, v in pol.SOURCES.items():
        ds.add_row(t, [lambda c, k=k: ds.style_run(c.paragraphs[0].add_run(k), size=8.2, color=ds.NAVY, bold=True), v])
    for k, v in pol.STATUS_RULES.items():
        pass

    # ---------------- B
    h1(doc, "B  Item register")
    note(doc, "One block per Claim, in the order of the Training report (relation rows keep the report's order, Direction "
              "before Relation type). Final texts are verbatim; line breaks inside a Final are shown as “ / ”.")
    widths = [0.8, 2.6, 3.0] + [1.05] * 7 + [5.2, 2.4, 1.9, 2.3, 1.15]
    head = ["#", "Question", "Assigned"] + [ABBR[e] for e in EVALUATORS] + ["Final (verbatim)", "Normalised", "Status", "Differs", "Rules"]
    for paper in ("SRC-0006", "SRC-0009"):
        doc.add_paragraph(f"{paper}", style="Heading 2")
        t = ds.table(doc, widths, header=head, size=7.6)
        current = None
        for r in [x for x in items if x["paper"] == paper]:
            if r["id"] != current:
                current = r["id"]
                st = reg["statements"].get(current, "")
                row = ds.add_row(t, [""] * len(widths), fill=ds.PANEL, keep=True)
                cell = ds.merge_row(row)
                cell.paragraphs[0].text = ""
                for extra in cell.paragraphs[1:]:
                    extra._p.getparent().remove(extra._p)
                q = cell.paragraphs[0]
                ds.style_run(q.add_run(current + "  "), size=8, color=ds.NAVY, bold=True)
                ds.bookmark(q, "clm_" + current.replace("-", "_"))
                ds.style_run(q.add_run(st), size=7.4, color=ds.INK, italic=True)
            fin = " / ".join(p.strip() for p in r["final_paras"] if p.strip()) or "—"
            diff = ", ".join(ABBR[e] for e in r["differs"]) or ("—" if not r["differs_note"] else "")
            dn = r["differs_note"]
            if dn.startswith("Not compared"):
                diff = dn.replace("Not compared: ", "not compared: ")
            elif dn:
                diff = (diff + "\n" if diff else "") + dn.replace("Gated (not compared): ", "gated: ")
            cells = [str(r["n"]), r["question"], r["assigned"] or "—"] + [answers_cell(r, e) for e in EVALUATORS] + [
                fin, normalised(r), lambda c, r=r: ds.chip(c.paragraphs[0], r["status"], size=6.6), diff,
                lambda c, r=r: text(c.paragraphs[0], ", ".join(r["policy_ids"][:3]), size=7.2)]
            ds.add_row(t, cells)

    # ---------------- C
    h1(doc, "C  Missing-Concept proposals (Q14)")
    note(doc, "One row per proposed Concept. “Considered reasonable” records that the Final called the addition "
              "reasonable or acceptable; it does not mean that the Concept was judged necessary, missing or adopted (CC-4). "
              "Cells whose line breaks the report generator lost were split against the Concept vocabulary; every split "
              "matched known Concept names exactly.")
    disp = {"AGREED_MISSING": "Agreed as missing (meeting)", "NOT_ADOPTED": "Not adopted",
            "NOT_ADOPTED_OPEN_POLICY": "Not adopted; policy question open", "CONSIDERED_REASONABLE": "Considered reasonable",
            "REASONABLE_WITH_CHANGE": "Reasonable, with a change", "UNCLEAR": "Unclear"}
    t = ds.table(doc, [2.4, 2.0, 4.6, 1.4, 8.0, 4.4, 3.9], header=["Claim", "Evaluator", "Concept", "New?",
                                                                 "Final (verbatim)", "Disposition", "Basis"], size=7.8)
    for p in reg["proposals"]:
        ds.add_row(t, [p["claim"], p["evaluator"], p["concept"], "yes" if p["new"] else "", p["final"],
                       disp[p["disposition"]], p["basis"]])

    # ---------------- D
    h1(doc, "D  Paper-level items: Claim recall, Restatements, Missing Claims")
    note(doc, "No agreement is sought on which Claims are missing (proposal RC-1, open). Texts are verbatim.")
    for paper in ("SRC-0006", "SRC-0009"):
        doc.add_paragraph(paper, style="Heading 2")
        pl = [r for r in rows if r["id"] == paper]
        t = ds.table(doc, [3.4] + [2.6] * 7 + [5.1], header=["Question"] + EVALUATORS + ["Final"], size=7.8)
        for r in pl:
            if r["qid"] == "MISSING_CLAIMS":
                continue
            ds.add_row(t, [r["question"]] + [r["evaluators"][e]["answer"] for e in EVALUATORS] + [r["final"] or "— (marked yellow)" if r["manual_yellow"] and not r["final"] else r["final"]])
        mc = [r for r in pl if r["qid"] == "MISSING_CLAIMS"][0]
        q = ds.para(doc, "", before=4, after=2, keep=True)
        ds.style_run(q.add_run("Missing Claims (text), as written"), size=9, color=ds.BLUE, bold=True)
        t = ds.table(doc, [3.0, W - 3.0], size=7.8)
        for e in EVALUATORS:
            ev = mc["evaluators"][e]
            body = (ev["answer"] + ("\n" + ev["comment"] if ev["comment"] else "")).strip()
            if ev["answer"] == "not asked":
                continue
            ds.add_row(t, [e, body.replace("listed\n", "")], cant_split=False)
        ds.add_row(t, ["Not asked", ", ".join(e for e in EVALUATORS if mc["evaluators"][e]["answer"] == "not asked")
                       + " (recall answered All)"])
        ds.add_row(t, ["Final", mc["final"] or "—"])

    # ---------------- E
    h1(doc, "E  Flagged entries")
    note(doc, "Entries that are truncated, contradictory, tentative, empty, marked yellow, or corrected for case. Nothing has "
              "been repaired: the Final is shown as written.")
    t = ds.table(doc, [2.4, 3.2, 4.0, 6.0, 3.2, W - 18.8], header=["Claim", "Question", "Assigned", "Final (verbatim)", "Flag", "Reading"], size=7.8)
    for r in rows:
        flags = list(r["final_flags"])
        if r["final_category"] == "EMPTY":
            flags.append("EMPTY")
        if not flags and r["final_category"] != "UNRESOLVED":
            continue
        reading = r["final_reason"] or r["status_basis"]
        if "YELLOW_EVALUATOR_CELL" in flags:
            reading = "Only an evaluator cell (" + ", ".join(c for c in r["manual_yellow_cells"]) + ") is marked yellow; the meaning of the mark is not recorded. The Final is kept as proposed."
        if "CASE_NORMALISED" in flags:
            reading = "Lower-case “yes” read as Yes."
        ds.add_row(t, [r["id"], r["question"], r["assigned"] or "—", " / ".join(x for x in r["final_paras"] if x.strip()) or "—",
                       ", ".join(f.lower().replace("_", " ") for f in flags), reading])
    ds.add_row(t, ["CLM-0006-001", "Missing Concepts (Q14)", "selected / proposed", "Legal Literatcy", "typo",
                   "Read as “Legal literacy” (agreed at M07 23:03–23:22); the verbatim text is kept."])

    # ---------------- F
    h1(doc, "F  Review list per evaluator")
    note(doc, "Items where an evaluator's applicable answer differs from a Final that is not open: reconsider the answer, or "
              "add a comment explaining it. Most of these Finals are proposals (PROVISIONAL), not team decisions; differing "
              "from one is not an error. Items with an open Final are counted separately and are not corrections.")
    open_items = [r for r in items if r["status"] == "OPEN"]
    for e in EVALUATORS:
        mine = [r for r in items if e in r["differs"]]
        q = doc.add_paragraph(f"{e}", style="Heading 2")
        n_open = sum(1 for r in open_items if r["answers"][e])
        n_gated = sum(1 for r in items if e in r["gated"])
        note(doc, f"{len(mine)} items differ from a non-open Final ({sum(1 for r in mine if r['status'] == 'AGREED')} of them "
                  f"agreed at a meeting). {n_open} open items await a decision. {n_gated} stored answers are Not applicable "
                  f"under the gates.", size=8.2, after=2)
        if not mine:
            continue
        t = ds.table(doc, [0.9, 2.4, 3.3, 4.0, 1.6, 7.0, 2.2, W - 21.4], header=["#", "Claim", "Question", "Assigned",
                                                                                "Answer", "Final (verbatim)", "Status", "Rules"], size=7.6)
        for r in mine:
            ds.add_row(t, [str(r["n"]), r["id"], r["question"], r["assigned"] or "—", r["answers"][e],
                           " / ".join(x for x in r["final_paras"] if x.strip()),
                           lambda c, r=r: ds.chip(c.paragraphs[0], r["status"], size=6.6),
                           lambda c, r=r: text(c.paragraphs[0], ", ".join(r["policy_ids"][:3]), size=7.2)])

    # ---------------- G
    h1(doc, "G  Differences from the earlier summary (Appendix A)")
    note(doc, "Calibration/CALIBRATION_DECISIONS_SUMMARY.docx, Appendix A, compared row by row with this register (161 item "
              "rows; the summary omits the six paper-level rows). Whitespace-only differences in Final texts are ignored.")
    t = ds.table(doc, [2.4, 3.0, 4.6, W - 10.0], header=["Claim", "Question", "Assigned", "Difference"], size=7.8)
    for c in reg["summary_compare"]:
        detail = c["detail"]
        for e, a in ABBR.items():
            pass
        ds.add_row(t, [c["claim"], c["question"], c.get("assigned", "") or "—", detail])

    # ---------------- H
    h1(doc, "H  Reviewer comments in the Training report")
    note(doc, f'All {len(reg["comments"])} Word comments, verbatim, with the cell they are attached to. Ids are the report\'s '
              f"own comment ids (cited in the guide as RC#id).")
    where = {}
    for a in reg["anchored"]:
        if a["where"].startswith("Appendix B"):
            loc = f'{a["row"]} [{a["column"]}]'
        elif a["where"] == "paragraph":
            loc = f'Heading or paragraph “{a["row"]}”'
        else:
            loc = f'Report section table: {a["row"][:110]}… [{a["column"]}]'
        where.setdefault(a["comment_id"], []).append(loc)
    t = ds.table(doc, [2.0, 3.2, 1.9, 6.6, W - 13.7], header=["RC#", "Author", "Date", "Attached to", "Text"], size=7.6)

    def cid_key(c):
        return (c["date"], int(c["id"]) if c["id"].isdigit() else 0)
    for c in sorted(reg["comments"].values(), key=cid_key):
        loc = "; ".join(where.get(c["id"], ["(reply thread)" if c["reply_to"] else "(not located)"]))
        if c["reply_to"]:
            loc = f'Reply to RC#{c["reply_to"]}. ' + loc
        ds.add_row(t, [c["id"], c["author"], c["date"], loc, c["text"]], cant_split=False)

    # ---------------- I
    h1(doc, "I  Rule index and evidence")
    note(doc, "Each rule of the guide with its status, implementation and every quotation used as evidence. validate.py "
              "checks each quotation against its source text.")
    t = ds.table(doc, [2.0, 5.2, 2.4, 2.4, W - 12.0], header=["Rule", "Title", "Status", "Implementation", "Sources and quotations"], size=7.6)
    for p in pol.POLICIES:
        def rid(c, p=p):
            q = c.paragraphs[0]
            ds.style_run(q.add_run(p["id"]), size=8, color=ds.NAVY, bold=True)
            ds.bookmark(q, ds.bm_name(p["id"]))

        def ev(c, p=p):
            q = c.paragraphs[0]
            ds.style_run(q.add_run("; ".join(p["sources"])), size=7.4, color=ds.MUTED)
            for k, s in p["quotes"]:
                q = c.add_paragraph(); q.paragraph_format.space_after = Pt(0.5)
                ds.style_run(q.add_run(k + ": "), size=7.4, color=ds.BLUE, bold=True)
                ds.style_run(q.add_run("“" + s + "”"), size=7.4)
            if p["impl_evidence"]:
                q = c.add_paragraph(); q.paragraph_format.space_after = Pt(0)
                ds.style_run(q.add_run("Implementation: " + p["impl_evidence"]), size=7.2, color=ds.MUTED)
        ds.add_row(t, [rid, pol.TITLES[p["id"]], lambda c, p=p: ds.chip(c.paragraphs[0], p["status"], size=6.6),
                       ds.IMPL_LABEL[p["impl"]], ev], cant_split=False)
    doc.add_paragraph("Consistency checks", style="Heading 2")
    t = ds.table(doc, [1.6, 2.4, 5.0, W - 9.0], header=["Check", "Origin", "Items", "Point and evidence"], size=7.6)
    for c in pol.CONSISTENCY_CHECKS:
        def body(cell, c=c):
            text(cell.paragraphs[0], c["point"], size=7.6)
            for k, s in c["evidence"]:
                q = cell.add_paragraph(); q.paragraph_format.space_after = Pt(0)
                ds.style_run(q.add_run(f"{k}: “{s}”"), size=7.2, color=ds.MUTED)
        ds.add_row(t, [c["id"], c["origin"], ", ".join(c["items"]) or "—", body])
    doc.add_paragraph("Open questions of the earlier summary (Section 8) and where they are kept", style="Heading 2")
    t = ds.table(doc, [3.0, W - 3.0], size=7.8)
    for n, ids in pol.SUM_OPEN_QUESTIONS.items():
        ds.add_row(t, [f"Question {n}", lambda c, ids=ids: text(c.paragraphs[0], ", ".join(ids) + "  (decision " +
                                                                ", ".join(sorted({d["id"] for d in pol.OPEN_DECISIONS for i in ids if i in d["policies"]}, key=lambda x: int(x[1:]))) + ")", size=7.8)])

    # ---------------- J
    h1(doc, "J  Schema text and 4.1 calibration text")
    note(doc, "The schema text is the frozen definition shown to evaluators (app/data/definitions_v4.json, identical to "
              "SLiM_Brain/schema). The calibration text is shown under “Calibration” in instrument 4.1 "
              "(app/spec.py). Both are quoted verbatim.")
    t = ds.table(doc, [3.6, 3.0, 7.0, 7.0, W - 20.6], header=["Field", "Value", "Schema", "4.1 calibration text", "Reading"], size=7.8)
    for b in pol.BASELINE:
        ds.add_row(t, [b["field"], b["value"] or "—", "“" + b["schema"] + "”",
                       ("“" + b["calibration"] + "”") if b["calibration"] else "— (none)",
                       lambda c, b=b: text(c.paragraphs[0], b["reading"] + " (" + ", ".join(b["policies"]) + ")", size=7.8)])

    doc.core_properties.title = TITLE
    doc.core_properties.author = "SLiM Brain evaluation team"
    doc.save(out)


if __name__ == "__main__":
    build(json.loads((pathlib.Path(sys.argv[1]) / "register.json").read_text(encoding="utf-8")), sys.argv[2])
    print("written", sys.argv[2])
