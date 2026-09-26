---
id: CPT-explainability-and-transparency
status: anchor
concept_type: normative_concern
definition: The concern with whether a system's reasoning, grounds and provenance can be seen, traced and audited by those it affects.
run_ids: [RUN-2026-09-25-01]
---

# CPT-explainability-and-transparency

## What it means

The concern with whether a system's reasoning, grounds and provenance can be seen, traced and audited by those it affects. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0001-013] [CLM-0003-006] [CLM-0003-014].

## Claims

### Descriptive

**CN**

- In a human evaluation by three graduate students of Chinese law on layperson legal questions, responses generated with the SyLeR framework scored highest on correctness, logicality, explainability and trustworthiness, compared with naive supervised fine-tuning, retrieval-augmented fine-tuning and chain-of-thought fine-tuning baselines. — rests on factual basis (SRC-0011). [CLM-0011-017]
- Visually presenting the legal-article basis of each sentence of a large language model's legal-advice response helps users understand the advice and verify its reliability, a sentence lacking any legal basis serving as a warning that it may be incorrect; in a user study the legal article basis of the responses was accurately provided for approximately 95% of queries. — rests on factual basis (SRC-0014). [CLM-0014-004]
- Presenting China's judicial interpretations alongside large language model legal-advice responses can assist users in acquiring a better comprehension of the responses when interpretation is required: in a user study roughly 30% of the provided judicial interpretations served to clarify specific legal terminologies or special cases, while for the remaining 70% users claimed they were already familiar with their content. — rests on factual basis (SRC-0014). [CLM-0014-009]

**EU**

- Annotations produced automatically by LLMs can be exploited to distil LLM knowledge into much smaller models that obtain comparable results, reducing annotation costs and improving scalability; using a dedicated task-specific classifier for the final extraction of Judicial Interpretative Formulas combines the strengths of LLM prompting with a more transparent and reproducible model, mitigating LLM limitations at deployment. — rests on factual basis (SRC-0009). [CLM-0009-012]

**US**

- Prior work on the SARA benchmark suggests that standalone reasoning-optimized large language models achieve the highest accuracy, and that while agentic and symbolic frameworks offer advantages in interpretability, verification, and reliability, they do not clearly outperform strong large language models on that benchmark. — rests on literature (SRC-0021). [CLM-0021-011]
- DOGE developed a program using Google Gemini to compare existing federal regulations to the laws upon which they are based and identify regulations not authorized by those laws, hoping the tool would identify over 100,000 regulations that could be repealed; agencies have generally not disclosed information about their use of AI in the rulemaking process, so the extent of their reliance on it is difficult to ascertain. — rests on factual basis (SRC-0024). [CLM-0024-012]

**general**

