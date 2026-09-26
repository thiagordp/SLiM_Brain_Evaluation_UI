# Evaluation instrument 4.0: requirements, implementation and assessment

This report documents the revision of the SLiM Brain evaluation interface from
instrument 3.0 to instrument 4.0. It covers:

1. what was requested;
2. how the system worked before;
3. how the change was planned;
4. how it was carried out;
5. whether the result is what was requested.

State described: commit `6e79ecf` ("UI with New schema"), with a working tree
identical to it. Verified on 2026-09-26:

- `app/tests/test_app.py`: 200 checks, 0 failed;
- `app/tools/preflight.py`: 0 errors, 0 warnings;
- `app/tools/freeze_definitions.py --check`: definitions current
  (`b91c79054a40c224`).

---

## 1. What was requested

### 1.1 The specification (`new_intructions.txt`)

The instruction was to follow the specification literally and to start by
planning. Its 54 sections, grouped:

| Theme | Sections | Requirement, in short |
|---|---|---|
| Sources of truth | 1 | Current Brain schema and skills first; then meeting notes; then the old workbook and app, as history only |
| Language and typography | 2 | Concise, scientific wording; no HE identifiers; no code or monospace styling for schema names or values; each value next to its question |
| Definitions | 3, 46 | The complete definition under each schema question; every category of a categorical field; the jurisdiction rule, not ISO lists; definitions frozen for the round |
| Navigation | 4, 6 | Source → Claims → Datasets → Claim recall → Review; Claims one at a time ("Claim 3 of 8"); Concepts and Relations inside each Claim; answers persist across navigation |
| Source | 5, 50 | Information only; the full wiki inline; no counts, no questions, no CITES; no obsolete relation terminology |
| Claim Q1–Q5 | 7 | Exact wording. Q1 on Yes requires selecting the restated Claim from Claims already evaluated, stored structurally, with no SAME_AS edge. Q2 shows the Claim definition. Q3 shows anchors nearby. Q5 is Yes / In part / No with every anchor (quote and location). Premise removed |
| Schema fields Q6–Q11 | 8, 9 | One pattern: name, assigned value, definition, categories, question, Yes/No, correction on No. Removed: Positive form, Basis qualifier, Jurisdiction relation, Jurisdiction inferred |
| Concepts Q12–Q14 | 10–13 | The six families. Q12 is one judgment per assigned Concept, grouped by family. Q13 is for candidates only. Q14 is a search-and-select browser that excludes assigned Concepts, keeps selections when the search changes, shows a separate "Selected missing Concepts" area with × controls, has an explicit "no additional Concepts are missing" state, and allows proposing a new Concept without touching the Brain |
| Relations | 14–18 | Only Claim-to-Claim SUPPORTS, ATTACKS and SAME_AS. True From → To direction, with the current Claim marked. Grounding and Relation type judged independently. The Note stays visible. Each graph Relation evaluated once |
| Datasets | 19–27 | One at a time; the Dataset wiki in a modal that preserves state; no questions when there is no Dataset; no Dataset recall. Removed: Document type, Size, Annotation, Agreement reported, Used by. Description is Yes / In part / No with a required comment on In part / No |
| CITES | 28 | Removed from the human evaluation entirely |
| Claim recall | 29–31 | A four-level ordinal control (None / Some / Most / All); Missing Claims text for None, Some and Most; the Source-level Concept completeness question (HE-20.S) removed |
| Empty states, comments, Review | 32–34 | No fake N/A answers; comments secondary; Review lists only current items, per-Concept answers included |
| Backend | 35–44 | Impact analysis before building. Structured persistence for every new response. Identity at Claim×Concept and Relation level. A Q14 state model. Two Relation judgments. Dynamic progress. Criterion-specific semantics. Agreement defined per unit, with raw export where no metric exists. Both backends consistent. Preallocation reviewed |
| Versioning and provenance | 45–47 | A new spec version; v3 answers keep their meaning; frozen definitions; a preflight that rejects an incompatible snapshot before evaluation, with an administrator diagnostic |
| Adapter and fixture | 48–50 | Rework the Brain adapter against the current schema; replace the old fixture; no obsolete semantics from stale wiki text |
| Scope | 51 | No evaluation of absences, hypotheses, runs, syntheses, CITES or Source SAME_AS |
| Sequence | 52 | Adapter and persistence analysis first, UI later; not "only the criteria JSON" |
| Credentials | 53 | Do not expose keys; rotate the bundled one; exclude it from future archives |
| Acceptance | 54 | 48 criteria (assessed in §5) |

