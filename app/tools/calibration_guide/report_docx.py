"""Read the annotated Training report (.docx) without losing its structure.

Plain-text extraction drops the facts the calibration register depends on:
which cell a reviewer comment is attached to, which cells were marked yellow
by hand, and where a cell's answer ends and its comment begins. This module
reads ``word/document.xml`` and the comment parts directly.

Colours: the report generator (``training_report/build_report.js``) fills a
minority answer with ``FCE4D6`` and a tie with ``FFF2CC``. ``FFFF00`` fills and
yellow run highlights are never produced by the generator, so they are manual
marks added by reviewers.
"""
from __future__ import annotations

import re
import zipfile

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{%s}" % W_NS
W14 = "{http://schemas.microsoft.com/office/word/2010/wordml}"
W15 = "{http://schemas.microsoft.com/office/word/2012/wordml}"

EVALUATORS = ["Francesca", "Thibault", "Thiago", "Alessandro", "Giuseppe", "Giovanni", "Vaclav"]
ITEM_HEADER = ["Claim", "Question", "Assigned", *EVALUATORS, "Final"]
MINORITY, TIE, MANUAL_YELLOW = "FCE4D6", "FFF2CC", "FFFF00"


def _text(el) -> str:
    """Run text, with line breaks kept: Missing-Concept cells list one Concept per line."""
    out = []
    for x in el.iter(W + "t", W + "br", W + "cr", W + "tab"):
        if x.tag == W + "t":
            out.append(x.text or "")
        elif x.tag == W + "tab":
            out.append("\t")
        else:
            out.append("\n")
    return "".join(out)


def _paras(cell) -> list[str]:
    return [_text(p) for p in cell.findall(".//" + W + "p")]


def _cell(cell) -> dict:
    fills = {s.get(W + "fill") for s in cell.iter(W + "shd")} - {None, "auto"}
    return {
        "paras": _paras(cell),
        "minority": MINORITY in fills,
        "tie": TIE in fills,
        "manual_yellow": MANUAL_YELLOW in fills
        or any(h.get(W + "val") == "yellow" for h in cell.iter(W + "highlight")),
        "comment_ids": [c.get(W + "id") for c in cell.iter(W + "commentRangeStart")],
    }


def read_comments(z: zipfile.ZipFile) -> dict[str, dict]:
    """Word comments by id, with author, date, full text and reply parent."""
    root = etree.fromstring(z.read("word/comments.xml"))
    parent_of = {}
    if "word/commentsExtended.xml" in z.namelist():
        for e in etree.fromstring(z.read("word/commentsExtended.xml")):
            parent_of[e.get(W15 + "paraId")] = e.get(W15 + "paraIdParent")
    out, by_para = {}, {}
    for c in root.findall(W + "comment"):
        ps = c.findall(".//" + W + "p")
        cid = c.get(W + "id")
        last_para = ps[-1].get(W14 + "paraId") if ps else None
        by_para[last_para] = cid
        out[cid] = {
            "id": cid,
            "author": c.get(W + "author"),
            "date": (c.get(W + "date") or "")[:10],
            "text": "\n".join(_text(p) for p in ps).strip(),
            "_para": last_para,
        }
    for c in out.values():
        parent = parent_of.get(c.pop("_para"))
        c["reply_to"] = by_para.get(parent) if parent else None
    return out


def read_report(path: str) -> dict:
    """Item rows of Appendix B, Claim statements, and every anchored comment."""
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read("word/document.xml"))
    comments = read_comments(z)
    body = doc.find(W + "body")

    rows, statements, anchored = [], {}, []
    pending_statement = None
    for t in body.iter(W + "tbl"):
        trs = t.findall(W + "tr")
        header = [_text(c) for c in trs[0].findall(W + "tc")]
        if header == ITEM_HEADER:
            first_id = _paras(trs[1].findall(W + "tc")[0])[0] if len(trs) > 1 else ""
            for j, c in enumerate(trs[0].findall(W + "tc")):
                for s in c.iter(W + "commentRangeStart"):
                    anchored.append({"comment_id": s.get(W + "id"), "where": "Appendix B header",
                                     "row": f"header of the item table of {first_id}", "column": ITEM_HEADER[j]})
            for order, tr in enumerate(trs[1:]):
                cells = [_cell(c) for c in tr.findall(W + "tc")]
                head = cells[0]["paras"]
                ident, section = head[0], (head[1] if len(head) > 1 else "")
                if pending_statement and ident.startswith("CLM-"):
                    statements.setdefault(ident, pending_statement)
                rows.append({
                    "id": ident,
                    "section": section,
                    "question": " ".join(cells[1]["paras"]).strip(),
                    "assigned": " ".join(cells[2]["paras"]).strip(),
                    "evaluators": {
                        name: {
                            "answer": cells[3 + k]["paras"][0].strip() if cells[3 + k]["paras"] else "",
                            "comment": "\n".join(p for p in cells[3 + k]["paras"][1:] if p.strip()),
                            "minority": cells[3 + k]["minority"],
                            "tie": cells[3 + k]["tie"],
                            "comment_ids": cells[3 + k]["comment_ids"],
                        }
                        for k, name in enumerate(EVALUATORS)
                    },
                    "final_paras": [p for p in cells[10]["paras"]],
                    "final": " ".join(p.strip() for p in cells[10]["paras"] if p.strip()),
                    "manual_yellow": any(c["manual_yellow"] for c in cells),
                    "manual_yellow_cells": [ITEM_HEADER[i] for i, c in enumerate(cells) if c["manual_yellow"]],
                    "comment_ids": {ITEM_HEADER[i]: c["comment_ids"] for i, c in enumerate(cells) if c["comment_ids"]},
                })
            pending_statement = None
        elif len(trs) == 1 and len(trs[0].findall(W + "tc")) == 1:
            # The Claim statement box printed above each item table.
            pending_statement = header[0]
        else:
            # Narrative tables (Sections 4-8): keep comments with their row context.
            for tr in trs:
                cells = tr.findall(W + "tc")
                for j, c in enumerate(cells):
                    for s in c.iter(W + "commentRangeStart"):
                        anchored.append({
                            "comment_id": s.get(W + "id"),
                            "where": "narrative table",
                            "row": " | ".join(_text(x) for x in cells)[:300],
                            "column": header[j] if j < len(header) else f"col{j}",
                        })
    # Comments anchored in ordinary paragraphs (headings, body text).
    for p in body.iter(W + "p"):
        if any(a.tag == W + "tbl" for a in p.iterancestors()):
            continue
        for s in p.iter(W + "commentRangeStart"):
            anchored.append({"comment_id": s.get(W + "id"), "where": "paragraph", "row": _text(p)[:200], "column": ""})
    for r in rows:
        for col, ids in r["comment_ids"].items():
            for cid in ids:
                anchored.append({"comment_id": cid, "where": "Appendix B", "row": f'{r["id"]} | {r["question"]} | {r["assigned"]}', "column": col})
    return {"rows": rows, "statements": statements, "comments": comments, "anchored": anchored}


def doc_text(path: str) -> str:
    """All paragraph text of a .docx, one paragraph per line (tables included)."""
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read("word/document.xml"))
    return "\n".join(_text(p) for p in doc.iter(W + "p"))


def squash(s: str) -> str:
    """Normalise quotes, dashes and whitespace for verbatim-quote checks."""
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("…", "...").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip().lower()
