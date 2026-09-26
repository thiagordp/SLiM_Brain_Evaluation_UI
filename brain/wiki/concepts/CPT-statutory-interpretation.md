---
id: CPT-statutory-interpretation
status: anchor
concept_type: interpretation_object_type
definition: Interpretation whose object is legislation.
run_ids: [RUN-2026-09-25-01]
---

# CPT-statutory-interpretation

## What it means

Interpretation whose object is legislation. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0001-004] [CLM-0001-008] [CLM-0002-001].

## Claims

### Descriptive

**EU**

- The GDPR's dense legal language frequently links provisions across multiple articles — breach notifications, security safeguards, and data subject rights often depend on definitions or clauses found elsewhere in the text — and this cross-referential structure challenges NLP pipelines that treat sentences as independent units. — rests on literature (SRC-0001). [CLM-0001-004]
- Reformulating GDPR articles into concrete, binary-checkable rule statements identifies concrete compliance indicators, permits functional equivalence via references to established security standards, and reduces interpretive ambiguity. — rests on abstract considerations (SRC-0001). [CLM-0001-008]
- In an exploratory case study in which nine proprietary and open large language models from the Claude, GPT, Mistral and Llama families answered 19 legal questions of varying complexity on the EU VAT Directive, average truthfulness scores as rated by a legal expert fell between 7.4 and 8.6, indicating overall strong performance. — rests on factual basis (SRC-0002). [CLM-0002-001]
- On expert-scored truthfulness in answering legal questions about the EU VAT Directive, the two GPT-4 variants (GPT-4 Turbo and GPT-4o) achieved the best scores, Llama 3.1 405B the third highest, while Llama 3.1 8B and Mistral Large achieved the lowest scores. — rests on factual basis (SRC-0002). [CLM-0002-002]
- When answering questions that represent exceptional cases in the law, large language models do not align well on providing the correct response, which emphasizes the need to assess specific aspects of trustworthiness such as robustness — how well a model responds to questions regarding exceptional cases — in tasks like law interpretation. — rests on factual basis (SRC-0002). [CLM-0002-008]
- Because VAT harmonisation was implemented through a Directive that regulates only certain aspects and leaves others to national discretion, numerous inconsistencies have emerged over time; consequently the interpretation of VAT rules has frequently fallen to the CJEU, whose rulings have progressively shaped the substance of VAT law. — rests on legal sources (SRC-0009). [CLM-0009-003]

**KR**

- In South Korea, more than 500 statutes and rules are intricately interlinked with building codes and regulations, 24 amendments were introduced in 2023, and processing a single legal action such as issuing a building permit can require reviewing over 400 provisions; this complexity and frequency of revision make interpreting building codes significantly challenging for both legal experts and laypeople. — rests on literature (SRC-0004). [CLM-0004-001]
- When a long-context-window large language model retrieves provisions of the Korean Building Act and its subordinate regulations for legal interpretation using zero-shot Chain-of-Thought prompts, less guidance leads to higher accuracy: without a high-level community summary, unguided search achieved 63.16% accuracy on 171 legal interpretative question-answer pairs, outperforming exhaustive search (60.82%) and structured search (57.89%). — rests on factual basis (SRC-0004). [CLM-0004-004]
- During exhaustive legal provision search, a long-context-window large language model most frequently referenced the definition provisions in Article 2 of the Korean Building Act and of its Enforcement Decree - in 59.1% of inquiries - even though these were not explicitly mentioned in the inquiries, suggesting that the model has the ability to provide consistent legal interpretations even when presented with new inquiries. — rests on factual basis (SRC-0004). [CLM-0004-008]

**US**

- In 2025 the U.S. federal Executive Branch began directing agencies to identify 'unlawful' regulations for repeal: Executive Order 14219 required agencies to identify, within 60 days, regulations fitting seven categories that could be bases for repeal, and an April 9, 2025 presidential memorandum urged agencies to rely on the good-cause exception in the Administrative Procedure Act to dispense with notice and comment when repealing regulations deemed unlawful. — rests on legal sources (SRC-0024). [CLM-0024-011]
- American statutory interpretation lacks an intelligible, generally accepted and consistently applied theory: judges move among theories such as textualism, purposivism and intentionalism; for almost every canon of interpretation there is a counter-canon pointing the opposite way; courts give no stare decisis effect to interpretive methods; and judges can use the various canons and theories to read statutes in almost any way they desire if a majority of the court agrees. — rests on literature (SRC-0024). [CLM-0024-019]
- Even if trained on every statutory interpretation opinion ever recorded, large language models would struggle mightily to identify an objectively correct way to read a statute; prompting a model to adopt the perspective of a prototypical regulatory lawyer or circuit judge is fundamentally flawed because there is no more uniformity in judges and regulatory lawyers than there is in the rules of statutory interpretation. — rests on abstract considerations (SRC-0024). [CLM-0024-020]

