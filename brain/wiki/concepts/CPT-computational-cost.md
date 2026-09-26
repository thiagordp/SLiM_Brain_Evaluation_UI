---
id: CPT-computational-cost
status: emergent
concept_type: normative_concern
definition: The computational resources — execution time, token usage and associated cost — consumed by an analysis method, and the trade-off between that consumption and task performance.
run_ids: [RUN-2026-09-25-01]
---

# CPT-computational-cost

## What it means

The computational resources — execution time, token usage and associated cost — consumed by an analysis method, and the trade-off between that consumption and task performance. An emergent concept coined during the ingest of SRC-0004 and drawn from its claims [CLM-0004-007] [CLM-0004-010]. Promoted from candidate to emergent at this close-out: claims from 5 sources with no shared author are mapped to it (SRC-0001, SRC-0004, SRC-0007, SRC-0013, SRC-0017).

## Claims

### Descriptive

**KR**

- Using a high-level community summary significantly increases the execution time of long-context-window large language model provision search - by a factor of 1.24 for exhaustive search - even though token usage is only 1.02 times higher; this may be attributed to the model repeatedly referencing the entire summary for each hop. — rests on factual basis (SRC-0004). [CLM-0004-007]

**general**

- Chain-of-thought prompting approaches for guiding large language models through multi-step reasoning are not immune to lack of interpretability and to generating inconsistent reasoning, and can be computationally expensive when applied at scale. — rests on abstract considerations (SRC-0007). [CLM-0007-003]
- In contrast to prior approaches to generating structured rules from policy documents with large language models, which rely on human-designed schemas and helper functions and thereby constrain reasoning to facts explicitly represented in the input, dynamic rule generation from natural language — leveraging finetuned models and symbolic reasoning to automatically extract governing policy language and generate rules — eliminates the need for human-curated schemas and helper functions, with the intent to offer a scalable and cost-effective solution that reduces manual effort and reliance on frequent LLM inference. — rests on literature (SRC-0007). [CLM-0007-012]
- State-of-the-art multi-step prompting techniques such as Chain-of-Thought, Tree of Thoughts and Graph of Thoughts are still largely restricted to relatively simple tasks such as simple math and reasoning problems, often come with high inference costs, and are challenging to design, develop, maintain and scale. — rests on literature (SRC-0017). [CLM-0017-004]

**undetermined**

- A hybrid system that pairs a coverage-aware retriever with symbolic rule-based reasoning to surface relevant medical coverage policy language, organize it into explicit facts and rules, and generate auditable rationales minimizes the number of LLM inferences required, achieving a 44% reduction in inference cost alongside a 4.5% improvement in F1 score. — rests on factual basis (SRC-0007). [CLM-0007-002]
- For large-scale coverage adjudication, a symbolic rule-based system that performs attribute generation once per procedure code and rule generation once per coverage policy, and needs no GPU or LLM inference at run time, is dramatically cheaper than LLM-based inference: processing 11,000 CPT codes costs approximately $22, against $4,840 for GPT-5-mini and $9,680 for GPT-4.1 or o3, and the approach remains highly cost-effective even counting a one-time training cost of approximately $2,680. — rests on factual basis (SRC-0007). [CLM-0007-007]
- LLM-based methods given retrieved policy text achieve slightly higher accuracy and F1 scores (up to 0.94 accuracy and 0.96 F1) than symbolic rule-based approaches (up to 0.87 accuracy and 0.93 F1) in coverage assessment, but their inference costs scale rapidly with dataset size, making the rule-based approach far more cost-effective for large-scale adjudication tasks; choosing between them involves balancing optimal performance against operational cost. — rests on factual basis (SRC-0007). [CLM-0007-008]
- Providing a large language model with only the retrieved relevant policy passages instead of the entire coverage document significantly reduces the number of input tokens required for each inference and thereby the overall cost, while models that process entire documents are both less accurate (0.82 accuracy, 0.89 F1) and dramatically more expensive ($38,720 for 11,000 CPT codes). — rests on factual basis (SRC-0007). [CLM-0007-009]
- Embedding-based semantic search reduces each verification query over a privacy policy's extracted data practice edges to a small relevant subset - on average 6.4 edges for the TikTok policy and 18.5 for the Meta policy, a 99.38% and 99.50% reduction in the verification problem - enabling tractable formal reasoning by an SMT solver: 23 queries of varying complexity achieved zero timeouts with average query times of 3.39s and 3.91s, and although the Meta policy is 3.9 times larger than the TikTok policy, query times increased by only 1.15 times, demonstrating sub-linear scaling behavior. — rests on factual basis (SRC-0013). [CLM-0013-012]
- The first-order logic formulas produced from full privacy policies remain too complex for SMT solvers: without a semantic search phase reducing the search space, a query would require the SMT solver to reason about thousands of disjunctive clauses, which leads to exponential complexity. — rests on factual basis (SRC-0013). [CLM-0013-013]

