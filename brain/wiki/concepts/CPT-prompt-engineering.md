---
id: CPT-prompt-engineering
status: emergent
concept_type: technique_class
definition: The systematic design of prompts for large language models — instructions, role definitions, rule representations, context packaging and output constraints — as the mechanism that steers the model's reasoning and outputs on a task.
run_ids: [RUN-2026-09-25-01]
---

# CPT-prompt-engineering

## What it means

The systematic design of prompts for large language models — instructions, role definitions, rule representations, context packaging and output constraints — as the mechanism that steers the model's reasoning and outputs on a task. An emergent concept coined during the ingest of SRC-0001 and drawn from its claims [CLM-0001-002] [CLM-0001-003] [CLM-0001-008] [CLM-0001-009] [CLM-0001-010] [CLM-0001-012] [CLM-0001-013]. Promoted from candidate to emergent at this close-out: claims from 12 sources with no shared author are mapped to it (SRC-0001, SRC-0004, SRC-0007, SRC-0010, SRC-0011, SRC-0012, SRC-0015, SRC-0017, SRC-0018, SRC-0019, SRC-0020, SRC-0023).

## Claims

### Descriptive

**CN**

- In legal question answering, methods that enhance large language model reasoning through fine-tuning outperform methods that enhance reasoning through prompts, because legal problems involve complex legal concepts, rules and cases requiring specialized knowledge, while the amount of training data in legal scenarios is relatively limited. — rests on factual basis (SRC-0011). [CLM-0011-012]

**DE**

- In zero-shot extraction of normative sentences related to § 6 StVO from German court decisions with GPT-4o, Chain-of-Instructions prompting achieved superior Recall and F2 scores compared to Standard, Chain-of-Thought and Layer-of-Thoughts prompting, extracting 108 of 125 gold normative sentences against 99, 102 and 103 respectively. — rests on factual basis (SRC-0017). [CLM-0017-006]
- Asking GPT-4o to dynamically generate a Chain-of-Instructions prompt from a task description yields inconsistent results — a different prompt structure each time — and lower extraction performance, with the GPT-generated prompts extracting at most 75 of 125 correct normative sentences over three attempts. — rests on factual basis (SRC-0017). [CLM-0017-008]
- Breaking a complex extraction task into simpler sub-tasks addressed through the distinct layers of the Layer-of-Thoughts framework allows a large language model to focus on one specific aspect at a time, contributing to higher accuracy, and applying Standard prompts for the first two layers with Chain-of-Instructions prompting for the final layer enhances the framework's effectiveness. — rests on factual basis (SRC-0017). [CLM-0017-009]

**EU**

- A prompt-driven framework that places structured prompt engineering at the center of automated GDPR compliance assessment — dividing Data Processing Agreements into paragraph-level semantic units and evaluating them against optimized representations of GDPR obligations using tailored prompts — yields notable improvements in accuracy, precision, and F1-score. — rests on factual basis (SRC-0001). [CLM-0001-002]
- Reformulating GDPR articles into concrete, binary-checkable rule statements identifies concrete compliance indicators, permits functional equivalence via references to established security standards, and reduces interpretive ambiguity. — rests on abstract considerations (SRC-0001). [CLM-0001-008]
- In zero-shot GDPR compliance checking of Data Processing Agreements using paragraph-level semantic context units and a structured prompt template, GPT-5.1-thinking consistently outperforms GPT-4o across all metrics, achieving a 6.3% absolute improvement in accuracy and a 6.0% improvement in F1-score; the additional gains suggest that explicit reasoning provides measurable benefits in legal compliance tasks. — rests on factual basis (SRC-0001). [CLM-0001-010]

**KR**

- When a long-context-window large language model retrieves provisions of the Korean Building Act and its subordinate regulations for legal interpretation using zero-shot Chain-of-Thought prompts, less guidance leads to higher accuracy: without a high-level community summary, unguided search achieved 63.16% accuracy on 171 legal interpretative question-answer pairs, outperforming exhaustive search (60.82%) and structured search (57.89%). — rests on factual basis (SRC-0004). [CLM-0004-004]
- Incorporating a high-level community summary consisting of legal provision titles improves the robustness of long-context-window large language model provision retrieval to prompt variations, narrowing the accuracy gap between prompt variants from 5.27 to 1.17 percentage points, but it does not yield the highest performance: its primary effect is to ensure consistency in search results rather than directly enhancing accuracy. — rests on factual basis (SRC-0004). [CLM-0004-005]

