# Plan for optimization of the page.

The safest principle is:

> **Separate the evaluation specification, assignments, persistence, and UI. Change one layer at a time and keep the app runnable after every step.**

The workbook still gives us the underlying evaluation structure—Source, Claim, Dataset, CITES/recall, and the roll-up—but the 7 September calibration decisions modify some wording and response mechanics, as we have already incorporated page by page. 

## Overall implementation order

I suggest this sequence:

1. **Freeze the evaluation specification and UI decisions**
2. **Refactor the current app so storage is independent from the UI**
3. **Replace SQLite with Google Sheets**
4. **Implement Alessandro's evaluator/split assignments**
5. **Make autosave/concurrency/resume robust**
6. **Implement the UI revisions page by page**
7. **Implement paper completion and final submission**
8. **Admin/export**
9. **End-to-end testing on Streamlit**
10. **Deploy the evaluation version**

I would not ask Claude Code to do several of these at once.

---

# Step 1 — Freeze what the application is supposed to do

This should come **before touching Google Sheets or rewriting pages**.

We already have almost everything needed.

Claude Code should create one internal, versioned evaluation specification containing:

* question ID;
* visible title;
* exact question wording;
* criterion definition;
* answer choices;
* applicability rules;
* whether a comment is required;
* conditional free-text fields;
* section/order.

This should encode the **final wording we agreed page by page**, not dynamically read the Excel workbook.

For example:

```python
{
    "id": "HE-06",
    "section": "grounding",
    "title": "Textual grounding",
    "question": "Do the anchors provide sufficient textual grounding for this Claim in the source?",
    "answers": ["Yes", "In part", "No"],
    "comment_required_if": ["In part", "No"],
    ...
}
```

The Excel, meetings and schema remain the **development references**. They are not runtime dependencies.

Also give the specification a version, e.g.:

```text
EVAL_SPEC_VERSION = "2026-09-08"
```

Every stored review should later record this.

### Important special cases to encode

Claude Code should not assume every question has the same structure.

We have:

* ordinary Yes / In part / No questions;
* HE-21 automatically not applicable when no candidate was created;
* HE-19.3 missing Claims — free text;
* HE-20.b missing Concepts — free text;
* HE-18.3 missing/spurious CITES — conditional free text;
* edge-by-edge HE-16 judgments;
* Source-level conceptual coverage added during calibration;
* Dataset recall HE-14.3 assessed once for the Source, not once per Dataset.

This is exactly why we need a specification layer.

---

# Step 2 — Decouple storage before replacing SQLite

This is critical.

Do **not** tell Claude Code:

> Replace SQLite everywhere with Google Sheets.

That is likely to mix database changes into every page.

Instead, first create a storage interface such as conceptually:

```text
StorageBackend
    get_review(...)
    get_response(...)
    save_response(...)
    get_edge_response(...)
    save_edge_response(...)
    get_assignments(...)
    mark_paper_complete(...)
    final_submit(...)
```

The UI should call this interface and know nothing about SQLite or Google Sheets.

Initially:

```text
SQLiteBackend
```

continues to implement it.

Once the app still works after this refactor, add:

```text
GoogleSheetsBackend
```

Then switching database becomes configuration rather than rewriting the UI.

This is probably the most important architectural step.

---

# Step 3 — Google Sheets

Then migrate persistence.

I would use **one Google Sheets workbook for the entire experiment**, with these tabs:

```text
CONFIG
EVALUATORS
ASSIGNMENTS

REVIEWS
RESPONSES
EDGE_RESPONSES
```

### Configuration

`CONFIG`

```text
evaluation_spec_version
brain_snapshot_id
evaluation_open
```

### Evaluators

`EVALUATORS`

```text
evaluator_id
name
is_admin
```

### Assignments

`ASSIGNMENTS`

One explicit row per evaluator × split.

Do **not infer assignments from names or AGR letters**.

That matters because Alessandro's current naming is deliberately non-parallel:

* Giovanni + Alessandro → `AGR-C`
* Giuseppe + Vaclav → `AGR-B`
* Thiago + Francesca → `AGR-A`

So the app should simply read explicit assignments.

---

# Step 4 — Encode Alessandro's current division

The current configuration should become:

| Evaluator  | Agreement split | Individual split                         |
| ---------- | --------------- | ---------------------------------------- |
| Alessandro | AGR-C           | IND-3                                    |
| Giovanni   | AGR-C           | IND-5                                    |
| Giuseppe   | AGR-B           | IND-2                                    |
| Vaclav     | AGR-B           | IND-4                                    |
| Thiago     | AGR-A           | **TBD / IND-1 depending final decision** |
| Francesca  | AGR-A           | **TBD / IND-1 depending final decision** |

And for everybody:

```text
Training:
W0085
W0206
```

I would **not hard-code IND-1 yet** because Alessandro explicitly wrote:

> “if possible, depending on availability”.

Make it a configuration row that can be added once decided.

Also, I would stop displaying generic labels such as **Pair B** in the evaluator UI. They are now more confusing than helpful. The app can internally know the pair, but the evaluator mainly needs to see:

> Agreement: AGR-C
> Individual: IND-5

or simply the papers assigned to them.

---

# Step 5 — Preallocate Google Sheets rows

