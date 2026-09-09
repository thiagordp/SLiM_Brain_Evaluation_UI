# HE Evaluation Interface

A thin evaluation interface over the protocol defined in `HE_review_form.xlsx`.
It presents the Brain record under evaluation and records the reviewer's
judgment. It contains no scientific logic and never writes to the Brain.

## Run

```bash
pip install -r requirements.txt
export HE_APP_PASSWORD='...'      # shared password
export HE_ADMIN_SECRET='...'      # separate admin secret
streamlit run app/streamlit_app.py

python app/tests/test_app.py      # headless end-to-end checks
```

**Secrets exist only as environment variables** (or `st.secrets`, the same
mechanism on Community Cloud). There is no default and no fallback: the app
knows the variable names, never a value. With either unset, the login screen
refuses to accept anyone and says which variable is missing. Nothing secret
appears in the code, the manifest, or any committed file.

## Flow

```
shared password -> select evaluator -> confirm (identity locked for the session)
      -> Training | Agreement | Individual -> home -> paper -> sections
      -> review -> phase submission
```

The name is chosen once and cannot be changed in that session. The papers come
from the manifest, never from a choice. Admin is a separate secret, not a name.

### Three phases

```
training     the same two optional practice papers for everyone
agreement    both evaluators of a pair over one shared set of five
individual   one evaluator per paper
```

Each carries its own assignments, completion state and final submission, so
submitting Training does not submit Agreement and submitting Agreement does not
submit Individual.

**They are not a sequence.** All three are open from the start. **Training is
optional** calibration on W0085 and W0206: an evaluator may leave it untouched,
half-finished or unsubmitted and still work on — and finally submit — Agreement
and Individual. It is never reported as a configuration problem, only as
optional and incomplete. Agreement need not be closed before Individual is used. The open/closed switches in Admin are operational controls,
for pausing work or freezing a set before it is analysed, and all three default
to open.

Per paper:

```
0. Start          Source metadata, Open Source wiki, "I have read the full paper"
                  (sections below can then be visited in any order)
1. Source         HE-08.1 – HE-08.3
2. Claims         one page per claim, reachable in any order
                    A validity      HE-03, HE-25, HE-04, HE-05
                    B grounding     HE-06, HE-07
                    C attributes    HE-08.1 – HE-08.5
                    D concepts      HE-12, HE-21*, HE-20 (+ HE-20.b)
                    E relations     one judgment per edge; HE-16 is derived
3. Datasets       one page per dataset: HE-14.1/2, HE-15.1–7  (+ HE-14.3, source-level)
4. CITES          outgoing = evaluated; incoming = context only
5. Claim recall   HE-19.1 (+ HE-19.3)
6. Review         every missing item, clickable; marking complete unlocks when empty
```

### Completion and final submission

A paper with nothing missing is **marked complete**, which does **not** lock it.
Final submission happens once, from the paper list, and only when every assigned
paper is complete:

```
not started -> in progress -> complete (editable) -> submitted (locked)
```

An evaluator's reading steadies after several papers, so they must be able to
revisit earlier ones before anything is fixed. Only the administrator can reopen
a submitted paper.

**Navigation is free.** Every section and every claim is reachable at any time —
jump from Claims to Datasets and back, answer claim 7 before claim 2. `Back` and
`Next` are a convenience path through the list, disabled only at its two ends,
never by anything unanswered. An incomplete claim says so and lets you leave.

Because nothing is gated, the marks have to carry the whole picture. One glyph
means one thing wherever it appears — on a section, a claim, or a part of a
claim page:

```
○ untouched      ● in progress      ✓ complete
```

The section bar shows all six with `Claims n/m`; the claim selector marks every
claim; and each claim page shows its five parts — A · Claim, B · Grounding,
C · Attributes, D · Concepts, E · Relations — with their own counts.

### Denominators are per claim

A claim page reads `12/17 applicable items complete`, and the total differs from
claim to claim on purpose. HE-07 and HE-21 drop out where the Brain record
settles them, a conditional follow-up appears once its parent turns negative, and
the number of cross-source edges varies. A fixed total would report a finished
claim as unfinished.

