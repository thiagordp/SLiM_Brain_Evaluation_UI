# Deployment runbook

How to take this repository from a clean checkout to a Streamlit Community Cloud
deployment that six evaluators can use at the same time, writing into one shared
Google Sheets workbook.

Read it in order the first time. Every step ends in something you can verify, so
a failure names the thing to fix rather than surfacing later as lost answers.

---

## 0. What the deployed app needs

| Thing | Why |
|---|---|
| A Google Cloud **service account** and its JSON key | The app authenticates as a robot, not as a person. |
| The **Google Sheets API** enabled on that project | Reading and writing the workbook. |
| A **Google Sheets workbook**, shared with the service account as *Editor* | The live evaluation store. Streamlit Community Cloud does not guarantee that runtime-generated local files survive a restart, so SQLite is **not** a safe live store there. |
| Two secrets — `HE_APP_PASSWORD`, `HE_ADMIN_SECRET` | The shared evaluator password and the separate admin secret. |
| The **frozen Brain** in `brain/wiki/` | The artifact under evaluation. Its SHA-256 snapshot is pinned in the manifest and checked at startup. |

Nothing secret is ever committed. `.gitignore` excludes `.streamlit/`, `*.p12`,
`*.pem`, `*service-account*.json`, `*credentials*.json` and `.env*`. Confirm
before your first push:

```bash
git status --porcelain --ignored | grep -E 'service-account|secrets\.toml|\.p12' || echo "nothing sensitive tracked"
```

---

## 1. Local environment

Streamlit and gspread must be importable. In this working copy they live in the
`unibo_env` conda environment, not in `phd_env`:

```bash
/home/trdp/anaconda3/envs/unibo_env/bin/python  -c "import streamlit, gspread; print(streamlit.__version__, gspread.__version__)"
```

For a fresh machine:

```bash
pip install -r requirements.txt
```

Run the test suite before changing anything, and record the result:

```bash
/home/trdp/anaconda3/envs/unibo_env/bin/python app/tests/test_app.py
```

It runs the real Streamlit script headlessly against a throwaway database and
prints one line per check, then a summary. Everything must pass.

Run the app locally on SQLite (fine for dry runs, never for a live round):

```bash
export HE_APP_PASSWORD='…'
export HE_ADMIN_SECRET='…'
/home/trdp/anaconda3/envs/unibo_env/bin/streamlit run app/streamlit_app.py
```

---

## 2. Google Cloud service account

1. <https://console.cloud.google.com/> → create or select a project.
2. **APIs & Services → Library** → enable **Google Sheets API**.
   Also enable **Google Drive API** *only* if you want
   `bootstrap_sheets.py --create` to create the spreadsheet for you. Using a
   sheet you made yourself needs Sheets alone, and is the simpler path.
3. **IAM & Admin → Service Accounts → Create service account.** No project role
   is required — access is granted by sharing the sheet, not by IAM.
4. Open the account → **Keys → Add key → Create new key → JSON**. Download it.
5. Store it outside the repository, readable only by you:

   ```bash
   mkdir -p ~/.config/slim-brain && chmod 700 ~/.config/slim-brain
   mv ~/Downloads/<project>-<hash>.json ~/.config/slim-brain/service-account.json
   chmod 600 ~/.config/slim-brain/service-account.json
   ```

Note the account's address — `something@<project>.iam.gserviceaccount.com`. You
will share the sheet with it in the next step.

> Download the **JSON key from the service account's Keys tab**. An OAuth client
> id is a different artifact and will be rejected with a clear message.

---

## 3. The workbook

### Option A — a sheet you create (recommended)

1. Create a spreadsheet at <https://sheets.new>, name it e.g.
   *SLiM Brain HE Evaluation*.
2. **Share → paste the service-account address → role Editor → Share.**
   Your own access grants the service account nothing; it must be shared
   explicitly.
3. Take the id from the URL — the segment between `/d/` and `/edit`, **not** the
   whole URL and not the `#gid=` part.

### Option B — let the service account create it

Needs the Drive API enabled:

```bash
export GOOGLE_SERVICE_ACCOUNT_JSON=~/.config/slim-brain/service-account.json
/home/trdp/anaconda3/envs/unibo_env/bin/python app/tools/bootstrap_sheets.py \
    --create "SLiM Brain HE Evaluation" --share you@example.com
```

Without `--share` the sheet lives in the service account's own Drive and nobody
can open it.

### Create the tabs

```bash
export GOOGLE_SHEET_ID='<the id from the URL>'
export GOOGLE_SERVICE_ACCOUNT_JSON=~/.config/slim-brain/service-account.json
/home/trdp/anaconda3/envs/unibo_env/bin/python app/tools/bootstrap_sheets.py
```

This creates each tab with its exact header row, and rewrites a header that has
drifted. If headers change, rows written under the old layout should be
**re-preallocated, not migrated in place**.

### Verify end to end

```bash
/home/trdp/anaconda3/envs/unibo_env/bin/python app/tools/check_sheets.py --write
```

Each step reports separately: libraries, environment, credential parsing,
opening the workbook, tabs, reading every tab, and — with `--write` — appending,
updating and deleting a probe row to prove write access. Run the `--write` form
at least once **before evaluators start**.

---

## 4. Secrets

Streamlit Community Cloud provides no environment variables; secrets are the
only channel. Generate the block rather than pasting the PEM by hand — the
`private_key` is a multi-line PEM that must survive as literal `\n` escapes
inside a quoted TOML string:

```bash
/home/trdp/anaconda3/envs/unibo_env/bin/python app/tools/make_secrets.py \
    ~/.config/slim-brain/service-account.json --sheet-id "$GOOGLE_SHEET_ID"
```

