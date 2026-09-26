# Record: Hypothesis

A conjecture about the literature that the corpus cannot yet settle.

Hypotheses live in `wiki/hypotheses.jsonl`, beside the graph rather than in it: a conjecture is inferred by construction, so it is never cited as evidence and never deleted — a refuted one records something the corpus turned out to answer.

The gate checks the structure, not the conjecture. It cannot tell you whether a hypothesis is true or worth holding; it can insist that it is testable and that a retest is honest about what it proved.

## Fields

- **`id`** — prefixed `HYP-`. Example: `HYP-0001`.

- **`date`** — when the conjecture was written.

- **`statement`** — the conjecture, stated so a reader can see what would settle it. Example: "No paper addresses liability for hallucinated citations in a civil-law country".

- **`concepts`** — concept ids the conjecture is about. A query that touches one of these is what brings the hypothesis up for retest.

- **`absences`** — ABS ids it rests on, where it rests on any.

- **`query`** — the filter over `claims.jsonl` that would confirm or refute it. An entry without one is not a hypothesis.

- **`status`** — one of `open` | `confirmed` | `refuted`.

- **`evidence`** — the claim ids that settled it, once something does.

- **`retests`** — a list of `{date, run, retest_type, result, evidence}`, one per retest. `retest_type` is one of:
  - `query_sharpened`: the question was reworded;
  - `corpus_updated`: papers were added since;
  - `model_changed`: a different model re-ran it.

- **`run_ids`** — `schema/run.md`. The run also carries the corpus size at the time, which is what tells a later reader how much the conjecture was drawn from.
