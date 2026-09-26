---
id: CPT-annotation-guidelines
status: candidate
concept_type: technical_task
definition: Drafting, iteratively refining and validating written instructions that define what annotators should label in a text, serving both human annotators and automated annotation methods, with agreement measures used to validate them.
run_ids: [RUN-2026-09-25-01]
---

# CPT-annotation-guidelines

## What it means

Drafting, iteratively refining and validating written instructions that define what annotators should label in a text, serving both human annotators and automated annotation methods, with agreement measures used to validate them. A candidate concept coined during the ingest of SRC-0009 and drawn from its claims [CLM-0009-005] [CLM-0009-006] [CLM-0009-014].

## Claims

### Descriptive

**EU**

- Annotation guidelines for Judicial Interpretative Formulas in CJEU VAT decisions, refined over successive annotation stages, yield almost perfect inter-annotator agreement: Cohen's kappa, measured on an independently annotated document set at paragraph level and restricted to the relevant portions of the judgments, was 0.96. — rests on factual basis (SRC-0009). [CLM-0009-006]
- A novel corpus for Judicial Interpretative Formula extraction consists of 101 CJEU preliminary rulings on VAT — on the subtopics of taxable amounts and exemptions for the public interest, retrieved through a concept-based EUR-Lex search in December 2024 — structured into three document-level splits that separate manually annotated data for evaluation and development (21 expert-labelled decisions) from automatically annotated data for training (80 LLM-labelled decisions), with the test split containing only documents never used during guideline development. — rests on factual basis (SRC-0009). [CLM-0009-014]

**MY+AU**

- In human evaluation of ChatGPT's IRAC analyses by law students, the questions evaluating the generated assumptions are subjective — a common problem in law education: the Cohen's Kappa inter-annotator agreement score over all evaluation measures was 0.55, rising to 0.75 when the assumption evaluation was excluded. — rests on factual basis (SRC-0015). [CLM-0015-009]

### Interpretative

**EU**

- For annotation purposes a Judicial Interpretative Formula may be defined as an interpretative statement by the Court, either formulated for the first time or drawn from cited case law; the paragraphs identified as JIFs are those containing interpretation of a rule or general principle, consequences stemming from its interpretation or application, subsumption of a fact within a rule, or qualification of a fact as a concept contained within a rule, and the annotation unit is one paragraph, reflecting the typical structure of CJEU judgments, organised in numbered paragraphs each expressing an autonomous step of reasoning. — rests on abstract considerations (SRC-0009). [CLM-0009-005]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0009 holds “Annotation guidelines for Judicial Interpretative Formulas in CJEU VAT decisions, refined over successive annotation stages, yield almost …” [CLM-0009-006]; SRC-0008 holds “Annotating discourse functions in legal texts is a difficult task even for experts, because legal texts allow for multiple interpretations: …” [CLM-0008-009]. Note: Almost perfect inter-annotator agreement (Cohen's kappa 0.96) reached with iteratively refined annotation guidelines gives reasons against the contention that expert agreement on annotating legal texts is inherently low because legal texts allow multiple interpretations.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0009 | 2025 | 3 | 1 interpretative, 2 descriptive | 1 abstract, 2 factual | EU |
| SRC-0015 | unknown | 1 | 1 descriptive | 1 factual | MY+AU |

## Open questions

- Is low expert agreement on legal annotation inherent to legal text, or a symptom of unrefined guidelines?
