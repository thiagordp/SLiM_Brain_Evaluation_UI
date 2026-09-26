---
id: CPT-discourse-annotation
status: candidate
concept_type: technical_task
definition: Segmenting a text into discourse units and labelling the functions or relations that connect them — manually or automatically — under a discourse annotation scheme such as RST-derived markup, in order to make the text's discursive structure explicit.
run_ids: [RUN-2026-09-25-01]
---

# CPT-discourse-annotation

## What it means

Segmenting a text into discourse units and labelling the functions or relations that connect them — manually or automatically — under a discourse annotation scheme such as RST-derived markup, in order to make the text's discursive structure explicit. A candidate concept coined during the ingest of SRC-0008 and drawn from its claims [CLM-0008-001] [CLM-0008-007] [CLM-0008-008] [CLM-0008-009] [CLM-0008-010].

## Claims

### Descriptive

**RU**

- Legal Markup for Reasoning (LMR) is an XML-based discourse annotation scheme with a minimal set of attributes that captures the argumentative structure of legal reasoning in tax court decisions; inspired by Rhetorical Structure Theory but substantially modified, it replaces the full RST hierarchy with a minimal set of function tags tailored to legal reasoning, alongside segmentation into text units, participant roles and procedural stages. — rests on abstract considerations (SRC-0008). [CLM-0008-001]
- In discourse markup of legal texts, dividing semantic sections into elementary discourse units is ineffective, as it complicates the markup process and makes it more cluttered; identifying larger fragments of text that perform a single function and role — up to entire sentences serving a unified purpose — significantly improves the process and prevents duplication of functions and roles. — rests on factual basis (SRC-0008). [CLM-0008-007]
- When automatic annotation of Russian court decisions by a large language model (ChatGPT-4.1 with few-shot prompting) is compared with expert annotation, agreement is highest for procedural stages (97.31%), which are marked by clear formal indicators, and moderate for roles (65.59%) and discourse functions (53.76%). — rests on factual basis (SRC-0008). [CLM-0008-008]
- Annotating discourse functions in legal texts is a difficult task even for experts, because legal texts allow for multiple interpretations: agreement between two independent human annotators on discourse functions was only 40.65%, lower than the AI-human agreement rate of 53.76%. — rests on factual basis (SRC-0008). [CLM-0008-009]
- Automatic annotation of court decisions by a large language model is highly reproducible: across five iterations on the same pool of texts with identical parameters, average Cohen's Kappa was 0.82 — an almost perfect level of agreement — with average exact match 0.84, unigram Jaccard 0.92 and edit similarity 0.89, and the remaining differences are local in nature. — rests on factual basis (SRC-0008). [CLM-0008-010]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0008 holds “Automatic annotation of court decisions by a large language model is highly reproducible: across five iterations on the same pool of texts …” [CLM-0008-010]; SRC-0009 holds “Approaches to automated extraction of legal principles face two main drawbacks: data-driven methods require costly annotation, while …” [CLM-0009-004]. Note: Evidence that automatic LLM annotation of court decisions is highly reproducible across repeated runs with identical parameters (average Cohen's Kappa 0.82) gives a reason against the drawback that LLM-based methods lack reproducibility.
- SRC-0009 holds “Annotation guidelines for Judicial Interpretative Formulas in CJEU VAT decisions, refined over successive annotation stages, yield almost …” [CLM-0009-006]; SRC-0008 holds “Annotating discourse functions in legal texts is a difficult task even for experts, because legal texts allow for multiple interpretations: …” [CLM-0008-009]. Note: Almost perfect inter-annotator agreement (Cohen's kappa 0.96) reached with iteratively refined annotation guidelines gives reasons against the contention that expert agreement on annotating legal texts is inherently low because legal texts allow multiple interpretations.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0008 | 2026 | 5 | 5 descriptive | 1 abstract, 4 factual | RU |

## Open questions

- Is LLM annotation's instability a general property or an artifact of particular models and settings?
- Is low expert agreement on legal annotation inherent to legal text, or a symptom of unrefined guidelines?
