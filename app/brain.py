"""Read-only access to the Brain artifact.

Three layers are kept separate, per the design approach: the Brain data model,
its wiki projections, and this interface. Nothing here writes to the Brain.

Canonical stores  : wiki/claims/claims.jsonl, wiki/graph/edges.jsonl
Entity frontmatter: wiki/sources/*.md, wiki/concepts/*.md, wiki/datasets/*.md
"""
from __future__ import annotations

import collections
import dataclasses
import functools
import hashlib
import json
import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
BRAIN = ROOT / "brain"
WIKI = BRAIN / "wiki"

# Edge types that hold between two claims of different sources.
CLAIM_EDGE_TYPES = (
    "SUPPORTS",
    "ATTACKS",
    "SAME_AS",
    "COMPATIBLE_WITH",
    "IN_TENSION_WITH",
)

FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def _frontmatter(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER.match(text)
    if not match:
        return {}
    data = yaml.safe_load(match.group(1)) or {}
    return data if isinstance(data, dict) else {}


def _body(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER.match(text)
    return text[match.end():] if match else text


def _jsonl(path: pathlib.Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


WORK_ID = re.compile(r"(W\d{4})")
CLAIM_ID = re.compile(r"CLM-\d{4}-\d{3}")

# Concept lifecycle. A candidate is created during extraction; a candidate that
# reaches the independent-source threshold is promoted to emergent at batch
# close-out. Emergent is therefore a later status of a concept that was once a
# candidate, not a different origin.
NON_ANCHOR = ("candidate", "emergent")


def work_id_of(file_field: str) -> str:
    """`raw/W0013__Facts2Law_...md` -> `W0013`. Papers are named by work id."""
    match = WORK_ID.search(file_field or "")
    return match.group(1) if match else ""


def runtime_files() -> list[pathlib.Path]:
    """The Brain files the app is allowed to read, in a stable order.

    Deliberately excludes log.md, index.md, coverage/structure reports, PDFs,
    schema/ and skills: none of them is a runtime information source, and the
    log's prose changes between Brain runs.
    """
    files: list[pathlib.Path] = []
    files.extend(sorted((WIKI / "sources").glob("*.md")))
    files.extend(sorted((WIKI / "concepts").glob("*.md")))
    files.extend(sorted((WIKI / "datasets").glob("*.md")))
    files.append(WIKI / "claims" / "claims.jsonl")
    files.append(WIKI / "graph" / "edges.jsonl")
    return files


def compute_snapshot() -> str:
    """Deterministic identity of the frozen Brain artifact.

    SHA-256 over the runtime files, feeding each file's *path* as well as its
    content hash, so a rename changes the snapshot even when the bytes do not.
    Every review records this, so we always know which artifact was judged.
    """
    overall = hashlib.sha256()
    for path in runtime_files():
        per_file = hashlib.sha256(path.read_bytes()).hexdigest()
        relative = path.relative_to(BRAIN).as_posix()
        overall.update(relative.encode("utf-8"))
        overall.update(b"\0")
        overall.update(per_file.encode("ascii"))
        overall.update(b"\n")
    return overall.hexdigest()


class SnapshotMismatch(RuntimeError):
    """The Brain on disk is not the one the evaluation was configured against."""


def _motivating_claims(concept: dict) -> list[str]:
    """The claims that motivated a candidate/emergent concept's creation.

    Read from the Concept record itself: the schema requires a candidate or
    emergent concept's `definition` to be derived from the claims that motivated
    it, citing their ids. `log.md` is deliberately not used — it is an audit
    trail whose prose may change between Brain runs, so parsing it would make
    the interface brittle.

    A claim that merely maps to the concept is not motivating: retrofit adds a
    later concept to earlier claims, and those claims are not named here.
    """
    if concept.get("status") not in NON_ANCHOR:
        return []
    return sorted(set(CLAIM_ID.findall(concept.get("definition") or "")))


@dataclasses.dataclass(frozen=True)
class Brain:
    sources: dict[str, dict]
    claims: dict[str, dict]
    concepts: dict[str, dict]
    datasets: dict[str, dict]
    edges: list[dict]
    source_bodies: dict[str, str]
    concept_bodies: dict[str, str]
    dataset_bodies: dict[str, str]
    motivating_claims: dict[str, list[str]]   # concept_id -> claims that created it
    concept_provenance_gaps: list[str]        # non-anchor concepts naming no claim
    snapshot_id: str

    # ---- ordering -------------------------------------------------------
    @property
    def source_ids(self) -> list[str]:
        return sorted(self.sources)

    @property
    def short_snapshot(self) -> str:
        return self.snapshot_id[:16]

    @property
    def run_id(self) -> str:
        for claim in self.claims.values():
            if claim.get("run_id"):
                return str(claim["run_id"])
        return "unknown"

    @property
    def schema_version(self) -> str:
        for claim in self.claims.values():
            if claim.get("schema_version"):
                return str(claim["schema_version"])
        return "unknown"

    # ---- lookups --------------------------------------------------------
    def source(self, source_id: str) -> dict:
        return self.sources.get(source_id, {})

    def source_body(self, source_id: str) -> str:
        return self.source_bodies.get(source_id, "")

    def claims_of(self, source_id: str) -> list[dict]:
        rows = [c for c in self.claims.values() if c.get("source") == source_id]
        return sorted(rows, key=lambda c: c["id"])

    def concept(self, concept_id: str) -> dict:
        return self.concepts.get(concept_id, {})

    def dataset(self, dataset_id: str) -> dict:
        return self.datasets.get(dataset_id, {})

    def datasets_of(self, source_id: str) -> list[dict]:
        """Dataset nodes attached to a source via a USES edge or a claim."""
        ids = {
            e["to"]
            for e in self.edges
            if e["type"] == "USES" and e.get("from") == source_id
        }
        ids |= {
            c["dataset"]
            for c in self.claims_of(source_id)
            if c.get("dataset")
        }
        ids |= {
            d["id"]
            for d in self.datasets.values()
            if source_id in (d.get("used_by") or [])
            or d.get("introduced_by") == source_id
        }
        return [self.datasets[i] for i in sorted(ids) if i in self.datasets]

    def claims_using_dataset(self, source_id: str, dataset_id: str) -> list[dict]:
        return [c for c in self.claims_of(source_id) if c.get("dataset") == dataset_id]

    def cites_from(self, source_id: str) -> list[dict]:
        """Outgoing CITES edges: this source -> other corpus sources."""
        return [
            e for e in self.edges
            if e["type"] == "CITES" and e.get("from") == source_id
        ]

    def cites_to(self, source_id: str) -> list[dict]:
        return [
            e for e in self.edges
            if e["type"] == "CITES" and e.get("to") == source_id
        ]

    def relations_of(self, claim_id: str) -> list[dict]:
        """Cross-source claim edges touching this claim, in either direction.

        Each is returned with a stable ``edge_key`` used as the answer's
        object_id, plus the claim on the other end and the direction, so the
        UI can show the two claims side by side without a graph walk.
        """
        out = []
        for edge in self.edges:
            if edge["type"] not in CLAIM_EDGE_TYPES:
                continue
            if edge.get("from") == claim_id:
                other, direction = edge.get("to"), "outgoing"
            elif edge.get("to") == claim_id:
                other, direction = edge.get("from"), "incoming"
            else:
                continue
            out.append({
                **edge,
                "edge_key": f"{edge['from']}->{edge['to']}:{edge['type']}",
                "other_claim_id": other,
                "direction": direction,
            })
        return sorted(out, key=lambda e: (e["type"], e["edge_key"]))

    def source_of_claim(self, claim_id: str) -> str:
        return str(self.claims.get(claim_id, {}).get("source", ""))

    def concept_options(self) -> list[str]:
        """`CPT-id — Label` strings for the missing-concept selector."""
        return [
            f"{cid} — {self.concepts[cid].get('label', '')}"
            for cid in sorted(self.concepts)
        ]

    def source_options(self) -> list[str]:
        return [
            f"{sid} — {self.sources[sid].get('title', '')}"
            for sid in self.source_ids
        ]

    # ---- work ids ------------------------------------------------------
    def work_id(self, source_id: str) -> str:
        return work_id_of(self.source(source_id).get("file", ""))

    def label(self, source_id: str) -> str:
        """`W0085 — Title` : how a paper is named everywhere in the UI."""
        work = self.work_id(source_id)
        title = self.source(source_id).get("title", "")
        return f"{work} — {title}" if work else f"{source_id} — {title}"

    def source_by_work_id(self, work: str) -> str | None:
        for source_id in self.source_ids:
            if self.work_id(source_id) == work:
                return source_id
        return None

    # ---- concepts ------------------------------------------------------
    def concept_body(self, concept_id: str) -> str:
        return self.concept_bodies.get(concept_id, "")

    def dataset_body(self, dataset_id: str) -> str:
        return self.dataset_bodies.get(dataset_id, "")

    def concepts_by_family(self, concept_ids) -> dict[str, list[dict]]:
        """Group mapped concepts by concept_type, in the fixed family order."""
        families: dict[str, list[dict]] = collections.OrderedDict(
            (family, []) for family in
            ("legal_task", "technique_class", "normative_concern", "other")
        )
        for concept_id in concept_ids or []:
            concept = self.concept(concept_id)
            family = concept.get("concept_type") or "other"
            families.setdefault(family, []).append(concept)
        return families

    def candidate_created_for(self, claim_id: str) -> list[dict]:
        """Candidate concepts whose creation this claim motivated.

        Empty means HE-21 is N/A for the claim, whatever its current mappings
        are: an anchor never applies, and a candidate that was retrofitted onto
        this claim, or already existed when the claim was mapped, does not
        either.
        """
        return [
            self.concept(concept_id)
            for concept_id, claims in sorted(self.motivating_claims.items())
            if claim_id in claims
        ]

    def source_registry(self) -> list[dict]:
        """Every Source in the Brain, for the CITES completeness question.

        An evaluator can recognise their paper's bibliography, but cannot be
        expected to remember which of fifty publications the Brain happens to
        hold — and that is exactly what HE-18.2 asks them to judge.
        """
        rows = []
        for source_id in self.source_ids:
            source = self.sources[source_id]
            rows.append({
                "id": source_id,
                "work_id": self.work_id(source_id),
                "title": source.get("title", ""),
                "authors": source.get("authors") or [],
                "year": str(source.get("year", "")),
                "venue": source.get("venue", ""),
            })
        return rows

    def concepts_of_source(self, source_id: str) -> dict[str, list[dict]]:
        """Every concept mapped anywhere in this paper, grouped by family.

        Source-level conceptual coverage asks about the paper as a whole, so the
        evidence has to be the paper as a whole: one claim's mapping says nothing
        about whether a notion is carried elsewhere. Each entry counts the claims
        that map it.
        """
        counts: collections.Counter = collections.Counter()
        for claim in self.claims_of(source_id):
            for concept_id in claim.get("concepts") or []:
                counts[concept_id] += 1

        families: dict[str, list[dict]] = collections.OrderedDict(
            (family, []) for family in
            ("legal_task", "technique_class", "normative_concern", "other")
        )
        for concept_id, count in counts.items():
            concept = self.concept(concept_id)
            family = concept.get("concept_type") or "other"
            families.setdefault(family, []).append({
                "id": concept_id,
                "label": concept.get("label", ""),
                "status": concept.get("status", ""),
                "definition": concept.get("definition", ""),
                "claims": count,
            })
        for entries in families.values():
            entries.sort(key=lambda e: (-e["claims"], e["label"]))
        return families

    def concept_registry(self) -> list[dict]:
        """Every concept with its lifecycle status, for the searchable registry."""
        rows = []
        for concept_id in sorted(self.concepts):
            concept = self.concepts[concept_id]
            rows.append({
                "id": concept_id,
                "label": concept.get("label", ""),
                "status": concept.get("status", ""),
                "concept_type": concept.get("concept_type", ""),
                "definition": concept.get("definition", ""),
                "aliases": concept.get("aliases") or [],
            })
        return rows



@functools.lru_cache(maxsize=1)
def load_brain() -> Brain:
    sources, bodies = {}, {}
    for path in sorted((WIKI / "sources").glob("SRC-*.md")):
        data = _frontmatter(path)
        if data.get("id"):
            sources[str(data["id"])] = data
            bodies[str(data["id"])] = _body(path)

    concepts, concept_bodies = {}, {}
    for path in sorted((WIKI / "concepts").glob("CPT-*.md")):
        data = _frontmatter(path)
        if data.get("id"):
            concepts[str(data["id"])] = data
            concept_bodies[str(data["id"])] = _body(path)

    datasets, dataset_bodies = {}, {}
    for path in sorted((WIKI / "datasets").glob("DST-*.md")):
        data = _frontmatter(path)
        if data.get("id"):
            datasets[str(data["id"])] = data
            dataset_bodies[str(data["id"])] = _body(path)

    claims = {c["id"]: c for c in _jsonl(WIKI / "claims" / "claims.jsonl")}
    edges = _jsonl(WIKI / "graph" / "edges.jsonl")

    # HE-21 provenance, from the Concept records only.
    motivating: dict[str, list[str]] = {}
    gaps: list[str] = []
    for concept_id, concept in concepts.items():
        if concept.get("status") not in NON_ANCHOR:
            continue
        found = _motivating_claims(concept)
        if found:
            motivating[concept_id] = found
        else:
            # Flagged rather than guessed: without it HE-21 cannot be decided
            # for this concept, and silently falling back would hide that.
            gaps.append(concept_id)

    snapshot_id = compute_snapshot()

    return Brain(
        sources=sources,
        claims=claims,
        concepts=concepts,
        datasets=datasets,
        edges=edges,
        source_bodies=bodies,
        concept_bodies=concept_bodies,
        dataset_bodies=dataset_bodies,
        motivating_claims=motivating,
        concept_provenance_gaps=gaps,
        snapshot_id=snapshot_id,
    )
