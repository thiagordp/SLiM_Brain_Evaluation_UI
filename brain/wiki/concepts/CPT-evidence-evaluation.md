---
id: CPT-evidence-evaluation
status: candidate
concept_type: legal_task
definition: The task of assessing evidence — witness testimonies, documents and forensic data — to establish the factual record of a case, including judging the truthfulness of everyday facts and the credibility of witnesses.
run_ids: [RUN-2026-09-28-01]
---

# CPT-evidence-evaluation

## What it means

The task of assessing evidence — witness testimonies, documents and forensic data — to establish the factual record of a case, including judging the truthfulness of everyday facts and the credibility of witnesses. Coined as a candidate during the ingest of SRC-0026 and drawn from its claims [CLM-0026-005] [CLM-0026-006] [CLM-0026-008] [CLM-0026-016]; the retrofit at the close-out of RUN-2026-09-28-01 attached one older claim [CLM-0003-002].

## Claims

### Descriptive

**general**

- Large language models cannot judge the strength of evidence, reconcile competing juristic views, or distinguish between equivocal (ẓannī) and unequivocal (qaṭʿī) proofs; they treat textual inputs without considering evidentiary hierarchy, may present multiple juristic positions without evaluating them, and lack the epistemic calibration required for the assessment of proofs in Islamic law. — rests on abstract considerations (SRC-0003). [CLM-0003-002]
- Evidence evaluation is difficult to improve with techniques like retrieval-augmented generation because legal evidence pertains to the truthfulness of everyday facts: fine-tuning an LLM with legal corpora does not help it answer whether a certain person was in a certain place at a certain time, and LLMs struggle to evaluate the truthfulness of real-world facts, a task often reliant on human experience and credibility assessments. — rests on abstract considerations (SRC-0026). [CLM-0026-005]
- LLMs face a fundamental challenge in evaluating the truthfulness of information such as evidence, as their knowledge is derived from training data and provided context, not from lived experience or an innate sense of real-world plausibility; assessing witness credibility involves non-verbal cues, demeanor, consistency and potential biases that extend far beyond a written transcript, and evaluating real-world plausibility requires common-sense reasoning, an area in which LLMs continue to show significant limitations. — rests on literature (SRC-0026). [CLM-0026-006]
- Establishing the relevant facts of a case is a precondition for identifying the legal issue and determining the applicable law; issues of evidence and law may be intertwined, evidence presented during court proceedings can lead to a situation where the applicable rules change, and there is thus a continuous interaction between the facts and rules that can be difficult for AI to follow. — rests on abstract considerations (SRC-0026). [CLM-0026-016]

### Interpretative

**general**

- An AI system that attempts to render a decision based on insufficient evidence, rather than correctly identifying the issue as 'unproven' and applying burden of proof rules, would fundamentally undermine procedural justice. — rests on abstract considerations (SRC-0026). [CLM-0026-008]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0003 | 2026 | 1 | 1 descriptive | 1 abstract | general |
| SRC-0026 | 2026 | 4 | 3 descriptive, 1 interpretative | 3 abstract, 1 literature | general |

## What is missing

Absence records whose key names this concept (16, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0707 — `concept_pair:CPT-evidence-evaluation|CPT-agentic-systems` — No claim links CPT-evidence-evaluation to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0708 — `concept_pair:CPT-evidence-evaluation|CPT-context-granularity` — No claim links CPT-evidence-evaluation to CPT-context-granularity. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0709 — `concept_pair:CPT-evidence-evaluation|CPT-deep-learning` — No claim links CPT-evidence-evaluation to CPT-deep-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0710 — `concept_pair:CPT-evidence-evaluation|CPT-defeasible-reasoning` — No claim links CPT-evidence-evaluation to CPT-defeasible-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0711 — `concept_pair:CPT-evidence-evaluation|CPT-explicit-reasoning` — No claim links CPT-evidence-evaluation to CPT-explicit-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0712 — `concept_pair:CPT-evidence-evaluation|CPT-human-reinforcement-learning` — No claim links CPT-evidence-evaluation to CPT-human-reinforcement-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0713 — `concept_pair:CPT-evidence-evaluation|CPT-in-context-learning` — No claim links CPT-evidence-evaluation to CPT-in-context-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0714 — `concept_pair:CPT-evidence-evaluation|CPT-llm-as-a-judge` — No claim links CPT-evidence-evaluation to CPT-llm-as-a-judge. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0715 — `concept_pair:CPT-evidence-evaluation|CPT-llm-based-annotation` — No claim links CPT-evidence-evaluation to CPT-llm-based-annotation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0716 — `concept_pair:CPT-evidence-evaluation|CPT-machine-learning` — No claim links CPT-evidence-evaluation to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0717 — `concept_pair:CPT-evidence-evaluation|CPT-neuro-symbolic-hybrid` — No claim links CPT-evidence-evaluation to CPT-neuro-symbolic-hybrid. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0718 — `concept_pair:CPT-evidence-evaluation|CPT-prompt-engineering` — No claim links CPT-evidence-evaluation to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0719 — `concept_pair:CPT-evidence-evaluation|CPT-question-decomposition` — No claim links CPT-evidence-evaluation to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0720 — `concept_pair:CPT-evidence-evaluation|CPT-syllogistic-reasoning` — No claim links CPT-evidence-evaluation to CPT-syllogistic-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0721 — `concept_pair:CPT-evidence-evaluation|CPT-symbolic-rule-based` — No claim links CPT-evidence-evaluation to CPT-symbolic-rule-based. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0722 — `concept_pair:CPT-evidence-evaluation|CPT-zero-shot-learning` — No claim links CPT-evidence-evaluation to CPT-zero-shot-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Can any technique give a model access to the credibility and plausibility judgments that evidence evaluation demands, or is the task bound to human experience?
