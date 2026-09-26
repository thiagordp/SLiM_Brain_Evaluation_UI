---
id: CPT-question-answering
status: anchor
concept_type: technical_task
definition: The technical task of answering legal questions posed in natural language.
run_ids: [RUN-2026-09-25-01]
---

# CPT-question-answering

## What it means

The technical task of answering legal questions posed in natural language. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0002-001] [CLM-0002-002] [CLM-0002-003].

## Claims

### Descriptive

**CN**

- On both a Chinese layperson legal question-answering dataset and a Chinese legal-practitioner dataset, the SyLeR framework achieves the best performance across all metrics (ROUGE-1, ROUGE-2, ROUGE-L, BLEU and BERTScore), outperforming legal-specific large language models and open-domain baselines including prompting-based, retrieval-augmented and fine-tuning methods. — rests on factual basis (SRC-0011). [CLM-0011-010]
- Legal-specific large language models, although built on earlier and weaker base models, demonstrate strong performance on legal question answering because fine-tuning on large amounts of legal-related data embeds substantial legal knowledge, highlighting the importance of legal knowledge in enhancing the performance of large language models on legal tasks. — rests on factual basis (SRC-0011). [CLM-0011-011]
- In legal question answering, methods that enhance large language model reasoning through fine-tuning outperform methods that enhance reasoning through prompts, because legal problems involve complex legal concepts, rules and cases requiring specialized knowledge, while the amount of training data in legal scenarios is relatively limited. — rests on factual basis (SRC-0011). [CLM-0011-012]
- A model trained with the SyLeR framework on legal questions from one user group (legal laypersons or legal practitioners) achieves optimal performance when tested on the other group, demonstrating strong cross-domain generalization and indicating that the methodology is not domain-specific. — rests on factual basis (SRC-0011). [CLM-0011-014]
- In a human evaluation by three graduate students of Chinese law on layperson legal questions, responses generated with the SyLeR framework scored highest on correctness, logicality, explainability and trustworthiness, compared with naive supervised fine-tuning, retrieval-augmented fine-tuning and chain-of-thought fine-tuning baselines. — rests on factual basis (SRC-0011). [CLM-0011-017]

**EU**

- In an exploratory case study in which nine proprietary and open large language models from the Claude, GPT, Mistral and Llama families answered 19 legal questions of varying complexity on the EU VAT Directive, average truthfulness scores as rated by a legal expert fell between 7.4 and 8.6, indicating overall strong performance. — rests on factual basis (SRC-0002). [CLM-0002-001]
- On expert-scored truthfulness in answering legal questions about the EU VAT Directive, the two GPT-4 variants (GPT-4 Turbo and GPT-4o) achieved the best scores, Llama 3.1 405B the third highest, while Llama 3.1 8B and Mistral Large achieved the lowest scores. — rests on factual basis (SRC-0002). [CLM-0002-002]
- Llama 3.1 405B performs similarly to the GPT-4 large language models and significantly better than Llama 3.1 8B on truthfulness in answering questions on the EU VAT Directive, with clearly improved and more stable responses, indicating that scaling significantly improves the accuracy of results. — rests on factual basis (SRC-0002). [CLM-0002-003]
- Certain EU VAT Directive questions show more disagreement across large language models, suggesting they may be harder or more ambiguous to answer, while two questions achieved the highest score across all models, which may indicate that they are straightforward and less complex for the models to answer. — rests on factual basis (SRC-0002). [CLM-0002-007]

**MY+AU+US**

- Without IRAC analysis from legal professionals, ChatGPT achieves an average F1 of 0.49 for answering the legal questions of legal scenarios (0.35 on US Internal Revenue Code scenarios, 0.67 on Australian Social Act scenarios, 0.44 on Contract Act Malaysia scenarios), yet fails to produce complete and correct reasoning paths toward the answers for any evaluated scenario, although some of the answers are correct. — rests on factual basis (SRC-0015). [CLM-0015-003]

**US**

- In statutory tax reasoning, measured data contamination is strongly associated with large language model performance in the direct question-answering setting, especially on the entailment task, while the correlation between contamination and Prolog-based performance is weak, suggesting that structured reasoning pipelines can mitigate contamination effects. — rests on factual basis (SRC-0021). [CLM-0021-003]
- When the same large language models are used as translators into Prolog, Prolog-based reasoning significantly outperforms direct question answering on numerical tax inference — with the largest gains for models that perform poorly under direct question answering — whereas direct question answering remains strong on entailment and is harder to surpass. — rests on factual basis (SRC-0021). [CLM-0021-004]
- In direct question answering over tax statutes, textual entailment is consistently easier for large language models than numerical reasoning, which remains difficult even for recent models; entailment performance appears to be saturating, potentially due to contamination, and recent models may be overfitting to that setting. — rests on factual basis (SRC-0021). [CLM-0021-009]
- In direct question answering over tax statutes, newer large language models perform better on both entailment and numerical tasks, suggesting that scale remains a key factor for reasoning, and reasoning-optimized models outperform general large language models. — rests on factual basis (SRC-0021). [CLM-0021-012]

**general**