- Retrieval-augmented generation stabilizes answers and reduces unsupported claims in Islamic-domain question answering: anchoring responses in authoritative sources such as Dar al-Iftāʾ archives yields measurable reductions in hallucinations and improvements in answer stability, and creates a workflow in which scholars can trace an answer back to recognized sources and flag unsupported steps. — rests on literature (SRC-0003). [CLM-0003-006]
- Explainable AI techniques for large language models, such as chain-of-thought explanation, cannot supply the passive contextual information a mufti relies on — intention, social conditions, or local custom — but can show which sources shaped a model's answer and how the model weighed them, supporting scholarly oversight of whether the reasoning aligns with accepted interpretive methods. — rests on abstract considerations (SRC-0003). [CLM-0003-014]
- Chain-of-thought prompting approaches for guiding large language models through multi-step reasoning are not immune to lack of interpretability and to generating inconsistent reasoning, and can be computationally expensive when applied at scale. — rests on abstract considerations (SRC-0007). [CLM-0007-003]
- The traceability of a symbolic rule-based coverage system — showing which rule fired and which attribute conditions matched — allows a human reviewer to see exactly which factors contributed to a decision, providing transparency and context; direct prompting of a large language model does not offer this level of traceability and is more prone to hallucinations, making it less reliable for such a task. — rests on factual basis (SRC-0007). [CLM-0007-011]
- Approaches to automated extraction of legal principles face two main drawbacks: data-driven methods require costly annotation, while LLM-based methods often lack stability, transparency, and reproducibility, which are essential in the legal domain. — rests on literature (SRC-0009). [CLM-0009-004]
- A general limitation of using LLMs in the legal domain lies in their proprietary nature and lack of transparency, as well as susceptibility to hallucinations. — rests on literature (SRC-0009). [CLM-0009-013]
- Although existing large language models can generate responses to legal questions, they fail to perform explicit syllogistic reasoning, often producing implicit and unstructured answers that lack explainability and trustworthiness. — rests on literature (SRC-0011). [CLM-0011-002]
- Legal-specific large language models built by supervised fine-tuning on domain-specific datasets require a substantial amount of annotated data and still provide their final answers by implicit reasoning, lacking clear, logically structured explanations; this undermines their explainability and trustworthiness and hinders their deployment in real-world scenarios. — rests on literature (SRC-0011). [CLM-0011-003]
- Legal terminology may sometimes be embedded in large language models' legal-advice responses without sufficient explanations, posing potential understanding difficulties for users without domain knowledge. — rests on literature (SRC-0014). [CLM-0014-008]
- Prior legal datasets do not include intermediate reasoning paths understandable by legal professionals and neglect the aspect of defeasible reasoning; among existing legal QA datasets only LEGALBENCH applies the IRAC methodology, without full IRAC analysis on scenarios, and SARA codifies reasoning paths in Prolog, which is challenging for legal professionals to understand. — rests on literature (SRC-0015). [CLM-0015-002]
- Interpretability of model outputs is crucial for legal professionals in real-world legal applications; for legal scenario analysis with IRAC it is helpful for models to produce individual reasoning paths and their associated rules or precedents so that legal professionals can understand why models draw certain conclusions. — rests on literature (SRC-0015). [CLM-0015-013]
- Current computational methods for detecting undisclosed sponsored content on social media generally lack legal grounding or operate as opaque black boxes: they often lack a solid legal foundation, exposing regulators to pushback in relation to their decisions, and they prioritise accuracy over explanation, producing accurate predictions without interpretable reasoning. — rests on literature (SRC-0023). [CLM-0023-001]
- Although large language model responses may appear neutral and objective, the process by which the responses are generated embeds important value choices and policy considerations that are not disclosed to users, and models can provide biased responses in light of the biases included in their training data. — rests on literature (SRC-0024). [CLM-0024-005]
- The assumptions, algorithms and reasoning behind large language model responses are hidden in a black box; even when a user asks a model to explain the reasoning behind a conclusion, the model is not actually explaining its reasoning but predicting an appropriate response to the request for an explanation based on its training. — rests on literature (SRC-0024). [CLM-0024-008]

**undetermined**

- On ECtHR Article 10 cases GPT-5.4 spends 1.7k-3.5k billed tokens on internal reasoning, comparable to or larger than its visible output, yet almost none of it surfaces as text: the emitted reasoning summary is empty in 50/20/7% of cases across the three prompting settings despite those calls being billed thousands of reasoning tokens. — rests on factual basis (SRC-0020). [CLM-0020-011]

### Interpretative

**general**

- Carefully designed prompts can serve as the primary mechanism for guiding legal reasoning in LLM-based systems, offering a scalable, explainable, and cost-effective solution for continuous compliance assessment under evolving regulations such as the GDPR. — rests on factual basis (SRC-0001). [CLM-0001-013]
- A closed LLM's disclosed assessment need not reflect its actual internal computation: substantial hidden reasoning is billed but never returned, so a fluent assessment gives no guarantee that its stated reasons produced the decision — a transparency concern for closed models in high-stakes use. — rests on factual basis (SRC-0020). [CLM-0020-012]
- In legal case forecasting, model reasoning is not merely a path to better predictive accuracy but a lens into the model's decision-making — an explainability factor beyond brute-force pattern matching. — rests on abstract considerations (SRC-0020). [CLM-0020-019]
- The complexity of the minimal axiom set needed to ground an entailment classification is diagnostic: many or complex axioms signal genuine interpretive difficulty, while few and simple axioms suggest confident automated classification. — rests on abstract considerations (SRC-0022). [CLM-0022-012]
- Understanding where and why current legal AI systems break is not a limitation but the foundation of an agenda for trustworthy AI legal reasoning: only by honestly characterizing failure modes can it be identified where AI assistance can be responsibly applied, and systems be built that proactively surface interpretive uncertainty rather than asking lawyers to verify conclusions after the fact. — rests on abstract considerations (SRC-0022). [CLM-0022-019]

### Prescriptive

**US**

