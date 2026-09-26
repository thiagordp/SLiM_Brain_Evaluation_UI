# Record: Absence

An absence is an empty cell in a map the review draws. The review draws two, and they are the only things that carry absences:

| Map | Rows | Columns | Scope |
|---|---|---|---|
| 1 | legal task concepts | technique class concepts | `concept_pair` |
| 2 | normative concern concepts | the jurisdictions the corpus uses | `concept_jurisdiction` |

A map's rows and columns are the concepts the corpus actually uses. A concept no claim maps to is not in the graph at all, so it has no cells and no absence; `coverage.md` lists the grid entries the corpus never uses.

`tools/absences.py` computes every absence. None is ever written by hand.

## Fields

- **`id`** — prefixed `ABS-`. Example: `ABS-0001`.

- **`key`** — the cell, as `<scope>:<row>|<column>`. Example: `concept_jurisdiction:CPT-accountability-and-liability|EU`. Records are matched on this key, never on the wording.

- **`scope`** — the key's prefix, repeated for reading: `concept_pair` | `concept_jurisdiction`.

- **`description`** — one sentence, written from the key.

- **`reading`** — what the empty cell means. `unresolved` until a person decides, then one of:
  - `gap_in_literature`: nobody in the field has written it;
  - `extraction_shadow`: somebody has, and this corpus or this extraction missed it;
  - `tacit_link`: it is so obvious to the field that nobody states it.

  Never set this yourself. An empty cell is equally consistent with all three, and telling them apart takes someone who knows the field.

- **`lapsed`** — `false`, then `true` with a `lapsed_date` once the cell fills. Lapsed records are kept, never deleted.

- **`date`** — when the absence was first recorded.

- **`run_ids`** — `schema/run.md`.

## What is not an absence

| Mistaken for an absence | Where it belongs |
|---|---|
| a paper raises a concern but never addresses it | nowhere — the review maps the field, not one paper |
| a count of empty cells, given as one statement | one record per cell |
| a concept with few claims rather than none | `coverage.md`, as a count |
| an edge type nobody uses, or a paper connected to nothing | `structure.md` |
| a question a claim asks that no claim answers | the hypothesis register |
| figures that contradict each other, a mangled conversion | `wiki/log.md` |

Every other table in `coverage.md` is a plain count. A zero there is a number, not a finding, and gets no record.
