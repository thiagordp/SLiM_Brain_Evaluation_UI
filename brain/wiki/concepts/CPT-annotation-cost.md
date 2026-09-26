---
id: CPT-annotation-cost
status: emergent
concept_type: normative_concern
definition: The cost and effort of manual annotation of data by experts, a burden that constrains data-driven methods in the legal domain and that automated annotation approaches aim to reduce.
run_ids: [RUN-2026-09-25-01]
---

# CPT-annotation-cost

## What it means

The cost and effort of manual annotation of data by experts, a burden that constrains data-driven methods in the legal domain and that automated annotation approaches aim to reduce. An emergent concept coined during the ingest of SRC-0009 and drawn from its claims [CLM-0009-004] [CLM-0009-012]. Promoted from candidate to emergent at this close-out: claims from 7 sources with no shared author are mapped to it (SRC-0009, SRC-0011, SRC-0012, SRC-0016, SRC-0017, SRC-0018, SRC-0021).

## Claims

### Descriptive

**DE**

- Even with moderate precision, automated top-10 extraction of candidate normative sentences that reduces the review workload from 6,242 sentences to 560 would significantly streamline the manual review of court decisions. — rests on factual basis (SRC-0017). [CLM-0017-010]

**EU**

- Annotations produced automatically by LLMs can be exploited to distil LLM knowledge into much smaller models that obtain comparable results, reducing annotation costs and improving scalability; using a dedicated task-specific classifier for the final extraction of Judicial Interpretative Formulas combines the strengths of LLM prompting with a more transparent and reproducible model, mitigating LLM limitations at deployment. — rests on factual basis (SRC-0009). [CLM-0009-012]

**US**

- A synthetic test suite for statutory tax reasoning can be constructed from SARA by conservatively perturbing numerical values in rules and cases and paraphrasing case texts, minimizing data contamination while preserving legal and structural complexity, and — by applying identical perturbations to textual rules and Prolog programs — yielding precise formal representations and exact solutions without human expert effort. — rests on factual basis (SRC-0021). [CLM-0021-010]

**general**

- Approaches to automated extraction of legal principles face two main drawbacks: data-driven methods require costly annotation, while LLM-based methods often lack stability, transparency, and reproducibility, which are essential in the legal domain. — rests on literature (SRC-0009). [CLM-0009-004]
- For a given legal question there may exist multiple valid syllogistic reasoning paths leading to the same conclusion, and annotating diverse reasoning paths for supervised fine-tuning is expensive and labor-intensive, particularly in the legal domain where expert annotation is required. — rests on abstract considerations (SRC-0011). (same proposition also asserted by SRC-0016) [CLM-0011-006] [CLM-0016-004]
- Manual review of court decisions by legal experts to identify and extract normative statements related to specific traffic rules ensures high accuracy but is highly time-consuming and labor-intensive, and as the number of court decisions grows there is an urgent need for more efficient methods of extracting the implicit rules they contain. — rests on literature (SRC-0017). [CLM-0017-002]

**undetermined**

- Increasing the size of the instruction fine-tuning dataset improves a license-compliance foundation model's performance but with diminishing returns: median Prediction Agreement rises from 39.3% to 64.3% as the fine-tuning dataset expands from 100 to 450 licenses, with the most notable improvement between 100 and 250 licenses and performance gains tapering off beyond 300 licenses. — rests on factual basis (SRC-0012). [CLM-0012-012]

### Predictive

**general**

- In the absence of predefined factors from courts or legislative bodies, legal scholars manually analyze hundreds of cases to identify factors, a process that is highly time-consuming and costly; large-language-model-based factor discovery could enable a more efficient process of identifying factor representations of legal domain cases. — rests on abstract considerations (SRC-0018). [CLM-0018-011]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0008 holds “Automatic annotation of court decisions by a large language model is highly reproducible: across five iterations on the same pool of texts …” [CLM-0008-010]; SRC-0009 holds “Approaches to automated extraction of legal principles face two main drawbacks: data-driven methods require costly annotation, while …” [CLM-0009-004]. Note: Evidence that automatic LLM annotation of court decisions is highly reproducible across repeated runs with identical parameters (average Cohen's Kappa 0.82) gives a reason against the drawback that LLM-based methods lack reproducibility.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0009 | 2025 | 2 | 2 descriptive | 1 literature, 1 factual | EU, general |
| SRC-0011 | 2025 | 1 | 1 descriptive | 1 abstract | general |
| SRC-0012 | 2025 | 1 | 1 descriptive | 1 factual | undetermined |
| SRC-0016 | 2024 | 1 | 1 descriptive | 1 abstract | general |
| SRC-0017 | 2024 | 2 | 2 descriptive | 1 literature, 1 factual | DE, general |
| SRC-0018 | 2024 | 1 | 1 predictive | 1 abstract | general |
| SRC-0021 | unknown | 1 | 1 descriptive | 1 factual | US |

## What is missing

Absence records whose key names this concept (11, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0045 — `concept_jurisdiction:CPT-annotation-cost|AU` — No claim about CPT-annotation-cost concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0046 — `concept_jurisdiction:CPT-annotation-cost|BR` — No claim about CPT-annotation-cost concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0047 — `concept_jurisdiction:CPT-annotation-cost|CA` — No claim about CPT-annotation-cost concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0048 — `concept_jurisdiction:CPT-annotation-cost|CN` — No claim about CPT-annotation-cost concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0049 — `concept_jurisdiction:CPT-annotation-cost|GB` — No claim about CPT-annotation-cost concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0050 — `concept_jurisdiction:CPT-annotation-cost|KR` — No claim about CPT-annotation-cost concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0051 — `concept_jurisdiction:CPT-annotation-cost|MY` — No claim about CPT-annotation-cost concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0052 — `concept_jurisdiction:CPT-annotation-cost|NL` — No claim about CPT-annotation-cost concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0053 — `concept_jurisdiction:CPT-annotation-cost|NZ` — No claim about CPT-annotation-cost concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0054 — `concept_jurisdiction:CPT-annotation-cost|RU` — No claim about CPT-annotation-cost concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0055 — `concept_jurisdiction:CPT-annotation-cost|TR` — No claim about CPT-annotation-cost concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Is LLM annotation's instability a general property or an artifact of particular models and settings?