- When agencies relied on mathematical models to support decision-making, courts required them, as part of the duty to provide a reasonable explanation for their decisions, to explain the assumptions made by the models, justify the use of the models and validate the models; similar requirements should apply when agencies rely on large language models to reach decisions. — rests on legal sources (SRC-0024). [CLM-0024-024]
- Agencies should refrain from relying on large language models to identify 'unlawful' rules to be repealed; only in a future where some form of artificial intelligence can replicate human reasoning and fully explain its thought process might agencies be able to integrate generative AI more fully into the rulemaking process, and that future is not here yet. — rests on abstract considerations (SRC-0024). [CLM-0024-026]

**general**

- A legal large language model should communicate its different stages of reasoning, including which information is grounded in the retrieval database, and its main interpretative choices; it must be configurable to adapt its explanations to the user's mental model, level of knowledge, abilities and needs; and its interface should use counterfactual logic, identifying interpretative crossroads that lead to different results. — rests on literature (SRC-0005). [CLM-0005-016]
- Large language models should not be used for inherently normative tasks such as judging: normative values are always present in the legal process, and it is better to be explicit and choose socially desirable values than to accept without question the hidden and often harmful normative values forced on us by technology companies. — rests on abstract considerations (SRC-0019). [CLM-0019-009]
- Legal reasoning is an inherently compositional and complex task, and hybrid neuro-symbolic systems that combine large language model capabilities in parsing and formal translation with symbolic reasoning engines offer a more reliable and robust foundation for legal AI, improving generalization, interpretability, and verifiability. — rests on factual basis (SRC-0021). [CLM-0021-008]

### Predictive

**US**

- Agencies that rely on AI to conclude that rules are unlawful may find it very difficult to provide the reasonable explanation the Administrative Procedure Act requires, because AI cannot adequately explain the reasons behind its conclusions; any explanation developed by an agency to justify a decision that was made by a large language model obscures the agency's actual reasoning, and courts may scrutinize such explanations more scrupulously under the pretext and change-in-position doctrines. — rests on legal sources (SRC-0024). [CLM-0024-023]

**general**

