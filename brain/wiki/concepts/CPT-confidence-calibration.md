---
id: CPT-confidence-calibration
status: emergent
concept_type: technical_task
definition: A system's assessment of its own level of certainty — the alignment of expressed confidence with actual accuracy, and the ability to recognize when available information is insufficient and to abstain rather than answer with unwarranted certainty.
run_ids: [RUN-2026-09-28-01]
---

# CPT-confidence-calibration

## What it means

A system's assessment of its own level of certainty — the alignment of expressed confidence with actual accuracy, and the ability to recognize when available information is insufficient and to abstain rather than answer with unwarranted certainty. Coined as a candidate during the ingest of SRC-0026 and drawn from its claim [CLM-0026-007]; the retrofit at the close-out of RUN-2026-09-28-01 attached two older claims [CLM-0021-013] [CLM-0024-004]; promoted to emergent at the same close-out, when claims from three independent sources (SRC-0021, SRC-0024, SRC-0026) were mapped to it.

## Claims

### Descriptive

**US**

- Validating generated logical programs and deferring uncertain cases to human experts can substantially reduce tax penalties, underscoring the value of explicit reasoning even when full automation is not feasible. — rests on literature (SRC-0021). [CLM-0021-013]

**general**

- The most significant limitation of large language models is their tendency to hallucinate, providing plausible-sounding but inaccurate information — one study found hallucination rates of 69%-88% on legal queries; the models often overstate their confidence in responses, and the hallucination problem persists despite new model versions. — rests on literature (SRC-0024). [CLM-0024-004]
- Applying the burden of proof correctly requires a decision-maker first to assess its own level of certainty and recognize when the evidence is insufficient to meet the required threshold, which points to a critical technical limitation of current models: LLMs are notoriously poor at this form of self-assessment, their confidence scores are often misaligned with their actual accuracy — a problem known as poor calibration — and models frequently exhibit overconfidence. — rests on literature (SRC-0026). [CLM-0026-007]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0021 | unknown | 1 | 1 descriptive | 1 literature | US |
| SRC-0024 | unknown | 1 | 1 descriptive | 1 literature | general |
| SRC-0026 | 2026 | 1 | 1 descriptive | 1 literature | general |

## Open questions

- Is poor calibration treated in the literature as remediable by system design (validation, deferral) or as intrinsic to current models?
