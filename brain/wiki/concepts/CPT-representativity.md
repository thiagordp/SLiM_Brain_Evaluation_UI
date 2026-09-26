---
id: CPT-representativity
status: candidate
concept_type: normative_concern
definition: The concern that the perspectives, legal traditions and voices reflected in a dataset, expert pool or system are representative, including of marginalised perspectives.
run_ids: [RUN-2026-09-25-01]
---

# CPT-representativity

## What it means

The concern that the perspectives, legal traditions and voices reflected in a dataset, expert pool or system are representative, including of marginalised perspectives. A candidate concept coined during the ingest of SRC-0005 and drawn from its claims [CLM-0005-007] [CLM-0005-008] [CLM-0005-011] [CLM-0005-019].

## Claims

### Descriptive

**undetermined**

- A judgment-forecasting setup whose input includes the relevant legal framework and which requests the model's assessment (reasoning) as a part of supporting the model's decision is the closest to the real judicial process followed by the ECtHR, compared to the prior legal judgment prediction literature. — rests on literature (SRC-0020). [CLM-0020-017]

### Interpretative

**general**

- Two parameters are important for navigating the design decision about the content of the dataset used to fine-tune an international-law large language model: the perspective of the user and the question of representativity, as key features of what constitutes 'good' international law. — rests on abstract considerations (SRC-0005). [CLM-0005-007]
- The choice of fine-tuning data and retrieval-augmented generation database for an international-law large language model can be represented on a continuum between a narrow, restrictive approach based on a strict reading of the sources of Article 38(1) ICJ Statute — which offers clarity, coherence and predictability but risks perpetuating existing structural features of international law and excluding voices that challenge the status quo — and a broad, inclusive approach incorporating diverse perspectives — which enhances representativity but may lack the formal authority and consistency required for real-world application. — rests on abstract considerations (SRC-0005). [CLM-0005-008]

### Prescriptive

**general**

- The fine-tuning of a legal large language model requires a participative approach in which representativity is conceptualised on at least two axes — the biographies of the interpreters and the values used to justify substantial interpretations — and, along a critical participatory design approach, marginalised profiles should be proactively integrated. — rests on abstract considerations (SRC-0005). [CLM-0005-011]
- The idea of having one or a few large language models for international law should be abandoned; instead, a variety of LLMs should be developed, or a system able to be configured according to distinct sets of data and interpretations of key legal norms. — rests on abstract considerations (SRC-0005). [CLM-0005-019]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0019 holds “Prompt engineering and 'LLM shopping' are anticipated to become the new 'dictionary shopping': confirmation bias and politically motivated …” [CLM-0019-010]; SRC-0005 holds “The idea of having one or a few large language models for international law should be abandoned; instead, a variety of LLMs should be …” [CLM-0005-019]. Note: The prediction that choice among models and prompts enables 'LLM shopping', confirmation bias and politically motivated reasoning gives reasons against the prescription to develop a variety of LLMs configurable to distinct sets of data and interpretations of legal norms.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0005 | 2026 | 4 | 2 interpretative, 2 prescriptive | 4 abstract | general |
| SRC-0020 | 2025 | 1 | 1 descriptive | 1 literature | undetermined |

## What is missing

Absence records whose key names this concept (14, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0466 — `concept_jurisdiction:CPT-representativity|AU` — No claim about CPT-representativity concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0467 — `concept_jurisdiction:CPT-representativity|BR` — No claim about CPT-representativity concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0468 — `concept_jurisdiction:CPT-representativity|CA` — No claim about CPT-representativity concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0469 — `concept_jurisdiction:CPT-representativity|CN` — No claim about CPT-representativity concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0470 — `concept_jurisdiction:CPT-representativity|DE` — No claim about CPT-representativity concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0471 — `concept_jurisdiction:CPT-representativity|EU` — No claim about CPT-representativity concerns EU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0472 — `concept_jurisdiction:CPT-representativity|GB` — No claim about CPT-representativity concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0473 — `concept_jurisdiction:CPT-representativity|KR` — No claim about CPT-representativity concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0474 — `concept_jurisdiction:CPT-representativity|MY` — No claim about CPT-representativity concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0475 — `concept_jurisdiction:CPT-representativity|NL` — No claim about CPT-representativity concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0476 — `concept_jurisdiction:CPT-representativity|NZ` — No claim about CPT-representativity concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0477 — `concept_jurisdiction:CPT-representativity|RU` — No claim about CPT-representativity concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0478 — `concept_jurisdiction:CPT-representativity|TR` — No claim about CPT-representativity concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0479 — `concept_jurisdiction:CPT-representativity|US` — No claim about CPT-representativity concerns US. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Does a plurality of legal LLMs enable representativity, or license model shopping and motivated reasoning?