### Resume suggests; it never redirects

Reopening a paper lands on the first section still needing work, and a claim page
offers **Resume at claim N** when work was left elsewhere. Both are shortcuts:
opening claim 1 leaves you on claim 1, and the shortcut disappears once you are
already where it points.

Completeness is enforced where it matters instead: a paper cannot be **marked
complete** while anything is missing, and the **final submission** cannot run
until every assigned paper is complete.

What counts as missing is defined narrowly, on the existing form only: an
unanswered applicable question, a comment required for a partial or negative
answer, an applicable conditional field, an unanswered edge. No new mandatory
fields.

\* HE-21 is shown for every claim, but is **automatically not applicable**
unless a candidate concept's own record names this claim as motivating its
creation. A retrofitted or pre-existing candidate does not make it apply. See
"HE-21" below.

## The instrument: three layers, version 3.0

```
HE_review_form.xlsx
      |
data/he_criteria.json      verbatim workbook extract
      |
data/he_criteria_v2.json   the 2026-09-07 calibration meeting
      |
data/he_criteria_v3.json   the page-by-page UI and instrument review, 2026-09-08
```

Each layer is merged field by field over the one above, so unchanged criteria
keep their inherited text, changed ones are visibly overridden, and **the
workbook itself is never modified**. Every override records which review settled
it (`Question.provenance`), and `Question.changed_in_v2` / `changed_in_v3` say
which layers touched a criterion.

v2 applied the calibration meeting: "order of dominance" removed everywhere;
`other_versions` (HE-08.3) dropped from the human flow, since versions are
resolved in preprocessing; HE-25 reframed from "restatement" to duplication *by
the Brain within one paper*; HE-06 reframed from anchors that "warrant" a claim
to anchors as **textual grounding**; HE-07, HE-08.1, HE-08.3 and HE-08.4 moved to
the **defensibility** standard; HE-12 allowed reasonable inference; HE-20 bounded
to **mapping-relevant** concepts; and a **new source-level conceptual-coverage
question** (HE-20.S) after claim recall.

v3 froze the wording the team settled page by page. It carries the final question
text, the "How to judge" prose that replaces the dense schema quotations, the
visible criterion titles, and a **criterion-specific comment placeholder** for
every question. The Dataset and CITES criteria — which the meeting never reached
— got the same treatment: HE-14/15 and HE-18 keep their workbook substance but
state what each field means instead of asking "Is `size` correct?".

Because the instrument is the thing every answer is interpreted against, the app
**stops before login** if `EVAL_SPEC_VERSION` is not the `eval_spec_version` the
configuration was accepted against, naming both — the same treatment the Brain
snapshot gets.

## The response scale

`Yes` / `In part` / `No`, with a comment **required** for `In part` and `No`.
`Yes = 3`, `In part = 2`, `No = 1` for agreement analysis.

Two criteria depart from it, each for a stated reason:

**HE-20** (claim-level concept completeness) is **`Yes` / `No`**. Either every
mapping-relevant concept this claim needs is represented, or at least one is
missing — and HE-20.b then asks which. A middle value would record that
something is absent without saying what, which is exactly what the follow-up is
for. HE-12 and the source-level coverage question keep the three-value scale.

**HE-14.3** (dataset completeness) adds **`N/A`**, meaning the source genuinely
neither uses nor introduces any dataset, benchmark or corpus. See below.

There is no evaluator-facing `Unclear` and no evaluator-facing `N/A`.

`Unclear` was removed in v3: it had been an adjudication flag rather than a
score, and mixing it into the scale invited it to be used as one. The storage
column stays so v2 exports still parse; nothing writes to it.

`N/A` is almost never offered as a choice, because a criterion that can be
inapplicable is usually inapplicable for a reason the app can read off the Brain
record — and an N/A option invites the opposite error, choosing it where the
criterion does apply. Three criteria are decided by the application, which shows
a sentence instead of a control:

| Criterion | Not applicable when |
|---|---|
| HE-07 premise | `basis` is `none_stated` and the premise is correctly empty |
| HE-21 candidate concept | no candidate concept's record names this claim |
| HE-18.1 CITES accuracy | the Brain generated no outgoing CITES edge |