It prints the block to stdout and the service-account address to stderr. Omit
`--password` / `--admin-secret` and it generates strong ones and tells you what
they are. Add `--write` to save it to `.streamlit/secrets.toml` for local use
instead; that path is gitignored and written mode 600.

The block looks like this:

```toml
HE_APP_PASSWORD   = "…"
HE_ADMIN_SECRET   = "…"
GOOGLE_SHEET_ID   = "…"
HE_REQUIRE_SHEETS = true

[gcp_service_account]
type = "service_account"
project_id = "…"
private_key = "-----BEGIN PRIVATE KEY-----\n…\n-----END PRIVATE KEY-----\n"
client_email = "…@….iam.gserviceaccount.com"
…
```

### The variables

| Variable | Required | Purpose |
|---|---|---|
| `HE_APP_PASSWORD` | yes | shared evaluator password |
| `HE_ADMIN_SECRET` | yes | separate admin secret |
| `GOOGLE_SHEET_ID` | for the live store | the workbook id |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | for the live store | path to, or contents of, the key — **or** a `[gcp_service_account]` TOML table, which is the idiomatic Streamlit form |
| `HE_REQUIRE_SHEETS` | on a deployed run | refuse to start unless the workbook is reachable |

Every one is read from the environment **or** from `st.secrets`. There is no
default and no fallback value: with a required secret unset the login screen
refuses everyone and names the missing variable.

`HE_GOOGLE_SHEET_ID` / `HE_GOOGLE_CREDENTIALS` are accepted as aliases, so one
export can serve this app and the Splitter.

---

## 5. Deploy to Streamlit Community Cloud

1. Push the repository to GitHub. `brain/raw/` is gitignored, which holds the
   deployment near 5 MB instead of 58 MB.
2. <https://share.streamlit.io> → **New app** → pick the repo and branch.
3. **Main file path:** `app/streamlit_app.py`.
4. **Advanced settings → Secrets** → paste the block from step 4. Save.
5. Deploy, and watch the first boot log.

### Set `HE_REQUIRE_SHEETS = true` on every deployed run

Without it, a half-configured deployment would silently run on local SQLite:
every answer would be accepted and reported saved, the workbook would stay
empty, and Community Cloud could then wipe those files between restarts. With it
set the app stops on a clear screen instead.

The app also refuses to start when only *half* the Google configuration is
present — a sheet id without a service account, or the reverse. That is a
misconfiguration, never a request for SQLite.

---

## 6. Before opening a phase

The full sequence, in order:

1. **Freeze the Brain.** `brain/wiki/` must be the artifact the split was
   accepted against. Its SHA-256 snapshot is pinned in the manifest, and the app
   **stops on a mismatch screen** before the password form rather than letting
   answers be given against a moved target.
2. **Freeze the evaluation specification.** `spec.EVAL_SPEC_VERSION` must match
   the configured `eval_spec_version`; a mismatch stops the app the same way.
3. **Finalise the assignments** for the phase being opened.
4. **Snapshot** the configuration so the exact assignment set is reproducible.
5. **Bootstrap / verify** the workbook (steps 3 above).
6. **Preallocate** the phase's rows.
7. **Confirm the guards** — Brain snapshot, spec version, configuration.
8. Deploy.
9. Smoke-test as one evaluator: password → identity → paper list → open a paper
   → answer one question → confirm the row changed in the workbook.
10. Smoke-test Admin with `HE_ADMIN_SECRET`.
11. **Open the phase.**

Rows are preallocated so that evaluators never contend for the same row, resume
is trivial, and writes stay narrow. Never download a tab, edit it and write it
back while people are working — that silently overwrites a concurrent
evaluator's newer answer.

---

## 7. Troubleshooting

**"The workbook exists, but … cannot open it" (403)**
The sheet is not shared with the service account. Open the sheet → Share → paste
the address → set the role to **Editor** → Share. Your own access grants it
nothing.

**"No workbook with id … exists" (404)**
`GOOGLE_SHEET_ID` should be only the segment between `/d/` and `/edit` in the
URL — not the whole URL, not the `#gid=` part.

**"google sheets support needs `gspread` and `google-auth`"**
`pip install -r requirements.txt`, or on Cloud check that `requirements.txt` is
at the repository root and the build log installed it.

**"… is neither a readable JSON file path nor inline JSON"**
`GOOGLE_SERVICE_ACCOUNT_JSON` must be a path that exists, or the JSON itself.
On Cloud, prefer the `[gcp_service_account]` TOML table.

**"Brain snapshot mismatch"**
The Brain on disk is not the artifact the evaluation was configured against. The
screen prints both digests. Restore the frozen Brain, or regenerate the split
against the current one and re-import. Do **not** edit the pinned snapshot to
silence this — answers already given would become uninterpretable.

**"The application is not configured"**
`HE_APP_PASSWORD` or `HE_ADMIN_SECRET` is unset. The screen names which.

**The app runs but the workbook stays empty**
It fell back to SQLite. Set `HE_REQUIRE_SHEETS=true` so this fails loudly, and
re-run `check_sheets.py --write`.

**Quota errors under load (`429`, `RESOURCE_EXHAUSTED`)**
The Sheets API allows roughly 60 read requests per minute per user. Reads must
be scoped to one review's row range and cached per session; a full-tab read on
every rerun will exhaust the quota with six evaluators working.

**An evaluator's answers seem to have vanished after a restart**
The deployment was running on SQLite. Community Cloud does not guarantee that
runtime-generated files persist. This is exactly what `HE_REQUIRE_SHEETS`
prevents.

---

## 8. Exports

Admin → Exports downloads each tab as CSV plus a combined XLSX. The workbook
itself is also directly inspectable and exportable from Google Sheets, which is
part of why it was chosen as the live store.