**MY+AU**

- Providing ChatGPT with correct human-written intermediate reasoning paths progressively improves its final answers to legal scenario questions: the average F1 score improves to more than 0.86 when the complete human-written reasoning paths except final answers are fed to the model, reaching 0.89 for Contract Act Malaysia scenarios and 1.0 for Australian Social Act scenarios from lows of 0.10 and 0.0. — rests on factual basis (SRC-0015). [CLM-0015-004]

**NL**

- Adding regulatory text to the prompt improves the quality and perceived helpfulness of LLM-generated legal explanations, but does not consistently improve advertisement detection accuracy: the prompting strategy incorporating the most legal knowledge does not always yield the best classification performance. — rests on factual basis (SRC-0023). [CLM-0023-005]

**US**

- Even if judges consistently used a single prompting method, large language models would not remove human subjectivity from determinations of the ordinary meaning of legal text: they shift the source of bias to other parts of the process, such as model developers' design decisions; and in the more likely scenario of no consistent prompting method, using LLMs will not reduce the role of discretionary choices at all. — rests on abstract considerations (SRC-0019). [CLM-0019-001]

**general**

- Although previous studies have examined the performance of large language models on legal tasks, prompt engineering itself — the systematic design of instructions, context packaging, and compliance rule representations — has not been thoroughly investigated as a primary analytical mechanism. — rests on literature (SRC-0001). [CLM-0001-012]
- Even without legal fine-tuning, commercially available large language models can generate legal-like texts hardly distinguishable from human-created legal texts, although their outputs are overly generic and heavily dependent on the abilities of the human prompter. — rests on factual basis (SRC-0010). [CLM-0010-006]
- Techniques for enhancing large language model reasoning such as Chain-of-Thought prompting, supervised fine-tuning and retrieval-augmented fine-tuning remain largely domain-agnostic, focusing on open-domain problems such as mathematics, code and commonsense reasoning, and fail to address the distinct challenges of legal reasoning, particularly the need to generate explicit syllogistic reasoning paths that align legal rules with case-specific facts. — rests on literature (SRC-0011). [CLM-0011-004]
- Solving complex tasks with a single straightforward prompt often leads a large language model to imprecise or incorrect results, largely due to generative Transformer models' left-to-right, one-token-at-a-time architecture. — rests on abstract considerations (SRC-0017). [CLM-0017-003]
- State-of-the-art multi-step prompting techniques such as Chain-of-Thought, Tree of Thoughts and Graph of Thoughts are still largely restricted to relatively simple tasks such as simple math and reasoning problems, often come with high inference costs, and are challenging to design, develop, maintain and scale. — rests on literature (SRC-0017). [CLM-0017-004]
- Chain-of-Instructions (CoI) prompting, a newly proposed advanced variant of Chain-of-Thought prompting that replaces implicit reasoning directives with a series of explicit instructions directing the model through each stage of a task, seeks to mitigate potential ambiguities and enhance a model's ability to focus on specific aspects of the text by breaking the task into smaller, manageable steps. — rests on abstract considerations (SRC-0017). [CLM-0017-005]
- Applying prompting techniques for legal norm extraction in a zero-shot setting, rather than relying on the intermediate reasoning examples required in few-shot learning, makes the methodology more efficient and easily reusable across similar legal extraction tasks without additional fine-tuning. — rests on abstract considerations (SRC-0017). [CLM-0017-011]

**undetermined**