**HE-18.2 is still asked in that last case**: zero generated edges is not
automatically correct — the Brain may have missed a citation.

Such an item is stored as `answer = N/A` with `applicability = auto_na`, so an
inapplicable criterion is never confused with an unanswered one in the exported
data, and it is excluded from the "n of m complete" denominators rather than
silently making a finished claim look unfinished.

**HE-14.3 is the one exception**, and the distinction matters. Whether a paper
uses any dataset at all is a fact about the paper, not about the Brain record —
and the Brain having produced no Dataset node is *not* evidence for it, because
that absence may be the very failure HE-14.3 is asking about. So the evaluator
chooses, and a source with zero Dataset nodes is still asked with nothing
preselected.

The two kinds of N/A stay apart in the data:

| | `answer` | `applicability` |
|---|---|---|
| the application decided | `N/A` | `auto_na` |
| the evaluator decided (HE-14.3) | `N/A` | `applicable` |

An evaluator-chosen N/A needs no comment; `In part` and `No` still require one
naming the missing Dataset(s).

Where the *Brain's own value* is `not_applicable` or `not_stated` — `positive_form`,
`agreement_reported`, `availability` — the evaluator judges whether that value is
right, and answers `Yes` when it is.

## Two workbook rules that shape the code

**HE-16 is not a Yes/No answer.** In the workbook its cell is a formula over the
per-edge rows: `correct / evaluated (%)`. The app collects one judgment per edge
into `EDGE_RESPONSES` and derives the summary, exactly as Excel does. It has no
row of its own.

**Criterion ids are not unique.** HE-08.1 exists at Source level
(`contribution_type`) and Claim level (`claim_type`), as do HE-08.2 and HE-08.3.
Every question therefore carries an internal `question_key`
(`SOURCE_HE08_1` vs `CLAIM_HE08_1`), which the evaluator never sees.

## Storage

Three tables, long format, one row per human decision.

| Table | One row = |
|---|---|
| `REVIEWS` | one evaluator evaluating one paper — status, timestamps, `brain_snapshot_id`, `eval_spec_version` |
| `RESPONSES` | one ordinary answer — object, `question_key`, answer, comment, `applicability` |
| `EDGE_RESPONSES` | one edge judged under one claim — `label_correct`, corrected label |

Keys are deterministic, so a save is always "find my row and update it":

```
review_id        phase_id | evaluator_id | source_id
response_key     review_id | object_type | object_id | question_key
edge_key         type | from | to | grounding          (edges.jsonl has no id)
```

### Preallocation

Rows are created **in bulk, before anyone starts**, by `tools/preallocate.py`:
every review, every response row and every edge row for all 82 assignments,
reservations included — about 25,400 rows. Three things follow.

*Nobody appends during a round.* Each review's rows are written once, from one
machine, so evaluators never contend and no one appends into a tab others are
reading. The **superset** is created — the conditional follow-ups HE-20.b,
HE-18.3, HE-19.3 and HE-20.S.b included — so the first evaluator to answer "No"
does not have to append a row mid-round.

*Reads become narrow.* Each review's block is contiguous, and its first and last
row numbers are recorded on the review. Opening one paper is then a single range
read of a few hundred rows instead of a download of the whole tab.

*Reservations are ready.* Their storage exists too, so settling an undivided pool
is a one-field edit with nothing to create.

Preallocation is **not** evaluator activity: it stamps no provenance, does not
move `last_saved_at`, and locks no assignment. The app keeps a lazy fallback for
a local run where nobody executed the tool. Writes are narrow updates and
`updated_at` (microsecond precision, so two edits in the same second are
distinguishable) is compared before overwriting, so the same evaluator in two
tabs gets a `SaveConflict` rather than a silent clobber.

### Verified against a real workbook

The figures below are measured, not estimated. `app/tests/live_sheets.py` runs
them against a Google workbook holding the full configuration — 23,635 response
rows, 1,752 edge rows, 82 reviews — and refuses to start unless
`HE_LIVE_SHEET_OK` is set, so it cannot be pointed at the production sheet by
accident.

