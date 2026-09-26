"""Allocation configuration: who evaluates which Source, in which phase.

The allocation lives in a human-editable YAML file (`data/allocation/*.yaml`).
Replacing it never requires editing code:

    allocation file  ->  tools/build_assignments.py (validates)
                     ->  data/manifest.yaml (explicit rows)
                     ->  tools/bootstrap_round.py (writes the round workbook)

The file names Sources, pairs and splits; this module turns them into explicit
evaluator x Source x phase assignment rows. The running app reads only those
rows and never infers an assignment from a pair or group name.

File shape:

    allocation_id: DEV-2026-09-26
    status: development            # or: accepted
    evaluators:
      - {evaluator_id: thiago, name: Thiago, is_admin: true}
    pairs:
      A: [thiago, francesca]
    training:                      # every evaluator gets these
      - {source: SRC-0006, title: "Pseudolaw and the illusion of legal meaning"}
    agreement:                     # both members of the pair get every paper
      AGR-A: {pair: A, sources: [SRC-0001, ...]}
    individual:                    # exactly one evaluator per paper
      IND-1: {evaluator: thiago, sources: [SRC-0008, ...]}
    reserved:                      # optional, generic
      - {phase: individual, split: IND-1, evaluator: francesca, source: SRC-0010}

A Source may be written as a bare id or as `{source, title}`. When a title is
given it must match the Brain's, which catches a Source renumbered between
snapshots.
"""
from __future__ import annotations

import hashlib
import pathlib

import yaml

TRAINING, AGREEMENT, INDIVIDUAL = "training", "agreement", "individual"
PHASES = (TRAINING, AGREEMENT, INDIVIDUAL)
ASSIGNED, RESERVED = "assigned", "reserved"
STATUSES = ("development", "accepted")


class AllocationError(ValueError):
    """The allocation file is invalid. Carries every problem found."""

    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


def load(path: pathlib.Path) -> dict:
    data = yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise AllocationError([f"{path} is not a mapping"])
    return data


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:16]


def _entries(value) -> list[dict]:
    """Normalise a list of Sources to [{source, title}]."""
    out = []
    for item in value or []:
        if isinstance(item, dict):
            out.append({"source": str(item.get("source") or ""),
                        "title": str(item.get("title") or "")})
        else:
            out.append({"source": str(item), "title": ""})
    return out


def assignment_key(phase_id: str, evaluator_id: str, source_id: str) -> str:
    return f"{phase_id}|{evaluator_id}|{source_id}"


