# Node: Dataset

One node per dataset, benchmark, or corpus a claim rests on. A dataset a paper merely mentions gets no node: if no claim rests on it, the graph has nothing to say about it.

## Fields

- **`id`** — prefixed `DST-`. Example: `DST-0001`.

- **`name`** — the dataset's name as the source gives it.

- **`introduced_by`** — source id, when the dataset is introduced in the corpus; otherwise `external`.

- **`language`** — ISO 639-1 codes of the texts in the dataset.

- **`jurisdiction`** — legal system(s) the texts come from; jurisdiction codes in `schema/claim.md`.

- **`description`** — quantitative and qualitative features of dataset: the type of data (e.g judgments, statutes, contracts, exam questions, synthetic etc.), annotation method, if present; size;  

- **`availability`** — one of `public` | `on_request` | `proprietary` | `not_stated`.

- **`run_ids`** — `schema/run.md`.

