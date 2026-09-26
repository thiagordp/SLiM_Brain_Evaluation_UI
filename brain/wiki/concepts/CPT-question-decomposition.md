---
id: CPT-question-decomposition
status: candidate
concept_type: technique_class
definition: Dissecting a complex question into a sequence of smaller, simpler questions that guide a model stepwise toward the answer.
run_ids: [RUN-2026-09-25-01]
---

# CPT-question-decomposition

## What it means

Dissecting a complex question into a sequence of smaller, simpler questions that guide a model stepwise toward the answer. A candidate concept coined during the ingest of SRC-0015 and drawn from its claims [CLM-0015-006] [CLM-0015-010].

## Claims

### Descriptive

**DE**

- Breaking a complex extraction task into simpler sub-tasks addressed through the distinct layers of the Layer-of-Thoughts framework allows a large language model to focus on one specific aspect at a time, contributing to higher accuracy, and applying Standard prompts for the first two layers with Chain-of-Instructions prompting for the final layer enhances the framework's effectiveness. — rests on factual basis (SRC-0017). [CLM-0017-009]

**MY+AU**

- Decomposing the legal question of a scenario into simpler questions consistently improves ChatGPT's accuracy in identifying legal concepts, such as 'invitation to treat' — reaching a precision of 0.75, recall of 0.88 and an F1-score of 0.81 on legal concept identification — but does not always improve the correctness of the produced reasoning paths. — rests on factual basis (SRC-0015). [CLM-0015-006]
- After using in-context learning and decomposed questions, ChatGPT identifies and correctly discusses more assumptions in its defeasible legal reasoning, though the improvement in the analysis remains smaller than that in the assumptions. — rests on factual basis (SRC-0015). [CLM-0015-010]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0015 | unknown | 2 | 2 descriptive | 2 factual | MY+AU |
| SRC-0017 | 2024 | 1 | 1 descriptive | 1 factual | DE |

## What is missing

Absence records whose key names this concept (9, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0552 — `concept_pair:CPT-compliance-and-monitoring|CPT-question-decomposition` — No claim links CPT-compliance-and-monitoring to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0566 — `concept_pair:CPT-dataset-license-compliance|CPT-question-decomposition` — No claim links CPT-dataset-license-compliance to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0581 — `concept_pair:CPT-decision-support|CPT-question-decomposition` — No claim links CPT-decision-support to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0597 — `concept_pair:CPT-fatwa-issuance|CPT-question-decomposition` — No claim links CPT-fatwa-issuance to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0612 — `concept_pair:CPT-irac-analysis|CPT-question-decomposition` — No claim links CPT-irac-analysis to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0629 — `concept_pair:CPT-legal-drafting|CPT-question-decomposition` — No claim links CPT-legal-drafting to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0647 — `concept_pair:CPT-legal-education|CPT-question-decomposition` — No claim links CPT-legal-education to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0666 — `concept_pair:CPT-review-and-due-diligence|CPT-question-decomposition` — No claim links CPT-review-and-due-diligence to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0684 — `concept_pair:CPT-rulemaking|CPT-question-decomposition` — No claim links CPT-rulemaking to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- None recorded at this close-out.