```bash
export GOOGLE_SHEET_ID='<a disposable, empty workbook>'
export GOOGLE_SERVICE_ACCOUNT_JSON=.streamlit/service-account.json
python app/tools/bootstrap_sheets.py --seed
python app/tools/preallocate.py            # 25,469 rows, ~36 s
HE_LIVE_SHEET_OK=1 python app/tests/live_sheets.py
```

### What a page costs

The Sheets quota is counted in requests, so the cost that matters is how many a
page makes — not how long one takes. With ~23,600 response rows in the workbook:

| Action | Requests |
|---|---|
| open a paper | 1 range read of that review's block (~500 rows), 1 for its edges |
| render it again, or move between claims | none |
| answer a question | 1 targeted row write |
| the session's first write | + 1 whole-tab read, to build the row index once |
| several answers queued together | 1 batched write for all of them |
| `last_saved_at` | at most once a minute per review |

Rendering writes nothing. That needed fixing: an unanswered radio returns `None`
while its preallocated cell holds `""`, so comparing them raw had every render of
every unanswered question queue a write that changed nothing.

The row index is cached per process. Positions are stable once preallocated — an
append never moves an existing row and nothing deletes one during a round — so a
cached index can only be missing a new key, never wrong about an old one. A miss
rebuilds it once; a hit is trusted.

Saving is **asynchronous** (`savequeue.py`): changing an answer updates the UI
immediately and queues the write, repeated edits to the same answer collapse to
the latest pending value, and writes that arrive together go out together.
Navigation never waits for storage.

**A write is never dropped.** One that exhausts its attempts moves to a failed
registry and keeps being retried for as long as the session lives, rather than
disappearing behind a red status nobody can act on. The status line says how many
answers are outstanding and offers a retry; a newer answer for the same item
supersedes a failed one.

That is what makes the two gates honest:

> **Marking a paper complete, and submitting a phase, refuse while anything is
> unresolved** — and then re-read the stored answers rather than trusting what
> the session remembers.

Completion flushes, re-reads the review from storage, and recomputes the missing
list. Phase submission does the same for **every** assigned paper: `complete` was
recorded when the paper was finished, possibly days earlier, and submission is
irreversible. A paper that no longer survives the re-read is reopened and named,
and nothing is submitted — not even the sound papers.

### Two tabs

Each save carries the row's stored `updated_at` as an expectation, so the same
evaluator working in two tabs gets a `SaveConflict` rather than a silent
overwrite. The token is refreshed from each successful write, or the next
legitimate edit in the same session would compare against a timestamp storage had
already moved past and every second edit would look like a conflict.

Conflict-checked saves are still batched: the batch's rows lie inside one
review's block, so their stored stamps come back in one range read whatever the
batch's size. A first answer skips the check, having no stored stamp to compare
against — so that window is not covered, and this remains best-effort detection
rather than transactional locking.

### `complete` is a claim, and an edit withdraws it

Any edit to a completed paper returns it to `in_progress`, immediately and
without asking whether that particular edit broke anything. A conditional
follow-up can become required as a side effect of its parent changing, and an
optimistic "still complete" is a lie the evaluator would only discover at
submission. A **submitted** paper is not demoted: it is locked, and only an
administrator can reopen it. The status line shows `Saving… / Saved / Save problem —
retrying`.

**Submission is the exception.** Pressing Submit flushes every pending write,
verifies it landed, re-reads the responses and re-checks the missing list before
the paper is marked submitted — so an apparently submitted evaluation can never
have unsaved answers.

**Two backends, chosen by environment.** Setting `GOOGLE_SHEET_ID` (plus
`GOOGLE_SERVICE_ACCOUNT_JSON`, a service-account JSON path or inline JSON)
selects the shared Google Sheets workbook — the live store for a deployed run, because
Streamlit Community Cloud does not guarantee that runtime-generated local files
persist. Without it the app uses SQLite, which is fine for local development,
dry runs and tests but is **not** a safe live store on Community Cloud.

