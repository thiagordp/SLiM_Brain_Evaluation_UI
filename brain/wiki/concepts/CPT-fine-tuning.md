---
id: CPT-fine-tuning
status: emergent
concept_type: technique_class
definition: Adapting a pre-trained language model to a domain or task by further training on domain-related data — adapter or full-parameter, supervised or reinforcement-learning based — as a route to more accurate, better-suited models for legal use.
run_ids: [RUN-2026-09-25-01]
---

# CPT-fine-tuning

## What it means

Adapting a pre-trained language model to a domain or task by further training on domain-related data — adapter or full-parameter, supervised or reinforcement-learning based — as a route to more accurate, better-suited models for legal use. An emergent concept coined during the ingest of SRC-0002 and drawn from its claims [CLM-0002-004] [CLM-0002-009] [CLM-0002-011]. Promoted from candidate to emergent at this close-out: claims from 7 sources with no shared author are mapped to it (SRC-0002, SRC-0005, SRC-0007, SRC-0011, SRC-0012, SRC-0014, SRC-0022).

## Claims

### Descriptive

**CN**

- On both a Chinese layperson legal question-answering dataset and a Chinese legal-practitioner dataset, the SyLeR framework achieves the best performance across all metrics (ROUGE-1, ROUGE-2, ROUGE-L, BLEU and BERTScore), outperforming legal-specific large language models and open-domain baselines including prompting-based, retrieval-augmented and fine-tuning methods. — rests on factual basis (SRC-0011). [CLM-0011-010]
- Legal-specific large language models, although built on earlier and weaker base models, demonstrate strong performance on legal question answering because fine-tuning on large amounts of legal-related data embeds substantial legal knowledge, highlighting the importance of legal knowledge in enhancing the performance of large language models on legal tasks. — rests on factual basis (SRC-0011). [CLM-0011-011]
- In legal question answering, methods that enhance large language model reasoning through fine-tuning outperform methods that enhance reasoning through prompts, because legal problems involve complex legal concepts, rules and cases requiring specialized knowledge, while the amount of training data in legal scenarios is relatively limited. — rests on factual basis (SRC-0011). [CLM-0011-012]
- Each of the three key components of the SyLeR framework — the reasoning-path reward, tree-based retrieval of legal statutes and precedent cases, and reinforcement-learning exploration of multiple reasoning paths — plays a vital role: removing any of them leads to a noticeable decrease in performance on both layperson and practitioner legal question-answering datasets. — rests on factual basis (SRC-0011). [CLM-0011-013]
- Fine-tuning the general-purpose embedding model BGE on the Chinese legal case retrieval dataset LeCaRD yields a significant increase in each NDCG@K over BM25 and the non-fine-tuned BGE, showing that a fine-tuned embedding model can learn legal knowledge well and better distinguish legal cases that are semantically similar but not relevant in the legal domain, although specialised case-retrieval models such as CaseEncoder, SAILER and CaseFormer still outperform it. — rests on factual basis (SRC-0014). [CLM-0014-007]

**general**

- Determining the dataset used to fine-tune an international-law large language model — and the content of a retrieval-augmented generation database — requires taking decisions on contested questions about the sources of international law, including which customs should be used, whether and which international and national case-law is relevant, and whether soft law resources should be included; for the model to provide reliable outputs, the dataset must reflect a coherent and representative understanding of these sources. — rests on abstract considerations (SRC-0005). [CLM-0005-006]
- Legal-specific large language models built by supervised fine-tuning on domain-specific datasets require a substantial amount of annotated data and still provide their final answers by implicit reasoning, lacking clear, logically structured explanations; this undermines their explainability and trustworthiness and hinders their deployment in real-world scenarios. — rests on literature (SRC-0011). [CLM-0011-003]
- Techniques for enhancing large language model reasoning such as Chain-of-Thought prompting, supervised fine-tuning and retrieval-augmented fine-tuning remain largely domain-agnostic, focusing on open-domain problems such as mathematics, code and commonsense reasoning, and fail to address the distinct challenges of legal reasoning, particularly the need to generate explicit syllogistic reasoning paths that align legal rules with case-specific facts. — rests on literature (SRC-0011). [CLM-0011-004]
- For a given legal question there may exist multiple valid syllogistic reasoning paths leading to the same conclusion, and annotating diverse reasoning paths for supervised fine-tuning is expensive and labor-intensive, particularly in the legal domain where expert annotation is required. — rests on abstract considerations (SRC-0011). [CLM-0011-006]
- SyLeR pioneered the explicit incorporation of syllogistic legal reasoning into large language models through reinforcement fine-tuning, enabling a model to generate responses in the format of major premise, minor premise and conclusion. — rests on literature (SRC-0011). [CLM-0011-008]
- The SyLeR framework enables explicit syllogistic legal reasoning in large language models by combining a tree-structured hierarchical retrieval mechanism, which links legal statutes with the precedent cases that apply them to form comprehensive major premises, with a two-stage fine-tuning process: a supervised fine-tuning warm-up on GPT-4o-generated syllogistic reasoning paths, followed by reinforcement learning (Proximal Policy Optimization) with a structure-aware reward that scores the alignment of major premise, minor premise and conclusion and assigns zero reward to outputs deviating from the syllogistic structure. — rests on abstract considerations (SRC-0011). [CLM-0011-009]
- Evidence evaluation is difficult to improve with techniques like retrieval-augmented generation because legal evidence pertains to the truthfulness of everyday facts: fine-tuning an LLM with legal corpora does not help it answer whether a certain person was in a certain place at a certain time, and LLMs struggle to evaluate the truthfulness of real-world facts, a task often reliant on human experience and credibility assessments. — rests on abstract considerations (SRC-0026). [CLM-0026-005]