### 1.2 Decisions given in answer to the planning questions

- **Allocation.**
  - Allocation lives in a human-editable file; `build_assignments.py` validates
    it and generates an explicit manifest, with no allocation hardcoded.
  - Six evaluators in pairs: A = Thiago + Francesca, B = Giuseppe + Vaclav,
    C = Giovanni + Alessandro.
  - Training papers: "Pseudolaw and the illusion of legal meaning" and
    "Automated Extraction of Judicial Interpretative Formulas in EU Case Law on
    VAT", for all six.
  - A **development allocation**: 6 Agreement papers (2 per pair) and the 17
    remaining papers Individual, as even as possible.
  - The generator validates: Training Sources exist and are used nowhere else;
    every other Source is placed exactly once; Agreement papers yield exactly
    two assignments; Individual papers have exactly one evaluator; every Source
    exists; no duplicate keys.
  - No fake 26th Source. `reserved` kept as a generic capability.
- **Storage.**
  - Google Sheets is the only persistent store; SQLite is removed entirely and
    there is no fallback.
  - One fresh workbook per round, initialised by a bootstrap that refuses to
    overwrite a round without explicit administrative action.
  - The round id is configurable; review ids look like
    `ROUND-2026-01|agreement|thiago|SRC-0001`.
  - Round metadata stored in the workbook, keeping round id, spec version,
    snapshot and schema version apart.
  - Tests use a fake workbook.
- **Comments.** Optional everywhere except:
  - the Dataset Description comment on In part / No;
  - Missing Claims below "All";
  - the restated Claim on Q1 = Yes;
  - the Q14 structured state.
- **Definitions.** Reproduced verbatim from the schema and skills, never
  paraphrased. Grounding is taken from the create-edges skill.

### 1.3 Corrections to the plan

1. Q2 shows both the Claim definition and the Statement definition.
2. Q14 search must not require every word to match.
3. The remove control sits to the right: "Name ×".
4. Grid-only Concepts show no invented definition.
5. Do not infer one schema version from run history. Record the snapshot hash,
   the schema-file hashes, `definitions_id`, the run ids, and the canonical
   version only if the Brain exposes one.
6. Ordered ternary items use linear-weighted κ.
7. The old split-generation path is retired; there is one supported path.
8. Concept-selection writes must be idempotent.

### 1.4 Operational requests

- Run the UI against the new spreadsheet `1--QWv5RtLoz6lxfxAR5lxRQQf-B9R6kswatEa8udAJg`.
- Write this report.

---

## 2. The original implementation (instrument 3.0)

