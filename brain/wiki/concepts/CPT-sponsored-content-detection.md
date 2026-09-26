---
id: CPT-sponsored-content-detection
status: candidate
concept_type: technical_task
definition: The automatic identification of sponsored or advertising content on social media — including undisclosed or hidden advertising — and its separation from organic content, as a classification task supporting the enforcement of disclosure rules.
run_ids: [RUN-2026-09-25-01]
---

# CPT-sponsored-content-detection

## What it means

The automatic identification of sponsored or advertising content on social media — including undisclosed or hidden advertising — and its separation from organic content, as a classification task supporting the enforcement of disclosure rules. A candidate concept coined during the ingest of SRC-0023 and drawn from its claims [CLM-0023-001] [CLM-0023-003] [CLM-0023-004] [CLM-0023-008] [CLM-0023-009] [CLM-0023-010].

## Claims

### Descriptive

**NL**

- In classifying 1,143 English-language Instagram posts as sponsored or organic content, gpt-5-nano and gemini-2.5-flash-lite perform strongly (F1 up to 0.93), but on the 95 ambiguous posts where human annotators disagreed or expressed uncertainty, overall performance drops significantly, with F1 scores falling by over 10 percentage points compared to the full dataset. — rests on factual basis (SRC-0023). [CLM-0023-004]
- Undisclosed (hidden) advertisements exhibit the highest rate of mistaken potential cues in LLM explanations (28.57%) and notable unclear-citation errors, with hallucinations appearing more often than in other content categories; these patterns reflect the difficulty of detecting subtle promotions, where models must infer intent from indirect cues and often misidentify which signals indicate sponsorship. — rests on factual basis (SRC-0023). [CLM-0023-008]
- In detecting advertising on social media, model choice strongly influences both classification strength and error profile: gemini-2.5-flash-lite is more effective for recall-oriented tasks such as detecting hidden ads, whereas gpt-5-nano excels in precision, and its precision-oriented strengths do not extend to detecting subtle or undisclosed advertising cues. — rests on factual basis (SRC-0023). [CLM-0023-009]
- Large language models are not always superior to simple baselines such as TF-IDF logistic regression in overall classification of sponsored content, but they perform better in challenging cases: on ambiguous posts the baseline's decline exceeds a 30-point reduction in F1. — rests on factual basis (SRC-0023). [CLM-0023-010]

**general**

- Current computational methods for detecting undisclosed sponsored content on social media generally lack legal grounding or operate as opaque black boxes: they often lack a solid legal foundation, exposing regulators to pushback in relation to their decisions, and they prioritise accuracy over explanation, producing accurate predictions without interpretable reasoning. — rests on literature (SRC-0023). [CLM-0023-001]
- Prior research on evaluating LLM outputs has not extended explanation-evaluation frameworks to complex, domain-specific contexts such as legal interpretation in detecting undisclosed advertisements on social media, which is a key gap in compliance detection; a taxonomy of common errors in LLM-generated legal reasoning for this task is a novel addition to regulatory compliance technology. — rests on literature (SRC-0023). [CLM-0023-003]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0023 | unknown | 6 | 6 descriptive | 2 literature, 4 factual | NL, general |

## Open questions

- None recorded at this close-out.
