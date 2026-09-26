"""Freeze the schema and skill definitions shown to evaluators.

The evaluation shows the Brain's own definitions beside each question, word for
word. They are extracted here, once, from the snapshot's `schema/` and from the
Brain's skills, and written to `app/data/definitions_v4.json`. The running app
reads only that file, so the wording shown during a round cannot change because
the Brain repository moves on.

    python app/tools/freeze_definitions.py                 # write the file
    python app/tools/freeze_definitions.py --check         # compare, write nothing
    python app/tools/freeze_definitions.py --skills PATH   # skills directory

Every extracted passage is a verbatim slice of its source file. Nothing is
paraphrased, completed or reworded: where the Brain gives no definition, none
is added. The only transformation happens at display time, where backtick
markup is dropped so no schema name is shown in code typography.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

APP = pathlib.Path(__file__).resolve().parents[1]
ROOT = APP.parent
sys.path.insert(0, str(APP))

from brain import brain_dir  # noqa: E402

OUT = APP / "data" / "definitions_v4.json"
DEFAULT_SKILLS = ROOT.parent / "SLiM_Brain" / ".claude" / "skills"
SKILLS_USED = ("create-edges",)

FIELD = re.compile(r"^- \*\*`([a-z_]+)`\*\*(?:, \*\*`[a-z_]+`\*\*)?\s*(?:—\s*)?(.*)$")
CATEGORY = re.compile(r"^`([^`]+)`:\s*(.*)$")


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_paragraph(text: str) -> str:
    """The paragraph under the H1 heading: the node's own definition."""
    lines = text.splitlines()
    out, started = [], False
    for line in lines[1:]:
        if not line.strip():
            if started:
                break
            continue
        if line.startswith("#"):
            break
        started = True
        out.append(line)
    return "\n".join(out).strip()


def fields(text: str) -> dict[str, dict]:
    """Every `- **`field`** — text` bullet with its indented sub-bullets."""
    result: dict[str, dict] = {}
    current = None
    for line in text.splitlines():
        match = FIELD.match(line)
        if match:
            current = match.group(1)
            result[current] = {"text": match.group(2).rstrip(), "items": []}
            continue
        if current is None:
            continue
        if line.startswith("  - ") or line.startswith("    - "):
            item = line.strip()[2:].rstrip()
            category = CATEGORY.match(item)
            if category:
                result[current]["items"].append(
                    {"value": category.group(1), "text": category.group(2)})
            else:
                result[current]["items"].append({"value": "", "text": item})
            continue
        if line.startswith("#") or (line and not line.startswith(" ")):
            current = None
    return result


def pipe_values(text: str) -> list[str]:
    """`a` | `b` | `c` enumerations inside a field text, in order."""
    match = re.search(r"((?:`[^`]+`\s*\|\s*)+`[^`]+`)", text)
    return re.findall(r"`([^`]+)`", match.group(1)) if match else []


def edge_types(text: str) -> list[dict]:
    """The Claim-to-Claim rows of the edge table, `when` column verbatim."""
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and cells[1] == "Claim" and cells[2] == "Claim":
            rows.append({"value": cells[0], "text": cells[4]})
    return rows


def grid(text: str) -> dict[str, list[str]]:
    block = re.search(r"```yaml\n(.*?)```", text, re.S)
    out: dict[str, list[str]] = {}
    family = None
    for line in (block.group(1) if block else "").splitlines():
        if re.match(r"^[a-z_]+:\s*$", line):
            family = line.strip().rstrip(":")
            out[family] = []
        elif line.strip().startswith("- CPT-") and family:
            out[family].append(line.strip()[2:].strip())
    return out


def grounding_rule(skill_text: str) -> dict:
    """The grounding bullets of create-edges, verbatim with their sub-bullets."""
    lines = skill_text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("- **`extracted`**"))
    end = next(i for i, l in enumerate(lines) if l.startswith("- **`inferred`**"))
    extracted_head = lines[start]
    extracted_items = [l.strip()[2:] for l in lines[start + 1:end]
                       if l.strip().startswith("- ")]
    inferred = lines[end]
    lead = lines[start - 1] if start and lines[start - 1].strip() else ""
    head = re.match(r"^- \*\*`extracted`\*\*\s*(.*)$", extracted_head).group(1)
    tail = re.match(r"^- \*\*`inferred`\*\*\s*(.*)$", inferred).group(1)
    return {
        "lead": lead,
        "items": [
            {"value": "extracted", "text": head, "sub": extracted_items},
            {"value": "inferred", "text": tail, "sub": []},
        ],
        "verbatim": "\n".join(lines[start:end + 1]),
    }


def entry(label: str, source: str, text: str, items=None, **extra) -> dict:
    record = {"label": label, "source": source, "text": text}
    if items is not None:
        record["items"] = items
    record.update(extra)
    return record


