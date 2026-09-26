# SLiM Brain — human evaluation, instrument 4.0

An evaluation interface over the current Brain (schema 0.1.0). It shows each
Brain record next to the question about it, with the Brain's own definition
directly below, and stores the evaluator's judgment. It never writes to the
Brain.

```bash
pip install -r requirements.txt
python app/tests/test_app.py                  # in-memory workbook; must end "0 failed"
python app/tools/preflight.py                 # is the Brain snapshot evaluable?
streamlit run app/streamlit_app.py            # needs a bootstrapped round workbook
```

Deployment, workbook bootstrap and secrets: [`../DEPLOYMENT.md`](../DEPLOYMENT.md).

## Flow

```
password -> evaluator (locked for the session) -> Training | Agreement | Individual
    -> paper list -> "I have read the full paper" -> paper:
       Source · Claims · Datasets · Claim recall · Review
    -> mark paper complete -> final phase submission
```

The three phases are independent and open from the start. Training is optional.
Within a paper every section can be opened at any time. Completeness is
enforced only at "Mark paper complete" and at final submission, and both
re-read the stored answers first.

## The instrument

| Page | Asks |
|---|---|
| Source | nothing — metadata and the complete Source wiki, as context |
| Claims, one at a time | **Claim evaluation** Q1–Q5 · **Schema fields** Q6–Q11 · **Concepts** Q12–Q14 · **Relations** |
| Datasets, one at a time | Dataset node, Introduced by, Language, Jurisdiction, Description, Availability |
| Claim recall | four-level completeness, and Missing Claims below "All" |
| Review | every judgment, what is still missing, completion |

The wording is exactly the agreed wording (`spec.py`; `tests/test_app.py` pins
it). Evaluators never see an internal identifier.

- **Question 1** (restatement): on *Yes* the evaluator selects which
  already-evaluated Claim of the Source is restated. The Claim id is stored as
  structured data (`related_claim_id`). A restatement is an extraction problem,
  not a SAME_AS edge.
- **Question 5**: Yes / In part / No, with all anchors (quote and location)
  shown in place.
- **Questions 6–11** each show the field, the value the Brain assigned, the
  complete definition, and every category with its meaning. The assigned
  category is marked in words.
- **Question 12**: one independent Yes / No per assigned Concept, grouped by
  the six Concept families.
- **Question 13**: one per assigned *candidate* Concept; absent when there is
  none.
- **Question 14**: a Concept browser. It offers local, ranked search over name,
  id and definition, with results grouped by family. Already-assigned Concepts
  are excluded. A separate *Selected missing Concepts* area shows each choice
  as "Name ×". There is an explicit "No additional Concepts are missing", and a
  new Concept can be proposed (name, family, optional reason). A proposal is
  stored with the evaluation and never creates a Brain Concept. Anchors in the
  frozen grid that have no Concept page show "Definition not available in the
  current Concept wiki". No definition is invented.
- **Relations**: only SUPPORTS, ATTACKS and SAME_AS between Claims. Each graph
  Relation is evaluated exactly once, on the page of its **From** Claim (every
  Claim Relation in this Brain joins two Sources). The To side shows it as
  context. The card keeps the true From → To direction, marks the current
  Claim, and shows grounding and Note. Grounding and Relation type are two
  independent judgments.
- **Datasets**: the Datasets the Source's Claims rest on. With none, no Dataset
  question is asked. There is intentionally no Dataset-recall question.
- There is **no** CITES evaluation, no Source-level Concept completeness, and no
  Premise, Positive form, Basis qualifier, jurisdiction relation/inferred,
  Plausibility, Compatible with, In tension with, Document type, Size,
  Annotation, Agreement reported or Used by.

### Comments

Structured judgments come first. What is **required**:

- the restated Claim on Q1 = Yes;
- the Question 14 state (a selection, or "none missing");
- the Description comment on *In part* / *No*;
- the Missing Claims text when recall is below "All".

Every other comment is optional and appears only on a negative answer. It never
blocks completion.

### Meaning is per question

`spec.py` declares each question's semantics: `restatement_flag` (Yes =
defect), `correctness_binary`, `correctness_ternary`, `set_valued` (Q14),
`ordinal4` (recall) and `qualitative`. Review highlighting, progress and
analysis read these. Nothing infers correctness from the literal word "Yes".

## Definitions shown to evaluators

`data/definitions_v4.json` is frozen from the Brain's `schema/*.md` and its
`create-edges` skill by `tools/freeze_definitions.py`. The passages are verbatim
(tests check every one against its source). At display time only the backtick
markup is dropped, so no schema name or value appears in code typography. Field
and category names are shown as words ("Claim object", "On request").

The file records the source files' hashes, the canonical schema version
(`schema/__index__.md`) and a `definitions_id`. Every round records which
`definitions_id` its evaluators saw, and writes the definitions themselves into
its DEFINITIONS tab.

## Storage: one Google Sheets workbook per round

Google Sheets is the only persistent store. Nothing falls back to anything
else. Each round is a fresh workbook, initialised by `tools/bootstrap_round.py`.
Review ids carry the round namespace:

```
ROUND-2026-01|agreement|thiago|SRC-0001
```