**undetermined**

- A cross-encoder retriever finetuned on a large set of expert-annotated (CPT, subsection, relevance) pairs consistently outperforms a zero-shot retriever within a rule-based coverage assessment system, improving accuracy by an average of 2.69% and F1 score by 1.72%, because it aligns with the language and structure of coverage policies and prioritizes concise policy fragments that matter for symbolic reasoning. — rests on factual basis (SRC-0007). [CLM-0007-005]
- LicenseGPT, a foundation model fine-tuned on a curated dataset of 500 dataset licenses annotated by legal experts, significantly outperforms both legal and general-purpose foundation models in dataset license compliance analysis, achieving a Prediction Agreement of 64.30% — surpassing LawGPT by 20.55% and Qwen-1.5 by 4.58%, a statistically significant improvement with a large effect size — and a Semantic Similarity of 85.80%, though a Prediction Agreement of 64.30% indicates there is still room for further enhancement in model accuracy. — rests on factual basis (SRC-0012). [CLM-0012-008]
- Increasing the size of the instruction fine-tuning dataset improves a license-compliance foundation model's performance but with diminishing returns: median Prediction Agreement rises from 39.3% to 64.3% as the fine-tuning dataset expands from 100 to 450 licenses, with the most notable improvement between 100 and 250 licenses and performance gains tapering off beyond 300 licenses. — rests on factual basis (SRC-0012). [CLM-0012-012]

### Interpretative

**general**

- The architectural choices required to fine-tune a large language model for international law — selecting the domain-specific training data, integrating human expertise for reinforcement learning, and designing the user interface — embed jurisprudential assumptions and require designers to take a stance on fundamental questions concerning the nature of international law and legal interpretation. — rests on abstract considerations (SRC-0005). [CLM-0005-001]
- Reinforcement learning from human feedback in the context of training large language models for international law is fundamentally a debate about legal interpretation: providing feedback to the machine requires taking a position on what it means to interpret international law in general and specific legal concepts in particular. — rests on abstract considerations (SRC-0005). [CLM-0005-009]

### Prescriptive

**general**

- Because different large language models produce varying responses, there is a need to create and use standardized evaluation benchmarks across model families, and human oversight and domain-specific fine-tuning remain crucial in applications where consistency is essential, such as the legal domain. — rests on factual basis (SRC-0002). [CLM-0002-009]
- Enhancing open large language models by applying methods like fine-tuning or retrieval-augmented generation is a promising direction for making them more effective and better suited to legal use cases. — rests on abstract considerations (SRC-0002). [CLM-0002-011]
- The fine-tuning of a legal large language model requires a participative approach in which representativity is conceptualised on at least two axes — the biographies of the interpreters and the values used to justify substantial interpretations — and, along a critical participatory design approach, marginalised profiles should be proactively integrated. — rests on abstract considerations (SRC-0005). [CLM-0005-011]
- Rather than using LLM judges or human preferences as feedback, a formal verification tool can be used as a reward signal in training, teaching a model to distinguish formally supportable inferences from assumption-laden ones; when the solver flags an insufficiently grounded claim it also computes the minimal axioms required to ground it, feeding directly into targeted human review at the points where legal interpretation and formal grounding diverge. — rests on abstract considerations (SRC-0022). [CLM-0022-018]

### Predictive

**EU**

