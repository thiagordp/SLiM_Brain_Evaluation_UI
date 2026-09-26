# SLiM Brain Human Evaluation

SLiM Brain Human Evaluation is a Streamlit application for evaluating whether the **SLiM Brain faithfully represents scholarly Sources** through Source attributes, Claims, Concepts, Datasets, citation edges, and source-level coverage.

The application evaluates the **Brain representation**, not the quality, importance, persuasiveness, or legal correctness of the papers.

> **Navigation is free; completeness is strict.**

Evaluators may visit sections and Claims in any order. Missing answers never block navigation, but a paper cannot be marked complete until all required evaluation information is provided.

## Evaluation structure

Each paper contains six sections:

1. **Source**
2. **Claims**
3. **Datasets**
4. **Citations within the Brain**
5. **Source-level completeness**
6. **Review**

Claims are evaluated through five subsections:

* A · Claim
* B · Grounding
* C · Attributes
* D · Concepts
* E · Relations

Progress is shown as:

```text
○ untouched
● in progress
✓ complete
```

## Evaluation phases

The application has three independent phases:

* `training`
* `agreement`
* `individual`

Training is optional and uses W0085 and W0206.

Agreement papers are independently evaluated by pairs of evaluators. Individual papers are evaluated by one evaluator.

Reserved IND-1 assignments for Thiago and Francesca remain invisible and count toward nothing until activated.

## Saving and resume

Answers are saved automatically and asynchronously.

The interface updates immediately while writes are queued in the background. Failed writes are retained and retried, and unresolved writes prevent paper completion or final submission.

Evaluation state is reconstructed from persistent storage after refresh, browser restart, or application restart.

## Paper completion and submission

Paper lifecycle:

```text
not_started → in_progress → complete → submitted
```

A completed paper remains editable. Any later edit returns it to `in_progress`.

Final submission happens separately for Training, Agreement, and Individual.

## Production storage

Production data is stored in Google Sheets using seven tabs:

```text
CONFIG
EVALUATORS
ASSIGNMENTS
REVIEWS
RESPONSES
EDGE_RESPONSES
PHASE_SUBMISSIONS
```

Rows are preallocated and use deterministic keys. Normal evaluation uses targeted reads and writes rather than repeatedly downloading whole tables.

The production workbook contains live research data. Do not bootstrap, preallocate, clear, migrate, or otherwise modify it unless explicitly required.

## Evaluation specification

The current evaluation instrument is:

```text
EVAL_SPEC_VERSION = 3.0
```

Question wording and criterion definitions come from the evaluation specification files, not from the UI code.

Changing the instrument during live evaluation is a methodological decision, not an ordinary software change.

## Running locally

Python 3.11 is used.

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app/streamlit_app.py
```

Required production configuration includes:

```text
HE_APP_PASSWORD
HE_ADMIN_SECRET
GOOGLE_SHEET_ID
HE_REQUIRE_SHEETS
```

plus Google service-account credentials.

Never commit credentials to the repository.

## Deployment

The application is deployed through Streamlit Cloud.

Entrypoint:

```text
app/streamlit_app.py
```

See `DEPLOYMENT.md` for Google Sheets setup, secrets, deployment, and troubleshooting.

## Main files

```text
app/
├── streamlit_app.py   # application shell
├── views.py           # evaluation pages
├── ui.py              # shared UI and autosave behaviour
├── progress.py        # applicability and completeness
├── spec.py            # evaluation instrument
├── brain.py           # read-only Brain access
├── manifest.py        # evaluators and assignments
├── store.py           # storage abstraction
├── sheets.py          # Google Sheets backend
├── savequeue.py       # asynchronous saving
├── tests/
└── tools/
```

## Development during live evaluation

The system is now in production bug-fix mode.

Use:

> **Reproduce → identify cause → regression test → smallest fix → targeted verification → deploy.**

Avoid unrelated refactoring.

Unless explicitly approved, do not change:

* evaluation specification v3;
* question wording;
* scales or applicability;
* Brain snapshot;
* assignment methodology;
* phase semantics;
* storage schema;
* completion/submission rules.

UI and interaction bugs should normally require only a code change and redeployment, without touching production data.

## Known limitations

Same-evaluator conflict detection across multiple browser tabs is best-effort rather than transactional.

Google Sheets has API rate limits, so configuration and review data are cached and normal saves use narrow updates.

Streamlit subsection state is application-driven: a subsection being actively evaluated stays open while incomplete and may advance once complete.

## Status

The application is deployed and currently being used for human evaluation.
