"""Brain snapshot preflight: is this snapshot evaluable with instrument 4.0?

Run before a round is bootstrapped (`tools/bootstrap_round.py`), from the command
line (`tools/preflight.py`), and by the app at startup. Errors stop the round
before any evaluator sees a broken record; warnings are shown to the
administrator.

Compatibility is checked record by record against the structure the instrument
needs and against the frozen definitions — not by comparing a single schema
version read off run history, which a mature snapshot need not have.
"""
from __future__ import annotations

import dataclasses
import re

import brain as brain_module
import progress
import spec
import store

JURISDICTION_WORDS = ("EU", "general", "undetermined")
ISO_3166_ALPHA2 = re.compile(r"^[A-Z]{2}$")
ISO_639_1 = re.compile(r"^[a-z]{2}$")
REQUIRED_CLAIM_FIELDS = ("id", "source", "statement", "anchors", "claim_object",
                         "claim_type", "basis", "claim_jurisdiction",
                         "legal_reference", "temporal_reference", "concepts",
                         "datasets")
REQUIRED_DATASET_FIELDS = ("name", "introduced_by", "language", "jurisdiction",
                           "description", "availability")
REQUIRED_SOURCE_FIELDS = ("title", "file")
#: Fields of older Brain versions. The instrument does not read them; if a
#: record still carries one it is reported, never used.
OBSOLETE_CLAIM_FIELDS = ("premise", "positive_form", "basis_qualifier", "dataset",
                         "jurisdiction_relation", "jurisdiction_inferred", "quotes")
OBSOLETE_DATASET_FIELDS = ("used_by", "document_types", "size", "annotation",
                           "agreement_reported")


@dataclasses.dataclass
class Report:
    errors: list[str] = dataclasses.field(default_factory=list)
    warnings: list[str] = dataclasses.field(default_factory=list)
    summary: dict = dataclasses.field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def _allowed(entry_key: str) -> set[str]:
    return {item["value"] for item in spec.definition(entry_key).get("items", [])
            if item.get("value")}