| Aspect | v3 |
|---|---|
| Instrument | HE-xx criteria. Text extracted verbatim from `HE_review_form.xlsx` into `he_criteria.json`, with calibration layers `he_criteria_v2.json` and `he_criteria_v3.json` merged over it |
| Brain fixture | 50 Sources named by work ids (W0085, …). Old schema: Claims with Premise, Positive form, Basis qualifier, jurisdiction relation/inferred, a singular `dataset`; USES edges; COMPATIBLE_WITH and IN_TENSION_WITH relations; a Plausibility field; four Concept families (legal task, technique class, normative concern, other); a `label` field on Concepts; `used_by` and document types on Datasets |
| Sections | 1 Source (HE-08.x) · 2 Claims A–E · 3 Datasets (HE-14/15, with HE-14.3 Dataset recall) · 4 CITES (HE-18) · 5 Source-level completeness (HE-19.1, HE-20.S) · 6 Review |
| Scale | Yes / In part / No everywhere, with a comment required for In part and No; `SCORE = {Yes: 3, In part: 2, No: 1}` (defined, never used) |
| N/A | Three criteria decided automatically from the Brain record (`auto_na`); one evaluator-chosen N/A (HE-14.3) |
| Concepts | HE-12 one aggregate answer per Claim; HE-21 applicable only when a candidate's definition named the Claim; HE-20 plus a free-text list of missing Concepts |
| Relations | One label judgment per edge **per endpoint Claim** (`EDGE_RESPONSES` keyed by host Claim); HE-16 derived |
| Storage | SQLite by default, or Google Sheets when configured. Tabs: CONFIG, EVALUATORS, ASSIGNMENTS, REVIEWS, RESPONSES, EDGE_RESPONSES, PHASE_SUBMISSIONS. Preallocated blocks, narrow writes, an `updated_at` conflict token, and an asynchronous save queue (`savequeue.py`) |
| Configuration | `build_assignments.py` parsed the allocation **prose** in `Design/paper allocation/Evaluation_Splits.md`; IND-1 was a special reservation pool |
| Analysis | Raw table exports; no agreement computation |
| Tests | One ~6,800-line headless suite on a temporary SQLite database |

---

## 3. The plan

The full plan is `/home/trdp/.claude/plans/gentle-whistling-thompson.md`. It also
served as the backend and persistence impact analysis that §35 asks for.

### 3.1 Findings that shaped it

- The current Brain (`new_brain/`, schema 0.1.0) had 25 Sources, 374 Claims,
  107 Concepts, 25 Datasets and 266 edges. Its schema was byte-identical to
  `../SLiM_Brain/schema`, and the authoritative skills were in
  `../SLiM_Brain/.claude/skills`.
- **8 of 25 Dataset frontmatters are not valid YAML.** An unquoted colon sits
  inside `description`. The Brain's own `tools/gate.py` reads frontmatter
  line by line, not as YAML.
- **Every Claim-to-Claim edge joins two different Sources.** Hosting a Relation
  on its From Claim therefore evaluates it exactly once, in the From Source's
  review.
- 11 of the 50 anchors in the schema grid have no Concept page.
- 8 Sources have no Dataset.
- Source wikis still use "In tension with" headings.
- `../SLiM_Brain_Evaluation_UI.zip` contains `.streamlit/service-account.json`.
  It is not tracked in git.

### 3.2 Target architecture

The plan's ten parts:

1. Snapshot swap and adapter.
2. Frozen verbatim definitions.
3. A declarative spec 4.0 with per-question semantics.
4. Sheets-only storage with normalised tabs.
5. A round config, an allocation file and a bootstrap.
6. Dynamic progress.
7. Preflight.
8. Views.
9. Exports and agreement.
10. Hygiene and documentation.

It then followed the implementation sequence of §52.

---

## 4. What was done

### 4.1 Brain snapshot and adapter

- `brain/` now holds the current snapshot's `wiki/` and `schema/`. Schema files
  are tracked so the preflight can hash them. The v3 fixture was moved, not
  deleted, to `brain_v3_legacy/` (git-ignored).
- `brain.py` was rewritten:
  - frontmatter is read as the Brain's `gate.py` reads it;
  - `datasets` is plural;
  - `relations_from_claim` / `relations_to_claim` / `relations_hosted` keep the
    true From → To direction;
  - `concept_label` derives names deterministically from ids;
  - `vocabulary()` covers the Concept pages plus grid-only anchors, which get an
    empty definition;
  - `pdf_name()` gives the corpus file name;
  - the snapshot hash covers the wiki, `runs.jsonl` and `schema/`;
  - `canonical_schema_version()` is read from `schema/__index__.md`;
  - `run_schema_versions()` lists each run with its recorded version.
- All obsolete structures are gone: USES, `used_by`, singular `dataset`, the
  motivating-claims logic, Concept labels and work ids.