**general**

- There is a gap in the literature regarding the efficacy of large language models in specialized legal domains, which a comparison of model performance in interpreting the EU VAT Directive addresses. — rests on literature (SRC-0002). [CLM-0002-010]

### Interpretative

**KR**

- The Building Statutes Question Answering document published under the Korean Ministry of Government Legislation, comprising 171 statutory building code interpretation cases across 21 categories, is well-suited as ground truth for evaluating legal-interpretation prompts, because MOLEG provides standardized legal interpretation guidelines in South Korea to ensure consistency across administrative agencies' interpretations, and because the cases require interpreting the meaning and relationships between provisions, as the answers are not explicitly stated in the legal texts. — rests on abstract considerations (SRC-0004). [CLM-0004-011]

**US**

- The determination of a legal text's ordinary meaning is not an empirical project: ordinary meaning is a value-laden construct defined in part by the interpreter's judgment of what is reasonable, and textualist analysis of ordinary meaning is no more empirical or fact-based than the judicial search for congressional intent. — rests on abstract considerations (SRC-0019). [CLM-0019-002]
- The premise that a tool can identify an objectively correct answer about whether a regulation is unlawful is flawed: in many legal contexts, especially when interpreting ambiguous statutory language, there is no objectively correct answer, and agencies initially, and then judges, must choose among multiple competing values and interests and make policy decisions to interpret ambiguous legal language. — rests on abstract considerations (SRC-0024). [CLM-0024-013]
- Loper Bright v. Raimondo overruled the Chevron doctrine but left many questions unanswered regarding the scope of deference courts owe to agency interpretations of statutes, including when a statute expressly delegates discretionary authority to an agency, how courts should fix the boundaries of delegated authority and ensure reasoned decisionmaking within them, and to what extent courts will continue to apply Skidmore. — rests on legal sources (SRC-0024). [CLM-0024-017]

### Predictive

**US**

- The administrative common law that imposes broad obligations on agencies is well established but much of it is in tension with the modern judicial focus on textualism; having overturned bedrock principles of administrative law over the past decade, the Supreme Court could weaken the APA-based challenges to AI-driven repeals at any time and may loosen requirements it has imposed on agencies for decades. — rests on legal sources (SRC-0024). [CLM-0024-025]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0017 holds “In zero-shot extraction of normative sentences related to § 6 StVO from German court decisions with GPT-4o, Chain-of-Instructions prompting …” [CLM-0017-006]; SRC-0004 holds “When a long-context-window large language model retrieves provisions of the Korean Building Act and its subordinate regulations for legal …” [CLM-0004-004]. Note: The finding that detailed step-by-step Chain-of-Instructions prompts outperformed less structured prompts in zero-shot legal extraction gives reasons against the finding that less prompt guidance leads to higher accuracy in LLM-based legal provision retrieval.
- SRC-0019 holds “The determination of a legal text's ordinary meaning is not an empirical project: ordinary meaning is a value-laden construct defined in …” [CLM-0019-002]; SRC-0025 holds “Meaning in law, as distinguished from meaning in fact, is a disembodied meaning derived from the community; LLM-based generative …” [CLM-0025-007]. Note: The contention that ordinary meaning is a value-laden construct and its determination not an empirical project gives reasons against the claim that meaning in law is community meaning discoverable digitally from mass word usage.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0001 | unknown | 2 | 2 descriptive | 1 literature, 1 abstract | EU |
| SRC-0002 | unknown | 4 | 4 descriptive | 3 factual, 1 literature | EU, general |
| SRC-0004 | unknown | 4 | 3 descriptive, 1 interpretative | 1 literature, 2 factual, 1 abstract | KR |
| SRC-0009 | 2025 | 1 | 1 descriptive | 1 legal | EU |
| SRC-0019 | 2025 | 1 | 1 interpretative | 1 abstract | US |
| SRC-0024 | unknown | 6 | 3 descriptive, 2 interpretative, 1 predictive | 3 legal, 2 abstract, 1 literature | US |

## Open questions

- Does less prompt guidance help or hurt legal extraction — and does the answer depend on the task?
- Is community word usage an empirical ground for legal meaning, or a value-laden construction in disguise?
