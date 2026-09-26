---
id: CPT-zero-shot-learning
status: emergent
concept_type: technique_class
definition: Applying a model to a task with no task-specific training data and no in-prompt examples, relying on instructions alone to elicit the behaviour.
run_ids: [RUN-2026-09-25-01]
---

# CPT-zero-shot-learning

## What it means

Applying a model to a task with no task-specific training data and no in-prompt examples, relying on instructions alone to elicit the behaviour. An emergent concept coined during the ingest of SRC-0017 and drawn from its claims [CLM-0017-006] [CLM-0017-011]. Promoted from candidate to emergent at this close-out: claims from 4 sources with no shared author are mapped to it (SRC-0001, SRC-0007, SRC-0017, SRC-0018).

## Claims

### Descriptive

**DE**

- In zero-shot extraction of normative sentences related to § 6 StVO from German court decisions with GPT-4o, Chain-of-Instructions prompting achieved superior Recall and F2 scores compared to Standard, Chain-of-Thought and Layer-of-Thoughts prompting, extracting 108 of 125 gold normative sentences against 99, 102 and 103 respectively. — rests on factual basis (SRC-0017). [CLM-0017-006]

**US**

- Zero-shot prompting of a GPT-4 model to identify the span of paragraphs containing a court opinion's analysis and conclusion on the issue of reasonable suspicion is a reliable process, achieving high recall of the factor sets identified by an expert annotator. — rests on factual basis (SRC-0018). [CLM-0018-004]

**general**

- Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow natural-language instructions, they are uniquely suited for legal tasks where rule interpretation, justification, and flexible reasoning are essential; their ability to operate zero-shot without explicit domain-specific fine-tuning highlights their potential for scalable compliance checking. — rests on literature (SRC-0001). [CLM-0001-006]
- Applying prompting techniques for legal norm extraction in a zero-shot setting, rather than relying on the intermediate reasoning examples required in few-shot learning, makes the methodology more efficient and easily reusable across similar legal extraction tasks without additional fine-tuning. — rests on abstract considerations (SRC-0017). [CLM-0017-011]

**undetermined**