Writes to the workbook are narrow: a key→row index is built once and a save
updates exactly one row range. The whole tab is never downloaded, edited and
written back, which would silently overwrite a concurrent evaluator's newer
answer. `sheets.LocalWorkbook` writes the same three tabs as CSV for dry runs
and tests.

Responses are read **once per review per session**, not once per rerun. Streamlit
re-runs the whole script on every interaction, so rebuilding the context from
storage each time meant a read per radio click. The cache is write-through: a
queued save updates it immediately, so what the evaluator sees is what will be
persisted. `refresh()` forces a real re-read where correctness demands one —
before marking a paper complete, and before final submission.

The UI never knows which backend is active; everything goes through `store.py`.

The Excel `Summary` sheet is **not** stored. It is derivable from the atomic
rows, and storing it twice would let the two drift.

## Environment

| Variable | Required | Purpose |
|---|---|---|
| `HE_APP_PASSWORD` | yes | shared evaluator password |
| `HE_ADMIN_SECRET` | yes | separate admin secret |
| `GOOGLE_SHEET_ID` | for the live store | the shared workbook's id |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | for the live store | path to, or contents of, the service-account key |
| `HE_REQUIRE_SHEETS` | on a deployed run | refuse to start unless the workbook is reachable |

Every one is read from the environment **or from `st.secrets`** — Streamlit
Community Cloud provides no environment variables, so secrets are the only channel
there. The service-account key may also be given as a `[gcp_service_account]` TOML
table, which is the idiomatic Streamlit form.

The Google variables are the same names the Splitter uses, so one export serves
both applications; `HE_GOOGLE_SHEET_ID` / `HE_GOOGLE_CREDENTIALS` are accepted as
aliases. Without them the app runs on local SQLite — unless `HE_REQUIRE_SHEETS` is
set, in which case it stops with a clear error rather than writing into a store
that Community Cloud may wipe between restarts.

Set up and verify the workbook:

```bash
python app/tools/bootstrap_sheets.py        # create the three tabs, exact headers
python app/tools/check_sheets.py --write    # credentials, access, tabs, round-trip
python app/tools/make_secrets.py KEY.json --sheet-id ID   # the secrets block to paste
```

**Deploying: see [`../DEPLOYMENT.md`](../DEPLOYMENT.md)** for the full runbook —
service account, workbook, GitHub, Streamlit Cloud, and troubleshooting.

## Brain snapshot

The Brain is identified by a SHA-256 over its runtime files — `wiki/sources/*.md`,
`wiki/concepts/*.md`, `wiki/datasets/*.md`, `claims.jsonl`, `edges.jsonl` — with
each file's path *and* content hash entering the digest, so a rename changes the
snapshot. Every review records it.

If the Brain on disk is not the artifact the split was accepted against, the app
**stops on a mismatch screen** and never reaches the password form. A Brain that
moved mid-evaluation would silently invalidate answers already given, so this
fails loudly rather than warning.

## Runtime data sources

The app reads Brain content from exactly five places, and nothing else:

```
wiki/sources/SRC-*.md      frontmatter (values) + body (inspector only)
wiki/claims/claims.jsonl
wiki/concepts/CPT-*.md     frontmatter + body
wiki/datasets/DST-*.md     frontmatter + body
wiki/graph/edges.jsonl
```

Deliberately **not** runtime sources: `log.md` (an audit trail whose prose can
change between Brain runs), `schema/`, `.claude/skills/`, `index.md` (the source
registry is built by loading all Source frontmatters) and the PDFs. A test
verifies this behaviourally by recording every file the loader opens.

## HE-21, and where its answer comes from

HE-21 asks whether a candidate concept created *for this claim* was necessary.
The provenance comes from the **Concept record itself**: the schema requires a
candidate or emergent concept's `definition` to be derived from the claims that
motivated it, citing their ids. `brain.py` extracts those ids with the stable
`CLM-nnnn-nnn` pattern.

```
anchor                        -> HE-21 N/A
candidate / emergent          -> is this claim among the motivating ids?
                                    yes -> HE-21 applies
                                    no  -> HE-21 N/A   (retrofit, or pre-existing)
```

