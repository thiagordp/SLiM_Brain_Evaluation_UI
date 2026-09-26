---
id: CPT-machine-learning
status: anchor
concept_type: technique_class
definition: Statistical learning techniques generally, where a claim's point is not specific to deep or generative models.
run_ids: [RUN-2026-09-25-01]
---

# CPT-machine-learning

## What it means

Statistical learning techniques generally, where a claim's point is not specific to deep or generative models. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0009-004] [CLM-0009-010] [CLM-0022-003].

## Claims

### Descriptive

**NL**

- Large language models are not always superior to simple baselines such as TF-IDF logistic regression in overall classification of sponsored content, but they perform better in challenging cases: on ambiguous posts the baseline's decline exceeds a 30-point reduction in F1. — rests on factual basis (SRC-0023). [CLM-0023-010]

**general**

- Approaches to automated extraction of legal principles face two main drawbacks: data-driven methods require costly annotation, while LLM-based methods often lack stability, transparency, and reproducibility, which are essential in the legal domain. — rests on literature (SRC-0009). [CLM-0009-004]
- Current computational methods for detecting undisclosed sponsored content on social media generally lack legal grounding or operate as opaque black boxes: they often lack a solid legal foundation, exposing regulators to pushback in relation to their decisions, and they prioritise accuracy over explanation, producing accurate predictions without interpretable reasoning. — rests on literature (SRC-0023). [CLM-0023-001]

### Interpretative

**EU**

- In classifying CJEU decision paragraphs as containing Judicial Interpretative Formulas, a LinearSVC with TF-IDF features performs not much inferior to state-of-the-art Transformer models, suggesting that lexical cues play a crucial role in the task. — rests on factual basis (SRC-0009). [CLM-0009-010]

**general**

- The gap between legal interpretation and formal validity is largely invisible in legal AI research, because most systems either mimic legal interpretation through language model training or enforce formal validity through symbolic methods without acknowledging that the two regularly diverge; making this gap explicit, measurable and addressable is one of the most important open problems in legal AI. — rests on abstract considerations (SRC-0022). [CLM-0022-003]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0008 holds “Automatic annotation of court decisions by a large language model is highly reproducible: across five iterations on the same pool of texts …” [CLM-0008-010]; SRC-0009 holds “Approaches to automated extraction of legal principles face two main drawbacks: data-driven methods require costly annotation, while …” [CLM-0009-004]. Note: Evidence that automatic LLM annotation of court decisions is highly reproducible across repeated runs with identical parameters (average Cohen's Kappa 0.82) gives a reason against the drawback that LLM-based methods lack reproducibility.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0009 | 2025 | 2 | 1 descriptive, 1 interpretative | 1 literature, 1 factual | EU, general |
| SRC-0022 | unknown | 1 | 1 interpretative | 1 abstract | general |
| SRC-0023 | unknown | 2 | 2 descriptive | 1 literature, 1 factual | NL, general |

## What is missing

Absence records whose key names this concept (9, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0550 — `concept_pair:CPT-compliance-and-monitoring|CPT-machine-learning` — No claim links CPT-compliance-and-monitoring to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0563 — `concept_pair:CPT-dataset-license-compliance|CPT-machine-learning` — No claim links CPT-dataset-license-compliance to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0579 — `concept_pair:CPT-decision-support|CPT-machine-learning` — No claim links CPT-decision-support to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0594 — `concept_pair:CPT-fatwa-issuance|CPT-machine-learning` — No claim links CPT-fatwa-issuance to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0609 — `concept_pair:CPT-irac-analysis|CPT-machine-learning` — No claim links CPT-irac-analysis to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0627 — `concept_pair:CPT-legal-drafting|CPT-machine-learning` — No claim links CPT-legal-drafting to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0644 — `concept_pair:CPT-legal-education|CPT-machine-learning` — No claim links CPT-legal-education to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0663 — `concept_pair:CPT-review-and-due-diligence|CPT-machine-learning` — No claim links CPT-review-and-due-diligence to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0681 — `concept_pair:CPT-rulemaking|CPT-machine-learning` — No claim links CPT-rulemaking to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Is LLM annotation's instability a general property or an artifact of particular models and settings?
