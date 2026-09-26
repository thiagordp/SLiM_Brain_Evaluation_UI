---
id: CPT-training-data-selection
status: emergent
concept_type: technical_task
definition: Selecting and structuring the domain-specific data used to train or fine-tune a legal AI system, or to populate its retrieval database — including deciding which legal materials belong in the corpus.
run_ids: [RUN-2026-09-25-01]
---

# CPT-training-data-selection

## What it means

Selecting and structuring the domain-specific data used to train or fine-tune a legal AI system, or to populate its retrieval database — including deciding which legal materials belong in the corpus. An emergent concept coined during the ingest of SRC-0005 and drawn from its claims [CLM-0005-006] [CLM-0005-007] [CLM-0005-008]. Promoted from candidate to emergent at this close-out: claims from 3 sources with no shared author are mapped to it (SRC-0003, SRC-0005, SRC-0009).

## Claims

### Descriptive

**EU**

- A novel corpus for Judicial Interpretative Formula extraction consists of 101 CJEU preliminary rulings on VAT — on the subtopics of taxable amounts and exemptions for the public interest, retrieved through a concept-based EUR-Lex search in December 2024 — structured into three document-level splits that separate manually annotated data for evaluation and development (21 expert-labelled decisions) from automatically annotated data for training (80 LLM-labelled decisions), with the test split containing only documents never used during guideline development. — rests on factual basis (SRC-0009). [CLM-0009-014]

**general**

- Most Arabic large language models are trained mainly on Modern Standard Arabic drawn from news articles, Wikipedia, web forums and other edited text, while Classical Arabic and many spoken dialects appear much less often in large datasets; benchmark scores fall when models are tested on dialectal or pre-modern Arabic. — rests on literature (SRC-0003). [CLM-0003-009]
- Determining the dataset used to fine-tune an international-law large language model — and the content of a retrieval-augmented generation database — requires taking decisions on contested questions about the sources of international law, including which customs should be used, whether and which international and national case-law is relevant, and whether soft law resources should be included; for the model to provide reliable outputs, the dataset must reflect a coherent and representative understanding of these sources. — rests on abstract considerations (SRC-0005). [CLM-0005-006]

### Interpretative

**general**

- Two parameters are important for navigating the design decision about the content of the dataset used to fine-tune an international-law large language model: the perspective of the user and the question of representativity, as key features of what constitutes 'good' international law. — rests on abstract considerations (SRC-0005). [CLM-0005-007]
- The choice of fine-tuning data and retrieval-augmented generation database for an international-law large language model can be represented on a continuum between a narrow, restrictive approach based on a strict reading of the sources of Article 38(1) ICJ Statute — which offers clarity, coherence and predictability but risks perpetuating existing structural features of international law and excluding voices that challenge the status quo — and a broad, inclusive approach incorporating diverse perspectives — which enhances representativity but may lack the formal authority and consistency required for real-world application. — rests on abstract considerations (SRC-0005). [CLM-0005-008]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0003 | 2026 | 1 | 1 descriptive | 1 literature | general |
| SRC-0005 | 2026 | 3 | 1 descriptive, 2 interpretative | 3 abstract | general |
| SRC-0009 | 2025 | 1 | 1 descriptive | 1 factual | EU |

## Open questions

- None recorded at this close-out.