def validate(data: dict, brain) -> list[str]:
    """Every rule the allocation must satisfy, checked together."""
    problems: list[str] = []
    known = set(brain.sources)

    if data.get("status") not in STATUSES:
        problems.append(f"status must be one of {', '.join(STATUSES)}")
    if not data.get("allocation_id"):
        problems.append("allocation_id is missing")

    evaluators = data.get("evaluators") or []
    ids = [str(e.get("evaluator_id") or "") for e in evaluators]
    if not evaluators:
        problems.append("no evaluators are listed")
    if len(ids) != len(set(ids)) or "" in ids:
        problems.append("evaluator ids must be present and unique")
    evaluator_ids = set(ids)

    def check_entry(entry: dict, where: str) -> None:
        source = entry["source"]
        if source not in known:
            problems.append(f"{where}: {source} is not in the current Brain snapshot")
        elif entry["title"] and entry["title"] != brain.source(source).get("title"):
            problems.append(
                f"{where}: {source} is titled "
                f"{brain.source(source).get('title')!r} in the Brain, not "
                f"{entry['title']!r}")

    pairs = data.get("pairs") or {}
    for pair_id, members in pairs.items():
        members = list(members or [])
        if len(members) != 2 or len(set(members)) != 2:
            problems.append(f"pair {pair_id} must have exactly two distinct evaluators")
        for member in members:
            if member not in evaluator_ids:
                problems.append(f"pair {pair_id}: {member} is not a listed evaluator")
    paired = [m for members in pairs.values() for m in members or []]
    if len(paired) != len(set(paired)):
        problems.append("an evaluator belongs to more than one pair")

    training = _entries(data.get("training"))
    training_ids = [e["source"] for e in training]
    if len(training_ids) != len(set(training_ids)):
        problems.append("a Training Source is listed twice")
    for entry in training:
        check_entry(entry, "training")

    placed: dict[str, list[str]] = {}
    agreement = data.get("agreement") or {}
    for split, spec in agreement.items():
        spec = spec or {}
        pair_id = spec.get("pair")
        if pair_id not in pairs:
            problems.append(f"{split}: pair {pair_id!r} is not defined")
        for entry in _entries(spec.get("sources")):
            check_entry(entry, split)
            placed.setdefault(entry["source"], []).append(split)
    individual = data.get("individual") or {}
    for split, spec in individual.items():
        spec = spec or {}
        evaluator = spec.get("evaluator")
        if evaluator not in evaluator_ids:
            problems.append(f"{split}: evaluator {evaluator!r} is not listed")
        for entry in _entries(spec.get("sources")):
            check_entry(entry, split)
            placed.setdefault(entry["source"], []).append(split)

    for source, splits in sorted(placed.items()):
        if source in training_ids:
            problems.append(f"{source} is a Training Source and is also in "
                            f"{', '.join(splits)}")
        if len(splits) > 1:
            problems.append(f"{source} appears more than once: {', '.join(splits)}")
    unplaced = sorted(known - set(training_ids) - set(placed))
    if unplaced:
        problems.append(
            "every non-training Source must be an Agreement or Individual paper; "
            f"not placed: {', '.join(unplaced)}")

    for row in data.get("reserved") or []:
        if row.get("phase") not in PHASES:
            problems.append(f"reserved row has unknown phase {row.get('phase')!r}")
        if row.get("evaluator") not in evaluator_ids:
            problems.append(f"reserved row names unknown evaluator {row.get('evaluator')!r}")
        if str(row.get("source")) not in known:
            problems.append(f"reserved row names unknown Source {row.get('source')!r}")

    if not problems:
        rows = expand(data, brain)[1]
        keys = [r["assignment_key"] for r in rows]
        duplicates = sorted({k for k in keys if keys.count(k) > 1})
        if duplicates:
            problems.append(f"duplicate assignment keys: {', '.join(duplicates)}")
        for split, spec in agreement.items():
            for entry in _entries((spec or {}).get("sources")):
                made = [r for r in rows if r["phase_id"] == AGREEMENT
                        and r["source_id"] == entry["source"]
                        and r["assignment_state"] == ASSIGNED]
                if len(made) != 2:
                    problems.append(f"{split}: {entry['source']} yields {len(made)} "
                                    f"assignments, not 2")
        individual_rows = [r for r in rows if r["phase_id"] == INDIVIDUAL
                           and r["assignment_state"] == ASSIGNED]
        holders: dict[str, set] = {}
        for row in individual_rows:
            holders.setdefault(row["source_id"], set()).add(row["evaluator_id"])
        for source, who in sorted(holders.items()):
            if len(who) != 1:
                problems.append(f"{source} has {len(who)} Individual evaluators")
    return problems


def expand(data: dict, brain) -> tuple[list[dict], list[dict]]:
    """(evaluator rows, assignment rows) — explicit, one row per assignment."""
    pairs = {pid: list(members or []) for pid, members in (data.get("pairs") or {}).items()}
    pair_of = {m: pid for pid, members in pairs.items() for m in members}
    agreement = data.get("agreement") or {}
    individual = data.get("individual") or {}
    agreement_split = {m: split for split, spec in agreement.items()
                       for m in pairs.get((spec or {}).get("pair"), [])}
    individual_split = {(spec or {}).get("evaluator"): split
                        for split, spec in individual.items()}

    evaluators = []
    for entry in data.get("evaluators") or []:
        eid = str(entry["evaluator_id"])
        evaluators.append({
            "evaluator_id": eid, "name": str(entry.get("name") or eid),
            "is_admin": bool(entry.get("is_admin")),
            "pair_id": pair_of.get(eid, ""),
            "agreement_split": agreement_split.get(eid, ""),
            "individual_split": individual_split.get(eid, ""),
        })

    rows: list[dict] = []

    def add(phase, evaluator, split, source, order, state=ASSIGNED):
        rows.append({
            "assignment_key": assignment_key(phase, evaluator, source),
            "evaluator_id": evaluator, "phase_id": phase, "split_id": split,
            "source_id": source, "pdf_file": brain.pdf_name(source),
            "assignment_order": order, "assignment_state": state,
        })

    for evaluator in evaluators:
        for order, entry in enumerate(_entries(data.get("training")), start=1):
            add(TRAINING, evaluator["evaluator_id"], "TRAINING", entry["source"], order)
    for split, spec in agreement.items():
        for member in pairs.get((spec or {}).get("pair"), []):
            for order, entry in enumerate(_entries((spec or {}).get("sources")), start=1):
                add(AGREEMENT, member, split, entry["source"], order)
    for split, spec in individual.items():
        for order, entry in enumerate(_entries((spec or {}).get("sources")), start=1):
            add(INDIVIDUAL, (spec or {}).get("evaluator"), split, entry["source"], order)
    for order, row in enumerate(data.get("reserved") or [], start=1):
        add(row["phase"], row["evaluator"], str(row.get("split") or ""),
            str(row["source"]), order, RESERVED)
    rows.sort(key=lambda r: (PHASES.index(r["phase_id"]), r["evaluator_id"],
                             r["split_id"], r["assignment_order"]))
    return evaluators, rows