def build(schema_dir: pathlib.Path, skills_dir: pathlib.Path) -> dict:
    claim_md = (schema_dir / "claim.md").read_text(encoding="utf-8")
    dataset_md = (schema_dir / "dataset.md").read_text(encoding="utf-8")
    edge_md = (schema_dir / "edge.md").read_text(encoding="utf-8")
    concept_md = (schema_dir / "concept.md").read_text(encoding="utf-8")
    index_md = (schema_dir / "__index__.md").read_text(encoding="utf-8")
    create_edges = (skills_dir / "create-edges" / "SKILL.md").read_text(encoding="utf-8")

    claim = fields(claim_md)
    dataset = fields(dataset_md)
    edge = fields(edge_md)
    concept = fields(concept_md)

    version = re.search(r"schema_version:\s*([0-9A-Za-z.\-]+)", index_md).group(1)
    grounding = grounding_rule(create_edges)

    entries = {
        "claim.node": entry("Claim", "schema/claim.md", first_paragraph(claim_md)),
        "claim.statement": entry("Statement", "schema/claim.md", claim["statement"]["text"]),
        "claim.anchors": entry("Anchors", "schema/claim.md", claim["anchors"]["text"],
                               claim["anchors"]["items"]),
        "claim.claim_object": entry("Claim object", "schema/claim.md",
                                    claim["claim_object"]["text"],
                                    claim["claim_object"]["items"]),
        "claim.claim_type": entry("Claim type", "schema/claim.md",
                                  claim["claim_type"]["text"],
                                  claim["claim_type"]["items"]),
        "claim.basis": entry("Basis", "schema/claim.md", claim["basis"]["text"],
                             claim["basis"]["items"]),
        "claim.claim_jurisdiction": entry("Claim jurisdiction", "schema/claim.md",
                                          claim["claim_jurisdiction"]["text"],
                                          claim["claim_jurisdiction"]["items"]),
        "claim.legal_reference": entry("Legal reference", "schema/claim.md",
                                       claim["legal_reference"]["text"]),
        "claim.temporal_reference": entry("Temporal reference", "schema/claim.md",
                                          claim["temporal_reference"]["text"]),
        "dataset.node": entry("Dataset", "schema/dataset.md", first_paragraph(dataset_md)),
        "dataset.name": entry("Name", "schema/dataset.md", dataset["name"]["text"]),
        "dataset.introduced_by": entry("Introduced by", "schema/dataset.md",
                                       dataset["introduced_by"]["text"]),
        "dataset.language": entry("Language", "schema/dataset.md",
                                  dataset["language"]["text"]),
        "dataset.jurisdiction": entry("Jurisdiction", "schema/dataset.md",
                                      dataset["jurisdiction"]["text"]),
        "dataset.description": entry("Description", "schema/dataset.md",
                                     dataset["description"]["text"]),
        "dataset.availability": entry(
            "Availability", "schema/dataset.md", dataset["availability"]["text"],
            [{"value": v, "text": ""} for v in pipe_values(dataset["availability"]["text"])]),
        "edge.relation_type": entry("Relation type", "schema/edge.md",
                                    edge["type"]["text"], edge_types(edge_md)),
        "edge.note": entry("Relation Note", "schema/edge.md", edge["note"]["text"]),
        "edge.grounding": entry(
            "Grounding", ".claude/skills/create-edges/SKILL.md", grounding["lead"],
            grounding["items"], verbatim=grounding["verbatim"]),
        "concept.node": entry("Concept", "schema/concept.md", first_paragraph(concept_md)),
        "concept.status": entry("Concept status", "schema/concept.md",
                                concept["status"]["text"], concept["status"]["items"]),
        "concept.concept_type": entry(
            "Concept family", "schema/concept.md", concept["concept_type"]["text"],
            [{"value": v, "text": ""} for v in pipe_values(concept["concept_type"]["text"])]),
        "concept.definition": entry("Concept definition", "schema/concept.md",
                                    concept["definition"]["text"]),
    }

    sources = {f"schema/{p.name}": sha(p) for p in sorted(schema_dir.glob("*.md"))}
    for name in SKILLS_USED:
        sources[f".claude/skills/{name}/SKILL.md"] = sha(skills_dir / name / "SKILL.md")

    payload = {
        "canonical_schema_version": version,
        "source_hashes": sources,
        "concept_grid": grid(concept_md),
        "entries": entries,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    payload["definitions_id"] = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--schema", type=pathlib.Path, default=brain_dir() / "schema")
    parser.add_argument("--skills", type=pathlib.Path, default=DEFAULT_SKILLS)
    parser.add_argument("--check", action="store_true",
                        help="report whether the frozen file is current; write nothing")
    args = parser.parse_args()

    payload = build(args.schema, args.skills)
    rendered = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current == rendered:
            print(f"definitions are current ({payload['definitions_id']})")
            return 0
        print("definitions differ from the schema and skills on disk")
        return 1
    OUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} · definitions_id {payload['definitions_id']} "
          f"· schema {payload['canonical_schema_version']} · {len(payload['entries'])} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
