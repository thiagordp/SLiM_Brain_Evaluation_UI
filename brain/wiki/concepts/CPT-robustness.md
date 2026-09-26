---
id: CPT-robustness
status: emergent
concept_type: normative_concern
definition: How well a language model performs on edge cases — ambiguous, misleading or exceptional inputs, such as questions about exceptional cases in the law — as a distinct dimension of trustworthiness.
run_ids: [RUN-2026-09-25-01]
---

# CPT-robustness

## What it means

How well a language model performs on edge cases — ambiguous, misleading or exceptional inputs, such as questions about exceptional cases in the law — as a distinct dimension of trustworthiness. An emergent concept coined during the ingest of SRC-0002 and drawn from its claims [CLM-0002-008]. Promoted from candidate to emergent at this close-out: claims from 9 sources with no shared author are mapped to it (SRC-0002, SRC-0004, SRC-0008, SRC-0011, SRC-0012, SRC-0014, SRC-0017, SRC-0021, SRC-0024).

## Claims

### Descriptive

**CN**

- A model trained with the SyLeR framework on legal questions from one user group (legal laypersons or legal practitioners) achieves optimal performance when tested on the other group, demonstrating strong cross-domain generalization and indicating that the methodology is not domain-specific. — rests on factual basis (SRC-0011). [CLM-0011-014]
- The SyLeR framework achieves optimal performance across different large language model backbones, including Llama3-8B-Instruct as well as Qwen2-7B-Instruct, showing that it is not limited to a specific model architecture. — rests on factual basis (SRC-0011). [CLM-0011-016]

**DE**

- Asking GPT-4o to dynamically generate a Chain-of-Instructions prompt from a task description yields inconsistent results — a different prompt structure each time — and lower extraction performance, with the GPT-generated prompts extracting at most 75 of 125 correct normative sentences over three attempts. — rests on factual basis (SRC-0017). [CLM-0017-008]

**EU**

- When answering questions that represent exceptional cases in the law, large language models do not align well on providing the correct response, which emphasizes the need to assess specific aspects of trustworthiness such as robustness — how well a model responds to questions regarding exceptional cases — in tasks like law interpretation. — rests on factual basis (SRC-0002). [CLM-0002-008]

**KR**

- Incorporating a high-level community summary consisting of legal provision titles improves the robustness of long-context-window large language model provision retrieval to prompt variations, narrowing the accuracy gap between prompt variants from 5.27 to 1.17 percentage points, but it does not yield the highest performance: its primary effect is to ensure consistency in search results rather than directly enhancing accuracy. — rests on factual basis (SRC-0004). [CLM-0004-005]

**RU**

- Automatic annotation of court decisions by a large language model is highly reproducible: across five iterations on the same pool of texts with identical parameters, average Cohen's Kappa was 0.82 — an almost perfect level of agreement — with average exact match 0.84, unigram Jaccard 0.92 and edit similarity 0.89, and the remaining differences are local in nature. — rests on factual basis (SRC-0008). [CLM-0008-010]

**US**

- Under case and rule perturbations of statutory tax reasoning problems, direct question-answering performance of large language models drops sharply, whereas Prolog-based performance remains relatively stable, suggesting that externalizing reasoning to a Prolog solver largely eliminates the generalization gap. — rests on factual basis (SRC-0021). [CLM-0021-006]
- Monolithic large language models are relatively robust to linguistic variation in legal case descriptions: paraphrasing tax cases while preserving semantics produces no significant performance drop, and on such simpler conceptual entailment they can outperform Prolog-based approaches. — rests on factual basis (SRC-0021). [CLM-0021-007]
- A synthetic test suite for statutory tax reasoning can be constructed from SARA by conservatively perturbing numerical values in rules and cases and paraphrasing case texts, minimizing data contamination while preserving legal and structural complexity, and — by applying identical perturbations to textual rules and Prolog programs — yielding precise formal representations and exact solutions without human expert effort. — rests on factual basis (SRC-0021). [CLM-0021-010]

**general**

- Large language models may be sensitive to input perturbation, so that legal consultation responses can be contradictory when inputs differ only slightly, or even when an identical question is asked in a new conversation; this inconsistency can potentially confuse users and result in a lower-quality consultation. — rests on literature (SRC-0014). [CLM-0014-002]
- Large language models often produce inconsistent and seemingly random responses to prompts — across different models, across repetitions of the same prompt, and across different wordings of the same question; unless the temperature variable is set at the lowest level this inconsistency is a design feature rather than a bug, and the models are very sensitive to the wording of prompts. — rests on literature (SRC-0024). [CLM-0024-006]

