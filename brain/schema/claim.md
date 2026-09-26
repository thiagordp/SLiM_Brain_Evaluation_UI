# Node: Claim

A claim is a central thesis or hypothesis that a paper advances as part of its contribution, especially when supported through arguments or empirical data.


## Fields

- **`id`** — `<source id number>-<running number within source>`, prefixed `CLM-`. Example: `CLM-0001-003`.

- **`source`** — the id of the source the claim comes from. Example: `SRC-0001`.

- **`statement`** — the proposition itself, one per claim. Where one claim ends and the next begins is decided by the one-contention test in the `extract-claims` skill.

- **`anchors`** — a list of 1 to N textual quotes, each `{quote, location}`:
  - `quote` is a verbatim passage from the source, at most 50 words, where the claim and its `basis` are put forward.
  - `location` is a page number or, without pagination, section heading plus paragraph ordinal (e.g. "3.2, para 4");

- **`claim_object`** what the claim is about. One of:
  - `law`: the claim is about legislation, legal decisions, legal practices or regulators' behavior.
  - `technology`: the claim is about computational technologies, systems or models.
  - `other`: the claim object does not fit the `law` or `technology` categories.

- **`claim_type`** — how the object is addressed. One of:
  - `descriptive`: describes an aspect of the object or how it was/is handled.
  - `interpretative`: proposes a prefered view of an aspect or concept of the object; 
  - `prescriptive`: states how the object should be or should be handled;
  - `predictive`: is about future developments of the object and the ways it will or may be handled.

- **`basis`** — always filled; what the source offers for the claim:
  - `factual`: the claim is based on data, experiments, interviews, or observation;
  - `legal`: the claim is based on legislation, regulation and judicial decisions;
  - `literature`: the claim is based on or summarizes previous findings from the scientific literature;
  - `abstract`: the claim is based on abstract/conceptual considerations.

- **`claim_jurisdiction`** — legal system(s) the claim is about or the jurisdiction(s) of the data the claim is based on. It can be more than one. Possible values:
  - an ISO 3166-1 alpha-2 code for a state, or `EU` for the European Union
  - `general`: the claim is explicitly not tied to any legal system or concerns law in general (the source presents it as jurisdiction-independent);
  - `undetermined`: the claim does not say and the context does not settle it.

- **`legal_reference`** — instruments and provisions the claim is about, as written in the source, e.g. "AI Act, Art. 5"; "GDPR, Art. 22"; "Smith v Jones [2023] EWHC 1"; empty when none.

- **`temporal_reference`** — date or period of the legal or factual state the claim describes, when stated; otherwise `as_of_publication`.

- **`concepts`** — concept ids; the `map-concepts` skill owns the count and the per-family cap.

- **`datasets`** — the dataset ids the claim rests on, where it rests on any. A claim evaluated on three benchmarks names three.

- **`run_ids`** — `schema/run.md`.