def check(brain) -> Report:
    report = Report()
    err, warn = report.errors.append, report.warnings.append

    for where, what in brain.load_problems:
        err(f"{where}: {what}")

    # ---------------------------------------------------------- schema
    frozen = spec.frozen_source_hashes()
    for path, digest in brain.schema_hashes().items():
        if path in frozen and frozen[path] != digest:
            err(f"{path} differs from the schema the definitions were frozen from "
                f"— re-run tools/freeze_definitions.py only if the new schema is the "
                f"accepted one")
    for path in frozen:
        if path.startswith("schema/") and path not in brain.schema_hashes():
            err(f"{path} is missing from the snapshot")
    if brain.canonical_schema_version != spec.canonical_schema_version():
        err(f"the snapshot declares schema {brain.canonical_schema_version or '(none)'}"
            f", the frozen definitions are for {spec.canonical_schema_version()}")
    for run_id, version in brain.run_schema_versions().items():
        if version != brain.canonical_schema_version:
            warn(f"{run_id} recorded schema {version or '(none)'}; the records it "
                 f"touched were written under a different version than the current "
                 f"schema")

    # ---------------------------------------------------------- sources
    for source_id, source in brain.sources.items():
        for name in REQUIRED_SOURCE_FIELDS:
            if not source.get(name):
                err(f"{source_id}: `{name}` is missing")

    # ---------------------------------------------------------- claims
    objects, types, bases = (_allowed("claim.claim_object"),
                             _allowed("claim.claim_type"), _allowed("claim.basis"))
    for claim_id, claim in brain.claims.items():
        for name in REQUIRED_CLAIM_FIELDS:
            if name not in claim:
                err(f"{claim_id}: required field `{name}` is missing")
        if claim.get("source") not in brain.sources:
            err(f"{claim_id}: Source {claim.get('source')!r} does not resolve")
        if not str(claim.get("statement") or "").strip():
            err(f"{claim_id}: empty statement")
        anchors = claim.get("anchors")
        if not isinstance(anchors, list) or not anchors:
            err(f"{claim_id}: no anchors")
        else:
            for n, anchor in enumerate(anchors, 1):
                if not isinstance(anchor, dict) or not str(anchor.get("quote") or "").strip() \
                        or not str(anchor.get("location") or "").strip():
                    err(f"{claim_id}: anchor {n} lacks a quote or a location")
        for name, allowed in (("claim_object", objects), ("claim_type", types),
                              ("basis", bases)):
            if name in claim and claim[name] not in allowed:
                err(f"{claim_id}: {name} {claim[name]!r} is not one of "
                    f"{', '.join(sorted(allowed))}")
        jurisdictions = brain_module.as_list(claim.get("claim_jurisdiction"))
        if not jurisdictions:
            err(f"{claim_id}: claim_jurisdiction is empty")
        for value in jurisdictions:
            if value not in JURISDICTION_WORDS and not ISO_3166_ALPHA2.match(str(value)):
                err(f"{claim_id}: claim_jurisdiction {value!r} is not a jurisdiction code, "
                    f"EU, general or undetermined")
        if not str(claim.get("temporal_reference") or "").strip():
            err(f"{claim_id}: temporal_reference is empty")
        concepts = brain_module.as_list(claim.get("concepts"))
        if not concepts:
            err(f"{claim_id}: no Concept is assigned")
        for concept_id in concepts:
            if concept_id not in brain.concepts:
                err(f"{claim_id}: Concept {concept_id} does not resolve")
        for dataset_id in brain_module.as_list(claim.get("datasets")):
            if dataset_id not in brain.datasets:
                err(f"{claim_id}: Dataset {dataset_id} does not resolve")
        obsolete = [f for f in OBSOLETE_CLAIM_FIELDS if f in claim]
        if obsolete:
            warn(f"{claim_id}: carries obsolete fields ({', '.join(obsolete)}), which "
                 f"the instrument ignores")

    # ---------------------------------------------------------- concepts
    grid = spec.concept_grid()
    grid_family = {cid: family for family, ids in grid.items() for cid in ids}
    for concept_id, concept in brain.concepts.items():
        status, family = concept.get("status"), concept.get("concept_type")
        if status not in brain_module.CONCEPT_STATUSES:
            err(f"{concept_id}: status {status!r} is not anchor, candidate or emergent")
        if family not in brain_module.CONCEPT_FAMILIES:
            err(f"{concept_id}: concept_type {family!r} is not one of the six families")
        if not str(concept.get("definition") or "").strip():
            err(f"{concept_id}: no definition")
        if concept_id in grid_family:
            if status != "anchor":
                err(f"{concept_id}: listed in the anchor grid but has status {status!r}")
            if family != grid_family[concept_id]:
                err(f"{concept_id}: grid family {grid_family[concept_id]} but "
                    f"concept_type {family}")
        elif status == "anchor":
            err(f"{concept_id}: status anchor but not in the frozen anchor grid")

    # ---------------------------------------------------------- datasets
    availability = _allowed("dataset.availability")
    for dataset_id, dataset in brain.datasets.items():
        for name in REQUIRED_DATASET_FIELDS:
            if name not in dataset:
                err(f"{dataset_id}: required field `{name}` is missing")
        if dataset.get("availability") not in availability:
            err(f"{dataset_id}: availability {dataset.get('availability')!r} is not one "
                f"of {', '.join(sorted(availability))}")
        introduced = dataset.get("introduced_by")
        if introduced not in ("external", *brain.sources):
            err(f"{dataset_id}: introduced_by {introduced!r} is neither a Source nor "
                f"external")
        elif introduced != "external" and not brain.claims_using_dataset(introduced,
                                                                          dataset_id):
            warn(f"{dataset_id}: introduced by {introduced}, but no Claim of that "
                 f"Source rests on it")
        for value in brain_module.as_list(dataset.get("language")):
            if value != "unknown" and not ISO_639_1.match(str(value)):
                warn(f"{dataset_id}: language {value!r} is not an ISO 639-1 code")
        obsolete = [f for f in OBSOLETE_DATASET_FIELDS if f in dataset]
        if obsolete:
            warn(f"{dataset_id}: carries obsolete fields ({', '.join(obsolete)}), which "
                 f"the instrument ignores")

    # ---------------------------------------------------------- edges
    relation_types = _allowed("edge.relation_type")
    seen = set()
    for n, edge in enumerate(brain.edges, 1):
        kind, start, end = edge.get("type"), str(edge.get("from")), str(edge.get("to"))
        where = f"edge {n} ({kind} {start} → {end})"
        if kind not in brain_module.EDGE_TYPES:
            err(f"{where}: unknown type")
            continue
        claims = start in brain.claims and end in brain.claims
        sources = start in brain.sources and end in brain.sources
        if kind == "CITES" and not sources:
            err(f"{where}: CITES endpoints must both be Sources")
        if kind in ("SUPPORTS", "ATTACKS") and not claims:
            err(f"{where}: endpoints do not resolve to Claims")
        if kind == "SAME_AS" and not (claims or sources):
            err(f"{where}: endpoints do not resolve")
        if claims:
            if kind not in relation_types:
                err(f"{where}: {kind} is not a Claim-to-Claim relation type")
            if edge.get("grounding") not in brain_module.GROUNDINGS:
                err(f"{where}: grounding {edge.get('grounding')!r} is not extracted or "
                    f"inferred")
            if not str(edge.get("note") or "").strip():
                err(f"{where}: no note")
            key = brain_module.relation_key(edge)
            if key in seen:
                err(f"{where}: the same Relation is recorded twice")
            seen.add(key)

    # ---------------------------------------------------------- dry build
    empty = store.ReviewData()
    built = 0
    for source_id in brain.source_ids:
        try:
            rows = progress.review_rows(brain, "PREFLIGHT", source_id)
            progress.missing_items(brain, source_id, empty)
            built += sum(len(v) for v in rows.values())
        except Exception as error:                       # report, do not crash
            err(f"{source_id}: the evaluation items could not be built ({error!r})")

    report.summary = {
        "sources": len(brain.sources), "claims": len(brain.claims),
        "concepts": len(brain.concepts), "datasets": len(brain.datasets),
        "claim relations": len(brain.claim_relations()),
        "rows per full pass": built,
        "snapshot": brain.snapshot_id,
        "canonical schema": brain.canonical_schema_version,
        "definitions": spec.definitions_id(),
    }
    return report
