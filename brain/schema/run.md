# Record: Run

One record per session that writes to the graph: which schema version was in force, which model did the work, and how large the corpus was.


## Fields

- **`id`** — `RUN-<YYYY-MM-DD>-<NN>`, where `NN` is the next number for that date not already used anywhere in `wiki/` — a batch interrupted before its close-out has no Run record yet, but its id is in the log and on its records. With no `wiki/`, start at `01`. Mint one at the start of each ingest, query, or team-decision session. Example: `RUN-2026-09-21-01`.

- **`date`** — the date the run started.

- **`kind`** — one of `ingest` | `query` | `decision`. A `decision` run applies something the team has settled.

- **`schema_version`** — the version in force when the run wrote. To know how a claim was extracted, read its run's version, not the current one.

- **`model`** — the model that did the work, as precisely as it can be identified.

- **`corpus`** — the size of the graph when the run finished: sources, claims, edges.

## Every record points back

Each Source, Claim, Concept, Dataset, edge and absence carries **`run_ids`**: a list, in order.

- The first entry is the run that created the record.
- Every later run that changes the record in place appends its id.


Never rewrite an earlier entry and never reorder the list.
