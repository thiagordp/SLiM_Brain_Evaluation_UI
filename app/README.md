# SLiM Brain — human evaluation, instrument 4.1

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
What was requested, how it was built, and an assessment: [`../docs/EVALUATION_V4_REPORT.md`](../docs/EVALUATION_V4_REPORT.md).

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
| Source | nothing — metadata (the DOI with a small link to doi.org, opening in a new tab) and the complete Source wiki, as context, with its exact file under "Raw Markdown" |
| Claims, one at a time | **Claim evaluation** Q2–Q5 · **Schema fields** Q6–Q11 · **Concepts** Q12–Q14 · **Relations** |
| Datasets, one at a time | Dataset node, Introduced by, Language, Jurisdiction, Description, Availability |
| Claim recall | four-level completeness, Missing Claims below "All", and Restatements (groups of Claims stating the same proposition) |
| Review | every judgment, what is still missing, completion |

The wording is exactly the agreed wording (`spec.py`; `tests/test_app.py` pins
it). Evaluators never see an internal identifier.

- **No Question 1.** Instrument 4.1 removed the per-Claim restatement question;
  restatements are judged once per Source, in Claim recall. The other question
  keys keep their numbers (Q2–Q14).
- **Guidance** is always in a closed expander labelled **Instructions**, whether
  it comes from the schema or a skill. Where the calibration meeting added
  practical guidance, the block has two separately headed parts: **Schema /
  skill** (the frozen text, unchanged) and **Calibration** (from
  `spec.CALIBRATION`). Calibration appears at the start of Claim evaluation
  (three lines, Calibration only), under Basis, under Claim jurisdiction and
  under Relation Direction. It is not schema text: it is kept out of
  `definitions_v4.json` and `definitions_id`, and is recorded in the round's
  DEFINITIONS tab as `calibration.*` with source "calibration meeting (spec
  4.1)". Values and evidence (statement, assigned
  values, anchors, Description, relation endpoints, type, grounding, Note) stay
  outside it.
- **Claim under review.** On the Claim page the Claim id and statement stay
  pinned under the header while the page scrolls. It uses the documented
  keyed-container class and Streamlit's `stLayoutWrapper` test attribute, and it
  relies on the Streamlit pin: if a future version changes that wrapper, the
  panel becomes an ordinary card at the top of the page, and nothing else is
  affected.
- **Questions 3 and 4** carry the extract-claims skill's modality and
  standalone-statement passages, frozen verbatim.
- **Question 5**: Yes / In part / No, with all anchors (quote and location)
  shown in place.
- **Questions 6–11** each show the field, the value the Brain assigned, and —
  under Instructions — the complete frozen definition with every category and
  its meaning.
- **Question 12**: one independent Yes / No per assigned Concept, grouped by
  the six Concept families; each Concept shows its name and family, never its
  status. **No generated Concept definition is shown** in Q12,
  Q13 or Q14: Concepts are judged by the shared vocabulary itself.
- **Question 13**: one per assigned *candidate* Concept, shown as
  "family · Candidate"; absent when there is none.
- **Question 14**: a Concept browser with local, ranked search over name, id and
  family — never definitions — and results grouped by family, each shown with
  its name and family only (no status). Already-assigned
  Concepts are excluded. A separate *Selected missing Concepts* area lists each
  choice with its × on the right. There is an explicit "No additional Concepts
  are missing", and a new Concept can be proposed (name, family, optional
  reason). Directly above the proposal form: "Propose a new Concept only when no
  existing Concept can represent this Claim without bending it." A proposal is stored with the evaluation and never creates a Brain
  Concept.
- **Relations**: only SUPPORTS, ATTACKS and SAME_AS between Claims. Each graph
  Relation is evaluated exactly once, on the page of its **From** Claim (every
  Claim Relation in this Brain joins two Sources). The To side shows it as
  context. The card keeps the true From → To direction, marks the current
  Claim, and shows grounding and Note. Grounding has a short Quick guide above
  its question; the create-edges rule itself is under Instructions, word for
  word. For SUPPORTS and ATTACKS a **Direction** judgment sits between
  Grounding and Relation type: the assigned arrow ("CLM-a → CLM-b"), "Is the
  direction of this relation correct?", Yes / No, an optional comment on No, and
  Instructions with the edge schema's from/to text and the Direction
  calibration. SAME_AS is treated as symmetric and asks no Direction. Grounding,
  Direction and Relation type are independent: none disables, answers or clears
  another.
