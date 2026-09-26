---
id: CPT-explicit-reasoning
status: emergent
concept_type: technique_class
definition: The capability of a model to perform explicit multi-step reasoning before producing an answer, as in reasoning-enabled large language model variants, contrasted with plain instruction-following generation.
run_ids: [RUN-2026-09-25-01]
---

# CPT-explicit-reasoning

## What it means

The capability of a model to perform explicit multi-step reasoning before producing an answer, as in reasoning-enabled large language model variants, contrasted with plain instruction-following generation. An emergent concept coined during the ingest of SRC-0001 and drawn from its claims [CLM-0001-010] [CLM-0001-011]. Promoted from candidate to emergent at this close-out: claims from 9 sources with no shared author are mapped to it (SRC-0001, SRC-0003, SRC-0007, SRC-0008, SRC-0011, SRC-0015, SRC-0017, SRC-0020, SRC-0021).

## Claims

### Descriptive

**EU**

- In zero-shot GDPR compliance checking of Data Processing Agreements using paragraph-level semantic context units and a structured prompt template, GPT-5.1-thinking consistently outperforms GPT-4o across all metrics, achieving a 6.3% absolute improvement in accuracy and a 6.0% improvement in F1-score; the additional gains suggest that explicit reasoning provides measurable benefits in legal compliance tasks. — rests on factual basis (SRC-0001). [CLM-0001-010]
- The performance gains of GPT-5.1-thinking over GPT-4o in GDPR compliance checking are particularly pronounced for multi-part GDPR rules, such as those concerning breach notification content, security measures, and data subject rights: GPT-4o frequently classified paragraphs as compliant when only a subset of required elements was present, while GPT-5.1-thinking identified partial compliance cases more accurately, lowering the incidence of over-generalized acceptance. — rests on factual basis (SRC-0001). [CLM-0001-011]

**MY+AU**

- Providing ChatGPT with correct human-written intermediate reasoning paths progressively improves its final answers to legal scenario questions: the average F1 score improves to more than 0.86 when the complete human-written reasoning paths except final answers are fed to the model, reaching 0.89 for Contract Act Malaysia scenarios and 1.0 for Australian Social Act scenarios from lows of 0.10 and 0.0. — rests on factual basis (SRC-0015). [CLM-0015-004]
- Decomposing the legal question of a scenario into simpler questions consistently improves ChatGPT's accuracy in identifying legal concepts, such as 'invitation to treat' — reaching a precision of 0.75, recall of 0.88 and an F1-score of 0.81 on legal concept identification — but does not always improve the correctness of the produced reasoning paths. — rests on factual basis (SRC-0015). [CLM-0015-006]
- ChatGPT's generated IRAC analyses are fluent, but it does not provide enough information such as references to statutes or precedents in its reasoning paths — of 40 evaluated scenarios only one had an analysis with correct references to statutes and precedents, and only two produced high-quality reasoning paths — and its formulation of the analysis is sometimes very confusing and logically inconsistent. — rests on factual basis (SRC-0015). [CLM-0015-007]
- Although ChatGPT can produce correct conclusions in IRAC analysis of legal scenarios, its analysis in the Application part is mostly not aligned with the analyses of legal professionals, and its references to law and precedents are often missing or incorrect. — rests on factual basis (SRC-0015). [CLM-0015-008]

**MY+AU+US**

- Without IRAC analysis from legal professionals, ChatGPT achieves an average F1 of 0.49 for answering the legal questions of legal scenarios (0.35 on US Internal Revenue Code scenarios, 0.67 on Australian Social Act scenarios, 0.44 on Contract Act Malaysia scenarios), yet fails to produce complete and correct reasoning paths toward the answers for any evaluated scenario, although some of the answers are correct. — rests on factual basis (SRC-0015). [CLM-0015-003]

**RU**

- In tax decisions of the Russian Supreme Court, the common legal logic primarily follows the 'cause → legal_ref → conclusion' pattern — the most frequent three-element function chain — and most discourse functions are linked by the cause function, which confirms its structural importance in legal reasoning as the main connector. — rests on factual basis (SRC-0008). [CLM-0008-002]

**US**

- Validating generated logical programs and deferring uncertain cases to human experts can substantially reduce tax penalties, underscoring the value of explicit reasoning even when full automation is not feasible. — rests on literature (SRC-0021). [CLM-0021-013]

**general**

