"""Does the frozen instrument still say what the Design review agreed?

`he_criteria_v3.json` is the evaluation instrument: every answer in the study is
interpreted against its wording. The wording was settled page by page in
`Design/*.md`, so drift between the two is a silent change to the experiment.

This module makes the relationship checkable in both directions:

* every **question** must appear verbatim as a proposed question in the Design
  documents — no paraphrase, however well meant;
* every **definition sentence** must either appear verbatim in one of the agreed
  sources, or be declared in that criterion's ``derived`` list, which records the
  guidance that was inferred rather than quoted.

The agreed sources for definition prose are the Design documents **and the two
layers v3 sits on** — the 2026-09-07 calibration file and the verbatim workbook
extract. Prose carried forward from those was agreed earlier and is not an
invention of this layer; only text that appears in none of them is.

An undeclared sentence fails the check. That is the point: prose can still be
added, but not without saying so.
"""
from __future__ import annotations

import functools
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
DESIGN_DIR = ROOT / "Design"
DATA = ROOT / "app" / "data"
V3 = DATA / "he_criteria_v3.json"

#: The layers v3 inherits from. Text repeated from these was agreed earlier.
INHERITED = (DATA / "he_criteria_v2.json", DATA / "he_criteria.json")

#: Fragments shorter than this are punctuation noise, not prose worth pinning.
MIN_SENTENCE = 25


def normalise(text: str) -> str:
    """Strip Markdown emphasis and collapse whitespace, so wrapping cannot matter."""
    text = re.sub(r"[`*>#|]", "", text)
    return re.sub(r"\s+", " ", text).strip().lower()


@functools.lru_cache(maxsize=1)
def design_text() -> str:
    return normalise("\n".join(p.read_text(encoding="utf-8")
                               for p in sorted(DESIGN_DIR.glob("*.md"))))


@functools.lru_cache(maxsize=1)
def agreed_text() -> str:
    """Design review plus the earlier instrument layers, as one normalised corpus."""
    inherited = "\n".join(
        json.dumps(json.loads(p.read_text(encoding="utf-8")), ensure_ascii=False)
        .replace("\\n", "\n")
        for p in INHERITED if p.exists()
    )
    return design_text() + " " + normalise(inherited)


@functools.lru_cache(maxsize=1)
def design_questions() -> frozenset[str]:
    """Every bolded blockquote line in the Design docs — a proposed question."""
    raw = "\n".join(p.read_text(encoding="utf-8")
                    for p in sorted(DESIGN_DIR.glob("*.md")))
    return frozenset(
        normalise(q).rstrip("?")
        for q in re.findall(r"^>\s*\*\*(.+?)\*\*\s*$", raw, re.M)
    )


def sentences(text: str) -> list[str]:
    """Prose units of a criterion definition, as written in the JSON."""
    parts = re.split(r"(?<=[.;:])\s+|\n", text or "")
    return [p.strip() for p in parts if len(normalise(p)) >= MIN_SENTENCE]


def is_verbatim(sentence: str) -> bool:
    return normalise(sentence).rstrip(".;:") in agreed_text()


def question_matches_design(question: str) -> bool:
    return normalise(question).rstrip("?") in design_questions()


@functools.lru_cache(maxsize=1)
def criteria() -> dict:
    data = json.loads(V3.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def undeclared(entry: dict) -> list[str]:
    """Definition sentences that are neither verbatim Design nor declared derived."""
    declared = {normalise(d) for d in entry.get("derived", [])}
    out = []
    for field in ("check", "definition"):
        for sentence in sentences(entry.get(field, "")):
            if is_verbatim(sentence) or normalise(sentence) in declared:
                continue
            out.append(sentence)
    return out


def stale_declarations(entry: dict) -> list[str]:
    """Declared sentences that are no longer in the criterion, or now verbatim."""
    present = {normalise(s) for field in ("check", "definition")
               for s in sentences(entry.get(field, ""))}
    return [d for d in entry.get("derived", [])
            if normalise(d) not in present or is_verbatim(d)]
