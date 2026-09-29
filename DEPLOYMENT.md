# Deployment runbook

How to go from a clean checkout to an evaluation round that six evaluators use
at the same time.

**One evaluation round = one fresh Google Sheets workbook.** The workbook is the
only persistent store: there is no local database and no fallback. If the
workbook is missing, unreachable or not initialised for the configured round,
the app refuses to start.

Read it in order the first time. Every step ends in something you can verify.

---

## 0. What a round needs

| Thing | Where |
|---|---|
| The Brain snapshot under evaluation | `brain/wiki/` and `brain/schema/` |
| The frozen definitions shown to evaluators | `app/data/definitions_v4.json` |
| The round id and its allocation file | `app/data/round.yaml`, `app/data/allocation/<round>.yaml` |
| The generated manifest | `app/data/manifest.yaml` |
| A Google Cloud service account and its JSON key | outside the repository |
| A **new, empty** Google Sheets workbook shared with that account as Editor | Google Drive |
| `HE_APP_PASSWORD`, `HE_ADMIN_SECRET` | environment or Streamlit secrets |

Nothing secret is ever committed or archived. `.gitignore` excludes
`.streamlit/`, keys and `.env*`. Before sharing any archive of the project:

```bash
python app/tools/check_archive.py path/to/archive.zip
```

It must report no credential files. **A key that has ever been in an archive or
a commit must be rotated** (Cloud console → the service account → Keys → delete
the old key, create a new one).

---

## 1. Local environment

```bash
pip install -r requirements.txt            # streamlit, gspread, google-auth, …
python app/tests/test_app.py               # must end "0 failed"
```

The tests use an in-memory workbook; they never touch Google.

---

## 2. Prepare the round inputs

### 2.1 The Brain

Copy the Brain export's `wiki/` and `schema/` into `brain/`. Then:

```bash
python app/tools/preflight.py
```

It must report `0 error(s)`. The preflight checks every Claim, Concept, Dataset
and Relation against the structure the instrument needs, and the snapshot's
schema files against the frozen definitions.

### 2.2 The definitions

Only when the Brain's schema or the create-edges skill has changed, and the new
text is the accepted one:

```bash
python app/tools/freeze_definitions.py --skills ../SLiM_Brain/.claude/skills
```

This rewrites `definitions_v4.json` word for word from the schema and skills,
and changes its `definitions_id`. A round's definitions never change once it
has been bootstrapped.

### 2.3 The allocation

The allocation file is generated from the corpus-sampling clusters by the
separate `reviewer_allocation/` tool (`python reviewer_allocation/make_allocation.py`);
see its README. Agreement groups may have two or more members.


Edit `app/data/allocation/<round>.yaml` — the only place an allocation is
written — then:

```bash
python app/tools/build_assignments.py      # validates and writes manifest.yaml
```

It refuses an invalid allocation and names every problem: a Training paper used
elsewhere, a Source placed twice or not at all, an Agreement set without a
pair, an Individual paper without exactly one evaluator, a Source or title the
Brain does not have, a duplicate assignment.

The current file is a **development allocation**. When the 26th Source is in the
Brain, add it to `IND-6` as the file's header explains and rerun the tool.

---

## 3. Service account (once)

1. <https://console.cloud.google.com/> → project → **APIs & Services → Library**
   → enable **Google Sheets API**.
2. **IAM & Admin → Service Accounts → Create.** No project role is needed.
3. The account → **Keys → Add key → JSON**. Store it outside the repository:

   ```bash
   mkdir -p ~/.config/slim-brain && chmod 700 ~/.config/slim-brain
   mv ~/Downloads/<key>.json ~/.config/slim-brain/service-account.json
   chmod 600 ~/.config/slim-brain/service-account.json
   ```

---

## 4. Create and bootstrap the round workbook