- Most failures of LLM-generated symbolic coverage rules stem from two factors: in 73.5% of incorrect cases the correct attribute is not incorporated into the rule creation process — often because when the attribute list is lengthy the model overlooks or 'forgets' attributes appearing later in the input sequence — and in the remaining 26.5% the model fails to generate a sufficient set of rules, so no rule is triggered; careful attribute selection and prompt engineering are therefore important when constructing symbolic rules from complex policy language. — rests on factual basis (SRC-0007). [CLM-0007-010]
- Carefully crafted, task-specific custom prompts significantly improve a fine-tuned foundation model's performance in dataset license compliance analysis, and the model is highly sensitive to variations in prompt design: Prediction Agreement varied from only 4.8% with one system prompt to 64.3% with a custom-designed system prompt under the same user prompt. — rests on factual basis (SRC-0012). [CLM-0012-011]
- An expert-curated step-by-step reasoning prompt leads GPT-5.4 to more comprehensive legal reasoning on ECtHR Article 10 cases than guide-based or non-curated prompting — a ranking shared by human annotators and LLM judges — but does not result in more accurate predictions. — rests on factual basis (SRC-0020). [CLM-0020-003]

### Interpretative

**EU**

- In LLM-based legal compliance checking, the true driver of the accuracy gains observed when expanding context from sentences to paragraphs is the design of the prompt itself, not only the size of the context window; prompt quality is the dominant determinant of accuracy. — rests on factual basis (SRC-0001). [CLM-0001-003]

**NL**

- Large language models' ability to apply legal knowledge when identifying advertisements may rely more on patterns learned during pretraining than on the legal text provided in the prompt; current LLMs do not simply 'read and apply' legal norms but rely heavily on internal heuristics and contextual associations, so their performance may reflect an underlying competence in identifying pragmatic markers of advertising rather than understanding and applying legal knowledge. — rests on factual basis (SRC-0023). [CLM-0023-006]

**US**

- The proof of concept offered for asking GPT the ordinary meaning of statutory terms (Engel and McAdams) does not look like an empirical exploration: the LLM inquiries seem to have been engineered to carefully reconstruct results previously obtained from an empirical survey of actual humans, with the outcome viewed as objectively correct chosen in advance. — rests on literature (SRC-0019). [CLM-0019-006]

**general**

- Prompt engineering functions as a form of 'soft programming' that can replace complex feature extraction pipelines or rigid rule-based frameworks, placing prompts at the core of any LLM-driven compliance automation system and motivating the need to treat them as first-class artifacts in the design of legal analysis tools. — rests on abstract considerations (SRC-0001). [CLM-0001-009]
- Carefully designed prompts can serve as the primary mechanism for guiding legal reasoning in LLM-based systems, offering a scalable, explainable, and cost-effective solution for continuous compliance assessment under evolving regulations such as the GDPR. — rests on factual basis (SRC-0001). [CLM-0001-013]
- The principle of procedural fairness dictates that if an AI's output is to be used as evidence or to support a judicial decision, the process that generated that output must be transparent and open to challenge: the specific prompt used to generate a legal analysis becomes a piece of discoverable evidence, and the choice of a particular AI model is a methodological decision comparable to an expert witness selecting a specific scientific instrument, necessitating a transparency that extends beyond the final output to the entire generative process. — rests on abstract considerations (SRC-0026). [CLM-0026-017]

**undetermined**

- Even a prompt with no explicit description of the reasoning strategy elicits from GPT-5.4 the four doctrinal steps of the ECHR Article 10 test in roughly 90-100% of cases, because the four-step test is standard Article 10 doctrine already internalised by the model; curated prompts serve to make the model apply the test reliably, not to teach it from scratch. — rests on factual basis (SRC-0020). [CLM-0020-008]

### Prescriptive

**US**

- There is a need to incorporate fundamental legal knowledge into large language model prompting for more accurate and relevant discovery of legal factors. — rests on factual basis (SRC-0018). [CLM-0018-008]

### Predictive

**US**

- Prompt engineering and 'LLM shopping' are anticipated to become the new 'dictionary shopping': confirmation bias and politically motivated reasoning is the most likely outcome of increased adoption of large language models for legal interpretation, and empirical research on judges' use of these new interpretive methods is needed. — rests on literature (SRC-0019). [CLM-0019-010]

**general**

