---
id: CPT-llm-human-alignment
status: candidate
concept_type: normative_concern
definition: The degree to which a large language model's reasoning and outputs match those of human experts on the same task; misalignment names the gap between the model's reasoning paths and the analyses humans produce, even when final answers agree.
run_ids: [RUN-2026-09-25-01]
---

# CPT-llm-human-alignment

## What it means

The degree to which a large language model's reasoning and outputs match those of human experts on the same task; misalignment names the gap between the model's reasoning paths and the analyses humans produce, even when final answers agree. A candidate concept coined during the ingest of SRC-0015 and drawn from its claims [CLM-0015-008] [CLM-0015-014].

## Claims

### Descriptive

**MY+AU**

- Although ChatGPT can produce correct conclusions in IRAC analysis of legal scenarios, its analysis in the Application part is mostly not aligned with the analyses of legal professionals, and its references to law and precedents are often missing or incorrect. — rests on factual basis (SRC-0015). [CLM-0015-008]

**general**

- Recently released large language models often follow different, or even wrong, reasoning paths to obtain correct answers — an issue referred to as a misalignment problem between LLMs and humans — and this problem has not previously been investigated in the legal domain. — rests on literature (SRC-0015). [CLM-0015-014]

**undetermined**

- When evaluating LLM-generated legal reasoning on ECtHR cases, LLM-as-a-Judge evaluators (GPT-5.5, Claude Opus 4.7 and DeepSeek V4 Pro) are internally consistent yet align only weakly with trained human annotators (judge-judge α = 0.41 versus human-human α = 0.09 on comprehensiveness; judge-human ρ = 0.16-0.33): they are reliable but not a valid substitute for human evaluation. — rests on factual basis (SRC-0020). [CLM-0020-002]

### Predictive

**general**

- Because LLM judges agree with one another far more than with trained annotators and over-rate the hardest (proportionality) step, using them as the sole arbiter of good legal reasoning risks entrenching a shared model bias under a veneer of consensus. — rests on factual basis (SRC-0020). [CLM-0020-021]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0015 | unknown | 2 | 2 descriptive | 1 factual, 1 literature | MY+AU, general |
| SRC-0020 | 2025 | 2 | 1 descriptive, 1 predictive | 2 factual | general, undetermined |

## What is missing

Absence records whose key names this concept (12, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0366 — `concept_jurisdiction:CPT-llm-human-alignment|BR` — No claim about CPT-llm-human-alignment concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0367 — `concept_jurisdiction:CPT-llm-human-alignment|CA` — No claim about CPT-llm-human-alignment concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0368 — `concept_jurisdiction:CPT-llm-human-alignment|CN` — No claim about CPT-llm-human-alignment concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0369 — `concept_jurisdiction:CPT-llm-human-alignment|DE` — No claim about CPT-llm-human-alignment concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0370 — `concept_jurisdiction:CPT-llm-human-alignment|EU` — No claim about CPT-llm-human-alignment concerns EU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0371 — `concept_jurisdiction:CPT-llm-human-alignment|GB` — No claim about CPT-llm-human-alignment concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0372 — `concept_jurisdiction:CPT-llm-human-alignment|KR` — No claim about CPT-llm-human-alignment concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0373 — `concept_jurisdiction:CPT-llm-human-alignment|NL` — No claim about CPT-llm-human-alignment concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0374 — `concept_jurisdiction:CPT-llm-human-alignment|NZ` — No claim about CPT-llm-human-alignment concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0375 — `concept_jurisdiction:CPT-llm-human-alignment|RU` — No claim about CPT-llm-human-alignment concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0376 — `concept_jurisdiction:CPT-llm-human-alignment|TR` — No claim about CPT-llm-human-alignment concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0377 — `concept_jurisdiction:CPT-llm-human-alignment|US` — No claim about CPT-llm-human-alignment concerns US. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- None recorded at this close-out.
