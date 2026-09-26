---
id: CPT-in-context-learning
status: candidate
concept_type: technique_class
definition: Improving a large language model's performance on a task by including worked examples — similar cases together with their solutions — in the prompt, without updating the model's parameters.
run_ids: [RUN-2026-09-25-01]
---

# CPT-in-context-learning

## What it means

Improving a large language model's performance on a task by including worked examples — similar cases together with their solutions — in the prompt, without updating the model's parameters. A candidate concept coined during the ingest of SRC-0015 and drawn from its claims [CLM-0015-005] [CLM-0015-010].

## Claims

### Descriptive

**MY+AU**

- ChatGPT benefits from adding similar example scenarios with IRAC analysis to the prompt during in-context learning only if similar scenarios can be found: with the most similar example added, the quality of its reasoning paths improved by 27.5%, especially for Australian Social Act scenarios, and the F1 score on the analysis part changed from 0.34 to 0.66. — rests on factual basis (SRC-0015). [CLM-0015-005]
- After using in-context learning and decomposed questions, ChatGPT identifies and correctly discusses more assumptions in its defeasible legal reasoning, though the improvement in the analysis remains smaller than that in the assumptions. — rests on factual basis (SRC-0015). [CLM-0015-010]

### Interpretative

**NL**

- Large language models' ability to apply legal knowledge when identifying advertisements may rely more on patterns learned during pretraining than on the legal text provided in the prompt; current LLMs do not simply 'read and apply' legal norms but rely heavily on internal heuristics and contextual associations, so their performance may reflect an underlying competence in identifying pragmatic markers of advertising rather than understanding and applying legal knowledge. — rests on factual basis (SRC-0023). [CLM-0023-006]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0015 | unknown | 2 | 2 descriptive | 2 factual | MY+AU |
| SRC-0023 | unknown | 1 | 1 interpretative | 1 factual | NL |

## What is missing

Absence records whose key names this concept (8, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0548 — `concept_pair:CPT-compliance-and-monitoring|CPT-in-context-learning` — No claim links CPT-compliance-and-monitoring to CPT-in-context-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0560 — `concept_pair:CPT-dataset-license-compliance|CPT-in-context-learning` — No claim links CPT-dataset-license-compliance to CPT-in-context-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0577 — `concept_pair:CPT-decision-support|CPT-in-context-learning` — No claim links CPT-decision-support to CPT-in-context-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0591 — `concept_pair:CPT-fatwa-issuance|CPT-in-context-learning` — No claim links CPT-fatwa-issuance to CPT-in-context-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0624 — `concept_pair:CPT-legal-drafting|CPT-in-context-learning` — No claim links CPT-legal-drafting to CPT-in-context-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0640 — `concept_pair:CPT-legal-education|CPT-in-context-learning` — No claim links CPT-legal-education to CPT-in-context-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0659 — `concept_pair:CPT-review-and-due-diligence|CPT-in-context-learning` — No claim links CPT-review-and-due-diligence to CPT-in-context-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0678 — `concept_pair:CPT-rulemaking|CPT-in-context-learning` — No claim links CPT-rulemaking to CPT-in-context-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- None recorded at this close-out.
