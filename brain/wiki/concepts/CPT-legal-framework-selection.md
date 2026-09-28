---
id: CPT-legal-framework-selection
status: emergent
concept_type: legal_task
definition: Identifying the correct body of law for a case before interpretation begins — distinguishing jurisdiction from applicable law in cross-border disputes, choosing among supranational and national instruments, and selecting the right provision within a national system's hierarchy of norms.
run_ids: [RUN-2026-09-28-01]
---

# CPT-legal-framework-selection

## What it means

Identifying the correct body of law for a case before interpretation begins — distinguishing jurisdiction from applicable law in cross-border disputes, choosing among supranational and national instruments, and selecting the right provision within a national system's hierarchy of norms. Coined as a candidate during the ingest of SRC-0026 and drawn from its claims [CLM-0026-011] [CLM-0026-012]; the retrofit at the close-out of RUN-2026-09-28-01 attached two older claims [CLM-0013-007] [CLM-0016-009]; promoted to emergent at the same close-out, when claims from three independent sources (SRC-0013, SRC-0016, SRC-0026) were mapped to it.

## Claims

### Descriptive

**general**

- Privacy policies reference external context that is not defined within the policy text, such as which laws apply in each jurisdiction or how an application actually implements its settings; formalizing these statements requires information beyond the policy text itself, and even entity-sensitive analysis cannot determine which specific laws trigger sharing in which contexts. — rests on abstract considerations (SRC-0013). [CLM-0013-007]
- Reasoning on the compliance of AI tools with variable provisions differs from existing legal AI assistants and legal-reasoning benchmarks: given a large language model instructed to reason only on specific retrieved provisions, the user can select which provisions are considered by selecting those that can be retrieved, for example only laws that apply in the EU, plus provisions applying to the financial sector, plus the user's own ethical guidelines. — rests on abstract considerations (SRC-0016). [CLM-0016-009]
- Choosing the right provision within a single country's legal system is a multi-layered task in which an AI system must simultaneously respect the hierarchy of norms, the temporal scope of law, the maxim lex specialis derogat legi generali, and the correct internal procedural choice; this systemic reasoning challenge is difficult to implement with simple prompts and requires a complex dependency graph, and while a neuro-symbolic AI system could perhaps model hierarchies of statutes, defining all the rules and their internal relations is a monumental undertaking. — rests on abstract considerations (SRC-0026). [CLM-0026-012]

**general+EU**

- In cross-border disputes, AI must first distinguish between jurisdiction and applicable law and apply international instruments such as the Brussels I Recast Regulation and the Rome I Regulation; while knowledge retrieval systems can find the relevant regulations, AI systems may struggle to interpret the connecting factors that determine jurisdiction, such as a defendant's habitual residence or where the damage occurred, which normally allow for judicial discretion and context-sensitive application, and a multi-agent decomposition of the problem still relies on the agents' ability to interpret the often ambiguous and complex web of logical dependencies correctly. — rests on legal sources (SRC-0026). [CLM-0026-011]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0013 | 2025 | 1 | 1 descriptive | 1 abstract | general |
| SRC-0016 | 2024 | 1 | 1 descriptive | 1 abstract | general |
| SRC-0026 | 2026 | 2 | 2 descriptive | 1 abstract, 1 legal | general, EU |

## What is missing

Absence records whose key names this concept (16, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0723 — `concept_pair:CPT-legal-framework-selection|CPT-context-granularity` — No claim links CPT-legal-framework-selection to CPT-context-granularity. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0724 — `concept_pair:CPT-legal-framework-selection|CPT-deep-learning` — No claim links CPT-legal-framework-selection to CPT-deep-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0725 — `concept_pair:CPT-legal-framework-selection|CPT-defeasible-reasoning` — No claim links CPT-legal-framework-selection to CPT-defeasible-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0726 — `concept_pair:CPT-legal-framework-selection|CPT-explicit-reasoning` — No claim links CPT-legal-framework-selection to CPT-explicit-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0727 — `concept_pair:CPT-legal-framework-selection|CPT-fine-tuning` — No claim links CPT-legal-framework-selection to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0728 — `concept_pair:CPT-legal-framework-selection|CPT-human-reinforcement-learning` — No claim links CPT-legal-framework-selection to CPT-human-reinforcement-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0729 — `concept_pair:CPT-legal-framework-selection|CPT-in-context-learning` — No claim links CPT-legal-framework-selection to CPT-in-context-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0730 — `concept_pair:CPT-legal-framework-selection|CPT-large-language-models` — No claim links CPT-legal-framework-selection to CPT-large-language-models. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0731 — `concept_pair:CPT-legal-framework-selection|CPT-llm-as-a-judge` — No claim links CPT-legal-framework-selection to CPT-llm-as-a-judge. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0732 — `concept_pair:CPT-legal-framework-selection|CPT-llm-based-annotation` — No claim links CPT-legal-framework-selection to CPT-llm-based-annotation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0733 — `concept_pair:CPT-legal-framework-selection|CPT-machine-learning` — No claim links CPT-legal-framework-selection to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0734 — `concept_pair:CPT-legal-framework-selection|CPT-prompt-engineering` — No claim links CPT-legal-framework-selection to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0735 — `concept_pair:CPT-legal-framework-selection|CPT-question-decomposition` — No claim links CPT-legal-framework-selection to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0736 — `concept_pair:CPT-legal-framework-selection|CPT-syllogistic-reasoning` — No claim links CPT-legal-framework-selection to CPT-syllogistic-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0737 — `concept_pair:CPT-legal-framework-selection|CPT-symbolic-rule-based` — No claim links CPT-legal-framework-selection to CPT-symbolic-rule-based. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0738 — `concept_pair:CPT-legal-framework-selection|CPT-zero-shot-learning` — No claim links CPT-legal-framework-selection to CPT-zero-shot-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Is framework selection automatable by letting the user fix the applicable provisions, as one paper designs it, or does interpreting connecting factors always re-enter the loop?
