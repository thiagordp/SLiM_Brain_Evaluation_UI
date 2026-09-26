---
id: CPT-defeasible-reasoning
status: candidate
concept_type: technique_class
definition: Reasoning in which intermediate or final conclusions can be overturned when new evidence is considered or different assumptions are made to cope with missing information, as in default logic.
run_ids: [RUN-2026-09-25-01]
---

# CPT-defeasible-reasoning

## What it means

Reasoning in which intermediate or final conclusions can be overturned when new evidence is considered or different assumptions are made to cope with missing information, as in default logic. A candidate concept coined during the ingest of SRC-0015 and drawn from its claims [CLM-0015-002] [CLM-0015-009] [CLM-0015-010] [CLM-0015-012].

## Claims

### Descriptive

**MY+AU**

- In human evaluation of ChatGPT's IRAC analyses by law students, the questions evaluating the generated assumptions are subjective — a common problem in law education: the Cohen's Kappa inter-annotator agreement score over all evaluation measures was 0.55, rising to 0.75 when the assumption evaluation was excluded. — rests on factual basis (SRC-0015). [CLM-0015-009]
- After using in-context learning and decomposed questions, ChatGPT identifies and correctly discusses more assumptions in its defeasible legal reasoning, though the improvement in the analysis remains smaller than that in the assumptions. — rests on factual basis (SRC-0015). [CLM-0015-010]

**general**

- Prior legal datasets do not include intermediate reasoning paths understandable by legal professionals and neglect the aspect of defeasible reasoning; among existing legal QA datasets only LEGALBENCH applies the IRAC methodology, without full IRAC analysis on scenarios, and SARA codifies reasoning paths in Prolog, which is challenging for legal professionals to understand. — rests on literature (SRC-0015). [CLM-0015-002]
- Legal reasoning is defeasible: conclusions can be overturned by considering new evidence or by making different assumptions due to missing information. — rests on literature (SRC-0015). [CLM-0015-012]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0015 | unknown | 4 | 4 descriptive | 2 literature, 2 factual | MY+AU, general |

## What is missing

Absence records whose key names this concept (8, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0545 — `concept_pair:CPT-compliance-and-monitoring|CPT-defeasible-reasoning` — No claim links CPT-compliance-and-monitoring to CPT-defeasible-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0557 — `concept_pair:CPT-dataset-license-compliance|CPT-defeasible-reasoning` — No claim links CPT-dataset-license-compliance to CPT-defeasible-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0573 — `concept_pair:CPT-decision-support|CPT-defeasible-reasoning` — No claim links CPT-decision-support to CPT-defeasible-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0587 — `concept_pair:CPT-fatwa-issuance|CPT-defeasible-reasoning` — No claim links CPT-fatwa-issuance to CPT-defeasible-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0604 — `concept_pair:CPT-irac-analysis|CPT-defeasible-reasoning` — No claim links CPT-irac-analysis to CPT-defeasible-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0620 — `concept_pair:CPT-legal-drafting|CPT-defeasible-reasoning` — No claim links CPT-legal-drafting to CPT-defeasible-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0655 — `concept_pair:CPT-review-and-due-diligence|CPT-defeasible-reasoning` — No claim links CPT-review-and-due-diligence to CPT-defeasible-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0674 — `concept_pair:CPT-rulemaking|CPT-defeasible-reasoning` — No claim links CPT-rulemaking to CPT-defeasible-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- None recorded at this close-out.
