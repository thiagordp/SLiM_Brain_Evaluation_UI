# Calibration guide and decision register

Builds the calibration documents in `Calibration/` from the annotated Training report. Nothing is written to the sources.

| Output | What it is |
|---|---|
| `SLIM_BRAIN_CALIBRATION_GUIDE.docx` / `.pdf` | Main guide. Pages 1–2 are the overview: every rule in one line, then the open decisions. The detail follows. |
| `SLIM_BRAIN_CALIBRATION_ANNEX.docx` / `.pdf` | Full register of the 167 contested items, review lists, contradictions in the Finals, comments and evidence |
| `CALIBRATION_DECISION_REGISTER.csv`, `CALIBRATION_MISSING_CONCEPTS.csv` | Machine-readable register |

Use the `unibo_env` Python, which has python-docx and lxml. `register.json` holds evaluators' comments verbatim, so keep it out of the repository.

```bash
PY=/home/trdp/anaconda3/envs/unibo_env/bin/python
T=app/tools/calibration_guide
B=/tmp/calibration_build                                   # any directory outside the repo
$PY $T/extract_register.py $B                              # register.json
$PY $T/validate.py $B                                      # must report 0 errors
$PY $T/build_guide.py $B Calibration/SLIM_BRAIN_CALIBRATION_GUIDE.docx
$PY $T/build_annex.py $B Calibration/SLIM_BRAIN_CALIBRATION_ANNEX.docx
$PY -c "import sys,json; sys.path.insert(0,'$T'); import extract_register as e, pathlib; e.write_csv(json.load(open('$B/register.json')), pathlib.Path('Calibration'))"
$PY $T/check_links.py Calibration/SLIM_BRAIN_CALIBRATION_*.docx
(cd Calibration && soffice --headless --convert-to pdf SLIM_BRAIN_CALIBRATION_GUIDE.docx SLIM_BRAIN_CALIBRATION_ANNEX.docx)
```

After a content change, check that the guide's overview still fits on pages 1–2: page 3 must begin with "3  How to read this guide".

## Files

| File | Role |
|---|---|
| `report_docx.py` | Reads the report's XML directly, keeping cells, reviewer comments, highlights and line breaks |
| `extract_register.py` | Normalises each Final and applies the 4.1 gates when reading answers. It computes Differs, splits Missing-Concept proposals and compares against the earlier summary |
| `policies.py` | The hand-written content model: rules (with a one-line `brief` and an overview `group`), status, sources, quotations, decisions, consistency checks and the schema baseline |
| `validate.py` | Checks every quotation verbatim against its source, and checks the status rules, example ids and Differs. It also lints the prose: no rule ids inside sentences, no em dashes, no stock phrases |
| `docstyle.py` | python-docx style helpers |
| `build_guide.py`, `build_annex.py` | The two documents |
| `check_links.py` | Checks that every internal hyperlink has a bookmark |

When a source changes, edit `policies.py` and run the steps again. `validate.py` fails if a quotation no longer matches its source.
