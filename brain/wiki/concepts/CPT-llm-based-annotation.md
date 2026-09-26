---
id: CPT-llm-based-annotation
status: emergent
concept_type: technique_class
definition: Using large language models to label documents automatically, producing machine-annotated training data from which smaller task-specific models can be trained in place of costly manual annotation by experts.
run_ids: [RUN-2026-09-25-01]
---

# CPT-llm-based-annotation

## What it means

Using large language models to label documents automatically, producing machine-annotated training data from which smaller task-specific models can be trained in place of costly manual annotation by experts. An emergent concept coined during the ingest of SRC-0009 and drawn from its claims [CLM-0009-007] [CLM-0009-008] [CLM-0009-009] [CLM-0009-012] [CLM-0009-014]. Promoted from candidate to emergent at this close-out: claims from 4 sources with no shared author are mapped to it (SRC-0008, SRC-0009, SRC-0016, SRC-0018).

## Claims

### Descriptive

**EU**

- Among LLMs evaluated with a guideline-based prompt for paragraph-level annotation of Judicial Interpretative Formulas against a manually annotated validation split of CJEU VAT decisions — Gemini-1.5-pro, DeepSeek-R1 and Claude-3.7-sonnet — DeepSeek obtained the highest score and was therefore adopted to annotate the training documents. — rests on factual basis (SRC-0009). [CLM-0009-007]
- BERT-based architectures fine-tuned on LLM-annotated training data perform comparably to LLMs in classifying paragraphs of CJEU VAT decisions as containing Judicial Interpretative Formulas: the highest macro F1 score of 0.76 was achieved by both DistilRoBERTa and LEGAL-BERT, with all other models closely behind at a minimum of 0.72, comparable to or even better than DeepSeek. — rests on factual basis (SRC-0009). [CLM-0009-008]
- Annotations produced automatically by LLMs can be exploited to distil LLM knowledge into much smaller models that obtain comparable results, reducing annotation costs and improving scalability; using a dedicated task-specific classifier for the final extraction of Judicial Interpretative Formulas combines the strengths of LLM prompting with a more transparent and reproducible model, mitigating LLM limitations at deployment. — rests on factual basis (SRC-0009). [CLM-0009-012]
- A novel corpus for Judicial Interpretative Formula extraction consists of 101 CJEU preliminary rulings on VAT — on the subtopics of taxable amounts and exemptions for the public interest, retrieved through a concept-based EUR-Lex search in December 2024 — structured into three document-level splits that separate manually annotated data for evaluation and development (21 expert-labelled decisions) from automatically annotated data for training (80 LLM-labelled decisions), with the test split containing only documents never used during guideline development. — rests on factual basis (SRC-0009). [CLM-0009-014]

**RU**

- When automatic annotation of Russian court decisions by a large language model (ChatGPT-4.1 with few-shot prompting) is compared with expert annotation, agreement is highest for procedural stages (97.31%), which are marked by clear formal indicators, and moderate for roles (65.59%) and discourse functions (53.76%). — rests on factual basis (SRC-0008). [CLM-0008-008]
- Automatic annotation of court decisions by a large language model is highly reproducible: across five iterations on the same pool of texts with identical parameters, average Cohen's Kappa was 0.82 — an almost perfect level of agreement — with average exact match 0.84, unigram Jaccard 0.92 and edit similarity 0.89, and the remaining differences are local in nature. — rests on factual basis (SRC-0008). [CLM-0008-010]

**US**

- Outcome predictions based on factor sets identified by a large language model using an expert-defined canonical factor representation can come very close in quality to predictions from gold-standard expert annotations, which suggests that the canonical factor representation is robust across annotators. — rests on factual basis (SRC-0018). [CLM-0018-005]

### Interpretative

**EU**

- Transformer models trained on data annotated by DeepSeek exhibit behaviours similar to generative LLMs — higher recall and lower precision on the positive class — and it is reasonable to speculate that they may have learned similar patterns and a tendency to favour false positives over false negatives. — rests on factual basis (SRC-0009). [CLM-0009-009]

### Predictive

**general**

- A tool that automates the generation of compliance reasoning data — selecting real-world examples of AI technologies and explaining how specific legal and ethical guidelines impact them, followed by a refinement process so that only the best candidates are presented to annotators — aims to facilitate the development of AI-driven compliance assistants that can effectively align with global legal and ethical standards. — rests on abstract considerations (SRC-0016). [CLM-0016-007]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0008 holds “Automatic annotation of court decisions by a large language model is highly reproducible: across five iterations on the same pool of texts …” [CLM-0008-010]; SRC-0009 holds “Approaches to automated extraction of legal principles face two main drawbacks: data-driven methods require costly annotation, while …” [CLM-0009-004]. Note: Evidence that automatic LLM annotation of court decisions is highly reproducible across repeated runs with identical parameters (average Cohen's Kappa 0.82) gives a reason against the drawback that LLM-based methods lack reproducibility.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0008 | 2026 | 2 | 2 descriptive | 2 factual | RU |
| SRC-0009 | 2025 | 5 | 4 descriptive, 1 interpretative | 5 factual | EU |
| SRC-0016 | 2024 | 1 | 1 predictive | 1 abstract | general |
| SRC-0018 | 2024 | 1 | 1 descriptive | 1 factual | US |

## What is missing

Absence records whose key names this concept (8, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0562 — `concept_pair:CPT-dataset-license-compliance|CPT-llm-based-annotation` — No claim links CPT-dataset-license-compliance to CPT-llm-based-annotation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0578 — `concept_pair:CPT-decision-support|CPT-llm-based-annotation` — No claim links CPT-decision-support to CPT-llm-based-annotation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0593 — `concept_pair:CPT-fatwa-issuance|CPT-llm-based-annotation` — No claim links CPT-fatwa-issuance to CPT-llm-based-annotation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0608 — `concept_pair:CPT-irac-analysis|CPT-llm-based-annotation` — No claim links CPT-irac-analysis to CPT-llm-based-annotation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0626 — `concept_pair:CPT-legal-drafting|CPT-llm-based-annotation` — No claim links CPT-legal-drafting to CPT-llm-based-annotation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0643 — `concept_pair:CPT-legal-education|CPT-llm-based-annotation` — No claim links CPT-legal-education to CPT-llm-based-annotation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0662 — `concept_pair:CPT-review-and-due-diligence|CPT-llm-based-annotation` — No claim links CPT-review-and-due-diligence to CPT-llm-based-annotation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0680 — `concept_pair:CPT-rulemaking|CPT-llm-based-annotation` — No claim links CPT-rulemaking to CPT-llm-based-annotation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Is LLM annotation's instability a general property or an artifact of particular models and settings?
