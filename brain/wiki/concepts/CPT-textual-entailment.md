---
id: CPT-textual-entailment
status: candidate
concept_type: technical_task
definition: Deciding whether a statement is entailed or contradicted by a given text, such as determining whether a legal conclusion follows from a case under a set of statutes.
run_ids: [RUN-2026-09-25-01]
---

# CPT-textual-entailment

## What it means

Deciding whether a statement is entailed or contradicted by a given text, such as determining whether a legal conclusion follows from a case under a set of statutes. A candidate concept coined during the ingest of SRC-0021 and drawn from its claims [CLM-0021-004] [CLM-0021-007] [CLM-0021-009].

## Claims

### Descriptive

**US**

- When the same large language models are used as translators into Prolog, Prolog-based reasoning significantly outperforms direct question answering on numerical tax inference — with the largest gains for models that perform poorly under direct question answering — whereas direct question answering remains strong on entailment and is harder to surpass. — rests on factual basis (SRC-0021). [CLM-0021-004]
- Monolithic large language models are relatively robust to linguistic variation in legal case descriptions: paraphrasing tax cases while preserving semantics produces no significant performance drop, and on such simpler conceptual entailment they can outperform Prolog-based approaches. — rests on factual basis (SRC-0021). [CLM-0021-007]
- In direct question answering over tax statutes, textual entailment is consistently easier for large language models than numerical reasoning, which remains difficult even for recent models; entailment performance appears to be saturating, potentially due to contamination, and recent models may be overfitting to that setting. — rests on factual basis (SRC-0021). [CLM-0021-009]

**undetermined**

- Re-annotating ContractNLI examples under a strict formal definition of entailment yields a substantial proportion of label shifts, primarily from ENTAILMENT to NEUTRAL, revealing a systematic gap between pragmatic legal interpretation and strict formal entailment. — rests on factual basis (SRC-0022). [CLM-0022-004]
- Across three paradigms — pure LLM classification, LLM reasoning over formal logical representations, and a neuro-symbolic pipeline combining LLM formalization with an SMT solver — evaluated over five large language models on contract entailment, formal structure improves accuracy, but accuracy does not imply faithful reasoning: high-performing models succeed by mimicking legal interpretation, including its implicit assumptions, rather than by reasoning formally. — rests on factual basis (SRC-0022). [CLM-0022-007]
- A neuro-symbolic SMT pipeline for contract entailment is more conservative than LLM classification, returning a neutral classification whenever explicit grounding is lacking, and thereby surfaces the gap between legal interpretation and formal entailment rather than papering over it. — rests on factual basis (SRC-0022). [CLM-0022-008]
- In LLM classification of contract entailment, the dominant error across all models is NEUTRAL to ENTAILMENT misclassification, reflecting systematic assumption injection, while ENTAILMENT and CONTRADICTION confusions are rare, indicating that the challenge is insufficient grounding, not logical inconsistency. — rests on factual basis (SRC-0022). [CLM-0022-010]

### Interpretative

**general**

- Constructing minimal pairs — for each case where legal and formal annotation diverge, a minimally modified hypothesis that becomes formally entailed by supplying the missing assumption explicitly — transforms the opaque gap between legal interpretation and formal entailment into a tractable, analyzable object. — rests on factual basis (SRC-0022). [CLM-0022-006]

**undetermined**

- The label shifts observed when contract entailment examples are re-annotated under a strict formal definition are not errors: they are cases where the original conclusion depends on background legal knowledge or contextual assumptions reasonable for a lawyer to invoke but absent from the text. — rests on factual basis (SRC-0022). [CLM-0022-005]

### Prescriptive

**general**

- A benchmark dataset for stance misrepresentation should consist of LLM-generated legal and academic text annotated for stance misrepresentation at the claim level, using a three-way entailment framework and minimal pair methodology. — rests on abstract considerations (SRC-0022). [CLM-0022-017]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0021 holds “Monolithic large language models are relatively robust to linguistic variation in legal case descriptions: paraphrasing tax cases while …” [CLM-0021-007]; SRC-0014 holds “Large language models may be sensitive to input perturbation, so that legal consultation responses can be contradictory when inputs differ …” [CLM-0014-002]. Note: The finding that monolithic LLMs remain stable under semantics-preserving paraphrases of legal case descriptions gives a reason against the contention that slightly differing inputs make LLM legal responses contradictory, at least for purely linguistic variation.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0021 | unknown | 3 | 3 descriptive | 3 factual | US |
| SRC-0022 | unknown | 7 | 4 descriptive, 2 interpretative, 1 prescriptive | 6 factual, 1 abstract | general, undetermined |

## Open questions

- How sensitive are LLMs to legally irrelevant input variation, and does paraphrase robustness generalize beyond entailment tasks?