- Findings that minimal prompt guidance improves long-context-window large language model performance in legal provision retrieval, obtained without fine-tuning or retrieval-augmented generation using dataset-specific information, may extend to other legal systems or domains. — rests on abstract considerations (SRC-0004). [CLM-0004-009]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0007 holds “The traceability of a symbolic rule-based coverage system — showing which rule fired and which attribute conditions matched — allows a …” [CLM-0007-011]; SRC-0001 holds “Carefully designed prompts can serve as the primary mechanism for guiding legal reasoning in LLM-based systems, offering a scalable, …” [CLM-0001-013]. Note: The contention that direct prompting offers no comparable traceability and is more prone to hallucinations gives reasons against treating carefully designed prompts as a scalable, explainable primary mechanism for guiding legal reasoning in LLM-based systems.
- SRC-0007 holds “LLM-based methods given retrieved policy text achieve slightly higher accuracy and F1 scores (up to 0.94 accuracy and 0.96 F1) than …” [CLM-0007-008]; SRC-0001 holds “Prompt engineering functions as a form of 'soft programming' that can replace complex feature extraction pipelines or rigid rule-based …” [CLM-0001-009]. Note: Evidence that LLM inference costs scale rapidly while a rule-based system delivers competitive performance far more cheaply gives reasons against the contention that prompt engineering can replace rule-based frameworks in LLM-driven compliance systems.
- SRC-0017 holds “In zero-shot extraction of normative sentences related to § 6 StVO from German court decisions with GPT-4o, Chain-of-Instructions prompting …” [CLM-0017-006]; SRC-0004 holds “When a long-context-window large language model retrieves provisions of the Korean Building Act and its subordinate regulations for legal …” [CLM-0004-004]. Note: The finding that detailed step-by-step Chain-of-Instructions prompts outperformed less structured prompts in zero-shot legal extraction gives reasons against the finding that less prompt guidance leads to higher accuracy in LLM-based legal provision retrieval.
- SRC-0011 holds “In legal question answering, methods that enhance large language model reasoning through fine-tuning outperform methods that enhance …” [CLM-0011-012]; SRC-0017 holds “Applying prompting techniques for legal norm extraction in a zero-shot setting, rather than relying on the intermediate reasoning examples …” [CLM-0017-011]. Note: The contention that fine-tuning-based enhancement outperforms prompt-based enhancement in legal question answering gives reasons against the contention that zero-shot prompting without fine-tuning offers an efficient, reusable methodology for legal extraction tasks.
- SRC-0019 holds “Prompt engineering and 'LLM shopping' are anticipated to become the new 'dictionary shopping': confirmation bias and politically motivated …” [CLM-0019-010]; SRC-0005 holds “The idea of having one or a few large language models for international law should be abandoned; instead, a variety of LLMs should be …” [CLM-0005-019]. Note: The prediction that choice among models and prompts enables 'LLM shopping', confirmation bias and politically motivated reasoning gives reasons against the prescription to develop a variety of LLMs configurable to distinct sets of data and interpretations of legal norms.
- SRC-0020 holds “An expert-curated step-by-step reasoning prompt leads GPT-5.4 to more comprehensive legal reasoning on ECtHR Article 10 cases than …” [CLM-0020-003]; SRC-0015 holds “Providing ChatGPT with correct human-written intermediate reasoning paths progressively improves its final answers to legal scenario …” [CLM-0015-004]. Note: The finding that an expert-curated reasoning strategy yields more comprehensive reasoning but no gain in predictive accuracy gives reasons against expecting expert-provided reasoning guidance to improve an LLM's final answers, as found with human-written IRAC reasoning paths.
- SRC-0023 holds “Adding regulatory text to the prompt improves the quality and perceived helpfulness of LLM-generated legal explanations, but does not …” [CLM-0023-005]; SRC-0018 holds “There is a need to incorporate fundamental legal knowledge into large language model prompting for more accurate and relevant discovery of …” [CLM-0018-008]. Note: The finding that incorporating legal knowledge into the prompt improves explanations but not detection accuracy gives a reason against expecting accuracy gains from adding fundamental legal knowledge to LLM prompting.
- SRC-0007 holds “For large-scale coverage adjudication, a symbolic rule-based system that performs attribute generation once per procedure code and rule …” [CLM-0007-007]; SRC-0001 holds “Carefully designed prompts can serve as the primary mechanism for guiding legal reasoning in LLM-based systems, offering a scalable, …” [CLM-0001-013]. Note: That a symbolic rule-based coverage system needing no LLM inference at run time is dramatically cheaper at scale ($22 against $4,840-$9,680 for 11,000 codes) gives reasons against carefully designed prompts being a cost-effective solution for continuous compliance assessment.
- SRC-0007 holds “A cross-encoder retriever finetuned on a large set of expert-annotated (CPT, subsection, relevance) pairs consistently outperforms a …” [CLM-0007-005]; SRC-0017 holds “Applying prompting techniques for legal norm extraction in a zero-shot setting, rather than relying on the intermediate reasoning examples …” [CLM-0017-011]. Note: A cross-encoder retriever fine-tuned on expert-annotated pairs consistently outperforming a zero-shot retriever gives reasons against preferring a zero-shot setting without additional fine-tuning for reusable legal extraction pipelines.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0001 | unknown | 7 | 4 descriptive, 3 interpretative | 4 factual, 2 abstract, 1 literature | EU, general |
| SRC-0004 | unknown | 3 | 2 descriptive, 1 predictive | 2 factual, 1 abstract | KR, general |
| SRC-0007 | 2026 | 1 | 1 descriptive | 1 factual | undetermined |
| SRC-0010 | unknown | 1 | 1 descriptive | 1 factual | general |
| SRC-0011 | 2025 | 2 | 2 descriptive | 1 literature, 1 factual | general, CN |
| SRC-0012 | 2025 | 1 | 1 descriptive | 1 factual | undetermined |
| SRC-0015 | unknown | 1 | 1 descriptive | 1 factual | MY, AU |
| SRC-0017 | 2024 | 7 | 7 descriptive | 3 abstract, 1 literature, 3 factual | general, DE |
| SRC-0018 | 2024 | 1 | 1 prescriptive | 1 factual | US |
| SRC-0019 | 2025 | 3 | 1 descriptive, 1 interpretative, 1 predictive | 1 abstract, 2 literature | US |
| SRC-0020 | 2025 | 2 | 1 descriptive, 1 interpretative | 2 factual | undetermined |
| SRC-0023 | unknown | 2 | 1 descriptive, 1 interpretative | 2 factual | NL |
| SRC-0026 | 2026 | 1 | 1 interpretative | 1 abstract | general |