- A cross-encoder retriever finetuned on a large set of expert-annotated (CPT, subsection, relevance) pairs consistently outperforms a zero-shot retriever within a rule-based coverage assessment system, improving accuracy by an average of 2.69% and F1 score by 1.72%, because it aligns with the language and structure of coverage policies and prioritizes concise policy fragments that matter for symbolic reasoning. — rests on factual basis (SRC-0007). [CLM-0007-005]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0002 holds “Because different large language models produce varying responses, there is a need to create and use standardized evaluation benchmarks …” [CLM-0002-009]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: The assertion that human oversight and domain-specific fine-tuning remain crucial in the legal domain because different LLMs produce varying responses gives reasons against the contention that zero-shot operation without domain-specific fine-tuning highlights LLMs' potential for scalable legal compliance checking.
- SRC-0003 holds “Large language models do not perform reasoning in the juristic sense; their outputs are statistical reproductions of reasoning-like …” [CLM-0003-004]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: If LLM outputs are statistical reproductions of reasoning-like patterns rather than epistemic deliberation, that gives reasons against LLMs being uniquely suited to legal tasks where rule interpretation, justification and flexible reasoning are essential.
- SRC-0003 holds “For Islamic legal questions, deductive reasoning by large language models works most consistently where explicit Qurʾānic verses and widely …” [CLM-0003-011]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: The unreliability of abductive, causal and analogical reasoning in LLMs counts against the claim that they are uniquely suited to legal tasks demanding flexible legal reasoning.
- SRC-0006 holds “Large language models make predictions about the most likely next word in a sequence by treating each word as a number …” [CLM-0006-013]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: The claim that LLMs make no attempt to understand or externally validate meaning gives reasons against LLMs being uniquely suited to legal tasks where rule interpretation, justification and flexible reasoning are essential.
- SRC-0017 holds “In zero-shot extraction of normative sentences related to § 6 StVO from German court decisions with GPT-4o, Chain-of-Instructions prompting …” [CLM-0017-006]; SRC-0004 holds “When a long-context-window large language model retrieves provisions of the Korean Building Act and its subordinate regulations for legal …” [CLM-0004-004]. Note: The finding that detailed step-by-step Chain-of-Instructions prompts outperformed less structured prompts in zero-shot legal extraction gives reasons against the finding that less prompt guidance leads to higher accuracy in LLM-based legal provision retrieval.
- SRC-0011 holds “In legal question answering, methods that enhance large language model reasoning through fine-tuning outperform methods that enhance …” [CLM-0011-012]; SRC-0017 holds “Applying prompting techniques for legal norm extraction in a zero-shot setting, rather than relying on the intermediate reasoning examples …” [CLM-0017-011]. Note: The contention that fine-tuning-based enhancement outperforms prompt-based enhancement in legal question answering gives reasons against the contention that zero-shot prompting without fine-tuning offers an efficient, reusable methodology for legal extraction tasks.
- SRC-0024 holds “Generative AI can be used effectively in the rulemaking process for tasks such as preparing summaries or plain-English versions of …” [CLM-0024-001]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: The contention that LLMs are a poor tool for tasks requiring legal analysis gives reasons against the contention that LLMs are uniquely suited for legal tasks where rule interpretation, justification and flexible reasoning are essential.
- SRC-0007 holds “A cross-encoder retriever finetuned on a large set of expert-annotated (CPT, subsection, relevance) pairs consistently outperforms a …” [CLM-0007-005]; SRC-0017 holds “Applying prompting techniques for legal norm extraction in a zero-shot setting, rather than relying on the intermediate reasoning examples …” [CLM-0017-011]. Note: A cross-encoder retriever fine-tuned on expert-annotated pairs consistently outperforming a zero-shot retriever gives reasons against preferring a zero-shot setting without additional fine-tuning for reusable legal extraction pipelines.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0001 | unknown | 1 | 1 descriptive | 1 literature | general |
| SRC-0007 | 2026 | 1 | 1 descriptive | 1 factual | undetermined |
| SRC-0017 | 2024 | 2 | 2 descriptive | 1 factual, 1 abstract | DE, general |
| SRC-0018 | 2024 | 1 | 1 descriptive | 1 factual | US |

## What is missing

Absence records whose key names this concept (8, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0570 — `concept_pair:CPT-dataset-license-compliance|CPT-zero-shot-learning` — No claim links CPT-dataset-license-compliance to CPT-zero-shot-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0583 — `concept_pair:CPT-decision-support|CPT-zero-shot-learning` — No claim links CPT-decision-support to CPT-zero-shot-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0600 — `concept_pair:CPT-fatwa-issuance|CPT-zero-shot-learning` — No claim links CPT-fatwa-issuance to CPT-zero-shot-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0616 — `concept_pair:CPT-irac-analysis|CPT-zero-shot-learning` — No claim links CPT-irac-analysis to CPT-zero-shot-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0633 — `concept_pair:CPT-legal-drafting|CPT-zero-shot-learning` — No claim links CPT-legal-drafting to CPT-zero-shot-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0651 — `concept_pair:CPT-legal-education|CPT-zero-shot-learning` — No claim links CPT-legal-education to CPT-zero-shot-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0670 — `concept_pair:CPT-review-and-due-diligence|CPT-zero-shot-learning` — No claim links CPT-review-and-due-diligence to CPT-zero-shot-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0688 — `concept_pair:CPT-rulemaking|CPT-zero-shot-learning` — No claim links CPT-rulemaking to CPT-zero-shot-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Can zero-shot LLM deployment be reconciled with the demand for human oversight and domain-specific fine-tuning where consistency is essential?
- Does statistical reproduction of reasoning-like patterns suffice for the rule interpretation and flexible reasoning legal tasks demand?
- Which legal tasks require the abductive and analogical reasoning LLMs perform least reliably?
- Can systems that make no attempt to validate meaning be entrusted with tasks where interpretation is essential?
- Does less prompt guidance help or hurt legal extraction — and does the answer depend on the task?
- When does fine-tuning beat prompt-based enhancement for legal NLP, and at what annotation cost?
- Which side of the boundary between clerical assistance and legal analysis do current LLM deployments actually sit on?
- Does zero-shot reusability survive the accuracy gains that task-specific fine-tuning delivers?
