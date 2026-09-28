"""Read-only access to the Brain snapshot under evaluation.

The Brain data model, its wiki projections and this interface are kept apart.
Nothing here writes to the Brain: corrections and proposals made by evaluators
belong to evaluation storage, never to these files.

Canonical stores  : wiki/claims/claims.jsonl, wiki/graph/edges.jsonl, wiki/runs.jsonl
Entity frontmatter: wiki/sources/*.md, wiki/concepts/*.md, wiki/datasets/*.md
Schema            : schema/*.md (hashed for provenance, never parsed for wording
                    at runtime — the wording shown is frozen in
                    data/definitions_v4.json)

Page frontmatter is read the way the Brain's own tooling reads it
(`tools/gate.py::frontmatter`): flat ``key: value`` lines and inline lists, not
YAML. Several Dataset pages carry an unquoted colon inside `description`, which a
YAML parser rejects and the Brain's format accepts.
"""
from __future__ import annotations

import collections
import dataclasses
import functools
import hashlib
import json
import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: The snapshot directory. Overridable so tests can point the adapter at a
#: mutated copy without touching the real one.
ENV_BRAIN_DIR = "HE_BRAIN_DIR"


def brain_dir() -> pathlib.Path:
    configured = os.environ.get(ENV_BRAIN_DIR)
    return pathlib.Path(configured).resolve() if configured else ROOT / "brain"


# Claim-to-Claim edge types (schema/edge.md). SAME_AS also exists between
# Sources; only the Claim-to-Claim form is evaluated.
CLAIM_EDGE_TYPES = ("SUPPORTS", "ATTACKS", "SAME_AS")
EDGE_TYPES = ("CITES", "SAME_AS", "SUPPORTS", "ATTACKS")
GROUNDINGS = ("extracted", "inferred")

#: The six Concept families of schema/concept.md, in the order the grid lists them.
CONCEPT_FAMILIES = (
    "legal_task", "technical_task", "technique_class", "normative_concern",
    "interpretation_object_type", "interpretation_canon",
)
CONCEPT_STATUSES = ("anchor", "candidate", "emergent")

CLAIM_ID = re.compile(r"^CLM-\d{4}-\d{3}$")


# ------------------------------------------------------------- frontmatter
def _parse_value(raw: str):
    value = raw.strip()
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(v) for v in parsed]
        except json.JSONDecodeError:
            pass
        inner = value[1:-1].strip()
        return [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
    return value.strip("'\"")


def parse_frontmatter(text: str) -> dict | None:
    """The page's frontmatter as a mapping, or None when it has none.

    Mirrors the Brain's reader: a line starting at column 0 with ``key:`` sets a
    key to the rest of the line; ``- item`` lines extend the previous key as a
    list. Nothing else is interpreted.
    """
    match = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    if not match:
        return None
    data: dict = {}
    current = None
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and current is not None and line != line.lstrip():
            if not isinstance(data.get(current), list):
                data[current] = []
            data[current].append(stripped[2:].strip().strip("'\""))
            continue
        if line != line.lstrip() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key.strip()):
            continue
        current = key.strip()
        data[current] = _parse_value(value) if value.strip() else ""
    return data


def _body(text: str) -> str:
    match = re.match(r"---\r?\n.*?\r?\n---\s*\n", text, re.S)
    return text[match.end():] if match else text


def _jsonl(path: pathlib.Path, problems: list) -> list[dict]:
    rows = []
    if not path.exists():
        problems.append((path.name, "file is missing"))
        return rows
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as error:
            problems.append((f"{path.name}:{number}", f"malformed JSON: {error}"))
    return rows


def as_list(value) -> list:
    """A field the schema allows as one value or a list."""
    if value in (None, "", []):
        return []
    return list(value) if isinstance(value, list) else [value]


