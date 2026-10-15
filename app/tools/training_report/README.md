# Training-phase calibration report

Builds `docs/TRAINING_AGREEMENT_REPORT.docx` from the round workbook. Read-only:
nothing is written to the workbook.

1. **Extract**: one JSON snapshot of all Training answers, comments, anchors and
   agreement statistics.

   ```bash
   GOOGLE_SHEET_ID=... GOOGLE_SERVICE_ACCOUNT_JSON=... \
     python app/tools/training_report/extract.py /tmp/training_data.json
   ```

   The JSON holds evaluators' answers and comments verbatim. Keep it out of the
   repository.

2. **Render**: needs the `docx` npm package. Install it outside the repository,
   for example `npm install --prefix /tmp/docxenv docx`.

   ```bash
   NODE_PATH=/tmp/docxenv/node_modules \
     node app/tools/training_report/build_report.js /tmp/training_data.json docs/TRAINING_AGREEMENT_REPORT.docx
   ```

All counts, percentages, splits and the appendices are computed from the JSON.
The interpretive text (Sections 1, 4–9) names specific items and quotes
comments through lookups that fail loudly if an item no longer exists. Each
time the data change, reread that text against the new figures.

**Gating** ("Evaluation 4.1 — October 7, 2026 calibration gating", see
`app/README.md`): a rater whose gate was answered No has no answer for the
gated item. The JSON lists them per item in `skipped` and per paper in
`skipped_answers`. They are not missing answers, and items nobody could answer
are counted in `items_all_skipped`. Appendix B shows such cells as "Not applicable"
(a label; the statistics read the `skipped` list, never the text) and the
per-evaluator statistics leave them out. Sentences such as "there are
no missing answers" or "every item has seven answers" must be reread after a
rerun.

**Appendix B** lists every contested item (landscape, one table per Claim):
- **Above each table:** the Claim statement in a box, then its anchors.
- **Columns:** one per evaluator; each cell holds the answer and the verbatim comment.
- **Highlighting:** orange for an answer outside the row's majority; yellow for a tie.
- **Other rows:** Missing Concepts (Q14) where the evaluators differ, and Claim
  recall, restatements and Missing Claims per paper.

**Appendix C (agreement coefficients)** reads the `coefficients` block of the JSON:
- **Where it comes from:** `extract.py` writes it.
- **Adding it to an existing JSON:** run
  `python app/tools/training_report/coefficients.py DATA.json`, which updates the
  file in place and takes about 20 s because of the bootstrap.
- **What it contains:** percentage agreement, Cohen/Light and Fleiss κ,
  Krippendorff's α (nominal, and MASI for Missing Concepts), Gwet's AC1,
  positive/negative specific agreement, and bootstrap confidence intervals.

**Calibration cases (meeting handout):** `build_cases.js` renders
`docs/CALIBRATION_CASES.md` as `docs/CALIBRATION_CASES.docx`, in the report's
style. Edit the .md, then run:

    NODE_PATH=<dir with node_modules/docx> node app/tools/training_report/build_cases.js docs/CALIBRATION_CASES.md docs/CALIBRATION_CASES.docx

**Timelines** (work sessions per evaluator and paper, read-only):

    python app/tools/training_report/timeline.py docs/TRAINING_TIMELINE.md              # Training
    python app/tools/training_report/timeline.py docs/AGREEMENT_TIMELINE.md agreement    # any other phase

Render the Mermaid chart to SVG/PNG with mermaid-cli. If puppeteer has no
browser of its own, point it at the system Chrome with a config file
`{"executablePath": "/usr/bin/google-chrome"}`:

    mmdc -p puppeteer.json -i chart.mmd -o docs/AGREEMENT_TIMELINE.svg --size 1500 -b white

(Older mermaid-cli releases take `-w 1500` instead of `--size 1500`.)
