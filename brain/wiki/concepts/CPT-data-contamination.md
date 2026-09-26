---
id: CPT-data-contamination
status: candidate
concept_type: normative_concern
definition: Overlap between a model's training data and the material used to evaluate it, including memorisation of specific cases or documents, which undermines the validity of evaluation results.
run_ids: [RUN-2026-09-25-01]
---

# CPT-data-contamination

## What it means

Overlap between a model's training data and the material used to evaluate it, including memorisation of specific cases or documents, which undermines the validity of evaluation results. A candidate concept coined during the ingest of SRC-0020 and drawn from its claims [CLM-0020-007].

## Claims

### Descriptive

**US**

- The strong performance of recent large language models on legal reasoning benchmarks is partly inflated by data contamination and benchmark memorization: much publicly available legal data may have been incorporated into training corpora, compromising evaluation validity and motivating contamination-free test sets. — rests on factual basis (SRC-0021). [CLM-0021-001]
- Newer frontier large language models exhibit higher data contamination on the SARA statutory reasoning benchmark than earlier models; this trend may reflect greater exposure to SARA-like data in recent web-scale training corpora, but it does not imply a causal link to model scale. — rests on factual basis (SRC-0021). [CLM-0021-002]
- In statutory tax reasoning, measured data contamination is strongly associated with large language model performance in the direct question-answering setting, especially on the entailment task, while the correlation between contamination and Prolog-based performance is weak, suggesting that structured reasoning pipelines can mitigate contamination effects. — rests on factual basis (SRC-0021). [CLM-0021-003]
- In direct question answering over tax statutes, textual entailment is consistently easier for large language models than numerical reasoning, which remains difficult even for recent models; entailment performance appears to be saturating, potentially due to contamination, and recent models may be overfitting to that setting. — rests on factual basis (SRC-0021). [CLM-0021-009]
- A synthetic test suite for statutory tax reasoning can be constructed from SARA by conservatively perturbing numerical values in rules and cases and paraphrasing case texts, minimizing data contamination while preserving legal and structural complexity, and — by applying identical perturbations to textual rules and Prolog programs — yielding precise formal representations and exact solutions without human expert effort. — rests on factual basis (SRC-0021). [CLM-0021-010]

**general**

- Using only very recent cases in a legal evaluation dataset reduces, though does not fully eliminate, overlap with an examined model's training data; in early experiments models were found to memorize cases, especially popular ones that have been heavily discussed. — rests on factual basis (SRC-0020). [CLM-0020-007]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0020 | 2025 | 1 | 1 descriptive | 1 factual | general |
| SRC-0021 | unknown | 5 | 5 descriptive | 5 factual | US |

## What is missing

Absence records whose key names this concept (13, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0133 — `concept_jurisdiction:CPT-data-contamination|AU` — No claim about CPT-data-contamination concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0134 — `concept_jurisdiction:CPT-data-contamination|BR` — No claim about CPT-data-contamination concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0135 — `concept_jurisdiction:CPT-data-contamination|CA` — No claim about CPT-data-contamination concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0136 — `concept_jurisdiction:CPT-data-contamination|CN` — No claim about CPT-data-contamination concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0137 — `concept_jurisdiction:CPT-data-contamination|DE` — No claim about CPT-data-contamination concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0138 — `concept_jurisdiction:CPT-data-contamination|EU` — No claim about CPT-data-contamination concerns EU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0139 — `concept_jurisdiction:CPT-data-contamination|GB` — No claim about CPT-data-contamination concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0140 — `concept_jurisdiction:CPT-data-contamination|KR` — No claim about CPT-data-contamination concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0141 — `concept_jurisdiction:CPT-data-contamination|MY` — No claim about CPT-data-contamination concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0142 — `concept_jurisdiction:CPT-data-contamination|NL` — No claim about CPT-data-contamination concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0143 — `concept_jurisdiction:CPT-data-contamination|NZ` — No claim about CPT-data-contamination concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0144 — `concept_jurisdiction:CPT-data-contamination|RU` — No claim about CPT-data-contamination concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0145 — `concept_jurisdiction:CPT-data-contamination|TR` — No claim about CPT-data-contamination concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- None recorded at this close-out.