- **Restatements** (Claim recall, after completeness and Missing Claims): "Are
  any extracted Claims restatements of the same proposition?" No / Yes. On Yes
  the evaluator selects two or more of the Source's Claims and adds them as a
  group; several groups may exist. A group has no primary or canonical member.
  A Claim can be in only one active group — a second placement is refused with
  the reason. While groups exist the answer stays Yes and No is disabled ("Remove
  the restatement groups to answer No."); each group has a Remove button.
- **Datasets**: the Datasets the Source's Claims rest on. With none, no Dataset
  question is asked. There is intentionally no Dataset-recall question.
- There is **no** CITES evaluation, no Source-level Concept completeness, and no
  Premise, Positive form, Basis qualifier, jurisdiction relation/inferred,
  Plausibility, Compatible with, In tension with, Document type, Size,
  Annotation, Agreement reported or Used by.

### Comments

Structured judgments come first. What is **required**:

- the Restatements answer, and on Yes at least one valid group;
- the Question 14 state (a selection, or "none missing");
- the Description comment on *In part* / *No*;
- the Missing Claims text when recall is below "All".

Every other comment is optional and appears only on a negative answer. It never
blocks completion.

### Meaning is per question

`spec.py` declares each question's semantics: `correctness_binary`,
`correctness_ternary`, `set_valued` (Q14),
`ordinal4` (recall), `qualitative` and `restatement_groups` (stored `none` /
`present`, shown No / Yes). Review highlighting, progress and
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
| RESPONSES | one scalar judgment: Q2–Q11 per Claim, Q14 state, Dataset questions, recall, Missing Claims, Restatements state |
| CONCEPT_RESPONSES | one Claim × Concept judgment (Q12) or Claim × candidate judgment (Q13) |
| RELATION_RESPONSES | one graph Relation: copies of From, To, type, grounding, Note, plus the Grounding, Direction and Type judgments (`direction_*` empty for SAME_AS) |
| MISSING_CONCEPTS | one Concept selected as missing for one Claim (`active` flag) |
| PROPOSED_CONCEPTS | one proposed Concept for one Claim (`active` flag) |
| RESTATEMENTS | one Claim's membership of one restatement group (`group_id`, `active` flag) |
| SUBMISSIONS | one final phase submission |

- **Preallocated.** Every REVIEWS, RESPONSES, CONCEPT_RESPONSES and
  RELATION_RESPONSES row a review can need is created by bootstrap, in one
  contiguous block per review, with its row range recorded on the review.
  Nobody appends to these tabs during a round.
- **One read per paper.** Opening a paper is a single `values.batchGet`: the
  three blocks plus the three selection tabs.
- **Narrow, conflict-checked writes.** Answers are saved in the background in
  batches. Each write names its row and carries the row's `updated_at`, so the
  same evaluator in two browser tabs gets a conflict, not a silent overwrite.
  The session's own earlier writes to that row are not conflicts. Conflicts are
  **per answer**: the rest of a batch is still written. A row that already
  holds exactly the values being written is never a conflict — that is a retry
  whose first attempt reached Google although its response was lost (a timeout,
  a quota error), so a retry can never report a stored answer as "not applied".
- **Free text is bounded** (comments 5,000 characters, Missing Claims 20,000),
  well inside Google's 50,000-character cell limit.
- **Integrity check.** `tools/audit_workbook.py`, or Admin → System → *Check
  data integrity*, reads the whole workbook (two requests) and checks it
  against the instrument, the Brain and the round layout: block ranges and
  keys, every row the instrument needs and no other, every answer among its
  question's options, Question 14 and Restatements state against their
  selections and groups, SAME_AS without Direction, complete and submitted
  papers with nothing missing, submissions with their marker. Read-only; it
  reports, a person decides. `app/integrity.py` documents each check.
- **Idempotent selections.** The three selection tabs grow by upserts on
  deterministic keys (`review|claim|concept`, `review|claim|proposal`,
  `review|group|claim`). Removal
  sets `active = FALSE` on the same row. On load, rows sharing a key collapse to
  the latest, so a duplicate appended by two sessions at once cannot enter the
  effective state.
- **Question 14's state** lives on its RESPONSES row: `""` (not evaluated),
  `none_missing`, or `missing` (with at least one active selection or
  proposal). Search text is never stored.
- **Restatement groups.** `group_id = "RG-" + sha256("|".join(sorted ids))[:12]`,
  so the same set of Claims is always the same group, whatever the selection
  order. A group is validated before it is written (Claims of this Source, at
  least two distinct, none already in another active group); removal sets its
  rows `active = FALSE`, and re-adding the same set reactivates them. The
  Restatements state (`none` / `present`) is stored on its RESPONSES row and is
  never inferred from the groups; malformed stored groups are ignored for
  completion and reported under Review.

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

The allocation file is the only place an allocation is written. The current one,
**CLUSTER-2026-09-28**, is generated from the corpus-sampling clusters by the
separate `reviewer_allocation/` tool (see its README), which shares nothing with
this app except that file:

- Training: SRC-0006 and SRC-0009, for all seven evaluators;
- Agreement: four papers per group, each from the group's cluster —
  P1 Francesca + Thibault + Thiago (cluster 0), P2 Alessandro + Giuseppe
  (cluster 1), P3 Giovanni + Vaclav (cluster 2);
- Individual: the twelve remaining papers, one or two per evaluator (own-cluster
  leftovers, then the shared compliance cluster 3 dealt at random).

Agreement groups may have **two or more** members; every member evaluates every
paper of the group's set, and agreement is computed over every pair of members.

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

  In a group of three, every pair of its members is compared and the metric
  pools those pairwise comparisons.

Direction is exported as its own row in `relation_judgments` (SUPPORTS and
ATTACKS only) and, being binary, gets Cohen's κ like Grounding and Type.
`restatement_groups` has one row per Claim membership of an active group, with
review provenance; `raw_restatements` keeps every row, removed ones included.
Question 14 sets, proposals, restatement groups and Missing Claims are exported
raw. No metric is invented for them.

After "Prepare exports" (one read of the workbook), the main button **Download
all tables (.xlsx)** gives every table in one workbook, one tab per table, named
after it; empty tables keep their tab. Characters Excel cannot store are dropped
and cells are cut at Excel's 32,767-character limit — the per-table CSVs, under
"Individual tables (CSV)", keep the text exactly.

## Files

| File | Role |
|---|---|
| `streamlit_app.py` | guards, login, paper list, paper routing, submission, Admin |
| `views.py` | Source, Claims, Datasets, Claim recall, Review |
| `ui.py` | review cache, autosaving controls, wiki modal, definition blocks |
| `spec.py` | instrument 4.1: questions, semantics, frozen definitions, calibration |
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
