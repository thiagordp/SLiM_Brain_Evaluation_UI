"""Generate the runtime manifest from an accepted Splitter output.

The evaluation app never constructs pairs. It reads what the Splitter accepted,
so the manifest is reproducible rather than hand-edited:

    assignments.csv        one row per evaluator x paper x mode
    reproducibility.json   evaluators, pair assignments, snapshot, seed

Run:
    python app/tools/import_split.py <path-to-accepted-split-directory>
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "manifest.yaml"

# The Splitter assigns papers; it has no reason to name an administrator, who
# evaluates nothing. Admin is Thiago behind a separate secret (spec 15.3, 22),
# so this one row is added here and marked as not coming from the Splitter.
ADMIN = {"evaluator_id": "thiago", "name": "Thiago", "pair_id": None, "is_admin": True}

HEADER = """\
# Runtime manifest — generated from an accepted Splitter output.
#
#   python app/tools/import_split.py <accepted-split-directory>
#
# The evaluation app only READS this file. Pair construction, clustering and
# sampling live in the Splitter, so moving from 2 to 3 pairs means regenerating
# this manifest, not editing code.
#
# Everything below comes from the Splitter, with one exception noted inline:
# the administrator, who is assigned no papers.
"""


def load(split_dir: pathlib.Path) -> tuple[list[dict], list[dict], dict]:
    assignments_path = split_dir / "assignments.csv"
    repro_path = split_dir / "reproducibility.json"
    for path in (assignments_path, repro_path):
        if not path.exists():
            raise SystemExit(f"not an accepted split directory: {path} is missing")

    with assignments_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    repro = json.loads(repro_path.read_text(encoding="utf-8"))
    return rows, repro.get("evaluators", []), repro


def build(split_dir: pathlib.Path) -> dict:
    rows, evaluators, repro = load(split_dir)

    assignments = []
    for row in rows:
        assignments.append({
            "evaluator_id": row["evaluator_id"],
            "pair_id": row["pair_id"] or None,
            "work_id": row["work_id"],
            "source_id": row["source_id"],
            "mode": row["mode"],
            "assignment_order": int(row["assignment_order"]),
        })
    assignments.sort(key=lambda a: (a["evaluator_id"], a["mode"], a["assignment_order"]))

    people = [{
        "evaluator_id": entry["evaluator_id"],
        "name": entry["evaluator_name"],
        "pair_id": entry.get("pair_id"),
        "is_admin": bool(entry.get("is_admin")),
    } for entry in evaluators]
    if not any(person["is_admin"] for person in people):
        people.append(dict(ADMIN))

    return {
        "config": {
            "brain_snapshot_id": repro["brain_snapshot_id"],
            "eval_spec_version": str(repro.get("evaluation_spec_version", "1.0")),
            "number_of_pairs": int(repro.get("number_of_pairs", 0)),
            "random_seed": repro.get("random_seed"),
            "split_id": split_dir.name,
            "accepted_at": repro.get("accepted_at"),
            "training_open": True,
            "evaluation_open": True,
        },
        "evaluators": people,
        "assignments": assignments,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("split_dir", type=pathlib.Path,
                        help="an accepted split output directory")
    args = parser.parse_args()

    manifest = build(args.split_dir.resolve())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        HEADER + yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    evaluation = [a for a in manifest["assignments"] if a["mode"] == "evaluation"]
    training = {a["source_id"] for a in manifest["assignments"] if a["mode"] == "training"}
    print(f"wrote {OUT}")
    print(f"  split           {manifest['config']['split_id']}")
    print(f"  snapshot        {manifest['config']['brain_snapshot_id'][:16]}…")
    print(f"  pairs           {manifest['config']['number_of_pairs']}")
    print(f"  evaluators      {len(manifest['evaluators'])} "
          f"({sum(1 for p in manifest['evaluators'] if p['is_admin'])} admin)")
    print(f"  assignments     {len(manifest['assignments'])} rows "
          f"({len(evaluation)} evaluation, {len(manifest['assignments']) - len(evaluation)} training)")
    print(f"  distinct papers {len({a['source_id'] for a in evaluation})} evaluation, "
          f"{len(training)} training")
    if training & {a["source_id"] for a in evaluation}:
        sys.exit("ERROR: a training paper also appears in an evaluation set")


if __name__ == "__main__":
    main()