### 4.2 Frozen definitions

`tools/freeze_definitions.py` extracts verbatim passages from the snapshot
schema and from `create-edges/SKILL.md` into `app/data/definitions_v4.json`:

- 23 entries, among them:
  - the Claim node and Statement;
  - Anchors;
  - the six Claim fields with their categories;
  - the Dataset node and fields;
  - relation types (the Claim-to-Claim rows of the edge table);
  - the Relation Note;
  - Grounding (from the skill);
  - Concept node, status, family and definition;
- the 50-anchor grid;
- the hash of every source file;
- the canonical schema version and a `definitions_id`.

`--check` compares the file with the sources. At display time only the backtick
markup is removed.

### 4.3 Specification 4.0 (`spec.py`)

- 24 questions, each with:
  - a key;
  - a unit: claim, claim_concept, claim_candidate, relation, dataset or source;
  - the agreed wording, verbatim;
  - its options;
  - its semantics: `restatement_flag`, `correctness_binary`,
    `correctness_ternary`, `set_valued`, `ordinal4` or `qualitative`;
  - its definition references and follow-up rules (related Claim, optional or
    required comment, conditional child).
- `problem()`, `ordinal()`, `comment_visible()` and `comment_required()` are
  criterion-specific.
- No HE ids. The v3 criteria files and tools moved to `app/data/archive/v3/`.

### 4.4 Storage (`sheets.py`, `store.py`)

- **SQLite removed.** That covers the code, the migrations, the fallback and
  the local database. `store.workbook()` raises `StorageNotConfigured` when no
  workbook is configured.
- **12 tabs:**
  - metadata: ROUND, DEFINITIONS;
  - configuration: CONFIG, EVALUATORS, ASSIGNMENTS;
  - evaluation: REVIEWS, RESPONSES (scalar judgments, Q1's `related_claim_id`,
    the Q14 state), CONCEPT_RESPONSES (Q12/Q13 per Claim×Concept),
    RELATION_RESPONSES (one row per graph Relation, with copies of From, To,
    type, grounding and Note and two judgment/comment pairs), MISSING_CONCEPTS,
    PROPOSED_CONCEPTS and SUBMISSIONS.
- **Preallocated blocks** per review in the three block tabs, with ranges
  recorded on REVIEWS.
- **One `values.batchGet` per paper** (the three blocks and the two selection
  tabs).
- **Batched, conflict-checked writes.** A write's own earlier stamps are not
  treated as conflicts.
- **Selections.** Idempotent upsert: re-read the key column, then update or
  append. Removal sets `active = FALSE`; on load, duplicate keys collapse to the
  latest row.

### 4.5 Round, allocation and bootstrap

- **`data/round.yaml`** holds `round_id: ROUND-2026-01`; `HE_ROUND_ID`
  overrides it.
- **`allocation.py` + `data/allocation/ROUND-2026-01.yaml`:**
  - the development allocation, with titles checked against the Brain;
  - Training SRC-0006 and SRC-0009;
  - AGR-A SRC-0001/0002, AGR-B SRC-0003/0004, AGR-C SRC-0005/0007;
  - IND-1…IND-6 in blocks of three, with IND-6 (Alessandro) holding two.
- **`tools/build_assignments.py`:** validates the file and writes the explicit
  `manifest.yaml`: 12 Training, 12 Agreement and 17 Individual rows. The old
  prose parser and `import_split.py` were removed.
- **`tools/bootstrap_round.py`:**
  - validates preflight, allocation and manifest freshness;
  - refuses a non-empty workbook, or an existing round without
    `--overwrite-round <id>` (plus `--discard-evaluations` if work exists);
  - `--extend` adds new assignments;
  - writes ROUND, DEFINITIONS, CONFIG, EVALUATORS and ASSIGNMENTS;
  - preallocates, then reads back the first and last row of every block.
- **On the real workbook it created** 41 reviews, 7,810 RESPONSES,
  2,359 CONCEPT_RESPONSES and 452 RELATION_RESPONSES in 38 s, and every block
  verified.

