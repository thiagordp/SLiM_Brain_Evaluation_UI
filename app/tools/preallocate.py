"""Create every row the evaluation will need, before anyone starts.

Preallocation is what makes the workbook usable by six people at once. Rows are
appended once, in bulk, from one machine; after that every save is a targeted
update of a row nobody else owns, and no evaluator ever appends into a tab the
others are reading.

Three things follow from doing it up front:

* each review's rows are **contiguous**, and the block's first and last row
  numbers are recorded on the review — so opening one paper reads a few hundred
  cells instead of the whole tab;
* the **superset** is created, conditional follow-ups included, so the first
  evaluator to answer "No" does not have to append a row mid-round;
* **reservations** are preallocated too, so settling an undivided pool later is
  a one-field edit with no storage to create.

Preallocation is not evaluator activity: it stamps no provenance, and it locks
no assignment.

    python app/tools/preallocate.py --dry-run     # what it would create
    python app/tools/preallocate.py               # create it
    python app/tools/preallocate.py --phase agreement
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import time
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import manifest  # noqa: E402
import progress  # noqa: E402
import store  # noqa: E402
from brain import load_brain  # noqa: E402


def plan(brain, rows) -> list[dict]:
    """What each assignment needs, without touching storage."""
    out = []
    for row in rows:
        source_id = row["source_id"]
        items = progress.all_possible_items(brain, source_id)
        edges = [(claim["id"], edge)
                 for claim in brain.claims_of(source_id)
                 for edge in brain.relations_of(claim["id"])]
        out.append({**row, "items": items, "edges": edges})
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", action="append", choices=manifest.PHASES,
                        help="limit to one phase (repeatable); default all")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    brain = load_brain()
    store.init()

    phases = args.phase or list(manifest.PHASES)
    rows = [a for a in manifest.assignments() if a["phase_id"] in phases]
    work = plan(brain, rows)

    print(f"store: {store.backend_name()}")
    print(f"configuration: {manifest.source_name()} · {manifest.config_version()}\n")

    by_phase = collections.Counter(r["phase_id"] for r in rows)
    by_state = collections.Counter(manifest.state_of(r) for r in rows)
    responses = sum(len(w["items"]) for w in work)
    edges = sum(len(w["edges"]) for w in work)
    print(f"  {len(rows)} assignments: "
          + ", ".join(f"{n} {phase}" for phase, n in sorted(by_phase.items())))
    print(f"  {by_state[manifest.ASSIGNED]} assigned, "
          f"{by_state[manifest.RESERVED]} reserved")
    print(f"  {responses} response rows, {edges} edge rows, "
          f"{len(rows)} review rows\n")

    if args.dry_run:
        print("--dry-run: nothing written")
        return

    entries = [{
        "phase_id": item["phase_id"], "evaluator_id": item["evaluator_id"],
        "evaluator_name": (manifest.evaluator(item["evaluator_id"]) or {}).get("name", ""),
        "pair_id": manifest.pair_of(item["evaluator_id"]),
        "source_id": item["source_id"], "work_id": item["work_id"],
        "assignment_key": item["assignment_key"],
        "items": [(i.object_type, i.object_id, i.question,
                   store.AUTO_NA if i.auto_na else "") for i in item["items"]],
        "edges": item["edges"],
    } for item in work]

    started = time.monotonic()
    summary = store.preallocate_bulk(entries)
    elapsed = time.monotonic() - started

    print(f"  {summary.get('new_reviews', summary['reviews'])} review rows")
    print(f"  {summary.get('responses', 0)} response rows")
    print(f"  {summary.get('edges', 0)} edge rows")
    print(f"\n{summary['rows']} rows created in {elapsed:.1f}s.")
    print("Preallocation stamps no provenance and locks no assignment: a review "
          "becomes real when its evaluator starts it.")


if __name__ == "__main__":
    main()