| Tab | One row = |
|---|---|
| ROUND | one metadata key: round, instrument, definitions, snapshot, schema, runs, allocation |
| DEFINITIONS | one definition shown to evaluators |
| CONFIG / EVALUATORS / ASSIGNMENTS | switch / evaluator / explicit assignment |
| REVIEWS | one evaluator × paper: status, provenance, block ranges |
| RESPONSES | one scalar judgment: Q1–Q11 per Claim, Q14 state, Dataset questions, recall, Missing Claims |
| CONCEPT_RESPONSES | one Claim × Concept judgment (Q12) or Claim × candidate judgment (Q13) |
| RELATION_RESPONSES | one graph Relation: copies of From, To, type, grounding, Note, plus both judgments |
| MISSING_CONCEPTS | one Concept selected as missing for one Claim (`active` flag) |
| PROPOSED_CONCEPTS | one proposed Concept for one Claim (`active` flag) |
| SUBMISSIONS | one final phase submission |

- **Preallocated.** Every REVIEWS, RESPONSES, CONCEPT_RESPONSES and
  RELATION_RESPONSES row a review can need is created by bootstrap, in one
  contiguous block per review, with its row range recorded on the review.
  Nobody appends to these tabs during a round.
- **One read per paper.** Opening a paper is a single `values.batchGet`: the
  three blocks plus the two selection tabs.
- **Narrow, conflict-checked writes.** Answers are saved in the background in
  batches. Each write names its row and carries the row's `updated_at`, so the
  same evaluator in two browser tabs gets a conflict, not a silent overwrite.
  The session's own earlier writes to that row are not conflicts.
- **Idempotent selections.** The two selection tabs grow by upserts on
  deterministic keys (`review|claim|concept`, `review|claim|proposal`). Removal
  sets `active = FALSE` on the same row. On load, rows sharing a key collapse to
  the latest, so a duplicate appended by two sessions at once cannot enter the
  effective state.
- **Question 14's state** lives on its RESPONSES row: `""` (not evaluated),
  `none_missing`, or `missing` (with at least one active selection or
  proposal). Search text is never stored.

## Brain snapshot and preflight

`brain.py` reads `brain/wiki/` read-only. Frontmatter is parsed the way the
Brain's own `tools/gate.py` parses it, as flat `key: value` lines, not YAML. The
snapshot id is a SHA-256 over the runtime files, `runs.jsonl` and `schema/`.

`preflight.py` checks, before bootstrap and at every app start:

- required Claim fields, enums and jurisdiction codes;
- that Concept and Dataset ids resolve, and Concept families and statuses;
- grid anchors against their pages;
- Dataset availability;
- Relation types, grounding, Notes and endpoints;
- the schema files against the frozen definitions;
- a dry build of every evaluation item.

Runs whose recorded schema version differs from the canonical one are listed as
warnings. No single schema version is inferred from run history.

## Allocation

```
data/allocation/<round>.yaml  --build_assignments.py-->  data/manifest.yaml  --bootstrap_round.py-->  workbook
```

The allocation file is the only place an allocation is written. The current one
is a **development allocation**:

- Training: SRC-0006 and SRC-0009, for all six evaluators;
- Agreement: two papers per pair — A Thiago + Francesca, B Giuseppe + Vaclav,
  C Giovanni + Alessandro;
- Individual: 17 papers, three per evaluator, except Alessandro, who has two
  until the 26th Source arrives.

`reserved` rows remain a generic capability. The app never infers an assignment
from a pair or split name.

## Exports and agreement

Admin → Exports gives:

- the raw tabs;
- normalised tables joined with review provenance (every row names its
  `round_id` and `eval_spec_version`);
- for the agreement phase, the paired units and the metrics per question:
  - binary items: observed agreement and Cohen's κ;
  - Q5 and Dataset Description: observed agreement and linear-weighted κ;
  - Claim recall: linear-weighted κ.

Question 14 sets, proposals, Q1 targets and Missing Claims are exported raw.
No metric is invented for them.

## Files

| File | Role |
|---|---|
| `streamlit_app.py` | guards, login, paper list, paper routing, submission, Admin |
| `views.py` | Source, Claims, Datasets, Claim recall, Review |
| `ui.py` | review cache, autosaving controls, wiki modal, definition blocks |
| `spec.py` | instrument 4.0: questions, semantics, frozen definitions |
| `progress.py` | dynamic items, criterion-specific completion, storage layout |
| `store.py` / `sheets.py` | the round workbook |
| `savequeue.py` | background write queue: collapse, batch, retry |
| `brain.py` | read-only Brain adapter |
| `preflight.py` | snapshot compatibility checks |
| `allocation.py` | allocation file validation and expansion |
| `analysis.py` | normalised exports and agreement |
| `conceptsearch.py` | Question 14 search |
| `data/definitions_v4.json` | frozen definitions |
| `data/round.yaml`, `data/allocation/`, `data/manifest.yaml` | the round's configuration |
| `data/archive/v3/` | the instrument 3.0 criteria and tools, kept for provenance only |
| `tools/freeze_definitions.py`, `build_assignments.py`, `preflight.py`, `bootstrap_round.py`, `check_sheets.py`, `snapshot_config.py`, `make_secrets.py`, `check_archive.py` | see DEPLOYMENT.md |
| `tests/test_app.py`, `tests/fakes.py`, `tests/live_sheets.py` | tests; the last only against a disposable real workbook |
| `tests/run_with_fake.py` | look at the UI in a browser against an in-memory round (test tool; answers vanish on exit) |

## Version 3

Instrument 3.0 (HE-xx criteria) is retired, not reinterpreted. Its answers stay
in their own workbook with their original meaning. Its criteria, tools and
configuration snapshots are in `data/archive/v3/`. The v3-era Brain fixture is
kept locally in `brain_v3_legacy/` (ignored by git).