- Identifying the stable discursive patterns that constitute the logic of legal court decision texts will facilitate the construction of reasoning datasets in legal and other non-STEM domains, and lays a foundation for improving the explainability of large language models in legal decision prediction; the identified function chains can serve as building blocks enabling the automatized reconstruction of court decisions. — rests on abstract considerations (SRC-0008). [CLM-0008-015]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0004 holds “Retrieval-augmented generation approaches to supplying legal information to large language models lose contextual information because data …” [CLM-0004-002]; SRC-0003 holds “Retrieval-augmented generation stabilizes answers and reduces unsupported claims in Islamic-domain question answering: anchoring responses …” [CLM-0003-006]. Note: The claim that similarity-based retrieval can surface passages whose keywords appear in unrelated or misleading contexts gives reasons against RAG reliably stabilizing and grounding legal question answering.
- SRC-0007 holds “The traceability of a symbolic rule-based coverage system — showing which rule fired and which attribute conditions matched — allows a …” [CLM-0007-011]; SRC-0001 holds “Carefully designed prompts can serve as the primary mechanism for guiding legal reasoning in LLM-based systems, offering a scalable, …” [CLM-0001-013]. Note: The contention that direct prompting offers no comparable traceability and is more prone to hallucinations gives reasons against treating carefully designed prompts as a scalable, explainable primary mechanism for guiding legal reasoning in LLM-based systems.
- SRC-0008 holds “Automatic annotation of court decisions by a large language model is highly reproducible: across five iterations on the same pool of texts …” [CLM-0008-010]; SRC-0009 holds “Approaches to automated extraction of legal principles face two main drawbacks: data-driven methods require costly annotation, while …” [CLM-0009-004]. Note: Evidence that automatic LLM annotation of court decisions is highly reproducible across repeated runs with identical parameters (average Cohen's Kappa 0.82) gives a reason against the drawback that LLM-based methods lack reproducibility.
- SRC-0020 holds “OpenAI GPT-5.4 scores far from ideal in legal reasoning on European Court of Human Rights cases concerning ECHR Article 10: it produces …” [CLM-0020-001]; SRC-0011 holds “Although existing large language models can generate responses to legal questions, they fail to perform explicit syllogistic reasoning, …” [CLM-0011-002]. Note: The finding that a recent top-tier LLM reliably reproduces a structurally complete doctrinal analysis gives reasons against the claim that existing LLMs produce implicit and unstructured answers lacking explicit reasoning steps.
- SRC-0019 holds “Large language models should not be used for inherently normative tasks such as judging: normative values are always present in the legal …” [CLM-0019-009]; SRC-0025 holds “The third party who observes and understands the objective manifestations of contractual agreement can be a large language model, even …” [CLM-0025-008]. Note: The contention that LLMs should not be used for inherently normative tasks such as judging gives reasons against the claim that an LLM can serve as the third party deciding contract interpretation disputes with a more satisfying result than a coin flip.
- SRC-0007 holds “For large-scale coverage adjudication, a symbolic rule-based system that performs attribute generation once per procedure code and rule …” [CLM-0007-007]; SRC-0001 holds “Carefully designed prompts can serve as the primary mechanism for guiding legal reasoning in LLM-based systems, offering a scalable, …” [CLM-0001-013]. Note: That a symbolic rule-based coverage system needing no LLM inference at run time is dramatically cheaper at scale ($22 against $4,840-$9,680 for 11,000 codes) gives reasons against carefully designed prompts being a cost-effective solution for continuous compliance assessment.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0001 | unknown | 1 | 1 interpretative | 1 factual | general |
| SRC-0003 | 2026 | 2 | 2 descriptive | 1 literature, 1 abstract | general |
| SRC-0005 | 2026 | 1 | 1 prescriptive | 1 literature | general |
| SRC-0007 | 2026 | 2 | 2 descriptive | 1 abstract, 1 factual | general |
| SRC-0008 | 2026 | 1 | 1 predictive | 1 abstract | general |
| SRC-0009 | 2025 | 3 | 3 descriptive | 2 literature, 1 factual | EU, general |
| SRC-0011 | 2025 | 3 | 3 descriptive | 2 literature, 1 factual | CN, general |
| SRC-0014 | unknown | 3 | 3 descriptive | 2 factual, 1 literature | CN, general |
| SRC-0015 | unknown | 2 | 2 descriptive | 2 literature | general |
| SRC-0019 | 2025 | 1 | 1 prescriptive | 1 abstract | general |
| SRC-0020 | 2025 | 3 | 1 descriptive, 2 interpretative | 2 factual, 1 abstract | general, undetermined |
| SRC-0021 | unknown | 2 | 1 prescriptive, 1 descriptive | 1 factual, 1 literature | US, general |
| SRC-0022 | unknown | 2 | 2 interpretative | 2 abstract | general |
| SRC-0023 | unknown | 1 | 1 descriptive | 1 literature | general |
| SRC-0024 | unknown | 6 | 3 descriptive, 1 predictive, 2 prescriptive | 2 literature, 1 factual, 2 legal, 1 abstract | US, general |

## What is missing

Absence records whose key names this concept (11, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0173 — `concept_jurisdiction:CPT-explainability-and-transparency|AU` — No claim about CPT-explainability-and-transparency concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0174 — `concept_jurisdiction:CPT-explainability-and-transparency|BR` — No claim about CPT-explainability-and-transparency concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0175 — `concept_jurisdiction:CPT-explainability-and-transparency|CA` — No claim about CPT-explainability-and-transparency concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0176 — `concept_jurisdiction:CPT-explainability-and-transparency|DE` — No claim about CPT-explainability-and-transparency concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0177 — `concept_jurisdiction:CPT-explainability-and-transparency|GB` — No claim about CPT-explainability-and-transparency concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0178 — `concept_jurisdiction:CPT-explainability-and-transparency|KR` — No claim about CPT-explainability-and-transparency concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0179 — `concept_jurisdiction:CPT-explainability-and-transparency|MY` — No claim about CPT-explainability-and-transparency concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0180 — `concept_jurisdiction:CPT-explainability-and-transparency|NL` — No claim about CPT-explainability-and-transparency concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0181 — `concept_jurisdiction:CPT-explainability-and-transparency|NZ` — No claim about CPT-explainability-and-transparency concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0182 — `concept_jurisdiction:CPT-explainability-and-transparency|RU` — No claim about CPT-explainability-and-transparency concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0183 — `concept_jurisdiction:CPT-explainability-and-transparency|TR` — No claim about CPT-explainability-and-transparency concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Does RAG's dependence on chunked, similarity-based retrieval undermine the answer stability it is credited with?
- Can prompt-driven LLM pipelines reach the traceability that symbolic rules offer a human reviewer?
- Is LLM annotation's instability a general property or an artifact of particular models and settings?
- Have newer models overtaken the finding that LLM legal answers lack explicit doctrinal structure?
- Are interpretive determinations inherently normative tasks that models should not perform?
- Is prompt-driven LLM inference cost-effective for continuous compliance at adjudication scale?