### 4.6 Preflight (`preflight.py`, `tools/preflight.py`)

**Errors:**
- load problems;
- schema-file hash or canonical-version mismatch with the frozen definitions;
- required Source, Claim and Dataset fields;
- Claim enums and jurisdiction codes;
- Concept and Dataset references;
- Concept status and family, and the grid agreeing with the pages;
- Dataset availability and `introduced_by`;
- edge types, endpoints, grounding, Notes and duplicates;
- a dry build of every evaluation item.

**Warnings:**
- runs recorded under another schema version;
- obsolete fields present;
- a Dataset introduced by a Source that no Claim of that Source rests on;
- non-ISO language codes.

The current snapshot has 0 errors and 0 warnings.

### 4.7 Progress (`progress.py`)

Items are generated from the record:

- per Claim: Q1–Q11, one Q12 per assigned Concept, one Q13 per candidate, one
  Q14, and two judgments per Relation hosted by that Claim;
- six questions per Dataset;
- recall, plus Missing Claims when it is shown.

Completion follows the required-data rules, and optional comments never block
it. There are no Source or CITES counts. `review_rows()` defines the
preallocation layout.

### 4.8 Interface (`ui.py`, `views.py`, `streamlit_app.py`, `conceptsearch.py`)

- **Saving.** Every control saves through `on_change`, writing through the
  session cache so counts update immediately. Writes are queued.
- **Guards, in order:** storage reachable and correctly shaped → preflight
  (evaluators see "not available"; the admin secret shows the diagnostic) →
  workbook ROUND matches round, spec, definitions and snapshot.
- **Source:** metadata and the full wiki. Obsolete headings are relabelled
  "Attacks" / "Attacked by", and local links become plain text.
- **Claim:**
  - "Claim i of n" with a selector and the statement card;
  - four parts with dynamic counts;
  - Q1 with the restatement selector;
  - Q2 with both definitions;
  - Q3 and Q5 with the anchors;
  - Q6–Q11 in the field pattern, with the assigned category marked in words;
  - Q12 grouped by family;
  - Q13 for candidates;
  - Q14 browser: ranked local search, results grouped by family, a bordered
    "Selected missing Concepts" area with "Name ×", the explicit checkbox, and a
    proposal form;
  - Relations: a From / type / To card with the current Claim marked, grounding
    and Note, "Open Claim" / "Open Source" in the modal, two judgments, and
    incoming Relations as read-only context.
- **Datasets:** "Dataset i of n", the modal wiki, the six questions, and a
  message plus a continue button when there is none.
- **Claim recall:** the Claim list, a segmented four-level control, and Missing
  Claims with the agreed instruction.
- **Review:** section status, the missing items with "Go" buttons, every answer
  per item (flagged answers marked in words), and "Mark paper complete" after a
  flush and re-read.
- **Admin:** progress, assignments and reservation activation, phases, reopen,
  exports, and system (round metadata, preflight, configuration).

### 4.9 Exports and agreement (`analysis.py`)

- **Raw tabs**, exported as stored.
- **Normalised tables** — `claim_judgments`, `concept_judgments`,
  `missing_concepts_state`, `missing_concepts`, `proposed_concepts`,
  `relation_judgments`, `dataset_judgments`, `claim_recall` — each row joined
  with `round_id`, `eval_spec_version`, `definitions_id`, the snapshot, phase,
  evaluator, pair and split.
- **Agreement** (agreement phase only):
  - paired units;
  - Cohen's κ for binary items;
  - linear-weighted κ for Q5, Description and recall;
  - no metric for Q14, proposals, Q1 targets or Missing Claims.

### 4.10 Tests and tools

- `tests/fakes.py` is an in-memory workbook that counts requests.
  `tests/test_app.py` (200 checks) covers:
  - adapter, definitions and spec wording;
  - allocation rules with negative cases;
  - preflight rejection cases;
  - bootstrap refusals, overwrite and verification;
  - store round-trip, conflicts, idempotence and deduplication;
  - progress rules, the zero-Claim Source, search and agreement;
  - UI guards, the Claim/Q14 flow, the no-Dataset path, completion, the
    preflight page, Dataset and Concept independence, and submission locking.
