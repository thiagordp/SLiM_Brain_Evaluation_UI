---
id: CPT-deep-learning
status: anchor
concept_type: technique_class
definition: Neural-network techniques, including trained transformer models, used as learnable components distinct from prompted general-purpose LLMs.
run_ids: [RUN-2026-09-25-01]
---

# CPT-deep-learning

## What it means

Neural-network techniques, including trained transformer models, used as learnable components distinct from prompted general-purpose LLMs. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0007-006] [CLM-0009-008] [CLM-0009-009].

## Claims

### Descriptive

**CN**

- Fine-tuning the general-purpose embedding model BGE on the Chinese legal case retrieval dataset LeCaRD yields a significant increase in each NDCG@K over BM25 and the non-fine-tuned BGE, showing that a fine-tuned embedding model can learn legal knowledge well and better distinguish legal cases that are semantically similar but not relevant in the legal domain, although specialised case-retrieval models such as CaseEncoder, SAILER and CaseFormer still outperform it. — rests on factual basis (SRC-0014). [CLM-0014-007]

**EU**

- BERT-based architectures fine-tuned on LLM-annotated training data perform comparably to LLMs in classifying paragraphs of CJEU VAT decisions as containing Judicial Interpretative Formulas: the highest macro F1 score of 0.76 was achieved by both DistilRoBERTa and LEGAL-BERT, with all other models closely behind at a minimum of 0.72, comparable to or even better than DeepSeek. — rests on factual basis (SRC-0009). [CLM-0009-008]

**undetermined**

- A cross-encoder architecture, which jointly processes the query and passage through its attention layers, is essential for retrieving coverage-governing policy passages because it captures fine-grained interactions between a procedure code and subtle policy phrases that are often lost in compressed vector representations; exhaustive cross-encoder scoring is feasible because the candidate pool of subsections per plan is small and well-defined. — rests on abstract considerations (SRC-0007). [CLM-0007-006]

### Interpretative

**EU**

- Transformer models trained on data annotated by DeepSeek exhibit behaviours similar to generative LLMs — higher recall and lower precision on the positive class — and it is reasonable to speculate that they may have learned similar patterns and a tendency to favour false positives over false negatives. — rests on factual basis (SRC-0009). [CLM-0009-009]
- LEGAL-BERT may be considered the best model for Judicial Interpretative Formula extraction: it is the most stable and has the best macro F1 score and the best F1 score on the positive class, and its near-best recall on the positive class is particularly relevant for tools intended for legal practitioners, since the presence of additional JIFs is preferable to the absence of fundamental ones — users can easily discard a few irrelevant paragraphs, but cannot know if a crucial JIF is missing. — rests on factual basis (SRC-0009). [CLM-0009-011]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0007 | 2026 | 1 | 1 descriptive | 1 abstract | undetermined |
| SRC-0009 | 2025 | 3 | 1 descriptive, 2 interpretative | 3 factual | EU |
| SRC-0014 | unknown | 1 | 1 descriptive | 1 factual | CN |

## What is missing

Absence records whose key names this concept (8, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0544 — `concept_pair:CPT-compliance-and-monitoring|CPT-deep-learning` — No claim links CPT-compliance-and-monitoring to CPT-deep-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0556 — `concept_pair:CPT-dataset-license-compliance|CPT-deep-learning` — No claim links CPT-dataset-license-compliance to CPT-deep-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0586 — `concept_pair:CPT-fatwa-issuance|CPT-deep-learning` — No claim links CPT-fatwa-issuance to CPT-deep-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0603 — `concept_pair:CPT-irac-analysis|CPT-deep-learning` — No claim links CPT-irac-analysis to CPT-deep-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0619 — `concept_pair:CPT-legal-drafting|CPT-deep-learning` — No claim links CPT-legal-drafting to CPT-deep-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0636 — `concept_pair:CPT-legal-education|CPT-deep-learning` — No claim links CPT-legal-education to CPT-deep-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0654 — `concept_pair:CPT-review-and-due-diligence|CPT-deep-learning` — No claim links CPT-review-and-due-diligence to CPT-deep-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0673 — `concept_pair:CPT-rulemaking|CPT-deep-learning` — No claim links CPT-rulemaking to CPT-deep-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- None recorded at this close-out.