- Large language models do not perform reasoning in the juristic sense; their outputs are statistical reproductions of reasoning-like patterns emerging from probabilistic associations learned from vast corpora, not from epistemic deliberation or normative judgment, and successful reasoning often reflects recognition of trained forms rather than construction of new legal or logical structure. — rests on literature (SRC-0003). (same proposition also asserted by SRC-0008) [CLM-0003-004] [CLM-0008-005]
- For Islamic legal questions, deductive reasoning by large language models works most consistently where explicit Qurʾānic verses and widely transmitted hadiths are involved, and inductive pattern matching functions well for established fiqh categories, but abductive, causal, and analogical reasoning that depends on identifying the operative cause (ʿillah) remains less reliable because it requires conceptual and contextual precision that statistical methods cannot capture. — rests on abstract considerations (SRC-0003). [CLM-0003-011]
- Explainable AI techniques for large language models, such as chain-of-thought explanation, cannot supply the passive contextual information a mufti relies on — intention, social conditions, or local custom — but can show which sources shaped a model's answer and how the model weighed them, supporting scholarly oversight of whether the reasoning aligns with accepted interpretive methods. — rests on abstract considerations (SRC-0003). [CLM-0003-014]
- Chain-of-thought prompting approaches for guiding large language models through multi-step reasoning are not immune to lack of interpretability and to generating inconsistent reasoning, and can be computationally expensive when applied at scale. — rests on abstract considerations (SRC-0007). [CLM-0007-003]
- Reasoning large language models have become a focal point in applied computational linguistics, but their development and evaluation remain largely limited to verifiable domains such as mathematics and programming, while reasoning in the humanities and social sciences, particularly in law, has received less attention. — rests on literature (SRC-0008). (same proposition also asserted by SRC-0020) [CLM-0008-003] [CLM-0020-018]
- Although existing large language models can generate responses to legal questions, they fail to perform explicit syllogistic reasoning, often producing implicit and unstructured answers that lack explainability and trustworthiness. — rests on literature (SRC-0011). [CLM-0011-002]
- Legal-specific large language models built by supervised fine-tuning on domain-specific datasets require a substantial amount of annotated data and still provide their final answers by implicit reasoning, lacking clear, logically structured explanations; this undermines their explainability and trustworthiness and hinders their deployment in real-world scenarios. — rests on literature (SRC-0011). [CLM-0011-003]
- Techniques for enhancing large language model reasoning such as Chain-of-Thought prompting, supervised fine-tuning and retrieval-augmented fine-tuning remain largely domain-agnostic, focusing on open-domain problems such as mathematics, code and commonsense reasoning, and fail to address the distinct challenges of legal reasoning, particularly the need to generate explicit syllogistic reasoning paths that align legal rules with case-specific facts. — rests on literature (SRC-0011). [CLM-0011-004]
- Prior legal datasets do not include intermediate reasoning paths understandable by legal professionals and neglect the aspect of defeasible reasoning; among existing legal QA datasets only LEGALBENCH applies the IRAC methodology, without full IRAC analysis on scenarios, and SARA codifies reasoning paths in Prolog, which is challenging for legal professionals to understand. — rests on literature (SRC-0015). [CLM-0015-002]
- Interpretability of model outputs is crucial for legal professionals in real-world legal applications; for legal scenario analysis with IRAC it is helpful for models to produce individual reasoning paths and their associated rules or precedents so that legal professionals can understand why models draw certain conclusions. — rests on literature (SRC-0015). [CLM-0015-013]
- Recently released large language models often follow different, or even wrong, reasoning paths to obtain correct answers — an issue referred to as a misalignment problem between LLMs and humans — and this problem has not previously been investigated in the legal domain. — rests on literature (SRC-0015). [CLM-0015-014]
- State-of-the-art multi-step prompting techniques such as Chain-of-Thought, Tree of Thoughts and Graph of Thoughts are still largely restricted to relatively simple tasks such as simple math and reasoning problems, often come with high inference costs, and are challenging to design, develop, maintain and scale. — rests on literature (SRC-0017). [CLM-0017-004]
- Chain-of-Instructions (CoI) prompting, a newly proposed advanced variant of Chain-of-Thought prompting that replaces implicit reasoning directives with a series of explicit instructions directing the model through each stage of a task, seeks to mitigate potential ambiguities and enhance a model's ability to focus on specific aspects of the text by breaking the task into smaller, manageable steps. — rests on abstract considerations (SRC-0017). [CLM-0017-005]

**undetermined**

- On ECtHR Article 10 cases GPT-5.4 spends 1.7k-3.5k billed tokens on internal reasoning, comparable to or larger than its visible output, yet almost none of it surfaces as text: the emitted reasoning summary is empty in 50/20/7% of cases across the three prompting settings despite those calls being billed thousands of reasoning tokens. — rests on factual basis (SRC-0020). [CLM-0020-011]

### Interpretative

**general**

- A closed LLM's disclosed assessment need not reflect its actual internal computation: substantial hidden reasoning is billed but never returned, so a fluent assessment gives no guarantee that its stated reasons produced the decision — a transparency concern for closed models in high-stakes use. — rests on factual basis (SRC-0020). [CLM-0020-012]
- In legal case forecasting, model reasoning is not merely a path to better predictive accuracy but a lens into the model's decision-making — an explainability factor beyond brute-force pattern matching. — rests on abstract considerations (SRC-0020). [CLM-0020-019]