**Instrument 4.1 needs a fresh workbook.** It adds the RESTATEMENTS tab and the
Relation `direction_*` columns, drops `related_claim_id`, and changes the
definitions id. A workbook bootstrapped for 4.0 is refused at startup ("does not
have the headers this version expects"); there is no migration.

1. Create a new spreadsheet at <https://sheets.new>, named after the round, e.g.
   *SLiM Brain evaluation — ROUND-2026-01*.
2. **Share** it with the service account's address as **Editor**.
3. Take its id: the part of the URL between `/d/` and `/edit`.

```bash
export GOOGLE_SHEET_ID='<id>'
export GOOGLE_SERVICE_ACCOUNT_JSON=~/.config/slim-brain/service-account.json

python app/tools/check_sheets.py --write        # access, and "ready for bootstrap"
python app/tools/bootstrap_round.py --dry-run   # validates everything, writes nothing
python app/tools/bootstrap_round.py             # initialises the round
```

The bootstrap validates the preflight, the allocation and the manifest's
freshness first. It then creates every tab with its exact header, and writes
the round's self-description:

| Tab | Holds |
|---|---|
| ROUND | round id, instrument version, definitions id, Brain snapshot, canonical schema version, runs, schema hashes, allocation id and status, creation time and app commit |
| DEFINITIONS | every definition shown to evaluators, verbatim |
| CONFIG, EVALUATORS, ASSIGNMENTS | phase switches and the explicit assignments |
| REVIEWS, RESPONSES, CONCEPT_RESPONSES, RELATION_RESPONSES | one preallocated block per review |
| MISSING_CONCEPTS, PROPOSED_CONCEPTS | Question 14 selections and proposals |
| RESTATEMENTS | restatement-group memberships (Claim recall) |
| SUBMISSIONS | final phase submissions |

Finally it reads back the first and last row of every block and fails loudly if
a recorded range is wrong.

It **refuses** a workbook holding anything but blank default sheets, and a
workbook that already holds a round. `--overwrite-round <ROUND_ID>` names the
round it may replace; if anybody has started work there, `--discard-evaluations`
must be given as well. An interrupted bootstrap is replaced with
`--overwrite-round PARTIAL`.

`--extend` adds reviews for assignments that are new to the same round —
activated reservations, a Source added to the allocation — without touching
existing rows. It refuses when the Brain, instrument or definitions differ from
the round's: those make a new round, in a new workbook.

---

## 5. Secrets and deployment

```bash
python app/tools/make_secrets.py ~/.config/slim-brain/service-account.json \
    --sheet-id "$GOOGLE_SHEET_ID"
```

It prints the block to paste into Streamlit Cloud → **Advanced settings →
Secrets** (`--write` saves `.streamlit/secrets.toml` for local use instead).

| Variable | Purpose |
|---|---|
| `HE_APP_PASSWORD` | shared evaluator password |
| `HE_ADMIN_SECRET` | separate admin secret |
| `GOOGLE_SHEET_ID` | the round workbook |
| `GOOGLE_SERVICE_ACCOUNT_JSON` or `[gcp_service_account]` | the key |
| `HE_ROUND_ID` | optional override of `round.yaml`'s round id |

Streamlit Cloud: **New app** → repository → main file `app/streamlit_app.py` →
paste the secrets → deploy.

At startup the app checks, in order:

1. that the workbook is reachable and every tab has its exact header;
2. that the Brain snapshot passes the preflight. Evaluators then see "The
   evaluation is not available", and the admin secret reveals the diagnostic;
3. that the workbook's ROUND names this round, instrument, definitions and
   Brain snapshot.

Any failure stops the app on a screen saying what is wrong.

---

## 6. Before opening the round

1. Sign in as one evaluator: open a paper, answer one question, and confirm the
   row changed in the workbook.
2. Admin → System: the round metadata, 0 preflight errors, a consistent
   configuration.
3. `python app/tools/audit_workbook.py` — must report 0 errors. Run it again at
   any time during the round (read-only); Admin → System → *Check data
   integrity* shows the same report.
4. `python app/tools/snapshot_config.py` and commit the snapshot.

**Quota.** Every evaluator's saves go through the one service account, whose
Sheets quota is about 60 read and 60 write requests per minute. Answers are
batched, and a refused request is retried and retained, never dropped; at a
busy moment saving is slower, and the status line says "Saving…" until
everything is stored.

**Real-Google check.** `HE_LIVE_SHEET_OK=1 python app/tests/live_sheets.py`
exercises the storage against a *disposable* workbook (it re-bootstraps it):
round trips, a stale write, a mixed batch, Direction, restatement groups, and
finally the integrity audit. Never point it at a round in use.

---

## 7. Troubleshooting

**"The workbook exists, but … cannot open it"** — share it with the service
account as Editor.

**"No workbook with id …"** — `GOOGLE_SHEET_ID` is only the segment between
`/d/` and `/edit`.

**"The workbook is missing ROUND, …"** — it was never bootstrapped. Run
`bootstrap_round.py`.

**"This workbook does not belong to this deployment"** — the workbook holds a
different round, instrument, definitions or Brain snapshot. Point the app at the
right workbook. Never re-bootstrap a workbook that holds a finished round.

**"Google Sheets is busy"** — the per-minute request quota. Nothing is wrong;
wait and retry. Opening a paper costs one batched read, and answers are
written in batches.

---

## 8. Exports

Admin → Exports produces, per round:

- `raw_*` — every tab exactly as stored;
- `claim_judgments`, `concept_judgments`, `missing_concepts_state`,
  `missing_concepts`, `proposed_concepts`, `relation_judgments` (Grounding,
  Direction, Type), `dataset_judgments`, `claim_recall`, `restatement_groups` —
  joined with review provenance. Each row
  carries `round_id` and `eval_spec_version`;
- `agreement_pairs`, `agreement_metrics` — the agreement phase only.

**Download all tables (.xlsx)** puts all of them in one file, one tab per table;
each table is also available as a CSV under "Individual tables (CSV)".

The v3 evaluation data stays in its own workbook, unchanged; nothing in this
version reads or rewrites it.