## What is missing

Absence records whose key names this concept (10, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0565 — `concept_pair:CPT-dataset-license-compliance|CPT-prompt-engineering` — No claim links CPT-dataset-license-compliance to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0580 — `concept_pair:CPT-decision-support|CPT-prompt-engineering` — No claim links CPT-decision-support to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0596 — `concept_pair:CPT-fatwa-issuance|CPT-prompt-engineering` — No claim links CPT-fatwa-issuance to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0611 — `concept_pair:CPT-irac-analysis|CPT-prompt-engineering` — No claim links CPT-irac-analysis to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0646 — `concept_pair:CPT-legal-education|CPT-prompt-engineering` — No claim links CPT-legal-education to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0665 — `concept_pair:CPT-review-and-due-diligence|CPT-prompt-engineering` — No claim links CPT-review-and-due-diligence to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0683 — `concept_pair:CPT-rulemaking|CPT-prompt-engineering` — No claim links CPT-rulemaking to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0701 — `concept_pair:CPT-burden-of-proof|CPT-prompt-engineering` — No claim links CPT-burden-of-proof to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0718 — `concept_pair:CPT-evidence-evaluation|CPT-prompt-engineering` — No claim links CPT-evidence-evaluation to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0734 — `concept_pair:CPT-legal-framework-selection|CPT-prompt-engineering` — No claim links CPT-legal-framework-selection to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Can prompt-driven LLM pipelines reach the traceability that symbolic rules offer a human reviewer?
- At what scale do LLM inference costs outweigh the flexibility that prompt-centred designs buy?
- Does less prompt guidance help or hurt legal extraction — and does the answer depend on the task?
- When does fine-tuning beat prompt-based enhancement for legal NLP, and at what annotation cost?
- Does a plurality of legal LLMs enable representativity, or license model shopping and motivated reasoning?
- Does supplying better reasoning paths improve conclusions, or only the reasoning's appearance?
- Does injecting legal knowledge into prompts improve legal accuracy, or only the plausibility of explanations?
- Is prompt-driven LLM inference cost-effective for continuous compliance at adjudication scale?
- Does zero-shot reusability survive the accuracy gains that task-specific fine-tuning delivers?
