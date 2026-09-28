---
id: CPT-information-retrieval
status: anchor
concept_type: technical_task
definition: The technical task of finding the relevant documents or passages, by search, ranking or embedding similarity.
run_ids: [RUN-2026-09-25-01]
---

# CPT-information-retrieval

## What it means

The technical task of finding the relevant documents or passages, by search, ranking or embedding similarity. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0004-002] [CLM-0004-004] [CLM-0004-006].

## Claims

### Descriptive

**CN**

- Even when legal large language models are combined with legal article retrieval components, the advice given can still be incorrect or baseless: current legal article retrieval models cannot ensure that all relevant legal articles are retrieved and all irrelevant ones left out, and while missed articles reduce the completeness of responses, retrieved irrelevant articles bring noise that leads the models to produce incomplete, incorrect or inconsistent information. — rests on factual basis (SRC-0014). [CLM-0014-001]
- Retrieving relevant legal cases and highlighting the sentences related to the user's query provides users with comprehensive reference information in legal consultation: in a user study the legal case retrieval module proved beneficial for 77% of queries on average, and all users agreed that highlighting pertinent sentences significantly streamlines reading the cases and improves reading efficiency. — rests on factual basis (SRC-0014). [CLM-0014-006]
- Fine-tuning the general-purpose embedding model BGE on the Chinese legal case retrieval dataset LeCaRD yields a significant increase in each NDCG@K over BM25 and the non-fine-tuned BGE, showing that a fine-tuned embedding model can learn legal knowledge well and better distinguish legal cases that are semantically similar but not relevant in the legal domain, although specialised case-retrieval models such as CaseEncoder, SAILER and CaseFormer still outperform it. — rests on factual basis (SRC-0014). [CLM-0014-007]

**KR**

- When a long-context-window large language model retrieves provisions of the Korean Building Act and its subordinate regulations for legal interpretation using zero-shot Chain-of-Thought prompts, less guidance leads to higher accuracy: without a high-level community summary, unguided search achieved 63.16% accuracy on 171 legal interpretative question-answer pairs, outperforming exhaustive search (60.82%) and structured search (57.89%). — rests on factual basis (SRC-0004). [CLM-0004-004]
- Providing a high-level community summary of provision titles reduces the navigation effort of a long-context-window large language model during exhaustive legal provision search: the average number of referenced provisions per inquiry fell from 10.70 to 7.62 and the average longest multi-hop sequence from 3.35 to 2.91 hops, suggesting that the summary helps minimize unnecessary navigation and exploration across different documents. — rests on factual basis (SRC-0004). [CLM-0004-006]

**general**

- Retrieval-augmented generation approaches to supplying legal information to large language models lose contextual information because data must be segmented into chunks: similarity-based retrieval can fail to recognize contextual relationships between pre-divided chunks and can retrieve text containing relevant keywords presented in unrelated or misleading contexts, and addressing such retrieval failures requires extensive, time-intensive and costly pre-processing such as creating a well-structured database. — rests on literature (SRC-0004). (same proposition also asserted by SRC-0016) [CLM-0004-002] [CLM-0016-005]
- The SyLeR framework enables explicit syllogistic legal reasoning in large language models by combining a tree-structured hierarchical retrieval mechanism, which links legal statutes with the precedent cases that apply them to form comprehensive major premises, with a two-stage fine-tuning process: a supervised fine-tuning warm-up on GPT-4o-generated syllogistic reasoning paths, followed by reinforcement learning (Proximal Policy Optimization) with a structure-aware reward that scores the alignment of major premise, minor premise and conclusion and assigns zero reward to outputs deviating from the syllogistic structure. — rests on abstract considerations (SRC-0011). [CLM-0011-009]
- Relevant legal cases can offer users more in-depth reference information when large language models fail to produce coherent and complete responses, yet a legal case retrieval module has rarely been integrated into existing legal-domain large language models in civil law systems. — rests on literature (SRC-0014). [CLM-0014-003]
- The current generation of LLMs excels when legal tasks can be distilled into sophisticated information retrieval and pattern recognition, serving best in cases with abundant reference material, clearly defined concepts as opposed to open-textured standards, and decomposability into narrow, sequential sub-tasks; when these conditions are not met, a fundamental barrier remains — the gap between the probabilistic nature of language models and the principled, choice-driven nature of judicial reasoning. — rests on abstract considerations (SRC-0026). [CLM-0026-025]