The N/A case is shown, not hidden: the criterion still appears with the sentence
*"Not applicable — no candidate Concept was created for this Claim"*, so the
evaluator can see it was considered and settled.

A non-anchor concept whose definition names no claim is **flagged** as missing
evaluation context (`concept_provenance_gaps`) rather than guessed at — there is
no fallback to `log.md`. The current Brain has no such gap.

Concepts are shown grouped by family (`legal_task`, `technique_class`,
`normative_concern`, `other`) with lifecycle status, beside the **built-in
anchor grid** (36 anchors, shipped in `data/anchor_grid.json`) and a searchable
registry of every concept in the Brain. The grid is built in, not read from
`schema/`, so the instrument stays frozen even if the Brain's schema evolves.

## The wiki modal

One modal carries every piece of supporting material:

```
Source wiki · Concept wiki · Dataset wiki · generated Claim detail
Concept registry · Brain Source registry · all Claims from this Source
```

It opens centred at about three quarters of the viewport, scrolls inside itself,
and offers `← Back` and `✕ Close`. There is no minimise.

It replaced a right-hand panel that shared the width with the evaluation. The
panel's real problem was not the width: **whether it was open changed what the
evaluation area looked like**, so a context control had become part of the page.
A modal sits over the work and leaves it exactly as it was — opening or closing
one touches no answer, no progress and no navigation, and a test asserts each of
those.

**Links inside a wiki are buttons.** A Markdown link cannot call back into
Python, so rather than render links that quietly do nothing, the modal scans the
page for the ids it names — `SRC-`, `CPT-`, `DST-`, `CLM-` — and offers them as
controls. Following one pushes onto a history stack; `← Back` returns.

Every entry point starts a **fresh** history. A dismissal — the X, Esc, a click
outside — cannot be distinguished from never having opened the modal, so
`on_dismiss` clears the stack rather than letting a stale trail accumulate behind
it or the modal reopen itself on the next rerun.

The modal closes when the evaluation context changes: another claim, another
dataset, another section. What is on screen is no longer about what the evaluator
is looking at.

## Configuration

### Two sources, one interface

When a workbook is configured, **CONFIG / EVALUATORS / ASSIGNMENTS are the live
configuration**, and the administrator can close a phase without a redeploy —
which matters because the deployed checkout is not writable between restarts.
Without a workbook, `data/manifest.yaml` serves the same data. Callers cannot
tell which is active; `manifest.source_name()` reports it.

```bash
python app/tools/bootstrap_sheets.py --seed    # file -> workbook, first time
python app/tools/snapshot_config.py            # workbook -> versioned CSVs
```

`manifest.yaml` remains the bootstrap source, the local-development
configuration and the reproducibility snapshot. It is generated from the
**accepted paper allocation**:

```bash
python app/tools/build_assignments.py            # rewrite it
python app/tools/build_assignments.py --dry-run  # show what it would write
```

`accepted_at` records when the allocation was accepted, not when the
generator last ran: re-running it on an unchanged allocation carries the
date over, so the file stays byte-identical and a re-run produces no diff.

**The app never infers an assignment from a group label.** The labels in
circulation do not line up: the allocation email calls Giovanni and Alessandro
"Group A" while assigning them `AGR-C`. Every evaluator x paper x phase pair is
an explicit row, and `tools/build_assignments.py` is the only code that reads
allocation prose.

```
config       brain_snapshot_id, eval_spec_version, split_version, phase switches
evaluators   evaluator_id, name, is_admin, pair_id, agreement_split, individual_split
assignments  assignment_key, evaluator_id, phase_id, split_id, source_id,
             work_id, assignment_order, assignment_state
```

The two halves are cached separately, because they change at very different
rates: the phase switches for 15 seconds and cleared the moment an administrator
writes one, so a closed phase takes effect almost at once; the evaluator and
assignment tables for 5 minutes, since they are read on nearly every rerun and
almost never change.

### Configuration version