- On structured, rule-based Islamic inheritance problems posed as standardized multiple-choice scenarios, frontier large language models reach accuracies over 90% while Arabic-adapted open models cluster below 50%, and performance drops as soon as the legal chain requires school-specific maxims or the consideration of exceptions. — rests on literature (SRC-0003). [CLM-0003-005]
- Retrieval-augmented generation stabilizes answers and reduces unsupported claims in Islamic-domain question answering: anchoring responses in authoritative sources such as Dar al-Iftāʾ archives yields measurable reductions in hallucinations and improvements in answer stability, and creates a workflow in which scholars can trace an answer back to recognized sources and flag unsupported steps. — rests on literature (SRC-0003). [CLM-0003-006]
- Existing research on large language models in Islamic domains focuses on fatwa question answering and inheritance calculations, with fatwa and Hajj datasets emphasizing extraction rather than reasoning, and has not assessed whether these models follow the epistemic structure of Islamic legal theory. — rests on literature (SRC-0003). [CLM-0003-010]
- Although existing large language models can generate responses to legal questions, they fail to perform explicit syllogistic reasoning, often producing implicit and unstructured answers that lack explainability and trustworthiness. — rests on literature (SRC-0011). [CLM-0011-002]
- The SyLeR framework enables explicit syllogistic legal reasoning in large language models by combining a tree-structured hierarchical retrieval mechanism, which links legal statutes with the precedent cases that apply them to form comprehensive major premises, with a two-stage fine-tuning process: a supervised fine-tuning warm-up on GPT-4o-generated syllogistic reasoning paths, followed by reinforcement learning (Proximal Policy Optimization) with a structure-aware reward that scores the alignment of major premise, minor premise and conclusion and assigns zero reward to outputs deviating from the syllogistic structure. — rests on abstract considerations (SRC-0011). [CLM-0011-009]

**undetermined**

- The SyLeR framework achieves the best performance among compared methods on the French-language legal question-answering dataset LLeQA even when its tree-based retrieval module is omitted and replaced with BM25 retrieval of the most relevant legal statute, demonstrating cross-lingual generalization and effectiveness with simpler retrieval strategies. — rests on factual basis (SRC-0011). [CLM-0011-015]

### Interpretative

**KR**

- The Building Statutes Question Answering document published under the Korean Ministry of Government Legislation, comprising 171 statutory building code interpretation cases across 21 categories, is well-suited as ground truth for evaluating legal-interpretation prompts, because MOLEG provides standardized legal interpretation guidelines in South Korea to ensure consistency across administrative agencies' interpretations, and because the cases require interpreting the meaning and relationships between provisions, as the answers are not explicitly stated in the legal texts. — rests on abstract considerations (SRC-0004). [CLM-0004-011]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0004 holds “Retrieval-augmented generation approaches to supplying legal information to large language models lose contextual information because data …” [CLM-0004-002]; SRC-0003 holds “Retrieval-augmented generation stabilizes answers and reduces unsupported claims in Islamic-domain question answering: anchoring responses …” [CLM-0003-006]. Note: The claim that similarity-based retrieval can surface passages whose keywords appear in unrelated or misleading contexts gives reasons against RAG reliably stabilizing and grounding legal question answering.
- SRC-0011 holds “In legal question answering, methods that enhance large language model reasoning through fine-tuning outperform methods that enhance …” [CLM-0011-012]; SRC-0017 holds “Applying prompting techniques for legal norm extraction in a zero-shot setting, rather than relying on the intermediate reasoning examples …” [CLM-0017-011]. Note: The contention that fine-tuning-based enhancement outperforms prompt-based enhancement in legal question answering gives reasons against the contention that zero-shot prompting without fine-tuning offers an efficient, reusable methodology for legal extraction tasks.
- SRC-0020 holds “OpenAI GPT-5.4 scores far from ideal in legal reasoning on European Court of Human Rights cases concerning ECHR Article 10: it produces …” [CLM-0020-001]; SRC-0011 holds “Although existing large language models can generate responses to legal questions, they fail to perform explicit syllogistic reasoning, …” [CLM-0011-002]. Note: The finding that a recent top-tier LLM reliably reproduces a structurally complete doctrinal analysis gives reasons against the claim that existing LLMs produce implicit and unstructured answers lacking explicit reasoning steps.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0002 | unknown | 4 | 4 descriptive | 4 factual | EU |
| SRC-0003 | 2026 | 3 | 3 descriptive | 3 literature | general |
| SRC-0004 | unknown | 1 | 1 interpretative | 1 abstract | KR |
| SRC-0011 | 2025 | 8 | 8 descriptive | 1 literature, 1 abstract, 6 factual | CN, general, undetermined |
| SRC-0015 | unknown | 1 | 1 descriptive | 1 factual | MY+AU+US |
| SRC-0021 | unknown | 4 | 4 descriptive | 4 factual | US |

## Open questions

- Does RAG's dependence on chunked, similarity-based retrieval undermine the answer stability it is credited with?
- When does fine-tuning beat prompt-based enhancement for legal NLP, and at what annotation cost?
- Have newer models overtaken the finding that LLM legal answers lack explicit doctrinal structure?
