---
id: CPT-llm-as-a-judge
status: candidate
concept_type: technique_class
definition: Using large language models as evaluators that score or rank the outputs of other models against a rubric or evaluation protocol, in place of or alongside human raters.
run_ids: [RUN-2026-09-25-01]
---

# CPT-llm-as-a-judge

## What it means

Using large language models as evaluators that score or rank the outputs of other models against a rubric or evaluation protocol, in place of or alongside human raters. A candidate concept coined during the ingest of SRC-0020 and drawn from its claims [CLM-0020-002] [CLM-0020-005] [CLM-0020-020] [CLM-0020-021].

## Claims

### Descriptive

**undetermined**

- When evaluating LLM-generated legal reasoning on ECtHR cases, LLM-as-a-Judge evaluators (GPT-5.5, Claude Opus 4.7 and DeepSeek V4 Pro) are internally consistent yet align only weakly with trained human annotators (judge-judge α = 0.41 versus human-human α = 0.09 on comprehensiveness; judge-human ρ = 0.16-0.33): they are reliable but not a valid substitute for human evaluation. — rests on factual basis (SRC-0020). [CLM-0020-002]

### Prescriptive

**general**

- The research community should not rely solely on automated LLM-based evaluation of legal reasoning, and should not treat task accuracy as a proxy for reasoning quality. — rests on factual basis (SRC-0020). [CLM-0020-005]
- LLM systems in legal settings should support, not replace, human legal judgment, and automated evaluation of legal reasoning should be validated against, not substituted for, expert assessment. — rests on factual basis (SRC-0020). [CLM-0020-020]

### Predictive

**general**

- Because LLM judges agree with one another far more than with trained annotators and over-rate the hardest (proportionality) step, using them as the sole arbiter of good legal reasoning risks entrenching a shared model bias under a veneer of consensus. — rests on factual basis (SRC-0020). [CLM-0020-021]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0020 | 2025 | 4 | 1 descriptive, 2 prescriptive, 1 predictive | 4 factual | general, undetermined |

## What is missing

Absence records whose key names this concept (8, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0549 — `concept_pair:CPT-compliance-and-monitoring|CPT-llm-as-a-judge` — No claim links CPT-compliance-and-monitoring to CPT-llm-as-a-judge. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0561 — `concept_pair:CPT-dataset-license-compliance|CPT-llm-as-a-judge` — No claim links CPT-dataset-license-compliance to CPT-llm-as-a-judge. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0592 — `concept_pair:CPT-fatwa-issuance|CPT-llm-as-a-judge` — No claim links CPT-fatwa-issuance to CPT-llm-as-a-judge. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0607 — `concept_pair:CPT-irac-analysis|CPT-llm-as-a-judge` — No claim links CPT-irac-analysis to CPT-llm-as-a-judge. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0625 — `concept_pair:CPT-legal-drafting|CPT-llm-as-a-judge` — No claim links CPT-legal-drafting to CPT-llm-as-a-judge. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0642 — `concept_pair:CPT-legal-education|CPT-llm-as-a-judge` — No claim links CPT-legal-education to CPT-llm-as-a-judge. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0661 — `concept_pair:CPT-review-and-due-diligence|CPT-llm-as-a-judge` — No claim links CPT-review-and-due-diligence to CPT-llm-as-a-judge. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0679 — `concept_pair:CPT-rulemaking|CPT-llm-as-a-judge` — No claim links CPT-rulemaking to CPT-llm-as-a-judge. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- None recorded at this close-out.
