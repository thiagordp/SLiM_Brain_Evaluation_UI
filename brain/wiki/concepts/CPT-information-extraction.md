---
id: CPT-information-extraction
status: anchor
concept_type: technical_task
definition: The technical task of pulling structured elements — entities, statements, factors, roles — out of unstructured legal text.
run_ids: [RUN-2026-09-25-01]
---

# CPT-information-extraction

## What it means

The technical task of pulling structured elements — entities, statements, factors, roles — out of unstructured legal text. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0009-001] [CLM-0009-008] [CLM-0009-010].

## Claims

### Descriptive

**DE**

- In zero-shot extraction of normative sentences related to § 6 StVO from German court decisions with GPT-4o, Chain-of-Instructions prompting achieved superior Recall and F2 scores compared to Standard, Chain-of-Thought and Layer-of-Thoughts prompting, extracting 108 of 125 gold normative sentences against 99, 102 and 103 respectively. — rests on factual basis (SRC-0017). [CLM-0017-006]
- The complexity and nuance of legal language in court rulings makes it challenging for GPT-4o to consistently identify and extract the most relevant normative statements: the model occasionally extracts normative statements beyond the intended scope or includes irrelevant details, and even well-designed standard prompts have not consistently enabled it to interpret the content accurately. — rests on factual basis (SRC-0017). [CLM-0017-007]
- Even with moderate precision, automated top-10 extraction of candidate normative sentences that reduces the review workload from 6,242 sentences to 560 would significantly streamline the manual review of court decisions. — rests on factual basis (SRC-0017). [CLM-0017-010]

**EU**

- Manually extracting Judicial Interpretative Formulas (JIFs) from decisions of the Court of Justice of the European Union on Value Added Tax is effortful, automatic extraction had not previously been investigated in the VAT domain, and a pipeline method for automated JIF extraction in this domain is the first of its kind. — rests on literature (SRC-0009). [CLM-0009-001]
- BERT-based architectures fine-tuned on LLM-annotated training data perform comparably to LLMs in classifying paragraphs of CJEU VAT decisions as containing Judicial Interpretative Formulas: the highest macro F1 score of 0.76 was achieved by both DistilRoBERTa and LEGAL-BERT, with all other models closely behind at a minimum of 0.72, comparable to or even better than DeepSeek. — rests on factual basis (SRC-0009). [CLM-0009-008]

**US**

- Zero-shot prompting of a GPT-4 model to identify the span of paragraphs containing a court opinion's analysis and conclusion on the issue of reasonable suspicion is a reliable process, achieving high recall of the factor sets identified by an expert annotator. — rests on factual basis (SRC-0018). [CLM-0018-004]

**general**

- Existing automated privacy policy analysis tools rely on fixed categorization schemes that fail when policies mention novel concepts, and attempting to dynamically expand taxonomies risks creating overlapping categories that break the logical consistency needed for formal reasoning. — rests on literature (SRC-0013). [CLM-0013-005]
- Grammar-based parsers fail when semantically equivalent privacy policy phrases differ in syntax, and neural parsers would force vague terms into predefined categories; large language models, by contrast, can interpret varied expressions of the same concept and extract semantic roles while preserving vague terms for human interpretation. — rests on abstract considerations (SRC-0013). [CLM-0013-008]
- Full 'transmission principles' in the sense of Contextual Integrity - the complex social norms governing when data sharing is appropriate - are not extracted automatically from privacy policies because they require human judgment about social context and significant human interpretation. — rests on literature (SRC-0013). [CLM-0013-010]
- Manual review of court decisions by legal experts to identify and extract normative statements related to specific traffic rules ensures high accuracy but is highly time-consuming and labor-intensive, and as the number of court decisions grows there is an urgent need for more efficient methods of extracting the implicit rules they contain. — rests on literature (SRC-0017). [CLM-0017-002]
- LLM-based extraction of implicit traffic rules from court decisions constitutes a scalable and efficient framework that can be integrated into autonomous vehicle development pipelines, enabling continuous updates to the implicit rule corpus as new judicial decisions are issued. — rests on abstract considerations (SRC-0017). [CLM-0017-012]

**undetermined**

- An LLM-based extraction pipeline processed the privacy policies of TikTok (approximately 15,000 words) and Meta (over 40,000 words), extracting 974 and 3,801 distinct data practice edges respectively, demonstrating scalability from shorter to more comprehensive privacy documents and revealing complexities such as multi-actor data flows and individually trackable data types expanded from enumerated lists. — rests on factual basis (SRC-0013). [CLM-0013-011]

### Interpretative

**EU**

- In classifying CJEU decision paragraphs as containing Judicial Interpretative Formulas, a LinearSVC with TF-IDF features performs not much inferior to state-of-the-art Transformer models, suggesting that lexical cues play a crucial role in the task. — rests on factual basis (SRC-0009). [CLM-0009-010]
- LEGAL-BERT may be considered the best model for Judicial Interpretative Formula extraction: it is the most stable and has the best macro F1 score and the best F1 score on the positive class, and its near-best recall on the positive class is particularly relevant for tools intended for legal practitioners, since the presence of additional JIFs is preferable to the absence of fundamental ones — users can easily discard a few irrelevant paragraphs, but cannot know if a crucial JIF is missing. — rests on factual basis (SRC-0009). [CLM-0009-011]

### Prescriptive

**general**

- For evaluating the extraction of normative sentences from court decisions, the F2 measure is preferred because it effectively identifies more relevant sentences, which is crucial for reducing the risk of overlooking any important normative statements. — rests on abstract considerations (SRC-0017). [CLM-0017-013]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0017 holds “In zero-shot extraction of normative sentences related to § 6 StVO from German court decisions with GPT-4o, Chain-of-Instructions prompting …” [CLM-0017-006]; SRC-0004 holds “When a long-context-window large language model retrieves provisions of the Korean Building Act and its subordinate regulations for legal …” [CLM-0004-004]. Note: The finding that detailed step-by-step Chain-of-Instructions prompts outperformed less structured prompts in zero-shot legal extraction gives reasons against the finding that less prompt guidance leads to higher accuracy in LLM-based legal provision retrieval.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0009 | 2025 | 4 | 2 descriptive, 2 interpretative | 1 literature, 3 factual | EU |
| SRC-0013 | 2025 | 4 | 4 descriptive | 2 literature, 1 abstract, 1 factual | general, undetermined |
| SRC-0017 | 2024 | 6 | 5 descriptive, 1 prescriptive | 1 literature, 3 factual, 2 abstract | DE, general |
| SRC-0018 | 2024 | 1 | 1 descriptive | 1 factual | US |

## Open questions

- Does less prompt guidance help or hurt legal extraction — and does the answer depend on the task?
