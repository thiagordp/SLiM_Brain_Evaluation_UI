---
id: CPT-inter-model-agreement
status: candidate
concept_type: normative_concern
definition: The degree to which different language models produce consistent responses to the same questions, measured by agreement statistics such as Cohen's Kappa; low agreement across models signals variability that matters where consistency is essential.
run_ids: [RUN-2026-09-25-01]
---

# CPT-inter-model-agreement

## What it means

The degree to which different language models produce consistent responses to the same questions, measured by agreement statistics such as Cohen's Kappa; low agreement across models signals variability that matters where consistency is essential. A candidate concept coined during the ingest of SRC-0002 and drawn from its claims [CLM-0002-005] [CLM-0002-006] [CLM-0002-007] [CLM-0002-009].

## Claims

### Descriptive

**EU**

- Large language models from the same family show increased agreement scores in their answers to EU VAT Directive questions compared to the agreement between models from different families, possibly mirroring the anticipated impact of common architectures, training methodologies, or similar optimization processes. — rests on factual basis (SRC-0002). [CLM-0002-005]
- The highest agreement between large language models answering EU VAT Directive questions, a Cohen's Kappa coefficient of 0.65, was observed between GPT-4o and Llama 3.1 405B, meaning that these two models have a similar behavior in producing accurate responses. — rests on factual basis (SRC-0002). [CLM-0002-006]
- Certain EU VAT Directive questions show more disagreement across large language models, suggesting they may be harder or more ambiguous to answer, while two questions achieved the highest score across all models, which may indicate that they are straightforward and less complex for the models to answer. — rests on factual basis (SRC-0002). [CLM-0002-007]

**undetermined**

- When evaluating LLM-generated legal reasoning on ECtHR cases, LLM-as-a-Judge evaluators (GPT-5.5, Claude Opus 4.7 and DeepSeek V4 Pro) are internally consistent yet align only weakly with trained human annotators (judge-judge α = 0.41 versus human-human α = 0.09 on comprehensiveness; judge-human ρ = 0.16-0.33): they are reliable but not a valid substitute for human evaluation. — rests on factual basis (SRC-0020). [CLM-0020-002]

### Prescriptive

**general**

- Because different large language models produce varying responses, there is a need to create and use standardized evaluation benchmarks across model families, and human oversight and domain-specific fine-tuning remain crucial in applications where consistency is essential, such as the legal domain. — rests on factual basis (SRC-0002). [CLM-0002-009]

### Predictive

**general**

- Because LLM judges agree with one another far more than with trained annotators and over-rate the hardest (proportionality) step, using them as the sole arbiter of good legal reasoning risks entrenching a shared model bias under a veneer of consensus. — rests on factual basis (SRC-0020). [CLM-0020-021]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0002 holds “Because different large language models produce varying responses, there is a need to create and use standardized evaluation benchmarks …” [CLM-0002-009]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: The assertion that human oversight and domain-specific fine-tuning remain crucial in the legal domain because different LLMs produce varying responses gives reasons against the contention that zero-shot operation without domain-specific fine-tuning highlights LLMs' potential for scalable legal compliance checking.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0002 | unknown | 4 | 3 descriptive, 1 prescriptive | 4 factual | EU, general |
| SRC-0020 | 2025 | 2 | 1 descriptive, 1 predictive | 2 factual | general, undetermined |

## What is missing

Absence records whose key names this concept (13, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0219 — `concept_jurisdiction:CPT-inter-model-agreement|AU` — No claim about CPT-inter-model-agreement concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0220 — `concept_jurisdiction:CPT-inter-model-agreement|BR` — No claim about CPT-inter-model-agreement concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0221 — `concept_jurisdiction:CPT-inter-model-agreement|CA` — No claim about CPT-inter-model-agreement concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0222 — `concept_jurisdiction:CPT-inter-model-agreement|CN` — No claim about CPT-inter-model-agreement concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0223 — `concept_jurisdiction:CPT-inter-model-agreement|DE` — No claim about CPT-inter-model-agreement concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0224 — `concept_jurisdiction:CPT-inter-model-agreement|GB` — No claim about CPT-inter-model-agreement concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0225 — `concept_jurisdiction:CPT-inter-model-agreement|KR` — No claim about CPT-inter-model-agreement concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0226 — `concept_jurisdiction:CPT-inter-model-agreement|MY` — No claim about CPT-inter-model-agreement concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0227 — `concept_jurisdiction:CPT-inter-model-agreement|NL` — No claim about CPT-inter-model-agreement concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0228 — `concept_jurisdiction:CPT-inter-model-agreement|NZ` — No claim about CPT-inter-model-agreement concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0229 — `concept_jurisdiction:CPT-inter-model-agreement|RU` — No claim about CPT-inter-model-agreement concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0230 — `concept_jurisdiction:CPT-inter-model-agreement|TR` — No claim about CPT-inter-model-agreement concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0231 — `concept_jurisdiction:CPT-inter-model-agreement|US` — No claim about CPT-inter-model-agreement concerns US. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Can zero-shot LLM deployment be reconciled with the demand for human oversight and domain-specific fine-tuning where consistency is essential?