**undetermined**

- Standard semantic search is ill-suited for retrieving the policy language that governs a procedure code's coverage, because the signals that determine benefit status are often orthogonal to thematic content: passages thematically close to a procedure often do not determine its benefit status, while the actual coverage clause is often a concise exclusion or limitation found in a separate section. — rests on abstract considerations (SRC-0007). [CLM-0007-004]
- A cross-encoder retriever finetuned on a large set of expert-annotated (CPT, subsection, relevance) pairs consistently outperforms a zero-shot retriever within a rule-based coverage assessment system, improving accuracy by an average of 2.69% and F1 score by 1.72%, because it aligns with the language and structure of coverage policies and prioritizes concise policy fragments that matter for symbolic reasoning. — rests on factual basis (SRC-0007). [CLM-0007-005]
- A cross-encoder architecture, which jointly processes the query and passage through its attention layers, is essential for retrieving coverage-governing policy passages because it captures fine-grained interactions between a procedure code and subtle policy phrases that are often lost in compressed vector representations; exhaustive cross-encoder scoring is feasible because the candidate pool of subsections per plan is small and well-defined. — rests on abstract considerations (SRC-0007). [CLM-0007-006]
- Embedding-based semantic search reduces each verification query over a privacy policy's extracted data practice edges to a small relevant subset - on average 6.4 edges for the TikTok policy and 18.5 for the Meta policy, a 99.38% and 99.50% reduction in the verification problem - enabling tractable formal reasoning by an SMT solver: 23 queries of varying complexity achieved zero timeouts with average query times of 3.39s and 3.91s, and although the Meta policy is 3.9 times larger than the TikTok policy, query times increased by only 1.15 times, demonstrating sub-linear scaling behavior. — rests on factual basis (SRC-0013). [CLM-0013-012]

**general+EU**

- In cross-border disputes, AI must first distinguish between jurisdiction and applicable law and apply international instruments such as the Brussels I Recast Regulation and the Rome I Regulation; while knowledge retrieval systems can find the relevant regulations, AI systems may struggle to interpret the connecting factors that determine jurisdiction, such as a defendant's habitual residence or where the damage occurred, which normally allow for judicial discretion and context-sensitive application, and a multi-agent decomposition of the problem still relies on the agents' ability to interpret the often ambiguous and complex web of logical dependencies correctly. — rests on legal sources (SRC-0026). [CLM-0026-011]

### Predictive

**KR**