# ------------------------------------------------------------ identity
def runtime_files(root: pathlib.Path | None = None) -> list[pathlib.Path]:
    """The Brain files the app reads, in a stable order.

    Deliberately excludes log.md, index.md, coverage/structure/usage reports,
    absences, references and PDFs: none of them is evaluation input, and their
    prose changes between Brain runs. `runs.jsonl` and `schema/` are included
    because they say which schema the records were written under.
    """
    base = root or brain_dir()
    wiki = base / "wiki"
    files: list[pathlib.Path] = []
    files.extend(sorted((wiki / "sources").glob("*.md")))
    files.extend(sorted((wiki / "concepts").glob("*.md")))
    files.extend(sorted((wiki / "datasets").glob("*.md")))
    files.append(wiki / "claims" / "claims.jsonl")
    files.append(wiki / "graph" / "edges.jsonl")
    files.append(wiki / "runs.jsonl")
    files.extend(sorted((base / "schema").glob("*.md")))
    return files


def compute_snapshot(root: pathlib.Path | None = None) -> str:
    """SHA-256 over the runtime files, path and content alike.

    A rename changes the snapshot even when the bytes do not. Every review
    records it, so it is always known which artifact was judged.
    """
    base = root or brain_dir()
    overall = hashlib.sha256()
    for path in runtime_files(base):
        if not path.exists():
            continue
        per_file = hashlib.sha256(path.read_bytes()).hexdigest()
        overall.update(path.relative_to(base).as_posix().encode("utf-8"))
        overall.update(b"\0")
        overall.update(per_file.encode("ascii"))
        overall.update(b"\n")
    return overall.hexdigest()


def schema_file_hashes(root: pathlib.Path | None = None) -> dict[str, str]:
    base = root or brain_dir()
    return {path.relative_to(base).as_posix():
            hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((base / "schema").glob("*.md"))}


def canonical_schema_version(root: pathlib.Path | None = None) -> str:
    """The version the Brain repository itself declares in schema/__index__.md.

    Deliberately not derived from run history: a snapshot may hold records
    written under several runs, each recording the version in force at the time.
    """
    index = (root or brain_dir()) / "schema" / "__index__.md"
    if not index.exists():
        return ""
    match = re.search(r"schema_version:\s*([0-9A-Za-z.\-]+)",
                      index.read_text(encoding="utf-8"))
    return match.group(1) if match else ""


class SnapshotMismatch(RuntimeError):
    """The Brain on disk is not the one the round was bootstrapped against."""


# ------------------------------------------------------------ display names
#: Letters kept upper-case when an id is turned into a name. Fixed, so the same
#: id always yields the same name.
ACRONYMS = {"ai": "AI", "llm": "LLM", "llms": "LLMs", "nlp": "NLP", "irac": "IRAC",
            "gdpr": "GDPR", "rag": "RAG", "eu": "EU", "ml": "ML", "qa": "QA",
            "msme": "MSME", "vat": "VAT"}


def concept_label(concept_id: str) -> str:
    """`CPT-access-to-justice` -> `Access to justice`.

    The Concept schema has no label field and the wiki title is the id, so the
    name is derived from the id — the same way everywhere.
    """
    words = concept_id.removeprefix("CPT-").split("-")
    out = [ACRONYMS.get(w, w) for w in words if w]
    if out and out[0] == words[0]:
        out[0] = out[0][:1].upper() + out[0][1:]
    return " ".join(out)


def family_label(family: str) -> str:
    return family.replace("_", " ").capitalize()


def pdf_name(source: dict) -> str:
    """The corpus file an evaluator's PDF is named after (`SRC-0002.pdf`)."""
    name = pathlib.PurePosixPath(str(source.get("file") or "")).name
    return name[:-3] + ".pdf" if name.endswith(".md") else name


