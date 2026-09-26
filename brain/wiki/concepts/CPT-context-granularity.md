---
id: CPT-context-granularity
status: emergent
concept_type: technique_class
definition: The size and coherence of the textual unit an analysis method processes at a time — sentence-level versus paragraph-level or larger semantic units — and the effect of that choice on capturing cross-references, definitions and contextual dependencies in legal text.
run_ids: [RUN-2026-09-25-01]
---

# CPT-context-granularity

## What it means

The size and coherence of the textual unit an analysis method processes at a time — sentence-level versus paragraph-level or larger semantic units — and the effect of that choice on capturing cross-references, definitions and contextual dependencies in legal text. An emergent concept coined during the ingest of SRC-0001 and drawn from its claims [CLM-0001-001] [CLM-0001-002] [CLM-0001-003] [CLM-0001-004] [CLM-0001-005] [CLM-0001-006] [CLM-0001-007]. Promoted from candidate to emergent at this close-out: claims from 4 sources with no shared author are mapped to it (SRC-0001, SRC-0004, SRC-0008, SRC-0016).

## Claims

### Descriptive

**EU**

- A prompt-driven framework that places structured prompt engineering at the center of automated GDPR compliance assessment — dividing Data Processing Agreements into paragraph-level semantic units and evaluating them against optimized representations of GDPR obligations using tailored prompts — yields notable improvements in accuracy, precision, and F1-score. — rests on factual basis (SRC-0001). [CLM-0001-002]
- The GDPR's dense legal language frequently links provisions across multiple articles — breach notifications, security safeguards, and data subject rights often depend on definitions or clauses found elsewhere in the text — and this cross-referential structure challenges NLP pipelines that treat sentences as independent units. — rests on literature (SRC-0001). [CLM-0001-004]
- Data Processing Agreements — legally binding contracts formalizing the controller-processor relationship under GDPR Article 28 — vary considerably in structure and terminology in practice; relevant details such as role definitions or security measures are often distributed across paragraphs or depend on contextual interpretation, causing sentence-level analysis to frequently fall short. — rests on literature (SRC-0001). [CLM-0001-005]

**KR**

- When a long-context-window large language model retrieves provisions of the Korean Building Act and its subordinate regulations for legal interpretation using zero-shot Chain-of-Thought prompts, less guidance leads to higher accuracy: without a high-level community summary, unguided search achieved 63.16% accuracy on 171 legal interpretative question-answer pairs, outperforming exhaustive search (60.82%) and structured search (57.89%). — rests on factual basis (SRC-0004). [CLM-0004-004]

**RU**

- In discourse markup of legal texts, dividing semantic sections into elementary discourse units is ineffective, as it complicates the markup process and makes it more cluttered; identifying larger fragments of text that perform a single function and role — up to entire sentences serving a unified purpose — significantly improves the process and prevents duplication of functions and roles. — rests on factual basis (SRC-0008). [CLM-0008-007]

**general**

- Most existing automated compliance methods rely on sentence-level processing, manually crafted rules, or domain-specific features, which often fail to capture cross-references, legal definitions, and deeper semantic relationships across a document; sentence-level analysis is poorly suited to the contextual dependencies and hierarchical structure of regulatory texts. — rests on literature (SRC-0001). [CLM-0001-001]
- Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow natural-language instructions, they are uniquely suited for legal tasks where rule interpretation, justification, and flexible reasoning are essential; their ability to operate zero-shot without explicit domain-specific fine-tuning highlights their potential for scalable compliance checking. — rests on literature (SRC-0001). [CLM-0001-006]
- Segmenting Data Processing Agreements at the paragraph level into Semantic Context Units preserves referential integrity — pronouns, relative clauses and definitional references remain interpretable because their antecedents stay within the same unit — ensuring the LLM receives contextually complete information for each compliance assessment, whereas references break and misinterpretation follows when sentences are analyzed in isolation. — rests on abstract considerations (SRC-0001). [CLM-0001-007]
- Retrieval-augmented generation approaches to supplying legal information to large language models lose contextual information because data must be segmented into chunks: similarity-based retrieval can fail to recognize contextual relationships between pre-divided chunks and can retrieve text containing relevant keywords presented in unrelated or misleading contexts, and addressing such retrieval failures requires extensive, time-intensive and costly pre-processing such as creating a well-structured database. — rests on literature (SRC-0004). (same proposition also asserted by SRC-0016) [CLM-0004-002] [CLM-0016-005]
- Large language models with long context windows, despite strong information-retrieval performance, remain imperfect: they exhibit the 'lost-in-the-middle' problem, disproportionately focusing on the beginning and end of a prompt even when the context window is not fully utilized, and vanilla long-context-window models often perform poorly on domain-specific tasks such as legal interpretation. — rests on literature (SRC-0004). [CLM-0004-003]
- A retrieval-augmented generation method that preserves the structure of legal texts — dividing a legal document into its pre-defined articles and paragraphs and segmenting each paragraph into overlapping passages for dense retrieval — ensures accurate retrieval and interpretation of relevant provisions and more accurate, contextually aware reasoning. — rests on abstract considerations (SRC-0016). [CLM-0016-006]