- Llama 3.1 8B faces increased variation in truthfulness across legal questions on the EU VAT Directive but achieved very good scores on some questions, indicating a potential for improvement, for example by fine-tuning it using domain-related data to enable more accurate responses. — rests on factual basis (SRC-0002). [CLM-0002-004]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0002 holds “Because different large language models produce varying responses, there is a need to create and use standardized evaluation benchmarks …” [CLM-0002-009]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: The assertion that human oversight and domain-specific fine-tuning remain crucial in the legal domain because different LLMs produce varying responses gives reasons against the contention that zero-shot operation without domain-specific fine-tuning highlights LLMs' potential for scalable legal compliance checking.
- SRC-0004 holds “Retrieval-augmented generation approaches to supplying legal information to large language models lose contextual information because data …” [CLM-0004-002]; SRC-0002 holds “Enhancing open large language models by applying methods like fine-tuning or retrieval-augmented generation is a promising direction for …” [CLM-0002-011]. Note: Context loss from chunking and the extensive, costly pre-processing RAG requires give reasons against retrieval-augmented generation as a promising enhancement of LLMs for legal use cases.
- SRC-0011 holds “In legal question answering, methods that enhance large language model reasoning through fine-tuning outperform methods that enhance …” [CLM-0011-012]; SRC-0017 holds “Applying prompting techniques for legal norm extraction in a zero-shot setting, rather than relying on the intermediate reasoning examples …” [CLM-0017-011]. Note: The contention that fine-tuning-based enhancement outperforms prompt-based enhancement in legal question answering gives reasons against the contention that zero-shot prompting without fine-tuning offers an efficient, reusable methodology for legal extraction tasks.
- SRC-0007 holds “A cross-encoder retriever finetuned on a large set of expert-annotated (CPT, subsection, relevance) pairs consistently outperforms a …” [CLM-0007-005]; SRC-0017 holds “Applying prompting techniques for legal norm extraction in a zero-shot setting, rather than relying on the intermediate reasoning examples …” [CLM-0017-011]. Note: A cross-encoder retriever fine-tuned on expert-annotated pairs consistently outperforming a zero-shot retriever gives reasons against preferring a zero-shot setting without additional fine-tuning for reusable legal extraction pipelines.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0002 | unknown | 3 | 1 predictive, 2 prescriptive | 2 factual, 1 abstract | EU, general |
| SRC-0005 | 2026 | 4 | 2 interpretative, 1 descriptive, 1 prescriptive | 4 abstract | general |
| SRC-0007 | 2026 | 1 | 1 descriptive | 1 factual | undetermined |
| SRC-0011 | 2025 | 9 | 9 descriptive | 3 literature, 2 abstract, 4 factual | general, CN |
| SRC-0012 | 2025 | 2 | 2 descriptive | 2 factual | undetermined |
| SRC-0014 | unknown | 1 | 1 descriptive | 1 factual | CN |
| SRC-0022 | unknown | 1 | 1 prescriptive | 1 abstract | general |
| SRC-0026 | 2026 | 1 | 1 descriptive | 1 abstract | general |

## What is missing

Absence records whose key names this concept (10, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0546 — `concept_pair:CPT-compliance-and-monitoring|CPT-fine-tuning` — No claim links CPT-compliance-and-monitoring to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0575 — `concept_pair:CPT-decision-support|CPT-fine-tuning` — No claim links CPT-decision-support to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0589 — `concept_pair:CPT-fatwa-issuance|CPT-fine-tuning` — No claim links CPT-fatwa-issuance to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0605 — `concept_pair:CPT-irac-analysis|CPT-fine-tuning` — No claim links CPT-irac-analysis to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0622 — `concept_pair:CPT-legal-drafting|CPT-fine-tuning` — No claim links CPT-legal-drafting to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0638 — `concept_pair:CPT-legal-education|CPT-fine-tuning` — No claim links CPT-legal-education to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0657 — `concept_pair:CPT-review-and-due-diligence|CPT-fine-tuning` — No claim links CPT-review-and-due-diligence to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0676 — `concept_pair:CPT-rulemaking|CPT-fine-tuning` — No claim links CPT-rulemaking to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0694 — `concept_pair:CPT-burden-of-proof|CPT-fine-tuning` — No claim links CPT-burden-of-proof to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0727 — `concept_pair:CPT-legal-framework-selection|CPT-fine-tuning` — No claim links CPT-legal-framework-selection to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Can zero-shot LLM deployment be reconciled with the demand for human oversight and domain-specific fine-tuning where consistency is essential?
- When does retrieval-augmented generation's context loss outweigh its grounding benefits for legal use?
- When does fine-tuning beat prompt-based enhancement for legal NLP, and at what annotation cost?
- Does zero-shot reusability survive the accuracy gains that task-specific fine-tuning delivers?
