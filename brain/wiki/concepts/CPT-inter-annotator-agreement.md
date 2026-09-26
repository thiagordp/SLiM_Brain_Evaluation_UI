---
id: CPT-inter-annotator-agreement
status: emergent
concept_type: normative_concern
definition: The degree to which independent human annotators assign the same labels or scores to the same items, reported through raw agreement or chance-corrected coefficients, as a measure of the reliability of a human evaluation.
run_ids: [RUN-2026-09-25-01]
---

# CPT-inter-annotator-agreement

## What it means

The degree to which independent human annotators assign the same labels or scores to the same items, reported through raw agreement or chance-corrected coefficients, as a measure of the reliability of a human evaluation. An emergent concept coined during the ingest of SRC-0020 and drawn from its claims [CLM-0020-015]. Promoted from candidate to emergent at this close-out: claims from 5 sources with no shared author are mapped to it (SRC-0008, SRC-0009, SRC-0015, SRC-0020, SRC-0023).

## Claims

### Descriptive

**EU**

- Annotation guidelines for Judicial Interpretative Formulas in CJEU VAT decisions, refined over successive annotation stages, yield almost perfect inter-annotator agreement: Cohen's kappa, measured on an independently annotated document set at paragraph level and restricted to the relevant portions of the judgments, was 0.96. — rests on factual basis (SRC-0009). [CLM-0009-006]

**MY+AU**

- In human evaluation of ChatGPT's IRAC analyses by law students, the questions evaluating the generated assumptions are subjective — a common problem in law education: the Cohen's Kappa inter-annotator agreement score over all evaluation measures was 0.55, rising to 0.75 when the assumption evaluation was excluded. — rests on factual basis (SRC-0015). [CLM-0015-009]

**NL**

- In classifying 1,143 English-language Instagram posts as sponsored or organic content, gpt-5-nano and gemini-2.5-flash-lite perform strongly (F1 up to 0.93), but on the 95 ambiguous posts where human annotators disagreed or expressed uncertainty, overall performance drops significantly, with F1 scores falling by over 10 percentage points compared to the full dataset. — rests on factual basis (SRC-0023). [CLM-0023-004]

**RU**

- Annotating discourse functions in legal texts is a difficult task even for experts, because legal texts allow for multiple interpretations: agreement between two independent human annotators on discourse functions was only 40.65%, lower than the AI-human agreement rate of 53.76%. — rests on factual basis (SRC-0008). [CLM-0008-009]

**undetermined**

- Trained human annotators evaluating LLM legal reasoning agree strongly in raw terms — disagreeing on step occurrence in only 11 of 240 cases (97% exact agreement) and landing within one point of each other 87-91% of the time on 1-5 criteria — while chance-corrected coefficients are low (κ/α = 0.09-0.14), a known artifact of ratings clustering at the top of the scale. — rests on factual basis (SRC-0020). [CLM-0020-015]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0009 holds “Annotation guidelines for Judicial Interpretative Formulas in CJEU VAT decisions, refined over successive annotation stages, yield almost …” [CLM-0009-006]; SRC-0008 holds “Annotating discourse functions in legal texts is a difficult task even for experts, because legal texts allow for multiple interpretations: …” [CLM-0008-009]. Note: Almost perfect inter-annotator agreement (Cohen's kappa 0.96) reached with iteratively refined annotation guidelines gives reasons against the contention that expert agreement on annotating legal texts is inherently low because legal texts allow multiple interpretations.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0008 | 2026 | 1 | 1 descriptive | 1 factual | RU |
| SRC-0009 | 2025 | 1 | 1 descriptive | 1 factual | EU |
| SRC-0015 | unknown | 1 | 1 descriptive | 1 factual | MY+AU |
| SRC-0020 | 2025 | 1 | 1 descriptive | 1 factual | undetermined |
| SRC-0023 | unknown | 1 | 1 descriptive | 1 factual | NL |

## What is missing

Absence records whose key names this concept (9, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0210 — `concept_jurisdiction:CPT-inter-annotator-agreement|BR` — No claim about CPT-inter-annotator-agreement concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0211 — `concept_jurisdiction:CPT-inter-annotator-agreement|CA` — No claim about CPT-inter-annotator-agreement concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0212 — `concept_jurisdiction:CPT-inter-annotator-agreement|CN` — No claim about CPT-inter-annotator-agreement concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0213 — `concept_jurisdiction:CPT-inter-annotator-agreement|DE` — No claim about CPT-inter-annotator-agreement concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0214 — `concept_jurisdiction:CPT-inter-annotator-agreement|GB` — No claim about CPT-inter-annotator-agreement concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0215 — `concept_jurisdiction:CPT-inter-annotator-agreement|KR` — No claim about CPT-inter-annotator-agreement concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0216 — `concept_jurisdiction:CPT-inter-annotator-agreement|NZ` — No claim about CPT-inter-annotator-agreement concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0217 — `concept_jurisdiction:CPT-inter-annotator-agreement|TR` — No claim about CPT-inter-annotator-agreement concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0218 — `concept_jurisdiction:CPT-inter-annotator-agreement|US` — No claim about CPT-inter-annotator-agreement concerns US. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Is low expert agreement on legal annotation inherent to legal text, or a symptom of unrefined guidelines?
