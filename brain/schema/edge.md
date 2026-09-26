# Edge

A relation between two records.

## Fields

- **`type`** — one of the four types below.

- **`from`**, **`to`** — the ids the relation runs between, in the direction the type's row gives.

- **`grounding`** — `extracted` | `inferred`, and fixed by the type: `extracted` means one of the two sources names or cites the other on this point. On the three claim-to-claim types only.

- **`note`** — one sentence saying why the edge holds; on `extracted` SUPPORTS and ATTACKS, naming the citation that grounds it. On the three claim-to-claim types only.

- **`run_ids`** — `schema/run.md`.

## The four types

| type | from | to | grounding | when |
|---|---|---|---|---|
| CITES | Source | Source | — | only when both are in the corpus |
| SAME_AS | Source | Source | — | one source is a duplicate, an extended or shorter version of another source 
| SUPPORTS | Claim | Claim | extracted or inferred | one claim gives reasons or evidence for another claim |
| ATTACKS | Claim | Claim | extracted  or inferred | one claim denies or gives reasons against another claim |
| SAME_AS | Claim | Claim | extracted or inferred | two claims from different sources assert the same proposition |
 