`config_version` is a digest of what the experiment **is** — Brain snapshot,
instrument version, evaluators, assignments — and is recorded on every review
beside `brain_snapshot_id` and `eval_spec_version`. Any answer can therefore be
traced to the exact assignment set it was given under.

Phase switches are deliberately **not** part of it. Closing Agreement changes
what people can do next; it does not change what any existing answer means, and
it must not look as though the assignments moved.

### Provenance is stamped when work begins

A review row is created by preallocation, long before anyone opens it, and a
reservation may be activated — changing the configuration — in between. So the
row records **identity** at creation and **provenance** at first activity:

```
reserved, preallocated under config A
        ↓  activate the assignment
config becomes B
        ↓  evaluator starts the review
recorded provenance = B
```

`start_review()` fills `brain_snapshot_id`, `eval_spec_version`,
`config_version`, `split_id` and `assignment_state` if they are blank, and
**never rewrites one that is not**. A later configuration change cannot alter
what an existing answer means.

The Admin export therefore carries two readings side by side:

| Column | Is |
|---|---|
| `assignment_state` | history — what the review was when its evaluator began |
| `current_assignment_state` | context — what the configuration says today |

Reading only the current table would let a change silently reinterpret a
finished evaluation; reading only the recorded one would hide that the
configuration has moved. A review nobody started has no recorded state, so only
the current one means anything for it — and `validate()` reports a reservation
that somehow acquired activity rather than letting it pass.

`tools/snapshot_config.py` writes the configuration itself beside the digest,
into `data/config_snapshots/<timestamp>_<version>/`, with the workbook's own
columns so a snapshot can be pasted back. Commit it — a snapshot that exists
only on the machine that made it is not a record.

### When an assignment may still be changed

Immutability is keyed to the **individual assignment**, not to the phase. Every
phase is open from the start, so "frozen once the phase opens" would freeze the
whole configuration immediately and leave IND-1 permanently unassignable.

> An assignment row is editable until an evaluator has actually done something
> to it, and locked from then on.

**The existence of a REVIEWS row is not activity.** Rows are preallocated for
every assigned paper before anyone opens the application, so treating a row as
evidence of work would lock the whole configuration the moment the workbook was
prepared — including the IND-1 pool that must stay assignable. Activity is
durable evidence a person left: a status past `not_started`, the moment they
confirmed reading the paper, or any write against the review.

Adding a row, or naming the evaluator on a pending one, is always safe: it
creates work rather than invalidating any. Removing or reassigning a locked row
strands the answers already given, so `validate()` reports a started review whose
assignment row has gone, and Admin marks every locked row in the assignments
table.

The current allocation: 6 evaluators, 3 agreement pairs of 5 papers, 5 individual
splits, training W0085 + W0206. 82 assignment rows — 68 assigned and 14
reserved. Together with training, the splits cover all 50 Sources exactly once.

| Evaluator | Agreement | Individual |
|---|---|---|
| Alessandro | AGR-C | IND-3 |
| Giovanni | AGR-C | IND-5 |
| Giuseppe | AGR-B | IND-2 |
| Vaclav | AGR-B | IND-4 |
| Thiago *(also admin)* | AGR-A | IND-1, reserved |
| Francesca | AGR-A | IND-1, reserved |

### Assigned and reserved

`assignment_state` separates a real assignment from a technical reservation.

| State | Means |
|---|---|
| `assigned` | a real assignment: it appears in the evaluator's paper list, counts toward progress, completion and phase submission, and is an evaluated paper in the exported data |
| `reserved` | preallocated storage for a decision nobody has taken: invisible to the evaluator, counted toward nothing |

**IND-1 is not yet divided between Thiago and Francesca, so every possible
allocation is reserved** — one row per evaluator per paper, 14 rows over 7
papers. Their storage is preallocated too, so settling the division later is a
one-field edit, `reserved` → `assigned`, with no review, response, edge row or
row range to create at that moment. Admin does it a paper at a time, and it is
reversible until somebody starts work.

Both members of the pair are reserved for every paper on purpose, and exactly
one is ever activated. `validate()` reports a paper assigned to two evaluators
in the individual phase, because that would make the pool a second agreement set
— a different experiment.