### Interpretative

**EU**

- In LLM-based legal compliance checking, the true driver of the accuracy gains observed when expanding context from sentences to paragraphs is the design of the prompt itself, not only the size of the context window; prompt quality is the dominant determinant of accuracy. — rests on factual basis (SRC-0001). [CLM-0001-003]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0002 holds “Because different large language models produce varying responses, there is a need to create and use standardized evaluation benchmarks …” [CLM-0002-009]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: The assertion that human oversight and domain-specific fine-tuning remain crucial in the legal domain because different LLMs produce varying responses gives reasons against the contention that zero-shot operation without domain-specific fine-tuning highlights LLMs' potential for scalable legal compliance checking.
- SRC-0003 holds “Large language models do not perform reasoning in the juristic sense; their outputs are statistical reproductions of reasoning-like …” [CLM-0003-004]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: If LLM outputs are statistical reproductions of reasoning-like patterns rather than epistemic deliberation, that gives reasons against LLMs being uniquely suited to legal tasks where rule interpretation, justification and flexible reasoning are essential.
- SRC-0003 holds “For Islamic legal questions, deductive reasoning by large language models works most consistently where explicit Qurʾānic verses and widely …” [CLM-0003-011]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: The unreliability of abductive, causal and analogical reasoning in LLMs counts against the claim that they are uniquely suited to legal tasks demanding flexible legal reasoning.
- SRC-0004 holds “Retrieval-augmented generation approaches to supplying legal information to large language models lose contextual information because data …” [CLM-0004-002]; SRC-0002 holds “Enhancing open large language models by applying methods like fine-tuning or retrieval-augmented generation is a promising direction for …” [CLM-0002-011]. Note: Context loss from chunking and the extensive, costly pre-processing RAG requires give reasons against retrieval-augmented generation as a promising enhancement of LLMs for legal use cases.
- SRC-0004 holds “Retrieval-augmented generation approaches to supplying legal information to large language models lose contextual information because data …” [CLM-0004-002]; SRC-0003 holds “Retrieval-augmented generation stabilizes answers and reduces unsupported claims in Islamic-domain question answering: anchoring responses …” [CLM-0003-006]. Note: The claim that similarity-based retrieval can surface passages whose keywords appear in unrelated or misleading contexts gives reasons against RAG reliably stabilizing and grounding legal question answering.
- SRC-0006 holds “Large language models make predictions about the most likely next word in a sequence by treating each word as a number …” [CLM-0006-013]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: The claim that LLMs make no attempt to understand or externally validate meaning gives reasons against LLMs being uniquely suited to legal tasks where rule interpretation, justification and flexible reasoning are essential.
- SRC-0014 holds “Even when legal large language models are combined with legal article retrieval components, the advice given can still be incorrect or …” [CLM-0014-001]; SRC-0016 holds “A retrieval-augmented generation method that preserves the structure of legal texts — dividing a legal document into its pre-defined …” [CLM-0016-006]. Note: The finding that legal article retrieval cannot ensure all relevant articles are retrieved and that retrieved noise leads models to incomplete or incorrect responses gives reasons against the claim that a retrieval-augmented method ensures accurate retrieval and interpretation of relevant provisions.
- SRC-0007 holds “Standard semantic search is ill-suited for retrieving the policy language that governs a procedure code's coverage, because the signals …” [CLM-0007-004]; SRC-0016 holds “A retrieval-augmented generation method that preserves the structure of legal texts — dividing a legal document into its pre-defined …” [CLM-0016-006]. Note: The argument that similarity-based semantic search often misses the governing clause because relevance signals are orthogonal to thematic content counts against the claim that dense similarity retrieval over structured passages ensures accurate retrieval of the relevant provisions.
- SRC-0017 holds “In zero-shot extraction of normative sentences related to § 6 StVO from German court decisions with GPT-4o, Chain-of-Instructions prompting …” [CLM-0017-006]; SRC-0004 holds “When a long-context-window large language model retrieves provisions of the Korean Building Act and its subordinate regulations for legal …” [CLM-0004-004]. Note: The finding that detailed step-by-step Chain-of-Instructions prompts outperformed less structured prompts in zero-shot legal extraction gives reasons against the finding that less prompt guidance leads to higher accuracy in LLM-based legal provision retrieval.
- SRC-0024 holds “Generative AI can be used effectively in the rulemaking process for tasks such as preparing summaries or plain-English versions of …” [CLM-0024-001]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: The contention that LLMs are a poor tool for tasks requiring legal analysis gives reasons against the contention that LLMs are uniquely suited for legal tasks where rule interpretation, justification and flexible reasoning are essential.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0001 | unknown | 7 | 6 descriptive, 1 interpretative | 4 literature, 2 factual, 1 abstract | EU, general |
| SRC-0004 | unknown | 3 | 3 descriptive | 2 literature, 1 factual | KR, general |
| SRC-0008 | 2026 | 1 | 1 descriptive | 1 factual | RU |
| SRC-0016 | 2024 | 2 | 2 descriptive | 2 abstract | general |

