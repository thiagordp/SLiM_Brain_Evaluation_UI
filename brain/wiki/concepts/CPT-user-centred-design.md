---
id: CPT-user-centred-design
status: candidate
concept_type: normative_concern
definition: The requirement that design decisions for a legal AI system be taken from the perspective of its users — their goals, expertise and contextual constraints.
run_ids: [RUN-2026-09-25-01]
---

# CPT-user-centred-design

## What it means

The requirement that design decisions for a legal AI system be taken from the perspective of its users — their goals, expertise and contextual constraints. A candidate concept coined during the ingest of SRC-0005 and drawn from its claims [CLM-0005-002] [CLM-0005-007] [CLM-0005-012] [CLM-0005-016] [CLM-0005-018].

## Claims

### Interpretative

**general**

- Two parameters are important for navigating the design decision about the content of the dataset used to fine-tune an international-law large language model: the perspective of the user and the question of representativity, as key features of what constitutes 'good' international law. — rests on abstract considerations (SRC-0005). [CLM-0005-007]

### Prescriptive

**general**

- Architectural design choices for a large language model for international law should be made by adopting the user's point of view, with 'what is the LLM for, from the perspective of the user?' as the key question guiding design decisions. — rests on abstract considerations (SRC-0005). [CLM-0005-002]
- If the user of an international-law large language model is looking for answers as to what is allowed or prohibited, its fine-tuning should be oriented towards a majority position on the interpretation of key legal norms; if the user is looking for frontier interpretations of specific norms, the reinforcement learning should guide the machine to consider minority interpretations. — rests on abstract considerations (SRC-0005). [CLM-0005-012]
- A legal large language model should communicate its different stages of reasoning, including which information is grounded in the retrieval database, and its main interpretative choices; it must be configurable to adapt its explanations to the user's mental model, level of knowledge, abilities and needs; and its interface should use counterfactual logic, identifying interpretative crossroads that lead to different results. — rests on literature (SRC-0005). [CLM-0005-016]
- Any benchmark trying to capture (international) legal work should add two layers: the relevance of the context of the users and the promotion of the law as a rich interpretative practice; a large language model cannot be benchmarked in a vacuum, and its performance must be measured on the basis of a specific type of user and context. — rests on abstract considerations (SRC-0005). [CLM-0005-018]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0005 | 2026 | 5 | 4 prescriptive, 1 interpretative | 4 abstract, 1 literature | general |

## What is missing

Absence records whose key names this concept (14, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0529 — `concept_jurisdiction:CPT-user-centred-design|AU` — No claim about CPT-user-centred-design concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0530 — `concept_jurisdiction:CPT-user-centred-design|BR` — No claim about CPT-user-centred-design concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0531 — `concept_jurisdiction:CPT-user-centred-design|CA` — No claim about CPT-user-centred-design concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0532 — `concept_jurisdiction:CPT-user-centred-design|CN` — No claim about CPT-user-centred-design concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0533 — `concept_jurisdiction:CPT-user-centred-design|DE` — No claim about CPT-user-centred-design concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0534 — `concept_jurisdiction:CPT-user-centred-design|EU` — No claim about CPT-user-centred-design concerns EU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0535 — `concept_jurisdiction:CPT-user-centred-design|GB` — No claim about CPT-user-centred-design concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0536 — `concept_jurisdiction:CPT-user-centred-design|KR` — No claim about CPT-user-centred-design concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0537 — `concept_jurisdiction:CPT-user-centred-design|MY` — No claim about CPT-user-centred-design concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0538 — `concept_jurisdiction:CPT-user-centred-design|NL` — No claim about CPT-user-centred-design concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0539 — `concept_jurisdiction:CPT-user-centred-design|NZ` — No claim about CPT-user-centred-design concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0540 — `concept_jurisdiction:CPT-user-centred-design|RU` — No claim about CPT-user-centred-design concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0541 — `concept_jurisdiction:CPT-user-centred-design|TR` — No claim about CPT-user-centred-design concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0542 — `concept_jurisdiction:CPT-user-centred-design|US` — No claim about CPT-user-centred-design concerns US. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- None recorded at this close-out.
