---
id: CPT-assumption-injection
status: candidate
concept_type: normative_concern
definition: The failure mode in which reasoning silently bridges gaps with unstated inferences, presenting assumption-laden conclusions as if they were logically grounded in the source text.
run_ids: [RUN-2026-09-25-01]
---

# CPT-assumption-injection

## What it means

The failure mode in which reasoning silently bridges gaps with unstated inferences, presenting assumption-laden conclusions as if they were logically grounded in the source text. A candidate concept coined during the ingest of SRC-0022 and drawn from its claims [CLM-0022-001] [CLM-0022-009] [CLM-0022-010] [CLM-0022-016] [CLM-0022-018].

## Claims

### Descriptive

**general**

- A model trained to reason like a lawyer will routinely infer more from a cited source than it strictly supports, because that is what legal interpretation does. — rests on abstract considerations (SRC-0022). [CLM-0022-016]
- Because large language models predict how words will be used in context based on past usage, they are particularly ill-suited to weigh and balance competing values and interests in making policy decisions in the same manner as an agency or a judge; they will implicitly make policy decisions without disclosing them, present their conclusions with an air of objectivity, and are likely to be particularly untrustworthy in evaluating the lawfulness of rules where there is no precedent on the scope of statutory authority. — rests on abstract considerations (SRC-0024). [CLM-0024-014]

**undetermined**

- Three failure modes recur in LLM reasoning over contract entailment: assumption injection, where the reasoning silently bridges gaps with unstated inferences; scope laundering, where the reasoning presents informal conclusions as formally grounded; and implicit constraint blindness, where the reasoning overlooks constraints present in formal representations. — rests on factual basis (SRC-0022). [CLM-0022-009]
- In LLM classification of contract entailment, the dominant error across all models is NEUTRAL to ENTAILMENT misclassification, reflecting systematic assumption injection, while ENTAILMENT and CONTRADICTION confusions are rare, indicating that the challenge is insufficient grounding, not logical inconsistency. — rests on factual basis (SRC-0022). [CLM-0022-010]

### Interpretative

**general**

- The central problem of large language models in legal practice is not simply that they hallucinate facts and references; it is that they systematically draw inferences that go beyond what the source text actually supports, presenting assumption-laden conclusions as if they were logically grounded. — rests on abstract considerations (SRC-0022). [CLM-0022-001]

### Prescriptive

**general**

- Rather than using LLM judges or human preferences as feedback, a formal verification tool can be used as a reward signal in training, teaching a model to distinguish formally supportable inferences from assumption-laden ones; when the solver flags an insufficiently grounded claim it also computes the minimal axioms required to ground it, feeding directly into targeted human review at the points where legal interpretation and formal grounding diverge. — rests on abstract considerations (SRC-0022). [CLM-0022-018]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0022 | unknown | 5 | 1 interpretative, 3 descriptive, 1 prescriptive | 3 abstract, 2 factual | general, undetermined |
| SRC-0024 | unknown | 1 | 1 descriptive | 1 abstract | general |

## What is missing

Absence records whose key names this concept (14, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0056 — `concept_jurisdiction:CPT-assumption-injection|AU` — No claim about CPT-assumption-injection concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0057 — `concept_jurisdiction:CPT-assumption-injection|BR` — No claim about CPT-assumption-injection concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0058 — `concept_jurisdiction:CPT-assumption-injection|CA` — No claim about CPT-assumption-injection concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0059 — `concept_jurisdiction:CPT-assumption-injection|CN` — No claim about CPT-assumption-injection concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0060 — `concept_jurisdiction:CPT-assumption-injection|DE` — No claim about CPT-assumption-injection concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0061 — `concept_jurisdiction:CPT-assumption-injection|EU` — No claim about CPT-assumption-injection concerns EU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0062 — `concept_jurisdiction:CPT-assumption-injection|GB` — No claim about CPT-assumption-injection concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0063 — `concept_jurisdiction:CPT-assumption-injection|KR` — No claim about CPT-assumption-injection concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0064 — `concept_jurisdiction:CPT-assumption-injection|MY` — No claim about CPT-assumption-injection concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0065 — `concept_jurisdiction:CPT-assumption-injection|NL` — No claim about CPT-assumption-injection concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0066 — `concept_jurisdiction:CPT-assumption-injection|NZ` — No claim about CPT-assumption-injection concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0067 — `concept_jurisdiction:CPT-assumption-injection|RU` — No claim about CPT-assumption-injection concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0068 — `concept_jurisdiction:CPT-assumption-injection|TR` — No claim about CPT-assumption-injection concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0069 — `concept_jurisdiction:CPT-assumption-injection|US` — No claim about CPT-assumption-injection concerns US. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- None recorded at this close-out.