- Because a long-context-window large language model typically requires fewer than three hops to locate relevant legal provisions, predefining the top three related provisions could help reduce token costs while maintaining high accuracy in legal interpretation tasks. — rests on factual basis (SRC-0004). [CLM-0004-010]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0004 holds “Retrieval-augmented generation approaches to supplying legal information to large language models lose contextual information because data …” [CLM-0004-002]; SRC-0002 holds “Enhancing open large language models by applying methods like fine-tuning or retrieval-augmented generation is a promising direction for …” [CLM-0002-011]. Note: Context loss from chunking and the extensive, costly pre-processing RAG requires give reasons against retrieval-augmented generation as a promising enhancement of LLMs for legal use cases.
- SRC-0004 holds “Retrieval-augmented generation approaches to supplying legal information to large language models lose contextual information because data …” [CLM-0004-002]; SRC-0003 holds “Retrieval-augmented generation stabilizes answers and reduces unsupported claims in Islamic-domain question answering: anchoring responses …” [CLM-0003-006]. Note: The claim that similarity-based retrieval can surface passages whose keywords appear in unrelated or misleading contexts gives reasons against RAG reliably stabilizing and grounding legal question answering.
- SRC-0014 holds “Even when legal large language models are combined with legal article retrieval components, the advice given can still be incorrect or …” [CLM-0014-001]; SRC-0016 holds “A retrieval-augmented generation method that preserves the structure of legal texts — dividing a legal document into its pre-defined …” [CLM-0016-006]. Note: The finding that legal article retrieval cannot ensure all relevant articles are retrieved and that retrieved noise leads models to incomplete or incorrect responses gives reasons against the claim that a retrieval-augmented method ensures accurate retrieval and interpretation of relevant provisions.
- SRC-0007 holds “Standard semantic search is ill-suited for retrieving the policy language that governs a procedure code's coverage, because the signals …” [CLM-0007-004]; SRC-0016 holds “A retrieval-augmented generation method that preserves the structure of legal texts — dividing a legal document into its pre-defined …” [CLM-0016-006]. Note: The argument that similarity-based semantic search often misses the governing clause because relevance signals are orthogonal to thematic content counts against the claim that dense similarity retrieval over structured passages ensures accurate retrieval of the relevant provisions.
- SRC-0017 holds “In zero-shot extraction of normative sentences related to § 6 StVO from German court decisions with GPT-4o, Chain-of-Instructions prompting …” [CLM-0017-006]; SRC-0004 holds “When a long-context-window large language model retrieves provisions of the Korean Building Act and its subordinate regulations for legal …” [CLM-0004-004]. Note: The finding that detailed step-by-step Chain-of-Instructions prompts outperformed less structured prompts in zero-shot legal extraction gives reasons against the finding that less prompt guidance leads to higher accuracy in LLM-based legal provision retrieval.
- SRC-0007 holds “A cross-encoder retriever finetuned on a large set of expert-annotated (CPT, subsection, relevance) pairs consistently outperforms a …” [CLM-0007-005]; SRC-0017 holds “Applying prompting techniques for legal norm extraction in a zero-shot setting, rather than relying on the intermediate reasoning examples …” [CLM-0017-011]. Note: A cross-encoder retriever fine-tuned on expert-annotated pairs consistently outperforming a zero-shot retriever gives reasons against preferring a zero-shot setting without additional fine-tuning for reusable legal extraction pipelines.
- SRC-0010 holds “No technical limitation of large language models has yet been found that would convince the community that the models are, in principle, unable to …” [CLM-0010-010]; SRC-0026 holds “The current generation of LLMs excels when legal tasks can be distilled into sophisticated information retrieval and pattern recognition …” [CLM-0026-025]. Note: The claim that no technical limitation has been found showing LLMs in principle unable to perform law-creation and law-interpretation gives reasons against the assertion of a fundamental barrier between probabilistic models and judicial reasoning.
- SRC-0025 holds “Large language models may be the adjudicatory technology that resolves the text-versus-context issue at the practical lawyering scale where it …” [CLM-0025-010]; SRC-0026 holds “The current generation of LLMs excels when legal tasks can be distilled into sophisticated information retrieval and pattern recognition …” [CLM-0026-025]. Note: The claim that LLMs may become the adjudicatory technology resolving the text-versus-context issue at practical scale, letting judges relax old safeguards, gives reasons against a fundamental barrier confining LLMs to retrieval-like legal tasks.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0004 | unknown | 4 | 3 descriptive, 1 predictive | 1 literature, 3 factual | general, KR |
| SRC-0007 | 2026 | 3 | 3 descriptive | 2 abstract, 1 factual | undetermined |
| SRC-0011 | 2025 | 1 | 1 descriptive | 1 abstract | general |
| SRC-0013 | 2025 | 1 | 1 descriptive | 1 factual | undetermined |
| SRC-0014 | unknown | 4 | 4 descriptive | 3 factual, 1 literature | CN, general |
| SRC-0016 | 2024 | 1 | 1 descriptive | 1 abstract | general |
| SRC-0026 | 2026 | 2 | 2 descriptive | 1 legal, 1 abstract | general, EU |

## Open questions

- When does retrieval-augmented generation's context loss outweigh its grounding benefits for legal use?
- Does RAG's dependence on chunked, similarity-based retrieval undermine the answer stability it is credited with?
- Does structure-aware retrieval actually remove the retrieval noise that misleads legal RAG systems?
- Do the signals that govern legal relevance defeat similarity-based retrieval even when document structure is preserved?
- Does less prompt guidance help or hurt legal extraction — and does the answer depend on the task?
- Does zero-shot reusability survive the accuracy gains that task-specific fine-tuning delivers?