### Interpretative

**general**

- Carefully designed prompts can serve as the primary mechanism for guiding legal reasoning in LLM-based systems, offering a scalable, explainable, and cost-effective solution for continuous compliance assessment under evolving regulations such as the GDPR. — rests on factual basis (SRC-0001). [CLM-0001-013]

### Predictive

**KR**

- Because a long-context-window large language model typically requires fewer than three hops to locate relevant legal provisions, predefining the top three related provisions could help reduce token costs while maintaining high accuracy in legal interpretation tasks. — rests on factual basis (SRC-0004). [CLM-0004-010]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0007 holds “The traceability of a symbolic rule-based coverage system — showing which rule fired and which attribute conditions matched — allows a …” [CLM-0007-011]; SRC-0001 holds “Carefully designed prompts can serve as the primary mechanism for guiding legal reasoning in LLM-based systems, offering a scalable, …” [CLM-0001-013]. Note: The contention that direct prompting offers no comparable traceability and is more prone to hallucinations gives reasons against treating carefully designed prompts as a scalable, explainable primary mechanism for guiding legal reasoning in LLM-based systems.
- SRC-0007 holds “LLM-based methods given retrieved policy text achieve slightly higher accuracy and F1 scores (up to 0.94 accuracy and 0.96 F1) than …” [CLM-0007-008]; SRC-0001 holds “Prompt engineering functions as a form of 'soft programming' that can replace complex feature extraction pipelines or rigid rule-based …” [CLM-0001-009]. Note: Evidence that LLM inference costs scale rapidly while a rule-based system delivers competitive performance far more cheaply gives reasons against the contention that prompt engineering can replace rule-based frameworks in LLM-driven compliance systems.
- SRC-0007 holds “For large-scale coverage adjudication, a symbolic rule-based system that performs attribute generation once per procedure code and rule …” [CLM-0007-007]; SRC-0001 holds “Carefully designed prompts can serve as the primary mechanism for guiding legal reasoning in LLM-based systems, offering a scalable, …” [CLM-0001-013]. Note: That a symbolic rule-based coverage system needing no LLM inference at run time is dramatically cheaper at scale ($22 against $4,840-$9,680 for 11,000 codes) gives reasons against carefully designed prompts being a cost-effective solution for continuous compliance assessment.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0001 | unknown | 1 | 1 interpretative | 1 factual | general |
| SRC-0004 | unknown | 2 | 1 descriptive, 1 predictive | 2 factual | KR |
| SRC-0007 | 2026 | 6 | 6 descriptive | 4 factual, 1 abstract, 1 literature | general, undetermined |
| SRC-0013 | 2025 | 2 | 2 descriptive | 2 factual | undetermined |
| SRC-0017 | 2024 | 1 | 1 descriptive | 1 literature | general |

## What is missing

Absence records whose key names this concept (13, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0082 — `concept_jurisdiction:CPT-computational-cost|AU` — No claim about CPT-computational-cost concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0083 — `concept_jurisdiction:CPT-computational-cost|BR` — No claim about CPT-computational-cost concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0084 — `concept_jurisdiction:CPT-computational-cost|CA` — No claim about CPT-computational-cost concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0085 — `concept_jurisdiction:CPT-computational-cost|CN` — No claim about CPT-computational-cost concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0086 — `concept_jurisdiction:CPT-computational-cost|DE` — No claim about CPT-computational-cost concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0087 — `concept_jurisdiction:CPT-computational-cost|EU` — No claim about CPT-computational-cost concerns EU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0088 — `concept_jurisdiction:CPT-computational-cost|GB` — No claim about CPT-computational-cost concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0089 — `concept_jurisdiction:CPT-computational-cost|MY` — No claim about CPT-computational-cost concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0090 — `concept_jurisdiction:CPT-computational-cost|NL` — No claim about CPT-computational-cost concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0091 — `concept_jurisdiction:CPT-computational-cost|NZ` — No claim about CPT-computational-cost concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0092 — `concept_jurisdiction:CPT-computational-cost|RU` — No claim about CPT-computational-cost concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0093 — `concept_jurisdiction:CPT-computational-cost|TR` — No claim about CPT-computational-cost concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0094 — `concept_jurisdiction:CPT-computational-cost|US` — No claim about CPT-computational-cost concerns US. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Can prompt-driven LLM pipelines reach the traceability that symbolic rules offer a human reviewer?
- At what scale do LLM inference costs outweigh the flexibility that prompt-centred designs buy?
- Is prompt-driven LLM inference cost-effective for continuous compliance at adjudication scale?