# ------------------------------------------------------------------ Brain
@dataclasses.dataclass(frozen=True)
class Brain:
    root: pathlib.Path
    sources: dict[str, dict]
    claims: dict[str, dict]
    concepts: dict[str, dict]
    datasets: dict[str, dict]
    edges: list[dict]
    runs: list[dict]
    source_bodies: dict[str, str]
    concept_bodies: dict[str, str]
    dataset_bodies: dict[str, str]
    raw_pages: dict                 # (kind, id) -> the page's exact file text
    load_problems: tuple            # (where, what) — surfaced by the preflight
    snapshot_id: str

    # ---- identity ------------------------------------------------------
    @property
    def source_ids(self) -> list[str]:
        return sorted(self.sources)

    @property
    def short_snapshot(self) -> str:
        return self.snapshot_id[:16]

    @property
    def run_ids(self) -> list[str]:
        return [str(r.get("id")) for r in self.runs if r.get("id")]

    def run_schema_versions(self) -> dict[str, str]:
        """Each run with the schema version it recorded, in file order."""
        return {str(r.get("id")): str(r.get("schema_version") or "")
                for r in self.runs if r.get("id")}

    @property
    def canonical_schema_version(self) -> str:
        return canonical_schema_version(self.root)

    def schema_hashes(self) -> dict[str, str]:
        return schema_file_hashes(self.root)

    # ---- sources -------------------------------------------------------
    def source(self, source_id: str) -> dict:
        return self.sources.get(source_id, {})

    def source_body(self, source_id: str) -> str:
        return self.source_bodies.get(source_id, "")

    def raw_page(self, kind: str, identifier: str) -> str:
        """The wiki page exactly as it is on disk, frontmatter included."""
        return self.raw_pages.get((kind, identifier), "")

    def label(self, source_id: str) -> str:
        """`SRC-0006 — Title`: how a paper is named everywhere in the UI."""
        return f"{source_id} — {self.source(source_id).get('title', '')}"

    def pdf_name(self, source_id: str) -> str:
        return pdf_name(self.source(source_id))

    def source_of_claim(self, claim_id: str) -> str:
        return str(self.claims.get(claim_id, {}).get("source", ""))

    # ---- claims --------------------------------------------------------
    def claims_of(self, source_id: str) -> list[dict]:
        rows = [c for c in self.claims.values() if c.get("source") == source_id]
        return sorted(rows, key=lambda c: c["id"])

    def claim(self, claim_id: str) -> dict:
        return self.claims.get(claim_id, {})

    # ---- concepts ------------------------------------------------------
    def concept(self, concept_id: str) -> dict:
        return self.concepts.get(concept_id, {})

    def concept_body(self, concept_id: str) -> str:
        return self.concept_bodies.get(concept_id, "")

    def concepts_of_claim(self, claim_id: str) -> list[str]:
        return [str(c) for c in as_list(self.claim(claim_id).get("concepts"))]

    def candidates_of_claim(self, claim_id: str) -> list[str]:
        """Assigned Concepts whose status is candidate (Question 13)."""
        return [c for c in self.concepts_of_claim(claim_id)
                if self.concept(c).get("status") == "candidate"]

    def group_by_family(self, concept_ids) -> dict[str, list[str]]:
        """Concept ids under the six families, in grid order; unknown last."""
        groups: dict[str, list[str]] = collections.OrderedDict(
            (family, []) for family in CONCEPT_FAMILIES)
        for concept_id in concept_ids:
            family = str(self.concept(concept_id).get("concept_type") or "")
            groups.setdefault(family, []).append(concept_id)
        return groups

    def vocabulary(self, grid: dict[str, list[str]]) -> list[dict]:
        """Every Concept an evaluator may name as missing (Question 14).

        The Concept pages of this snapshot, plus anchors of the frozen grid that
        have no page yet. A grid-only anchor has no definition: none is invented.
        """
        rows = {}
        for concept_id, concept in self.concepts.items():
            rows[concept_id] = {
                "id": concept_id, "label": concept_label(concept_id),
                "family": str(concept.get("concept_type") or ""),
                "status": str(concept.get("status") or ""),
                "definition": str(concept.get("definition") or ""),
                "has_page": True,
            }
        for family, ids in grid.items():
            for concept_id in ids:
                rows.setdefault(concept_id, {
                    "id": concept_id, "label": concept_label(concept_id),
                    "family": family, "status": "anchor", "definition": "",
                    "has_page": False,
                })
        return sorted(rows.values(), key=lambda r: r["label"].lower())

    # ---- datasets ------------------------------------------------------
    def dataset(self, dataset_id: str) -> dict:
        return self.datasets.get(dataset_id, {})

    def dataset_body(self, dataset_id: str) -> str:
        return self.dataset_bodies.get(dataset_id, "")

    def dataset_ids_of(self, source_id: str) -> list[str]:
        """The Datasets the Claims of this Source rest on (Claim `datasets`)."""
        ids = {str(d) for claim in self.claims_of(source_id)
               for d in as_list(claim.get("datasets"))}
        return sorted(ids)

    def datasets_of(self, source_id: str) -> list[dict]:
        return [{"id": d, **self.dataset(d)} for d in self.dataset_ids_of(source_id)]

    def claims_using_dataset(self, source_id: str, dataset_id: str) -> list[dict]:
        return [c for c in self.claims_of(source_id)
                if dataset_id in as_list(c.get("datasets"))]

    # ---- relations -----------------------------------------------------
    def claim_relations(self) -> list[dict]:
        """Every Claim-to-Claim edge, with its endpoints' Sources attached."""
        out = []
        for edge in self.edges:
            if edge.get("type") not in CLAIM_EDGE_TYPES:
                continue
            start, end = str(edge.get("from", "")), str(edge.get("to", ""))
            if not (CLAIM_ID.match(start) and CLAIM_ID.match(end)):
                continue                  # Source-to-Source SAME_AS
            out.append({**edge, "key": relation_key(edge),
                        "from_source": self.source_of_claim(start),
                        "to_source": self.source_of_claim(end)})
        return out

    def relations_hosted(self, source_id: str) -> list[dict]:
        """Relations evaluated in this Source's review: those whose From Claim
        belongs to it. Each graph Relation has exactly one From, so it is
        evaluated exactly once."""
        return sorted((r for r in self.claim_relations()
                       if r["from_source"] == source_id),
                      key=lambda r: (r["from"], r["type"], r["to"]))

    def relations_from_claim(self, claim_id: str) -> list[dict]:
        return [r for r in self.claim_relations() if r["from"] == claim_id]

    def relations_to_claim(self, claim_id: str) -> list[dict]:
        """Context only: evaluated in the review of the From Claim's Source."""
        return sorted((r for r in self.claim_relations() if r["to"] == claim_id),
                      key=lambda r: (r["from"], r["type"]))