### Predictive

**general**

- Identifying the stable discursive patterns that constitute the logic of legal court decision texts will facilitate the construction of reasoning datasets in legal and other non-STEM domains, and lays a foundation for improving the explainability of large language models in legal decision prediction; the identified function chains can serve as building blocks enabling the automatized reconstruction of court decisions. — rests on abstract considerations (SRC-0008). [CLM-0008-015]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0003 holds “Large language models do not perform reasoning in the juristic sense; their outputs are statistical reproductions of reasoning-like …” [CLM-0003-004]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: If LLM outputs are statistical reproductions of reasoning-like patterns rather than epistemic deliberation, that gives reasons against LLMs being uniquely suited to legal tasks where rule interpretation, justification and flexible reasoning are essential.
- SRC-0003 holds “For Islamic legal questions, deductive reasoning by large language models works most consistently where explicit Qurʾānic verses and widely …” [CLM-0003-011]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: The unreliability of abductive, causal and analogical reasoning in LLMs counts against the claim that they are uniquely suited to legal tasks demanding flexible legal reasoning.
- SRC-0020 holds “OpenAI GPT-5.4 scores far from ideal in legal reasoning on European Court of Human Rights cases concerning ECHR Article 10: it produces …” [CLM-0020-001]; SRC-0011 holds “Although existing large language models can generate responses to legal questions, they fail to perform explicit syllogistic reasoning, …” [CLM-0011-002]. Note: The finding that a recent top-tier LLM reliably reproduces a structurally complete doctrinal analysis gives reasons against the claim that existing LLMs produce implicit and unstructured answers lacking explicit reasoning steps.
- SRC-0020 holds “An expert-curated step-by-step reasoning prompt leads GPT-5.4 to more comprehensive legal reasoning on ECtHR Article 10 cases than …” [CLM-0020-003]; SRC-0015 holds “Providing ChatGPT with correct human-written intermediate reasoning paths progressively improves its final answers to legal scenario …” [CLM-0015-004]. Note: The finding that an expert-curated reasoning strategy yields more comprehensive reasoning but no gain in predictive accuracy gives reasons against expecting expert-provided reasoning guidance to improve an LLM's final answers, as found with human-written IRAC reasoning paths.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0001 | unknown | 2 | 2 descriptive | 2 factual | EU |
| SRC-0003 | 2026 | 3 | 3 descriptive | 1 literature, 2 abstract | general |
| SRC-0007 | 2026 | 1 | 1 descriptive | 1 abstract | general |
| SRC-0008 | 2026 | 4 | 3 descriptive, 1 predictive | 1 factual, 2 literature, 1 abstract | RU, general |
| SRC-0011 | 2025 | 3 | 3 descriptive | 3 literature | general |
| SRC-0015 | unknown | 8 | 8 descriptive | 3 literature, 5 factual | MY+AU, MY+AU+US, general |
| SRC-0017 | 2024 | 2 | 2 descriptive | 1 literature, 1 abstract | general |
| SRC-0020 | 2025 | 4 | 2 descriptive, 2 interpretative | 2 factual, 1 literature, 1 abstract | general, undetermined |
| SRC-0021 | unknown | 1 | 1 descriptive | 1 literature | US |

## What is missing

Absence records whose key names this concept (7, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0558 — `concept_pair:CPT-dataset-license-compliance|CPT-explicit-reasoning` — No claim links CPT-dataset-license-compliance to CPT-explicit-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0574 — `concept_pair:CPT-decision-support|CPT-explicit-reasoning` — No claim links CPT-decision-support to CPT-explicit-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0588 — `concept_pair:CPT-fatwa-issuance|CPT-explicit-reasoning` — No claim links CPT-fatwa-issuance to CPT-explicit-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0621 — `concept_pair:CPT-legal-drafting|CPT-explicit-reasoning` — No claim links CPT-legal-drafting to CPT-explicit-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0637 — `concept_pair:CPT-legal-education|CPT-explicit-reasoning` — No claim links CPT-legal-education to CPT-explicit-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0656 — `concept_pair:CPT-review-and-due-diligence|CPT-explicit-reasoning` — No claim links CPT-review-and-due-diligence to CPT-explicit-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0675 — `concept_pair:CPT-rulemaking|CPT-explicit-reasoning` — No claim links CPT-rulemaking to CPT-explicit-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Does statistical reproduction of reasoning-like patterns suffice for the rule interpretation and flexible reasoning legal tasks demand?
- Which legal tasks require the abductive and analogical reasoning LLMs perform least reliably?
- Have newer models overtaken the finding that LLM legal answers lack explicit doctrinal structure?
- Does supplying better reasoning paths improve conclusions, or only the reasoning's appearance?