**undetermined**

- The SyLeR framework achieves the best performance among compared methods on the French-language legal question-answering dataset LLeQA even when its tree-based retrieval module is omitted and replaced with BM25 retrieval of the most relevant legal statute, demonstrating cross-lingual generalization and effectiveness with simpler retrieval strategies. — rests on factual basis (SRC-0011). [CLM-0011-015]
- Carefully crafted, task-specific custom prompts significantly improve a fine-tuned foundation model's performance in dataset license compliance analysis, and the model is highly sensitive to variations in prompt design: Prediction Agreement varied from only 4.8% with one system prompt to 64.3% with a custom-designed system prompt under the same user prompt. — rests on factual basis (SRC-0012). [CLM-0012-011]

### Prescriptive

**general**

- Legal reasoning is an inherently compositional and complex task, and hybrid neuro-symbolic systems that combine large language model capabilities in parsing and formal translation with symbolic reasoning engines offer a more reliable and robust foundation for legal AI, improving generalization, interpretability, and verifiability. — rests on factual basis (SRC-0021). [CLM-0021-008]

### Predictive

**general**

- Findings that minimal prompt guidance improves long-context-window large language model performance in legal provision retrieval, obtained without fine-tuning or retrieval-augmented generation using dataset-specific information, may extend to other legal systems or domains. — rests on abstract considerations (SRC-0004). [CLM-0004-009]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0008 holds “Automatic annotation of court decisions by a large language model is highly reproducible: across five iterations on the same pool of texts …” [CLM-0008-010]; SRC-0009 holds “Approaches to automated extraction of legal principles face two main drawbacks: data-driven methods require costly annotation, while …” [CLM-0009-004]. Note: Evidence that automatic LLM annotation of court decisions is highly reproducible across repeated runs with identical parameters (average Cohen's Kappa 0.82) gives a reason against the drawback that LLM-based methods lack reproducibility.
- SRC-0021 holds “Monolithic large language models are relatively robust to linguistic variation in legal case descriptions: paraphrasing tax cases while …” [CLM-0021-007]; SRC-0014 holds “Large language models may be sensitive to input perturbation, so that legal consultation responses can be contradictory when inputs differ …” [CLM-0014-002]. Note: The finding that monolithic LLMs remain stable under semantics-preserving paraphrases of legal case descriptions gives a reason against the contention that slightly differing inputs make LLM legal responses contradictory, at least for purely linguistic variation.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0002 | unknown | 1 | 1 descriptive | 1 factual | EU |
| SRC-0004 | unknown | 2 | 1 descriptive, 1 predictive | 1 factual, 1 abstract | KR, general |
| SRC-0008 | 2026 | 1 | 1 descriptive | 1 factual | RU |
| SRC-0011 | 2025 | 3 | 3 descriptive | 3 factual | CN, undetermined |
| SRC-0012 | 2025 | 1 | 1 descriptive | 1 factual | undetermined |
| SRC-0014 | unknown | 1 | 1 descriptive | 1 literature | general |
| SRC-0017 | 2024 | 1 | 1 descriptive | 1 factual | DE |
| SRC-0021 | unknown | 4 | 3 descriptive, 1 prescriptive | 4 factual | US, general |
| SRC-0024 | unknown | 1 | 1 descriptive | 1 literature | general |

## What is missing

Absence records whose key names this concept (8, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0480 — `concept_jurisdiction:CPT-robustness|AU` — No claim about CPT-robustness concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0481 — `concept_jurisdiction:CPT-robustness|BR` — No claim about CPT-robustness concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0482 — `concept_jurisdiction:CPT-robustness|CA` — No claim about CPT-robustness concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0483 — `concept_jurisdiction:CPT-robustness|GB` — No claim about CPT-robustness concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0484 — `concept_jurisdiction:CPT-robustness|MY` — No claim about CPT-robustness concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0485 — `concept_jurisdiction:CPT-robustness|NL` — No claim about CPT-robustness concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0486 — `concept_jurisdiction:CPT-robustness|NZ` — No claim about CPT-robustness concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0487 — `concept_jurisdiction:CPT-robustness|TR` — No claim about CPT-robustness concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Is LLM annotation's instability a general property or an artifact of particular models and settings?
- How sensitive are LLMs to legally irrelevant input variation, and does paraphrase robustness generalize beyond entailment tasks?
