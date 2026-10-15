"""Render the calibration guide (main document).

    python app/tools/calibration_guide/build_guide.py BUILD_DIR OUT.docx

Reads BUILD_DIR/register.json (extract_register.py) and the content model in
policies.py. Run validate.py first: this script trusts the content model.

Pages 1-2 are the overview (every rule in one line, then the open decisions);
the rest of the guide gives each rule in full.
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
from docx.shared import Cm, Pt  # noqa: E402

TITLE = "SLiM Brain Calibration Guide"
SCOPE = ("Human evaluation, Training phase \u00b7 instrument 4.1 \u00b7 papers SRC-0006 and SRC-0009 \u00b7 "
         "seven evaluators \u00b7 sources up to 14 October 2026")
W = 17.8                                       # A4 portrait text width at 1.6 cm margins (cm)
STATUS_FG = ds.STATUS_STYLE["OPEN"][0]
IDS = re.compile(r"\b((?:GEN|CL|GR|FD|CO|RE|RC|CC)-\d+|D\d{1,2})\b")
POL = pol.by_id()
DEC = {d["id"]: d for d in pol.OPEN_DECISIONS}
GROUP_NAME = dict(pol.GROUPS)


def anchor_for(i: str) -> str | None:
    if i in POL:
        return ds.bm_name(i)
    if i in DEC:
        return "dec_" + i
    return None


def text(p, s, size=9, color=None, bold=None, italic=None):
    """Rich text with **bold** and live links on any rule or decision id it contains."""
    for part in IDS.split(s):
        if not part:
            continue
        a = anchor_for(part) if IDS.fullmatch(part) else None
        if a:
            ds.link(p, part, a, size=size, color=ds.BLUE, bold=bold)
        else:
            ds.rich(p, part, size=size, color=color, bold=bold, italic=italic)
    return p


def tags(p, ids, size=7):
    """Comma-separated grey id tags, each linked to its entry."""
    for k, i in enumerate(ids):
        if k:
            ds.style_run(p.add_run(", "), size=size, color=ds.MUTED)
        ds.tag(p, i, anchor_for(i), size=size)
    return p


def h1(doc, s, page_break=False):
    if page_break:
        ds.page_break(doc)
    return doc.add_paragraph(s, style="Heading 1")


def h2(doc, s):
    return doc.add_paragraph(s, style="Heading 2")


def lead(doc, s, size=9, after=4, color=None):
    return text(ds.para(doc, "", after=after), s, size=size, color=color)


def caption(doc, s, before=2, after=4, keep=False):
    return text(ds.para(doc, "", before=before, after=after, keep=keep), s, size=8.2, color=ds.MUTED)


def bullet(doc, s, size=9):
    q = doc.add_paragraph(style="List Bullet")
    q.paragraph_format.space_after = Pt(1.5)
    return text(q, s, size=size)


def sublabel(cell, label, s, size=8.4, color=None):
    """A paragraph that starts with a small sub-heading (What to do, Basis, Limits)."""
    p = cell.add_paragraph()
    p.paragraph_format.space_after = Pt(1.2)
    ds.style_run(p.add_run(label + "  "), size=size - 0.8, color=ds.BLUE, bold=True)
    text(p, s, size=size, color=color)
    return p


# ------------------------------------------------------------------ register helpers
class Reg:
    def __init__(self, data):
        self.rows = data["rows"]

    def get(self, claim, qid, target=None):
        for r in self.rows:
            if r["id"] == claim and r["qid"] == qid and (target is None or target in r["assigned"]):
                return r
        return None


def short_final(r):
    f = r["final"] or "(no Final)"
    return f if len(f) <= 120 else f[:117] + "\u2026"


# ------------------------------------------------------------------ overview (pages 1-2)
def overview_rules(doc):
    """Every Agreed and Provisional rule in one line, grouped by question."""
    t = ds.table(doc, [W - 3.4, 1.9, 1.5], size=8.4, pad=18)
    for code, name in pol.GROUPS:
        ps = [p for p in pol.POLICIES if p["group"] == code and p["status"] != pol.OPEN]
        if not ps:
            continue
        row = ds.add_row(t, ["", "", ""], fill=ds.PANEL, keep=True)
        cell = ds.merge_row(row)
        for extra in cell.paragraphs[1:]:
            extra._p.getparent().remove(extra._p)
        ds.style_run(cell.paragraphs[0].add_run(name), size=8.4, color=ds.NAVY, bold=True)
        for p in ps:
            ds.add_row(t, [lambda c, p=p: text(c.paragraphs[0], p["brief"], size=8.4),
                           lambda c, p=p: ds.chip(c.paragraphs[0], p["status"], size=6.8),
                           lambda c, p=p: tags(c.paragraphs[0], [p["id"]], size=7.2)])
    for row in t.rows:
        for c in row.cells:
            for q in c.paragraphs:
                q.paragraph_format.line_spacing = 1.0
    return t


def overview_open(doc):
    """The open decisions in three lines each."""
    t = ds.table(doc, [1.3, W - 3.7, 2.4], size=8.4)
    for d in sorted(pol.OPEN_DECISIONS, key=lambda x: (x["priority"], int(x["id"][1:]))):
        def head(cell, d=d):
            q = cell.paragraphs[0]
            ds.link(q, d["id"], "dec_" + d["id"], size=10, color=ds.NAVY, bold=True)
            q2 = cell.add_paragraph(); q2.paragraph_format.space_after = Pt(0)
            ds.style_run(q2.add_run(f'Priority {d["priority"]}'), size=6.8, color=ds.MUTED)

        def body(cell, d=d):
            q = cell.paragraphs[0]
            q.paragraph_format.space_after = Pt(1)
            ds.style_run(q.add_run(d["title"] + "  "), size=8.6, color=ds.NAVY, bold=True)
            text(q, d["brief"], size=8.4)
            sublabel(cell, "Readings", d["readings"], size=8.2)
            p = sublabel(cell, "Meanwhile", d["meanwhile"], size=8.2)
            p.paragraph_format.space_after = Pt(0)

        def side(cell, d=d):
            ids = [i for i in d["policies"] if POL[i]["status"] == pol.OPEN] or d["policies"]
            tags(cell.paragraphs[0], ids, size=7.4)
        ds.add_row(t, [head, body, side])
    return t


# ------------------------------------------------------------------ detailed entries
def policy_cards(doc, ids):
    """Agreed and provisional rules in full; open rules in a compact table after them."""
    open_ids = [i for i in ids if POL[i]["status"] == pol.OPEN]
    ids = [i for i in ids if POL[i]["status"] != pol.OPEN]
    if ids:
        t = ds.table(doc, [2.5, W - 2.5], size=8.4, outer=True)
        for i in ids:
            p = POL[i]

            def left(cell, p=p):
                q = cell.paragraphs[0]
                ds.style_run(q.add_run(p["id"]), size=9, color=ds.NAVY, bold=True)
                ds.bookmark(q, ds.bm_name(p["id"]))
                q2 = cell.add_paragraph(); q2.paragraph_format.space_after = Pt(0.5)
                ds.chip(q2, p["status"], size=7)
                q3 = cell.add_paragraph(); q3.paragraph_format.space_after = Pt(0)
                ds.impl_tag(q3, p["impl"], size=7)

            def right(cell, p=p):
                q = cell.paragraphs[0]
                q.paragraph_format.space_after = Pt(1.5)
                ds.style_run(q.add_run(p["title"] + ".  "), size=8.9, color=ds.NAVY, bold=True)
                text(q, p["rule"], size=8.9)
                sublabel(cell, "What to do", p["apply"])
                sublabel(cell, "Basis", p["basis"])
                if p["limits"]:
                    sublabel(cell, "Limits", p["limits"])
                refs(cell, p)

            ds.add_row(t, [left, right])
    if open_ids:
        open_table(doc, open_ids)


def refs(cell, p, size=7.1):
    q = cell.add_paragraph(); q.paragraph_format.space_after = Pt(0)
    if p["examples"]:
        ds.style_run(q.add_run("Cases "), size=size, color=ds.BLUE, bold=True)
        ds.style_run(q.add_run(", ".join(p["examples"]) + "   "), size=size, color=ds.MUTED)
    ds.style_run(q.add_run("Sources "), size=size, color=ds.BLUE, bold=True)
    ds.style_run(q.add_run("; ".join(p["sources"])), size=size, color=ds.MUTED)


def open_table(doc, ids):
    q = ds.para(doc, "", before=5, after=2, keep=True)
    ds.style_run(q.add_run("Still open in this area"), size=8.8, color=STATUS_FG, bold=True)
    t = ds.table(doc, [2.0, W - 8.6, 5.0, 1.6], header=["", "Question", "Meanwhile", "Decision"], size=8.1)
    for i in ids:
        p = POL[i]

        def left(cell, p=p):
            q = cell.paragraphs[0]
            ds.style_run(q.add_run(p["id"]), size=8.6, color=ds.NAVY, bold=True)
            ds.bookmark(q, ds.bm_name(p["id"]))
            q2 = cell.add_paragraph(); q2.paragraph_format.space_after = Pt(0)
            ds.chip(q2, p["status"], size=6.8)

        def mid(cell, p=p):
            q = cell.paragraphs[0]
            q.paragraph_format.space_after = Pt(1)
            ds.style_run(q.add_run(p["title"] + ".  "), size=8.2, color=ds.NAVY, bold=True)
            text(q, p["rule"], size=8.1)
            q = cell.add_paragraph(); q.paragraph_format.space_after = Pt(1)
            text(q, p["basis"], size=7.8, color=ds.MUTED)
            if p["limits"]:
                q = cell.add_paragraph(); q.paragraph_format.space_after = Pt(1)
                text(q, p["limits"], size=7.8, color=ds.MUTED)
            refs(cell, p, size=6.8)

        ds.add_row(t, [left, mid, lambda c, p=p: text(c.paragraphs[0], p["apply"], size=8.1),
                       lambda c, p=p: tags(c.paragraphs[0], pol.decisions_for(p["id"]), size=8.4)])


def flow_box(cell, title, body=None, fill="EAF0F8", border=ds.BLUE, italic=False):
    ds.shade(cell, fill)
    for side in ("top", "bottom", "left", "right"):
        ds.cell_border(cell, side, border, sz=6)
    q = cell.paragraphs[0]
    q.paragraph_format.space_after = Pt(0.5)
    ds.style_run(q.add_run(title), size=8.4, color=ds.NAVY, bold=True, italic=italic)
    if body:
        q2 = cell.add_paragraph()
        q2.paragraph_format.space_after = Pt(0)
        text(q2, body, size=7.8, color=ds.INK, italic=italic)


def arrow(cell, s):
    q = cell.paragraphs[0]
    q.alignment = 1
    ds.style_run(q.add_run(s), size=8, color=ds.MUTED, bold=True)


def workflow(doc, title, rows):
    """rows: list of lists of (kind, title, body) where kind in box/gate/na/arrow/blank."""
    para = ds.para(doc, "", after=2, keep=True)
    ds.style_run(para.add_run(title), size=9, color=ds.BLUE, bold=True)
    t = ds.table(doc, [4.1, 1.3, 5.2, 1.3, 5.5], size=8, rules=False, outer=False)
    for r in rows:
        cells = []
        for kind, a, b in r:
            if kind == "gate":
                cells.append(lambda c, a=a, b=b: flow_box(c, a, b, fill="DCE3EE", border=ds.NAVY))
            elif kind == "box":
                cells.append(lambda c, a=a, b=b: flow_box(c, a, b))
            elif kind == "na":
                cells.append(lambda c, a=a, b=b: flow_box(c, a, b, fill="F2F2F2", border="9AA1AA", italic=True))
            elif kind == "arrow":
                cells.append(lambda c, a=a: arrow(c, a))
            else:
                cells.append("")
        ds.add_row(t, cells)
    ds.keep_table_together(t)
    return t


def simple_table(doc, widths, header, rows, size=8.4, bold_first=True, tag_last=False):
    t = ds.table(doc, widths, header=header, size=size)
    for row in rows:
        cells = list(row)
        if bold_first:
            cells[0] = lambda c, v=row[0]: ds.style_run(c.paragraphs[0].add_run(v), size=size, bold=True)
        if tag_last:
            cells[-1] = lambda c, v=row[-1]: tags(c.paragraphs[0], [x.strip() for x in v.split(",") if x.strip()], size=7.6)
        ds.add_row(t, cells)
    ds.keep_table_together(t)
    return t


def group_ids(code):
    return [p["id"] for p in pol.POLICIES if p["group"] == code]


# ------------------------------------------------------------------ the document
def build(reg_data, out):
    reg = Reg(reg_data)
    doc = ds.new_document(margins_cm=1.6)
    ds.header_footer(doc, "SLiM Brain \u00b7 Calibration Guide", "Instrument 4.1 \u00b7 Training phase",
                     "Sources up to 14 October 2026")
    counts = collections.Counter(p["status"] for p in pol.POLICIES)
    rs = collections.Counter(r["status"] for r in reg.rows)

    # ---------------- page 1: what we apply now
    p = doc.add_paragraph(TITLE, style="Title")
    p.paragraph_format.space_after = Pt(1)
    ds.para(doc, SCOPE, size=8.6, color=ds.MUTED, after=5)
    ds.para_border(doc.paragraphs[-1], "bottom", color=ds.RULE, sz=6, space=4)
    h1(doc, "1  What we apply now")
    q = lead(doc, f"The {counts['AGREED'] + counts['PROVISIONAL']} rules below are in force for instrument 4.1. ", size=8.8, after=2)
    ds.chip(q, pol.AGREED, size=7)
    text(q, " rules were accepted by the team. ", size=8.8)
    ds.chip(q, pol.PROVISIONAL, size=7)
    text(q, f" rules are in use but were never adopted, so they may change. The {counts['OPEN']} open questions "
            "are on the next page. Click an id for the full rule.", size=8.8)
    overview_rules(doc)

    # ---------------- page 2: still open
    h1(doc, "2  Still open", page_break=True)
    lead(doc, "The team has not yet decided these questions. Each one gives the competing readings and what to do in "
              "the meantime. Priority 1 affects how comparable the evaluators' answers are, priority 2 affects which "
              "answers enter the statistics, and priority 3 affects only what is reported.", size=8.8, after=3)
    overview_open(doc)
    caption(doc, f"The Training report lists {len(reg.rows)} contested items. Of these, {rs['AGREED']} were settled at a "
                 f"meeting, {rs['PROVISIONAL']} have a Final proposed by one reviewer, and {rs['OPEN']} are open. The "
                 "annex lists every item with the seven answers and the Final.", before=4)

    # ---------------- 3 how to read
    h1(doc, "3  How to read this guide", page_break=True)
    t = ds.table(doc, [2.6, W - 2.6], size=8.6)
    for st in (pol.AGREED, pol.PROVISIONAL, pol.OPEN):
        ds.add_row(t, [lambda c, st=st: ds.chip(c.paragraphs[0], st, size=7.4),
                       lambda c, st=st: text(c.paragraphs[0], pol.STATUS_RULES[st], size=8.6)])
    ds.add_row(t, [lambda c: ds.style_run(c.paragraphs[0].add_run("In the app"), size=8, color=ds.MUTED, italic=True),
                   "Each detailed entry also says whether the rule is built into the app (in the calibration text or the "
                   "interface), not built in, or a principle with nothing to build. This is separate from its status. A "
                   "rule can be in the app without being agreed."])
    ds.keep_table_together(t)
    caption(doc, "A Final in the Training report is one reviewer's proposal unless a meeting recorded the outcome. "
                 "Agreeing with a Final is not the same as being right, and a majority of evaluators does not settle a "
                 "question.", before=3)

    h2(doc, "The two gates")
    workflow(doc, "How a Claim is evaluated", [
        [("gate", "Q02 Central thesis or hypothesis", "Does the paper advance this proposition?"),
         ("arrow", "Yes \u2192", None),
         ("box", "Q03\u2013Q05 The Claim", "Strength and modality \u00b7 understood on its own \u00b7 textual grounding"),
         ("arrow", "\u2192", None),
         ("box", "Q06\u2013Q11 Schema fields", "Object \u00b7 type \u00b7 basis \u00b7 jurisdiction \u00b7 legal reference \u00b7 temporal reference")],
        [("blank", "", None), ("arrow", "No \u2193", None),
         ("na", "Q03\u2013Q11 Not applicable", "Not asked, not stored, not counted"),
         ("blank", "", None), ("blank", "", None)],
        [("box", "Always asked", "Q12 Concept assignment \u00b7 Q13 candidate Concept needed \u00b7 Q14 missing Concepts \u00b7 the Claim's Relations"),
         ("blank", "", None), ("blank", "", None), ("blank", "", None), ("blank", "", None)],
    ])
    ds.para(doc, "", after=4)
    workflow(doc, "How a relation is evaluated (SUPPORTS, ATTACKS, SAME_AS)", [
        [("gate", "Relation type", "Is the relation correctly classified? No if it should not exist or is of another kind."),
         ("arrow", "Yes \u2192", None),
         ("box", "Grounding", "Extracted only if one source cites the other on this point"),
         ("arrow", "\u2192", None),
         ("box", "Direction", "SUPPORTS and ATTACKS only. The arrow starts at the supporting or attacking Claim.")],
        [("blank", "", None), ("arrow", "No \u2193", None),
         ("na", "Grounding and Direction Not applicable", "Say in the comment why the type is wrong"),
         ("blank", "", None), ("blank", "", None)],
    ])
    claim_flow = doc.tables[-2]
    merged = claim_flow.rows[2].cells[0].merge(claim_flow.rows[2].cells[4])
    for extra in merged.paragraphs[2:]:
        if not extra.text.strip():
            extra._p.getparent().remove(extra._p)
    caption(doc, "A question skipped by a gate is Not applicable. It is neither Yes nor No, it is not a missing answer, and "
                 "it is left out of the agreement statistics. The Training answers were given before the gates existed. "
                 "They are kept and read under the gates, and whether to revise them is still open. In the annex these "
                 "answers are marked \u2020 and never compared with a Final.", before=4)

    # ---------------- 4 general principles
    h1(doc, "4  General principles")
    policy_cards(doc, group_ids("general"))

    # ---------------- 5 the Claim
    h1(doc, "5  The Claim (Q02\u2013Q04)")
    policy_cards(doc, group_ids("claim"))

    # ---------------- 6 grounding
    h1(doc, "6  Textual grounding (Q05)")
    lead(doc, "Three different questions concern the anchors. Only the second one is asked at Q05.", size=8.8, after=2)
    simple_table(doc, [6.2, 7.2, W - 13.4], ["Question", "Where it is judged", "Rules"], [
        ("Does the paper support the Claim?", "Q02, Q03 and Q06\u2013Q11, reading the paper in context", "GEN-2, CL-2"),
        ("Are the anchors enough to ground the Claim?", "Q05", "GR-1, GR-2, GR-5"),
        ("Do the anchors reproduce every detail of the Claim?", "Not asked", "GR-2"),
    ], tag_last=True)
    ds.para(doc, "", after=2)
    policy_cards(doc, group_ids("grounding"))

    h2(doc, "Checks for Q05, in order")
    caption(doc, "The checks are a reading aid. They do not say which rule wins when two conflict, for example a missing "
                 "quoted expression against the proposed threshold. That is part of the open question on In part.", before=0, after=3, keep=True)
    steps = [
        ("1", "Find each anchor on its page and read the passage around it.", "Agreed", "", "GR-1"),
        ("2", "Is part of the Claim missing only because the 50-word limit cut the sentence?", "Agreed",
         "Not a reason for In part by itself.", "GR-1"),
        ("3", "Is only a bibliographic reference missing?", "Provisional",
         "No penalty. A reference missing in the middle of an anchor is still open.", "GR-3"),
        ("4", "Does the Claim quote an expression that no anchor contains?", "Provisional",
         "In part. The outcome for CLM-0006-015 was agreed.", "GR-4"),
        ("5", "Is a whole sentence or concept of the Claim missing from the anchors?", "Open",
         "Say where it is found (passage, page, paper). Whether that is enough is undecided.", "GR-5, GR-6"),
        ("6", "Do the anchors show where the paper puts forward the Claim and its basis?", "Provisional",
         "Yes if they are sufficient, even if incomplete.", "GR-2"),
    ]
    t = ds.table(doc, [0.6, 7.4, 7.7, W - 15.7], header=["", "Check", "Current answer", "Rules"], size=8.3)
    for n, a, st, b, c in steps:
        def answer(cell, st=st, b=b):
            q = cell.paragraphs[0]
            ds.chip(q, st.upper(), size=6.8)
            if b:
                text(q, "  " + b, size=8.3)
        ds.add_row(t, [lambda c_, n=n: ds.style_run(c_.paragraphs[0].add_run(n), size=9, color=ds.NAVY, bold=True),
                       a, answer, lambda c_, c=c: tags(c_.paragraphs[0], [x.strip() for x in c.split(",")], size=7.6)])
    ds.keep_table_together(t)

    h2(doc, "Contested grounding cases")
    t = ds.table(doc, [2.3, 2.6, 7.4, 2.2, W - 14.5], header=["Claim", "Answers", "Final as written", "Status", "Rules"], size=8.1)
    for claim, rule in [("CLM-0006-004", "GR-4"), ("CLM-0006-015", "GR-4, GR-5"), ("CLM-0006-018", "GR-2"),
                        ("CLM-0009-006", "GR-1, GR-6"), ("CLM-0009-010", "GR-6"), ("CLM-0009-011", "GR-1, GR-6")]:
        r = reg.get(claim, "Q05")
        ds.add_row(t, [claim, r["split_stored"], short_final(r),
                       lambda c_, r=r: ds.chip(c_.paragraphs[0], r["status"], size=6.8),
                       lambda c_, rule=rule: tags(c_.paragraphs[0], [x.strip() for x in rule.split(",")], size=7.6)])

    # ---------------- 7 fields
    h1(doc, "7  Schema fields (Q06\u2013Q11)")
    box = ds.table(doc, [W], size=8.8, rules=False)

    def acc(cell):
        ds.shade(cell, ds.PANEL)
        q = cell.paragraphs[0]
        ds.style_run(q.add_run("Acceptable or best value?  "), size=9, color=ds.NAVY, bold=True)
        text(q, "Each field question asks whether the value is \u201ccorrectly assigned according to the schema "
                "definition\u201d. The team has not decided whether Yes means that the value is acceptable or that it is "
                "the best one. Until it does, answer No only when the assigned value cannot be defended, and name the "
                "value you would choose in the comment. For a Claim that mixes two types or bases, judge the dominant "
                "value.", size=8.8)
    ds.add_row(box, [acc])
    ds.para(doc, "", after=2)
    policy_cards(doc, group_ids("fields"))
    caption(doc, "For the Claim object values law and other, and for the Basis value literature, the 4.1 calibration text "
                 "departs from the frozen schema. This guide reads it as an interpretation of the schema, not a change to "
                 "it. Annex J sets the two texts side by side.", before=3)

    # ---------------- 8 concepts
    h1(doc, "8  Concepts (Q12\u2013Q14)")
    lead(doc, "The three Concept questions ask different things.", size=8.8, after=2)
    simple_table(doc, [3.6, 6.4, 4.8, W - 14.8], ["Question", "Ask", "Not a reason for No", "Rules"], [
        ("Q12 Does the assigned Concept fit?",
         "Is it a defensible label for what the Claim is about, even partly? Does it capture something real?",
         "Its Concept family. The Claim not naming it.", "CO-1, CO-2, CO-3"),
        ("Q13 Is the candidate needed?", "Could the existing vocabulary trace the Claim without it?",
         "That it fits. Fit is asked at Q12.", "CO-4"),
        ("Q14 Is a Concept missing?", "Is there a clear omission whose absence is felt?",
         "That some other relevant Concept could be added.", "CO-5"),
    ], size=8.3, tag_last=True)
    caption(doc, "In the SRC-0009 Finals many proposed Missing Concepts are called \u201creasonable\u201d. The annex records "
                 "them as considered reasonable, not as adopted or needed.")
    policy_cards(doc, group_ids("concepts"))

    # ---------------- 9 relations
    h1(doc, "9  Relations")
    lead(doc, "What to record in each situation:", size=8.8, after=2)
    t = ds.table(doc, [5.6, 1.9, 2.0, 2.0, W - 11.5], header=["Situation", "Type", "Grounding", "Direction", "Comment"], size=8.2)
    for row in [
        ("There is no meaningful relationship, so the relation should not exist", "No", "N/A", "N/A", "Say that the relation should not exist"),
        ("A relationship exists, but of another kind (for example compatible findings typed SUPPORTS)", "No", "N/A", "N/A", "Name the relationship you see"),
        ("Correct type, wrong direction", "Yes", "judge", "No", "Explain the reversed arrow"),
        ("Correct type, wrong grounding", "Yes", "No", "judge", "Say whether either source cites the other"),
        ("A correct SAME_AS relation", "Yes", "judge", "not asked", ""),
    ]:
        ds.add_row(t, [row[0], lambda c_, v=row[1]: ds.style_run(c_.paragraphs[0].add_run(v), size=8.2, bold=True),
                       row[2], row[3], row[4]])
    ds.keep_table_together(t)
    caption(doc, "The first two situations give the same answers, and only the comment tells them apart. The error "
                 "analysis of relations therefore depends on comments being written.")
    policy_cards(doc, group_ids("relations"))

    h2(doc, "Disputed relations")
    t = ds.table(doc, [4.2, 4.8, 4.6, W - 13.6], header=["Relation", "Type: Final as written", "Grounding and Direction", "Standing"], size=8)
    for src, tgt, standing in [
        ("CLM-0009-004", "CLM-0011-006", "Open. Tentative No; the Claims report parallel findings."),
        ("CLM-0009-004", "CLM-0016-004", "Open. The Final text is cut off."),
        ("CLM-0009-004", "CLM-0018-011", "Open. The Final reads \u201c??\u201d."),
        ("CLM-0009-006", "CLM-0008-009", "Type is a provisional No. The Direction Final reads N/A, but its own comment says No."),
        ("CLM-0009-012", "CLM-0016-007", "Provisional No with no reason given. Four of the seven evaluators answered Yes."),
        ("CLM-0009-013", "CLM-0019-009", "Open. The Final reads \u201c??\u201d on all three questions."),
    ]:
        rt = reg.get(src, "REL_TYPE", tgt)
        gr = reg.get(src, "REL_GROUNDING", tgt)
        di = reg.get(src, "REL_DIRECTION", tgt)
        typ = (rt["assigned"].split(" ")[0] if rt else (di or gr)["assigned"].split(" ")[0])
        if rt and rt["final_value"] == "No" and rt["status"] != "OPEN":
            absent = "Not applicable (type is No)"
        elif rt and rt["status"] == "OPEN":
            absent = "All seven agree; asked only if the type is Yes"
        else:
            absent = "All seven agree"

        def gd(cell, gr=gr, di=di, absent=absent):
            q = cell.paragraphs[0]
            ds.style_run(q.add_run("Grounding: "), size=7.8, color=ds.MUTED, bold=True)
            ds.style_run(q.add_run(short_final(gr) if gr else absent), size=7.8)
            q2 = cell.add_paragraph(); q2.paragraph_format.space_after = Pt(0)
            ds.style_run(q2.add_run("Direction: "), size=7.8, color=ds.MUTED, bold=True)
            ds.style_run(q2.add_run(short_final(di) if di else absent), size=7.8)
        ds.add_row(t, [f"{src} \u2192 {tgt}\n{typ} (inferred)", short_final(rt) + (f'\n[{rt["split_stored"]}]' if rt else ""),
                       gd, standing])
    caption(doc, "The open relations wait on the decision about parallel findings and attacks (D5).")

    # ---------------- 10 recall
    h1(doc, "10  Claim recall and restatements")
    lead(doc, "Vaclav argues, citing Quine, that turning a paper into a finite set of Claims is indeterminate, so two "
              "experts need not produce the same set. The proposal under discussion therefore does not measure recall in "
              "the usual sense.", size=8.8, after=3)
    simple_table(doc, [3.8, 6.0, W - 9.8], ["Measure", "What it needs", "In this evaluation"], [
        ("Conventional recall", "A fixed reference set of Claims for each paper", "Not available, and not sought"),
        ("Overall coverage", "Each evaluator's judgement of how completely the set represents the paper",
         "The recall scale (None / Some / Most / All), answered by everyone"),
        ("Proposed additions", "Missing Claims written as propositions, with a page",
         "Collected when recall is below All. They get no Final, by design."),
        ("Judging the additions", "Other evaluators judge whether each addition improves the set",
         "Proposed by Vaclav and Alessandro, not yet adopted or designed"),
    ], size=8.3)
    caption(doc, "For SRC-0006, four evaluators grouped restatements in four different ways.")
    policy_cards(doc, group_ids("recall"))

    # ---------------- 11 open decisions
    h1(doc, "11  Open decisions in detail", page_break=True)
    lead(doc, "Ordered by priority. No source assigns an owner to any decision.", size=8.8, after=3, color=ds.MUTED)
    t = ds.table(doc, [1.9, 8.6, W - 10.5], header=["", "Question and readings", "Cases, why it matters, what to decide"], size=8.1)
    for d in sorted(pol.OPEN_DECISIONS, key=lambda x: (x["priority"], int(x["id"][1:]))):
        def head(cell, d=d):
            q = cell.paragraphs[0]
            ds.style_run(q.add_run(d["id"]), size=10.5, color=ds.NAVY, bold=True)
            ds.bookmark(q, "dec_" + d["id"])
            q2 = cell.add_paragraph(); q2.paragraph_format.space_after = Pt(0.5)
            ds.style_run(q2.add_run(f'Priority {d["priority"]}'), size=7, color=ds.MUTED)
            tags(cell.add_paragraph(), d["policies"], size=7)

        def body(cell, d=d):
            q = cell.paragraphs[0]
            q.paragraph_format.space_after = Pt(1)
            ds.style_run(q.add_run(d["title"]), size=8.9, color=ds.NAVY, bold=True)
            q = cell.add_paragraph(); q.paragraph_format.space_after = Pt(1.5)
            text(q, d["question"], size=8.1)
            for s_ in d["interpretations"]:
                b = cell.add_paragraph(); b.paragraph_format.space_after = Pt(0.5)
                b.paragraph_format.left_indent = Cm(0.3); b.paragraph_format.first_line_indent = Cm(-0.3)
                text(b, "\u2013 " + s_, size=7.9)

        def side(cell, d=d):
            first = True
            if d["examples"]:
                q = cell.paragraphs[0]
                q.paragraph_format.space_after = Pt(1)
                ds.style_run(q.add_run("Cases  "), size=7.2, color=ds.BLUE, bold=True)
                ds.style_run(q.add_run(", ".join(d["examples"])), size=7.4, color=ds.MUTED)
                first = False
            for label, s_ in (("Why it matters", d["why"]), ("To decide", d["decide"]), ("Meanwhile", d["meanwhile"])):
                q = cell.paragraphs[0] if first else cell.add_paragraph()
                first = False
                q.paragraph_format.space_after = Pt(1)
                ds.style_run(q.add_run(label + "  "), size=7.2, color=ds.BLUE, bold=True)
                text(q, s_, size=7.9)
        ds.add_row(t, [head, body, side])

    # ---------------- 12 sources
    h1(doc, "12  Sources")
    lead(doc, "Each detailed entry ends with its sources. The keys are listed below. The annex reproduces every "
              "contested item of the Training report, each evaluator's review list, the contradictions found in the "
              "Finals, all reviewer comments and the quotations behind every rule.", size=8.6, after=3)
    short = [("M28", "Meeting, 28 Sep (instrument 4.0)"), ("M07", "Meeting, 7 Oct (4.1 Training answers)"),
             ("E08T", "Thiago, 8 Oct: calibration notes"), ("E08A", "Alessandro, 8 Oct: gates"),
             ("E09T", "Thiago, 9 Oct: Claim gate"), ("E09V", "Vaclav, 9 Oct: Finals SRC-0006; recall"),
             ("E11S", "Thibault, 11 Oct: model change"), ("E12T", "Thiago, 12 Oct: app ready"),
             ("E13V", "Vaclav, 13 Oct: resolve open points"), ("E13A", "Alessandro, 13 Oct: recall"),
             ("REP", "Training report, 14 Oct (Appendix B, Finals)"), ("RC#n", "Reviewer comment n (annex H)"),
             ("F:\u2026", "Final cell: Claim / question [/ target]"), ("EC:\u2026", "An evaluator's own comment in the report"),
             ("SPEC", "Instrument 4.1 code and calibration texts"), ("DEF", "Frozen schema shown to evaluators"),
             ("SUM", "Earlier summary (secondary only)"), ("", "")]
    t = ds.table(doc, [1.5, W / 2 - 1.5, 1.5, W / 2 - 1.5], size=7.8)
    for i in range(0, len(short), 2):
        (k1, v1), (k2, v2) = short[i], short[i + 1]
        ds.add_row(t, [lambda c_, k=k1: ds.style_run(c_.paragraphs[0].add_run(k), size=7.8, color=ds.NAVY, bold=True), v1,
                       lambda c_, k=k2: ds.style_run(c_.paragraphs[0].add_run(k), size=7.8, color=ds.NAVY, bold=True), v2])
    caption(doc, "Meeting references give the transcript timestamp. In the 28 September transcript one room microphone is "
                 "labelled \u201cGiuseppe Pisano\u201d for several people, so attributions there are uncertain. The email "
                 "thread is in Calibration/email-conversation.txt. Annex A describes each source in full.", before=3)

    doc.core_properties.title = TITLE
    doc.core_properties.subject = SCOPE
    doc.core_properties.author = "SLiM Brain evaluation team"
    doc.save(out)


if __name__ == "__main__":
    build(json.loads((pathlib.Path(sys.argv[1]) / "register.json").read_text(encoding="utf-8")), sys.argv[2])
    print("written", sys.argv[2])
