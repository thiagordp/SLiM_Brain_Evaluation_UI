---
id: CPT-agentic-systems
status: anchor
concept_type: technique_class
definition: Systems in which language models act with a degree of autonomy — planning, taking actions or producing relatively autonomous reasoning — rather than answering single prompts.
run_ids: [RUN-2026-09-25-01]
---

# CPT-agentic-systems

## What it means

Systems in which language models act with a degree of autonomy — planning, taking actions or producing relatively autonomous reasoning — rather than answering single prompts. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0010-009] [CLM-0021-011].

## Claims

### Descriptive

**US**

- Prior work on the SARA benchmark suggests that standalone reasoning-optimized large language models achieve the highest accuracy, and that while agentic and symbolic frameworks offer advantages in interpretability, verification, and reliability, they do not clearly outperform strong large language models on that benchmark. — rests on literature (SRC-0021). [CLM-0021-011]

**general**

- Generative AI models are agents despite lacking mental states or intelligence: they can output relatively autonomous reasonings and even actions if certain preconditions are met, and the outputs of the most advanced large language models can, for all intents and purposes, be compared with the outputs of a human law-creator. — rests on literature (SRC-0010). [CLM-0010-009]
- To apply general clauses — legal rules deliberately formulated in an imprecise manner using open-textured terms like 'reasonable', 'fair' or 'unconscionable' — AI cannot be a mere legal formalist: an understanding of social norms, ethics and common sense is required; such clauses are especially challenging for LLMs and cannot be solved simply with better information retrieval, as there is no reference material for general clauses in every context, nor by agentic systems, because the open-textured terminology cannot be broken down into well-defined factors. — rests on abstract considerations (SRC-0026). [CLM-0026-009]
- No single AI technique is a panacea for the demands of legal reasoning; a combination of approaches is required to achieve reliability, transparency and fairness in AI-assisted adjudication, and while techniques such as retrieval-augmented generation, multi-agent systems and neuro-symbolic AI can address specific narrow challenges, they fail to solve the more significant ones that remain, particularly in tasks requiring discretion and transparent, justifiable reasoning. — rests on literature (SRC-0026). [CLM-0026-018]

**general+EU**

- In cross-border disputes, AI must first distinguish between jurisdiction and applicable law and apply international instruments such as the Brussels I Recast Regulation and the Rome I Regulation; while knowledge retrieval systems can find the relevant regulations, AI systems may struggle to interpret the connecting factors that determine jurisdiction, such as a defendant's habitual residence or where the damage occurred, which normally allow for judicial discretion and context-sensitive application, and a multi-agent decomposition of the problem still relies on the agents' ability to interpret the often ambiguous and complex web of logical dependencies correctly. — rests on legal sources (SRC-0026). [CLM-0026-011]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0010 | unknown | 1 | 1 descriptive | 1 literature | general |
| SRC-0021 | unknown | 1 | 1 descriptive | 1 literature | US |
| SRC-0026 | 2026 | 3 | 3 descriptive | 1 abstract, 1 legal, 1 literature | general, EU |

## What is missing

Absence records whose key names this concept (11, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0543 — `concept_pair:CPT-compliance-and-monitoring|CPT-agentic-systems` — No claim links CPT-compliance-and-monitoring to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0554 — `concept_pair:CPT-dataset-license-compliance|CPT-agentic-systems` — No claim links CPT-dataset-license-compliance to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0571 — `concept_pair:CPT-decision-support|CPT-agentic-systems` — No claim links CPT-decision-support to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0584 — `concept_pair:CPT-fatwa-issuance|CPT-agentic-systems` — No claim links CPT-fatwa-issuance to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0601 — `concept_pair:CPT-irac-analysis|CPT-agentic-systems` — No claim links CPT-irac-analysis to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0617 — `concept_pair:CPT-legal-drafting|CPT-agentic-systems` — No claim links CPT-legal-drafting to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0634 — `concept_pair:CPT-legal-education|CPT-agentic-systems` — No claim links CPT-legal-education to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0652 — `concept_pair:CPT-review-and-due-diligence|CPT-agentic-systems` — No claim links CPT-review-and-due-diligence to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0671 — `concept_pair:CPT-rulemaking|CPT-agentic-systems` — No claim links CPT-rulemaking to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0689 — `concept_pair:CPT-burden-of-proof|CPT-agentic-systems` — No claim links CPT-burden-of-proof to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0707 — `concept_pair:CPT-evidence-evaluation|CPT-agentic-systems` — No claim links CPT-evidence-evaluation to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- None recorded at this close-out.