def relation_key(edge: dict) -> str:
    """edges.jsonl carries no id; type + from + to identifies a Relation."""
    return f"{edge.get('type', '')}|{edge.get('from', '')}|{edge.get('to', '')}"


def _read_pages(folder: pathlib.Path, prefix: str, problems: list, raw: dict, kind: str):
    records, bodies = {}, {}
    for path in sorted(folder.glob(f"{prefix}-*.md")):
        text = path.read_bytes().decode("utf-8")      # exact: no newline translation
        data = parse_frontmatter(text)
        if data is None:
            problems.append((path.name, "no frontmatter"))
            continue
        identifier = str(data.get("id") or "")
        if not identifier:
            problems.append((path.name, "frontmatter has no id"))
            continue
        if identifier in records:
            problems.append((path.name, f"duplicate id {identifier}"))
        records[identifier] = data
        bodies[identifier] = _body(text)
        raw[(kind, identifier)] = text
    return records, bodies


def load_brain_from(root: pathlib.Path) -> Brain:
    problems: list = []
    wiki = root / "wiki"
    raw: dict = {}
    sources, source_bodies = _read_pages(wiki / "sources", "SRC", problems, raw, "source")
    concepts, concept_bodies = _read_pages(wiki / "concepts", "CPT", problems, raw, "concept")
    datasets, dataset_bodies = _read_pages(wiki / "datasets", "DST", problems, raw, "dataset")

    claims: dict[str, dict] = {}
    for row in _jsonl(wiki / "claims" / "claims.jsonl", problems):
        identifier = str(row.get("id") or "")
        if not identifier:
            problems.append(("claims.jsonl", "claim without id"))
            continue
        if identifier in claims:
            problems.append(("claims.jsonl", f"duplicate claim id {identifier}"))
        claims[identifier] = row
    edges = _jsonl(wiki / "graph" / "edges.jsonl", problems)
    runs = _jsonl(wiki / "runs.jsonl", problems)

    return Brain(
        root=root, sources=sources, claims=claims, concepts=concepts,
        datasets=datasets, edges=edges, runs=runs,
        source_bodies=source_bodies, concept_bodies=concept_bodies,
        dataset_bodies=dataset_bodies, raw_pages=raw, load_problems=tuple(problems),
        snapshot_id=compute_snapshot(root),
    )


@functools.lru_cache(maxsize=4)
def _load_cached(root: str) -> Brain:
    return load_brain_from(pathlib.Path(root))


def load_brain() -> Brain:
    return _load_cached(str(brain_dir()))