- `tests/live_sheets.py` is an integration check against a disposable real
  workbook. `tests/run_with_fake.py` previews the UI in memory.
  `tools/check_archive.py` flags credentials inside zip files.
- `check_sheets.py`, `snapshot_config.py` and `make_secrets.py` were updated;
  `bootstrap_sheets.py` and `preallocate.py` were removed.
- `app/README.md` and `DEPLOYMENT.md` were rewritten.
  `Evaluation_Splits.md` is marked historical.

### 4.11 Operational log

For transparency:

- **Local database:** deleted `app/data/evaluations.sqlite`, as requested. It
  held one development review.
- **v3 config snapshots:** deleted by mistake, then restored from git into
  `app/data/archive/v3/config_snapshots/`.
- **The key used for the bootstrap:** the key in `~/.config/slim-brain/`
  belongs to a deleted service account. The live bootstrap therefore used
  `.streamlit/service-account.json`
  (`slim-brain-eval-bot-625@slim-brain.iam.gserviceaccount.com`), **the same key
  that is in the leaked archive.**
- **Browser review:** the visual review in Chrome was abandoned after the page
  renderer froze. The UI was verified headlessly with AppTest only.
- **Local run:** the app was started against the new workbook with temporary
  local passwords, then restarted bound to `localhost`.

---

## 5. Assessment: is what was built what was asked?

### 5.1 Acceptance criteria (§54)

| Criterion | Status | Evidence |
|---|---|---|
| Source shows the complete wiki, no questions | Met | `source_section`; test "the Source page asks nothing" |
| Claims one at a time | Met | `claims_section` |
| Q1 wording, and the restated Claim stored structurally | Met | `related_claim_id` column; wording test; UI test |
| Q2–Q11 exact wording | Met | wording tests for all 24 questions |
| Field questions show value and complete definition; categories with meanings | Met | `field_question`, `definition_html`; UI test "Claim object shows every category" |
| No code typography | Met | UI tests on the Claim and Dataset pages. Admin tables show raw column names (admin only) |
| Removed Claim fields absent | Met | UI test |
| Q12 grouped by the six families, independent answers | Met | UI test "each Concept judgment is independent" |
| Q13 only candidates, independent | Met | progress test |
| Q14 excludes assigned, free-text search, grouped results | Met | `missing_concepts` |
| Q14 keeps selections across searches; separate selected area; × control | Met | UI test "selections persist…", "× removes…" |
| Q14 distinguishes unanswered from none missing; proposals; Brain untouched | Met | Q14 state model; UI and progress tests |
| Relations keep From → To; evaluated once; independent judgments; Note visible | Met | `relations_hosted`; adapter test (265 hosted = 265 Relations) |
| No Plausibility, Compatible with, In tension with | Met | adapter and UI tests |
| Datasets one at a time; modal keeps state; none → no questions | Met | UI tests |
| Removed Dataset fields absent; Description Yes / In part / No with required comment | Met | UI tests |
| No human CITES | Met | no CITES section, question or count |
| Recall None / Some / Most / All; Missing Claims for None / Some / Most; no Source-level Concept completeness | Met | `recall_section`; progress test |
| Review only current items | Met | UI test |
| Dynamic progress | Met | progress tests |
| Structured selections persist across reruns and navigation | Met | UI and store tests |
| No global Yes/No inference | Met | `spec.problem` per semantics; spec tests |
| Own spec version; v3 data intact | Met | `EVAL_SPEC_VERSION = "4.0"`; separate workbook |
| Reproducible definitions | Met | frozen JSON, the DEFINITIONS tab, `definitions_id` on reviews and ROUND |
| Incompatible snapshot rejected before evaluation | Met | preflight; UI test |
| Sheets and SQLite implement the same model | Superseded | by the decision to use Sheets only |
| Exports preserve structured data | Met | `analysis.normalised` |
| Concise, natural, scientific interface | Unverified visually | wording reviewed in code; no visual review |

