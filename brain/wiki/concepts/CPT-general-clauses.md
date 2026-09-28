---
id: CPT-general-clauses
status: candidate
concept_type: interpretation_object_type
definition: Legal rules deliberately formulated in an imprecise manner with open-textured terms such as 'reasonable', 'fair' or 'unconscionable', delegating discretion to courts to decide cases on broad principles like good faith, fairness or public policy.
run_ids: [RUN-2026-09-28-01]
---

# CPT-general-clauses

## What it means

Legal rules deliberately formulated in an imprecise manner with open-textured terms such as 'reasonable', 'fair' or 'unconscionable', delegating discretion to courts to decide cases on broad principles like good faith, fairness or public policy. Coined as a candidate during the ingest of SRC-0026 and drawn from its claims [CLM-0026-009] [CLM-0026-025]; the retrofit at the close-out of RUN-2026-09-28-01 attached two older claims [CLM-0013-002] [CLM-0013-009].

## Claims

### Descriptive

**general**

- Privacy policies use terms, such as 'business operations', that have no computational definition; these terms are intentionally flexible to cover future business needs, whereas formal verification requires precise predicates. — rests on abstract considerations (SRC-0013). [CLM-0013-002]
- To apply general clauses — legal rules deliberately formulated in an imprecise manner using open-textured terms like 'reasonable', 'fair' or 'unconscionable' — AI cannot be a mere legal formalist: an understanding of social norms, ethics and common sense is required; such clauses are especially challenging for LLMs and cannot be solved simply with better information retrieval, as there is no reference material for general clauses in every context, nor by agentic systems, because the open-textured terminology cannot be broken down into well-defined factors. — rests on abstract considerations (SRC-0026). [CLM-0026-009]
- The current generation of LLMs excels when legal tasks can be distilled into sophisticated information retrieval and pattern recognition, serving best in cases with abundant reference material, clearly defined concepts as opposed to open-textured standards, and decomposability into narrow, sequential sub-tasks; when these conditions are not met, a fundamental barrier remains — the gap between the probabilistic nature of language models and the principled, choice-driven nature of judicial reasoning. — rests on abstract considerations (SRC-0026). [CLM-0026-025]

### Prescriptive

**general**

- Privacy policy formalization should embrace rather than abstract away the limitations of legal language: a large language model can identify six key elements of each policy statement - the data sender, receiver, data subject, data type, action performed, and any conditions - and the extracted elements can be encoded as first-order logic, while vague terms are preserved as uninterpreted predicates rather than defined, making the ambiguity explicit for human review. — rests on abstract considerations (SRC-0013). [CLM-0013-009]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0010 holds “No technical limitation of large language models has yet been found that would convince the community that the models are, in principle, unable to …” [CLM-0010-010]; SRC-0026 holds “The current generation of LLMs excels when legal tasks can be distilled into sophisticated information retrieval and pattern recognition …” [CLM-0026-025]. Note: The claim that no technical limitation has been found showing LLMs in principle unable to perform law-creation and law-interpretation gives reasons against the assertion of a fundamental barrier between probabilistic models and judicial reasoning.
- SRC-0025 holds “Large language models may be the adjudicatory technology that resolves the text-versus-context issue at the practical lawyering scale where it …” [CLM-0025-010]; SRC-0026 holds “The current generation of LLMs excels when legal tasks can be distilled into sophisticated information retrieval and pattern recognition …” [CLM-0026-025]. Note: The claim that LLMs may become the adjudicatory technology resolving the text-versus-context issue at practical scale, letting judges relax old safeguards, gives reasons against a fundamental barrier confining LLMs to retrieval-like legal tasks.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0013 | 2025 | 2 | 1 descriptive, 1 prescriptive | 2 abstract | general |
| SRC-0026 | 2026 | 2 | 2 descriptive | 2 abstract | general |

## Open questions

- Do open-textured terms resist every decomposition strategy the corpus discusses, or only retrieval and agentic decomposition?