## What is missing

Absence records whose key names this concept (8, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0555 — `concept_pair:CPT-dataset-license-compliance|CPT-context-granularity` — No claim links CPT-dataset-license-compliance to CPT-context-granularity. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0572 — `concept_pair:CPT-decision-support|CPT-context-granularity` — No claim links CPT-decision-support to CPT-context-granularity. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0585 — `concept_pair:CPT-fatwa-issuance|CPT-context-granularity` — No claim links CPT-fatwa-issuance to CPT-context-granularity. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0602 — `concept_pair:CPT-irac-analysis|CPT-context-granularity` — No claim links CPT-irac-analysis to CPT-context-granularity. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0618 — `concept_pair:CPT-legal-drafting|CPT-context-granularity` — No claim links CPT-legal-drafting to CPT-context-granularity. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0635 — `concept_pair:CPT-legal-education|CPT-context-granularity` — No claim links CPT-legal-education to CPT-context-granularity. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0653 — `concept_pair:CPT-review-and-due-diligence|CPT-context-granularity` — No claim links CPT-review-and-due-diligence to CPT-context-granularity. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0672 — `concept_pair:CPT-rulemaking|CPT-context-granularity` — No claim links CPT-rulemaking to CPT-context-granularity. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Can zero-shot LLM deployment be reconciled with the demand for human oversight and domain-specific fine-tuning where consistency is essential?
- Does statistical reproduction of reasoning-like patterns suffice for the rule interpretation and flexible reasoning legal tasks demand?
- Which legal tasks require the abductive and analogical reasoning LLMs perform least reliably?
- When does retrieval-augmented generation's context loss outweigh its grounding benefits for legal use?
- Does RAG's dependence on chunked, similarity-based retrieval undermine the answer stability it is credited with?
- Can systems that make no attempt to validate meaning be entrusted with tasks where interpretation is essential?
- Does structure-aware retrieval actually remove the retrieval noise that misleads legal RAG systems?
- Do the signals that govern legal relevance defeat similarity-based retrieval even when document structure is preserved?
- Does less prompt guidance help or hurt legal extraction — and does the answer depend on the task?
- Which side of the boundary between clerical assistance and legal analysis do current LLM deployments actually sit on?