### 5.2 Decisions and corrections

| Item | Status |
|---|---|
| Allocation file, validating generator, explicit manifest, the six rules, development allocation, no fake Source | Met |
| Generic `reserved` kept | Partly met: stored, preallocated and activatable, but Admin has no "return to reserved" control |
| Sheets only; no SQLite; no fallback; one workbook per round; namespaced ids; safe bootstrap; self-describing metadata | Met (tested; bootstrap exercised on the real workbook) |
| Comment rules | Met (progress tests) |
| Definitions verbatim; Grounding from the create-edges skill | Met (verbatim tests) |
| Corrections 1–6 and 8 | Met |
| Correction 7 (retire the old split path) | Mostly met. The old parser and `import_split.py` are removed, and `Evaluation_Splits.md` is marked historical. The README does not mention the Brain's `make_eval_splits.py`, as the plan promised, and that script still exists in the Brain repository (outside this project) |

### 5.3 Interpretations made

- **"Already evaluated" Claims (Q1 selector)** are the Claims with at least one
  stored answer.
- **Category and value names** are shown as words ("On request", "SAME AS",
  "As of publication"). Definition sentences are verbatim, with only the
  backtick markup removed.
- **Q14 with an empty search** lists every eligible Concept inside
  **collapsed** family expanders. §13.2 says "show all eligible Concepts"; they
  are all present, but one click away.
- **The Description instruction** is shown twice: as a caption, and as the
  field's tooltip.
- **The impact analysis (§35)** exists in the plan document, not as a
  standalone report.
- **v3 answers** remain intact in their own workbook. The v3 app code is
  retired, so this application cannot display them.

### 5.4 Not done or not verified

1. **No visual review in a browser.** Layout, spacing and the overall
   impression of the pages were never seen. Only headless checks ran.
2. **`live_sheets.py` has not been run.** The real workbook was exercised only
   by the bootstrap (verified) and one login-to-paper-list flow.
3. **The credential has not been rotated.** The leaked key is the one now in
   use. The archive has not been rebuilt, although `check_archive.py` flags it.
4. **Test gaps:**
   - no UI test for a Source with zero Claims (covered at progress level);
   - no UI test answering a Relation;
   - no UI test of the recall answer path;
   - no performance test of the Claim page, which renders about 100 Q14 "Add"
     buttons per Claim in collapsed expanders.
5. **Quota risk in Admin → Progress.** It makes one read request per started
   review. With many started reviews that approaches the 60-reads-per-minute
   Sheets quota.
6. **No conflict detection on Q14 selections.** Writes are idempotent and
   deduplicated, but last writer wins, so two browser tabs editing the same
   Claim's Q14 at once are not detected.
7. **The allocation is a development allocation.** The 26th Source is not yet
   in the Brain.

### 5.5 Verdict

Functionally, the delivered system is what was asked for. Every question,
removal, structural requirement and backend rule in the specification is
implemented. So are the four decisions and the eight corrections, apart from
the partial items in §5.2. Most of the acceptance criteria are covered by
automated checks. The architecture follows the requested model:

- one frozen instrument;
- one Brain snapshot, validated before use;
- one Google Sheets workbook per round, with round-namespaced, structured and
  normalised responses.

It is **not yet ready for evaluators**. What remains is verification and
operations, not design. In order:

1. Rotate the service-account key and rebuild or delete the zip.
2. Look through every page in a browser, and fix what a human sees that tests
   cannot.
3. Run `HE_LIVE_SHEET_OK=1 python app/tests/live_sheets.py` on a disposable
   workbook.
4. Decide on the collapsed-expander behaviour of Q14, the reservation release
   control, and the README note on `make_eval_splits.py`.
5. Add the missing UI tests.
6. Replace the development allocation once the 26th Source is in the Brain,
   then bootstrap the real round into a fresh workbook.