Reservations do **not** hold the Individual phase closed. The phase is open;
those particular papers are simply waiting for a decision.

Being the administrator does not remove Thiago's own papers; he evaluates like
everyone else, behind a separate secret for the Admin page.

Evaluators are shown their split ids (`Agreement: AGR-C`), never a pair letter.
`pair_id` survives internally on the stored review rows; nothing displays it.

Papers are identified by **work id** (`W0085`) in the interface and by
`source_id` internally. The app validates the manifest at startup — unknown
sources, a training paper inside an evaluation split, a source in two splits, a
duplicate assignment key, an evaluator with no agreement split, a snapshot
mismatch — and lists problems for the administrator rather than crashing.

## Files

| File | Role |
|---|---|
| `streamlit_app.py` | entry flow, home, paper routing, section bar, admin |
| `views.py` | the six section screens |
| `ui.py` | the wiki modal, response cache, scroll-to-top, autosaving question widget |
| `spec.py` | built-in evaluation specification, `EVAL_SPEC_VERSION` |
| `progress.py` | applicability, completeness, locking, missing-items list |
| `store.py` | REVIEWS / RESPONSES / EDGE_RESPONSES |
| `savequeue.py` | asynchronous write queue: collapse, retry, flush |
| `sheets.py` | Google Sheets workbook + local CSV workbook for dry runs |
| `manifest.py` | phases, evaluators, assignments + secrets |
| `brain.py` | read-only Brain access, work ids, concept history, snapshot |
| `data/he_criteria.json` | criterion text extracted verbatim from the workbook |
| `data/he_criteria_v2.json` | the 2026-09-07 calibration changes, merged over it |
| `data/he_criteria_v3.json` | the final page-by-page wording, merged over that |
| `data/anchor_grid.json` | the 36 predefined anchor concepts, built in |
| `tools/extract_criteria.py` | regenerates it from `HE_review_form.xlsx` |
| `tools/build_assignments.py` | generates the manifest from the accepted allocation |
| `tools/snapshot_config.py` | freezes the live configuration as versioned CSVs |
| `tools/preallocate.py` | creates every row the evaluation will need, in bulk |
| `tools/import_split.py` | superseded; kept for the older Splitter format |
| `tests/fidelity.py` | pins the instrument's wording to the Design review |
| `tests/live_sheets.py` | the same storage paths against a real Google workbook |
| `tools/bootstrap_sheets.py` | creates the workbook tabs and headers |
| `tools/check_sheets.py` | verifies the Google setup step by step |
| `tools/make_secrets.py` | turns the service-account key into the Streamlit secrets TOML |
| `tests/test_app.py` | headless end-to-end checks |

The deployed app never reads the workbook, schema or skills at runtime: the
bundled JSON plus `spec.py` are the versioned instrument. Every review records
which `eval_spec_version` and which `brain_snapshot_id` produced it.

## Relationship to `SLiM_Brain_Evaluation_v2`

The authoritative design document is
`../SLiM_Brain_Evaluation_v2/SLiM_Brain_Evaluation_Platform_Implementation_Spec_v1.md`,
and that project also holds the Splitter (`apps/splitter_app.py`) and a parallel
implementation of the loaders, evaluation spec and storage in `slim_eval/`.

This app is a **standalone implementation of the evaluation UI only**. It
deliberately duplicates some of `slim_eval/`, consumes the Splitter's accepted
output rather than reproducing it, and follows the spec on the points that
matter: no `log.md`, no PDFs, no schema/skills at runtime, HE-16 derived, HE-21
from Concept records, free-text fields kept exactly as the workbook has them,
and Google Sheets as the live store.

## Out of scope, deliberately

PDFs (distributed outside the platform via the Splitter's per-evaluator ZIPs;
the app only asks for confirmation that the paper was read), structured
selectors replacing the workbook's free-text correction fields (the workbook's
fields are kept exactly), automatic structural `SC-` results (kept away from human
evaluators so a structural failure cannot bias the substantive judgment), the
splitter, adjudication, any graph explorer, and any view of another evaluator's
answers. The admin progress view shows completion status only.
