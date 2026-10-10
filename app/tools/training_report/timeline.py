"""Write the Training timeline (Mermaid Gantt + time table) as Markdown.

Read-only: reads the save stamps of the round workbook. One bar per work
session; a pause longer than BREAK starts a new session. Time per paper is the
sum of the gaps between consecutive events (opening the paper, then each save)
within a session, as in analysis.activity(). A row keeps only
its latest save, so re-edits hide earlier activity (the figures are lower bounds).

    python app/tools/training_report/timeline.py docs/TRAINING_TIMELINE.md
"""
from __future__ import annotations

import collections
import datetime as dt
import pathlib
import sys

APP = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(APP))

import analysis  # noqa: E402
import sheets  # noqa: E402
import store  # noqa: E402

PAPERS = ("SRC-0006", "SRC-0009")
PHASE = "training"
BREAK = dt.timedelta(minutes=10)
MIN_BAR = 5                                   # minutes, so short sessions stay visible
CEST = dt.timezone(dt.timedelta(hours=2))


def hm(seconds: float) -> str:
    m = int(seconds // 60)
    return f"{m // 60} h {m % 60:02d}"


def main() -> int:
    out = pathlib.Path(sys.argv[1])
    raw = analysis.read_raw()
    evaluators = [(e["evaluator_id"], e["name"]) for e in raw[sheets.EVALUATORS]]
    reviews = {r["review_id"]: r for r in raw[sheets.REVIEWS] if r["phase_id"] == PHASE and r["source_id"] in PAPERS}
    stamps = collections.defaultdict(list)
    for tab in analysis._ANSWER_TABS:
        for row in raw.get(tab, []):
            when = analysis._when(row.get("updated_at", ""))
            if when and row.get("review_id") in reviews:
                stamps[row["review_id"]].append(when.astimezone(CEST))
    by = {(r["evaluator_id"], r["source_id"]): rid for rid, r in reviews.items()}
    for rid, r in reviews.items():                  # opening the paper counts as the first event
        started = analysis._when(r.get("started_at", ""))
        if started and stamps.get(rid):
            stamps[rid].append(started.astimezone(CEST))

    gantt, table, totals, latest = [], [], collections.Counter(), None
    for k, (eid, name) in enumerate(evaluators):
        row = {}
        for source in PAPERS:
            rid = by.get((eid, source))
            saves = sorted(stamps.get(rid, []))
            if not saves:
                row[source] = None
                continue
            latest = max(latest, saves[-1]) if latest else saves[-1]
            sessions, active = [[saves[0], saves[0]]], 0.0
            for a, b in zip(saves, saves[1:]):
                if b - a > BREAK:
                    sessions.append([b, b])
                else:
                    active += (b - a).total_seconds()
                    sessions[-1][1] = b
            gantt.append(f"    section {name} · {source}")
            for n, (s, e) in enumerate(sessions):
                minutes = max(MIN_BAR, round((e - s).total_seconds() / 60))
                gantt.append(f"    ·  :e{k}{source[-2:]}s{n}, {s:%Y-%m-%d %H:%M}, {minutes}m")
            status = reviews[rid].get("status", "")
            row[source] = (active, status)
            totals[source] += active
        if any(row.values()):
            table.append((name, row))

    table.sort(key=lambda t: -sum(v[0] for v in t[1].values() if v))
    lines = [
        "# Training timeline", "",
        f"Snapshot: {latest:%d %B %Y, %H:%M} CEST (latest saved answer).", "",
        "Work sessions on the Training papers, one line per evaluator and paper, grouped by evaluator. "
        "Times are when answers were saved, in CEST. A pause of more than 10 minutes starts a new bar; "
        "bars are at least 5 minutes long so short sessions stay visible. Re-editing an answer keeps only "
        "its latest save time, and reading without saving is not shown.", "",
        "```mermaid", "---", "displayMode: compact", "---", "gantt",
        "    title Training — work sessions per evaluator and paper (CEST)",
        "    dateFormat YYYY-MM-DD HH:mm", "    axisFormat %d %b %Hh", "    tickInterval 12hour",
        "    todayMarker off", *gantt, "```", "",
        "## Time per evaluator and paper", "",
        "Time between consecutive saved answers within each session (pauses over 10 minutes excluded). "
        "Empty: no answers saved on that paper.", "",
        "| Evaluator | " + " | ".join(PAPERS) + " | Total |", "|---|" + "---|" * (len(PAPERS) + 1),
    ]
    for name, row in table:
        cells = []
        for source in PAPERS:
            v = row[source]
            cells.append("" if v is None else hm(v[0]) + (" (in progress)" if v[1] == store.STATUS_IN_PROGRESS else ""))
        total = sum(v[0] for v in row.values() if v)
        lines.append(f"| {name} | " + " | ".join(cells) + f" | **{hm(total)}** |")
    lines.append("| **All** | " + " | ".join(f"**{hm(totals[s])}**" for s in PAPERS)
                 + f" | **{hm(sum(totals.values()))}** |")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", out, "latest save", latest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
