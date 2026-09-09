"""Extract the HE criteria text verbatim from HE_review_form.xlsx.

The workbook is the source of truth for criterion wording and schema
definitions. This writes app/data/he_criteria.json, which the Streamlit app
loads. Re-run whenever the workbook changes.

    python app/tools/extract_criteria.py
"""
from __future__ import annotations

import json
import pathlib
import re

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKBOOK = ROOT / "HE_review_form.xlsx"
OUT = ROOT / "app" / "data" / "he_criteria.json"

# sheet -> object level the criteria on it belong to
SHEETS = {"Source": "source", "CLAIM-TEMPLATE": "claim", "Dataset": "dataset"}

SPLIT = re.compile(r"\n\s*Schema definition\b", re.I)
CRITERION_ID = re.compile(r"^HE-\d+(\.\w+)?$")


def _clean(value) -> str:
    if value is None:
        return ""
    return re.sub(r"[ \t]+\n", "\n", str(value)).strip()


def extract() -> dict:
    wb = openpyxl.load_workbook(WORKBOOK)
    out: dict[str, dict] = {}

    for sheet, level in SHEETS.items():
        ws = wb[sheet]
        for row in ws.iter_rows(values_only=True):
            cells = [_clean(c) for c in row]
            # criterion rows look like: n | HE-xx | field | what to check | ...
            ids = [c for c in cells[:3] if CRITERION_ID.match(c)]
            if not ids:
                continue
            crit_id = ids[0]
            col = cells.index(crit_id)
            field = cells[col + 1] if col + 1 < len(cells) else ""
            what = cells[col + 2] if col + 2 < len(cells) else ""

            parts = SPLIT.split(what, maxsplit=1)
            check = parts[0].strip()
            definition = ""
            if len(parts) > 1:
                definition = ("Schema definition" + parts[1]).strip()

            out[f"{level}:{crit_id}"] = {
                "criterion_id": crit_id,
                "level": level,
                "field": field,
                "check": check,
                "definition": definition,
            }

    # HE-20.b and HE-18.3 / HE-19.3 are follow-ups with no schema definition;
    # they are still captured above because they carry an HE- id.
    return out


def main() -> None:
    data = extract()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {len(data)} criteria")
    for key in sorted(data):
        print(" ", key, "|", data[key]["field"][:50])


if __name__ == "__main__":
    main()
