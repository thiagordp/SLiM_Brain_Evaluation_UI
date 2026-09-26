---
id: CPT-legal-interpretation-formal-logic-gap
status: candidate
concept_type: normative_concern
definition: The systematic divergence between pragmatic legal interpretation, which draws on background knowledge and contextual inference, and strict formal logic, which demands that all inferences be explicitly grounded in the text, such that a legally sound conclusion may be formally invalid.
run_ids: [RUN-2026-09-25-01]
---

# CPT-legal-interpretation-formal-logic-gap

## What it means

The systematic divergence between pragmatic legal interpretation, which draws on background knowledge and contextual inference, and strict formal logic, which demands that all inferences be explicitly grounded in the text, such that a legally sound conclusion may be formally invalid. A candidate concept coined during the ingest of SRC-0022 and drawn from its claims [CLM-0022-002] [CLM-0022-003] [CLM-0022-004] [CLM-0022-005] [CLM-0022-006] [CLM-0022-008] [CLM-0022-011] [CLM-0022-012] [CLM-0022-013] [CLM-0022-016] [CLM-0022-019].

## Claims

### Descriptive

**general**

- The gap between legal interpretation and formal logic is not unique to contract entailment: it arises wherever AI systems cite sources to support legal claims, which is increasingly common in LLM-assisted drafting, regulatory analysis, and litigation support. — rests on literature (SRC-0022). [CLM-0022-013]
- A model trained to reason like a lawyer will routinely infer more from a cited source than it strictly supports, because that is what legal interpretation does. — rests on abstract considerations (SRC-0022). [CLM-0022-016]

**undetermined**

- Re-annotating ContractNLI examples under a strict formal definition of entailment yields a substantial proportion of label shifts, primarily from ENTAILMENT to NEUTRAL, revealing a systematic gap between pragmatic legal interpretation and strict formal entailment. — rests on factual basis (SRC-0022). [CLM-0022-004]
- A neuro-symbolic SMT pipeline for contract entailment is more conservative than LLM classification, returning a neutral classification whenever explicit grounding is lacking, and thereby surfaces the gap between legal interpretation and formal entailment rather than papering over it. — rests on factual basis (SRC-0022). [CLM-0022-008]

### Interpretative

**general**

- Legal interpretation and formal logic are not different levels of rigor but different modes of reasoning: legal interpretation draws on background knowledge and contextual inference, while formal logic demands that all inferences be explicitly grounded in the text, so a legally sound conclusion may be formally invalid because the norm it relies on is nowhere stated in the contract. — rests on abstract considerations (SRC-0022). [CLM-0022-002]
- The gap between legal interpretation and formal validity is largely invisible in legal AI research, because most systems either mimic legal interpretation through language model training or enforce formal validity through symbolic methods without acknowledging that the two regularly diverge; making this gap explicit, measurable and addressable is one of the most important open problems in legal AI. — rests on abstract considerations (SRC-0022). [CLM-0022-003]
- Constructing minimal pairs — for each case where legal and formal annotation diverge, a minimally modified hypothesis that becomes formally entailed by supplying the missing assumption explicitly — transforms the opaque gap between legal interpretation and formal entailment into a tractable, analyzable object. — rests on factual basis (SRC-0022). [CLM-0022-006]
- The complexity of the minimal axiom set needed to ground an entailment classification is diagnostic: many or complex axioms signal genuine interpretive difficulty, while few and simple axioms suggest confident automated classification. — rests on abstract considerations (SRC-0022). [CLM-0022-012]
- Understanding where and why current legal AI systems break is not a limitation but the foundation of an agenda for trustworthy AI legal reasoning: only by honestly characterizing failure modes can it be identified where AI assistance can be responsibly applied, and systems be built that proactively surface interpretive uncertainty rather than asking lawyers to verify conclusions after the fact. — rests on abstract considerations (SRC-0022). [CLM-0022-019]

**undetermined**

- The label shifts observed when contract entailment examples are re-annotated under a strict formal definition are not errors: they are cases where the original conclusion depends on background legal knowledge or contextual assumptions reasonable for a lawyer to invoke but absent from the text. — rests on factual basis (SRC-0022). [CLM-0022-005]

### Prescriptive

**general**

- A neutral entailment classification need not be a dead end: a system can compute the minimal set of additional axioms sufficient to shift the classification to ENTAILMENT or CONTRADICTION and present them to a legal reviewer with a targeted question, so that whether the lawyer validates the implicit norm or confirms the case is genuinely underspecified, legal expertise is applied precisely where formal methods reach their limit. — rests on abstract considerations (SRC-0022). [CLM-0022-011]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0022 | unknown | 11 | 6 interpretative, 4 descriptive, 1 prescriptive | 6 abstract, 4 factual, 1 literature | general, undetermined |

## What is missing

Absence records whose key names this concept (14, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0313 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|AU` — No claim about CPT-legal-interpretation-formal-logic-gap concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0314 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|BR` — No claim about CPT-legal-interpretation-formal-logic-gap concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0315 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|CA` — No claim about CPT-legal-interpretation-formal-logic-gap concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0316 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|CN` — No claim about CPT-legal-interpretation-formal-logic-gap concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0317 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|DE` — No claim about CPT-legal-interpretation-formal-logic-gap concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0318 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|EU` — No claim about CPT-legal-interpretation-formal-logic-gap concerns EU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0319 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|GB` — No claim about CPT-legal-interpretation-formal-logic-gap concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0320 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|KR` — No claim about CPT-legal-interpretation-formal-logic-gap concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0321 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|MY` — No claim about CPT-legal-interpretation-formal-logic-gap concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0322 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|NL` — No claim about CPT-legal-interpretation-formal-logic-gap concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0323 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|NZ` — No claim about CPT-legal-interpretation-formal-logic-gap concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0324 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|RU` — No claim about CPT-legal-interpretation-formal-logic-gap concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0325 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|TR` — No claim about CPT-legal-interpretation-formal-logic-gap concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0326 — `concept_jurisdiction:CPT-legal-interpretation-formal-logic-gap|US` — No claim about CPT-legal-interpretation-formal-logic-gap concerns US. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- None recorded at this close-out.