Before evaluators start, create all expected rows.

For example:

```text
Giovanni | W0336 | CLM... | HE-03
Giovanni | W0336 | CLM... | HE-04
...
Alessandro | W0336 | CLM... | HE-03
```

This makes concurrent use much safer.

Then every answer has a deterministic key such as:

```text
mode
+ evaluator
+ source
+ object
+ criterion
```

and every edge judgment has a deterministic edge-response key.

No evaluator ever writes into another evaluator's cells.

### Important rule

Never do:

> read entire sheet → modify dataframe → overwrite sheet

with six users working simultaneously.

Only targeted row/cell updates.

---

# Step 6 — Autosave

We already decided:

> **The UI should not wait for Google Sheets.**

The intended architecture is:

```text
Evaluator changes answer
        ↓
session state changes immediately
        ↓
write queued
        ↓
background targeted Sheets update
        ↓
Saved
```

Show only a small status:

* `Saving…`
* `Saved`
* `Retrying…`
* `Save failed`

Repeated rapid changes to the same response should collapse to the **latest value**.

### Important exception

These actions must flush pending writes:

* marking a paper complete;
* final Training submission;
* final Evaluation submission.

So:

```text
ordinary work = asynchronous

completion/submission = verify all writes first
```

I would make this a separate Claude Code task after the basic Google Sheets backend works synchronously. First make it correct; then make it asynchronous.

---

# Step 7 — Resume and state

Google Sheets becomes the durable source of truth.

If Giovanni closes the browser halfway through Claim 8:

```text
Wxxxx → In progress
```

When he returns:

> **Continue**

and the app reconstructs progress from persisted responses.

Do not depend on Streamlit session state for answers.

Session state should only hold temporary things such as:

* current page;
* current Claim;
* currently open modal;
* pending async writes;
* authenticated evaluator.

---

# Step 8 — Only now implement the UI changes

I would then give Claude Code **one page at a time**, in exactly the order we reviewed them:

1. Password
2. Evaluator selection
3. Training/Evaluation paper list
4. Paper start/read confirmation
5. Source
6. Claim
7. Dataset
8. CITES
9. Source-level completeness
10. Review

Do not give Claude all ten UI descriptions in one coding prompt.

For each page:

> implement → run → inspect visually → fix → commit → next page.

The **Claim page** should probably itself be split into smaller Claude tasks:

* Claim header/navigation;
* Claim/grounding;
* attributes;
* concepts + modal;
* relations;
* previous/next Claim dynamics.

---

# Step 9 — Standard modal system

Before doing Claim/Concept/Dataset/CITES UI, ask Claude Code to create **one reusable modal component**.

From Claim onward, all contextual records should use it:

* Source wiki;
* Concept wiki;
* Dataset wiki;
* Claim record;
* Source registry;
* Concept registry.

Properties:

* centred;
* ~75% viewport width;
* ~80–85% viewport height;
* background dimmed;
* its own scrolling;
* close button;
* internal navigation/back;
* must never affect evaluation progress;
* must never change main-page scroll position;
* automatically closes when changing Claim/Dataset/context.

That prevents each page from inventing its own wiki behaviour.

---

# Step 10 — Paper completion versus final submission

Claude Code needs to understand this distinction clearly.

### Paper

```text
Not started
→ In progress
→ Complete
```

`Complete` is **reversible**.

Evaluator can reopen:

**Review**

and modify answers.

If something becomes incomplete:

```text
Complete → In progress
```

### Mode-wide final submission

Only from the Training/Evaluation paper-list page:

```text
all assigned papers Complete
        ↓
Final submission enabled
```

After confirming:

```text
FINAL SUBMITTED
```

Everything in that mode becomes read-only.

That is the irreversible step.

Training and Evaluation use exactly the same mechanics.

---

# Step 11 — Review page

Do not store a second summary dataset.

The Review page should derive its state from:

```text
RESPONSES
EDGE_RESPONSES
```

and calculate:

* missing answers;
* required comments missing;
* conditional fields missing;
* incomplete Claims/Datasets/etc.

A `No` answer is **not incomplete**.

That distinction needs automated tests.

---

# Step 12 — Streamlit reliability tests

Before deployment, explicitly test:

* two reviewers simultaneously;
* ideally all six test sessions;
* rapid answer changes;
* browser refresh;
* close/reopen;
* background save failure;
* Google Sheets temporary failure;
* same reviewer in two tabs;
* completion with writes pending;
* final submission;
* read-only state;
* modal behaviour;
* long papers with 50+ Claims;
* Sources with zero Datasets;
* Sources with zero CITES;
* Claims with zero/one/many relations.

Only after these pass should the app be considered ready.

---

## I would therefore start with only one task now

Before asking Claude Code to touch Google Sheets or the pages, give it a **small architectural task**:

> **Inspect the current codebase and refactor persistence behind a storage interface without changing any visible behaviour. Keep SQLite as the active backend for now. Identify all places where UI code reads or writes SQLite directly and route them through the new interface. Do not modify evaluation wording, assignments, navigation or styling in this step. Run the existing app and verify behaviour remains unchanged.**

That gives us a clean foundation.

**Then**, once that is stable, I would move to **Google Sheets as Step 2**, and we can design that task in detail before you send anything to Claude Code.
