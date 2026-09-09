"""Generate the runtime manifest from the accepted paper allocation.

The evaluation app never infers who evaluates what. It reads explicit rows, one
per evaluator x paper x phase, because the labels in circulation do not line up:
Alessandro's email calls Giovanni + Alessandro "Group A" while assigning them
`AGR-C`. Anything derived from a group name would be wrong.

This tool is the one place that reads allocation prose. It parses the accepted
split tables, resolves every `SRC-xxxx` against the Brain, and writes the
manifest the app consumes.

    python app/tools/build_assignments.py                 # rewrite the manifest
    python app/tools/build_assignments.py --dry-run       # show what it would write

The three phases are `training`, `agreement` and `individual`. Training is the
same optional practice set for everyone; agreement is a shared set evaluated
independently by both members of a pair; individual is one evaluator per paper.

They are **not sequential**. All three are open from the start, and no phase's
completion or submission gates another.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import spec  # noqa: E402
from brain import load_brain  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
ALLOCATION = ROOT / "Design" / "paper allocation" / "Evaluation_Splits.md"
OUT = ROOT / "app" / "data" / "manifest.yaml"

TRAINING = ("W0085", "W0206")

#: From Alessandro's allocation email. Recorded explicitly, never inferred: the
#: "Group A/B/C" labels in that email do not correspond to the AGR split names.
#:
#:   Giovanni + Alessandro -> AGR-C      Alessandro -> IND-3   Giovanni -> IND-5
#:   Giuseppe + Vaclav     -> AGR-B      Giuseppe   -> IND-2   Vaclav   -> IND-4
#:   Thiago   + Francesca  -> AGR-A      IND-1 not yet divided between the two
EVALUATORS = (
    # evaluator_id, name, agreement_split, individual_split, is_admin
    ("alessandro", "Alessandro", "AGR-C", "IND-3", False),
    ("francesca",  "Francesca",  "AGR-A", "",      False),
    ("giovanni",   "Giovanni",   "AGR-C", "IND-5", False),
    ("giuseppe",   "Giuseppe",   "AGR-B", "IND-2", False),
    ("thiago",     "Thiago",     "AGR-A", "",      True),
    ("vaclav",     "Vaclav",     "AGR-B", "IND-4", False),
)

#: IND-1 belongs to the Thiago/Francesca pair, but the paper-by-paper division
#: between them is not settled. Rather than leave the papers nameless, every
#: possible future allocation is written as a **reserved** row: each IND-1 paper
#: gets one for Thiago and one for Francesca.
#:
#: A reserved row is a technical placeholder, not an assignment. It never appears
#: in an evaluator's paper list and never counts toward progress, completion,
#: phase submission or analysis. What it buys is that its storage — the review,
#: its responses, its edges, its row range — is preallocated up front, so
#: settling the division later is a one-field edit, `reserved` -> `assigned`,
#: with no rows to create at that moment.
#:
#: Both members of the pair are reserved for every paper on purpose. Only one of
#: each pair is ever activated: activating both would turn IND-1 into a second
#: agreement set and change the study design.
RESERVED = {"IND-1": ("thiago", "francesca")}

ASSIGNED, RESERVED_STATE = "assigned", "reserved"

SPLIT_HEADING = re.compile(r"^###\s+(AGR-[A-Z]|IND-\d+)\b", re.M)
SOURCE_IN_ROW = re.compile(r"\[(SRC-\d{4})\]")


def parse_allocation(path: pathlib.Path) -> dict[str, list[str]]:
    """split_id -> the source ids listed under it, in the order given."""
    text = path.read_text(encoding="utf-8")
    splits: dict[str, list[str]] = collections.OrderedDict()
    matches = list(SPLIT_HEADING.finditer(text))
    if not matches:
        raise SystemExit(f"no ### AGR-x / IND-n headings found in {path}")
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.start():end]
        found = [m.group(1) for m in SOURCE_IN_ROW.finditer(body)]
        seen: list[str] = []
        for source_id in found:                    # a table row may link twice
            if source_id not in seen:
                seen.append(source_id)
        splits[match.group(1)] = seen
    return splits


def build(brain, splits: dict[str, list[str]]) -> tuple[list[dict], list[dict]]:
    work_of = {sid: brain.work_id(sid) for sid in brain.source_ids}
    training_ids = []
    for work in TRAINING:
        source_id = brain.source_by_work_id(work)
        if source_id is None:
            raise SystemExit(f"training paper {work} is not in the Brain")
        training_ids.append(source_id)

    evaluators = [
        {"evaluator_id": eid, "name": name, "is_admin": is_admin,
         "pair_id": agreement.split("-")[-1] if agreement else None,
         "agreement_split": agreement, "individual_split": individual}
        for eid, name, agreement, individual, is_admin in EVALUATORS
    ]

    rows: list[dict] = []

    def add(evaluator_id, phase_id, split_id, source_id, order,
            state=ASSIGNED):
        rows.append({
            "assignment_key": f"{phase_id}|{evaluator_id}|{source_id}",
            "evaluator_id": evaluator_id,
            "phase_id": phase_id,
            "split_id": split_id,
            "source_id": source_id,
            "work_id": work_of.get(source_id, ""),
            "assignment_order": order,
            "assignment_state": state,
        })

    # ---- training: the same two papers for everyone
    for entry in evaluators:
        for order, source_id in enumerate(training_ids, start=1):
            add(entry["evaluator_id"], "training", "TRAINING", source_id, order)

    # ---- agreement: both evaluators of a pair over the same five papers
    for entry in evaluators:
        split = entry["agreement_split"]
        if not split:
            continue
        for order, source_id in enumerate(splits.get(split, []), start=1):
            add(entry["evaluator_id"], "agreement", split, source_id, order)

    # ---- individual: one evaluator per paper, except the undivided pool
    assigned_splits = {e["individual_split"] for e in evaluators if e["individual_split"]}
    for entry in evaluators:
        split = entry["individual_split"]
        if not split:
            continue
        for order, source_id in enumerate(splits.get(split, []), start=1):
            add(entry["evaluator_id"], "individual", split, source_id, order)

    # ---- reserved: every possible allocation of a split not yet divided
    for split, holders in RESERVED.items():
        if split in assigned_splits:
            raise SystemExit(f"{split} is both reserved and assigned")
        for order, source_id in enumerate(splits.get(split, []), start=1):
            for evaluator_id in holders:
                add(evaluator_id, "individual", split, source_id, order,
                    state=RESERVED_STATE)

    undeclared = [s for s in splits
                  if s.startswith("IND-") and s not in assigned_splits
                  and s not in RESERVED]
    if undeclared:
        raise SystemExit(f"individual splits with no holder and no reservation: "
                         f"{undeclared}")

    return evaluators, rows


HEADER = """\
# Runtime manifest — generated from the accepted paper allocation.
#
#   python app/tools/build_assignments.py
#
# The evaluation app only READS this file, and never infers an assignment from a
# group label: the labels in circulation do not line up (Giovanni + Alessandro
# are called "Group A" but hold AGR-C). Every evaluator x paper x phase pair is
# an explicit row.
#
# Phases: training, agreement, individual. Each carries its own assignments,
# status and final submission. They are NOT sequential — all three are open from
# the start, Training is optional practice, and no phase gates another.
#
# `assignment_state` separates a real assignment from a technical reservation.
# A `reserved` row is a preallocated possibility: it never appears in a paper
# list and never counts toward progress, completion or analysis. IND-1 carries
# one reservation per evaluator per paper, so settling the division later is a
# one-field edit rather than a round of row creation. Activate only one
# evaluator per paper; activating both would make the pool a second agreement
# set. Reservations do not hold the phase closed.
"""


def _accepted_at(out: pathlib.Path, split_version: str) -> tuple[str, bool]:
    """Keep the recorded acceptance date when the allocation has not changed.

    Returns the timestamp and whether it was carried over.
    """
    if out.exists():
        try:
            previous = yaml.safe_load(out.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            previous = {}
        config = previous.get("config") or {}
        if config.get("split_version") == split_version and config.get("accepted_at"):
            return str(config["accepted_at"]), True
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allocation", type=pathlib.Path, default=ALLOCATION)
    parser.add_argument("--out", type=pathlib.Path, default=OUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    brain = load_brain()
    splits = parse_allocation(args.allocation)
    evaluators, rows = build(brain, splits)

    unknown = sorted({r["source_id"] for r in rows} - set(brain.source_ids))
    if unknown:
        raise SystemExit(f"allocation names sources not in the Brain: {unknown}")

    digest = hashlib.sha256(
        "\n".join(sorted(r["assignment_key"] + "|" + r["split_id"] for r in rows))
        .encode("utf-8")
    ).hexdigest()

    # `accepted_at` records when this allocation was accepted, not when the
    # generator last ran. Re-running it on an unchanged allocation must leave the
    # date alone, or every run would look like a fresh acceptance in the diff.
    accepted_at, reused = _accepted_at(args.out, digest[:16])

    data = {
        "config": {
            "brain_snapshot_id": brain.snapshot_id,
            "eval_spec_version": spec.EVAL_SPEC_VERSION,
            "split_version": digest[:16],
            "accepted_at": accepted_at,
            # All three phases are open from the start. Availability is an
            # operational control, never a methodological gate: Training is
            # optional practice on W0085/W0206, and neither completing nor
            # submitting a phase is a prerequisite for any other. IND-1 rows
            # stay pending inside an open Individual phase.
            "training_open": True,
            "agreement_open": True,
            "individual_open": True,
        },
        "evaluators": evaluators,
        "assignments": rows,
    }

    body = HEADER + yaml.safe_dump(data, sort_keys=False, allow_unicode=True)

    # ---- report
    print(f"allocation: {args.allocation}")
    for split, sources in splits.items():
        print(f"  {split:8s} {len(sources)} papers")
    print()
    for entry in evaluators:
        mine = [r for r in rows if r["evaluator_id"] == entry["evaluator_id"]]
        counts = collections.Counter(
            r["phase_id"] for r in mine if r["assignment_state"] == ASSIGNED)
        held = sum(1 for r in mine if r["assignment_state"] == RESERVED_STATE)
        print(f"  {entry['name']:11s} "
              f"agreement {entry['agreement_split'] or '—':6s} "
              f"individual {entry['individual_split'] or '— (reserved)':12s} "
              f"| training {counts['training']}, agreement {counts['agreement']}, "
              f"individual {counts['individual']}"
              + (f", reserved {held}" if held else ""))
    held = [r for r in rows if r["assignment_state"] == RESERVED_STATE]
    if held:
        pools = sorted({r["split_id"] for r in held})
        papers = len({r["source_id"] for r in held})
        print(f"\n  {len(held)} reserved rows over {papers} papers "
              f"({', '.join(pools)}) — every possible allocation, preallocated.")
        print(f"  Activating one is `reserved` -> `assigned`; activate only one "
              f"evaluator per paper.")
    print(f"\n  {len(rows)} assignment rows, split_version {digest[:16]}")
    print(f"  accepted_at {accepted_at}"
          + ("  (unchanged allocation — date carried over)" if reused
             else "  (new or changed allocation)"))

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return
    args.out.write_text(body, encoding="utf-8")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
