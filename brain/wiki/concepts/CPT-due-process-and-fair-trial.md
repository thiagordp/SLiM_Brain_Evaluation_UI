---
id: CPT-due-process-and-fair-trial
status: anchor
concept_type: normative_concern
definition: The concern with procedural fairness — defensible, contestable decisions and fair procedure — when automated analysis feeds enforcement or adjudication.
run_ids: [RUN-2026-09-25-01]
---

# CPT-due-process-and-fair-trial

## What it means

The concern with procedural fairness — defensible, contestable decisions and fair procedure — when automated analysis feeds enforcement or adjudication. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0023-013] [CLM-0023-014].

## Claims

### Interpretative

**general**

- The judicial process is bound by a set of imperatives — impartiality, legal certainty, transparency, and the justifiability and controllability of every step of decision-making — which are not mere aspirations but functional requirements of a legitimate legal system, and these requirements are largely common regardless of how legal argumentation is theoretically or practically constructed. — rests on abstract considerations (SRC-0026). [CLM-0026-003]
- An AI system that attempts to render a decision based on insufficient evidence, rather than correctly identifying the issue as 'unproven' and applying burden of proof rules, would fundamentally undermine procedural justice. — rests on abstract considerations (SRC-0026). [CLM-0026-008]
- The principle of procedural fairness dictates that if an AI's output is to be used as evidence or to support a judicial decision, the process that generated that output must be transparent and open to challenge: the specific prompt used to generate a legal analysis becomes a piece of discoverable evidence, and the choice of a particular AI model is a methodological decision comparable to an expert witness selecting a specific scientific instrument, necessitating a transparency that extends beyond the final output to the entire generative process. — rests on abstract considerations (SRC-0026). [CLM-0026-017]

### Prescriptive

**general**

- High classification accuracy does not ensure trustworthy enforcement of advertising rules: an LLM that labels a post correctly but cites irrelevant or fabricated legal provisions cannot satisfy procedural fairness standards, so platforms using LLMs for detection must pair performance metrics with legal-reasoning audits to ensure that decisions are not only correct but also defensible. — rests on factual basis (SRC-0023). [CLM-0023-013]
- Not all errors in LLM-generated explanations are equally harmful for content moderation: vague reasoning may be tolerable, but fabricated citations or misapplied provisions threaten procedural fairness, and integrating severity-sensitive auditing into compliance monitoring would allow regulators to triage high-risk cases while ensuring that enforcement remains both effective and legitimate. — rests on abstract considerations (SRC-0023). [CLM-0023-014]
- AI-assisted adjudication must include system-design features for procedural fairness: audit trails recording all inputs, outputs and intermediate reasoning steps of the AI as a discoverable record — a legal necessity if AI outputs are to be contestable evidence in court; clear disclosure to the parties of an AI system's role in judicial decisions; and contestability with human oversight, so that there is always an avenue for a human decision-maker to review and, if necessary, override the AI's output. — rests on abstract considerations (SRC-0026). [CLM-0026-019]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0024 holds “Having a human in the loop to review the conclusions reached by a large language model does not make an agency's action reasonable, since the human …” [CLM-0024-022]; SRC-0026 holds “AI-assisted adjudication must include system-design features for procedural fairness: audit trails recording all inputs, outputs and intermediate …” [CLM-0026-019]. Note: The claim that a human in the loop cannot recreate or verify a model's reasoning and so does not make reliance on it reasonable gives reasons against human review and override sufficing as a procedural-fairness safeguard.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0023 | unknown | 2 | 2 prescriptive | 1 factual, 1 abstract | general |
| SRC-0026 | 2026 | 4 | 3 interpretative, 1 prescriptive | 4 abstract | general |

## What is missing

Absence records whose key names this concept (14, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0159 — `concept_jurisdiction:CPT-due-process-and-fair-trial|AU` — No claim about CPT-due-process-and-fair-trial concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0160 — `concept_jurisdiction:CPT-due-process-and-fair-trial|BR` — No claim about CPT-due-process-and-fair-trial concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0161 — `concept_jurisdiction:CPT-due-process-and-fair-trial|CA` — No claim about CPT-due-process-and-fair-trial concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0162 — `concept_jurisdiction:CPT-due-process-and-fair-trial|CN` — No claim about CPT-due-process-and-fair-trial concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0163 — `concept_jurisdiction:CPT-due-process-and-fair-trial|DE` — No claim about CPT-due-process-and-fair-trial concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0164 — `concept_jurisdiction:CPT-due-process-and-fair-trial|EU` — No claim about CPT-due-process-and-fair-trial concerns EU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0165 — `concept_jurisdiction:CPT-due-process-and-fair-trial|GB` — No claim about CPT-due-process-and-fair-trial concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0166 — `concept_jurisdiction:CPT-due-process-and-fair-trial|KR` — No claim about CPT-due-process-and-fair-trial concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0167 — `concept_jurisdiction:CPT-due-process-and-fair-trial|MY` — No claim about CPT-due-process-and-fair-trial concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0168 — `concept_jurisdiction:CPT-due-process-and-fair-trial|NL` — No claim about CPT-due-process-and-fair-trial concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0169 — `concept_jurisdiction:CPT-due-process-and-fair-trial|NZ` — No claim about CPT-due-process-and-fair-trial concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0170 — `concept_jurisdiction:CPT-due-process-and-fair-trial|RU` — No claim about CPT-due-process-and-fair-trial concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0171 — `concept_jurisdiction:CPT-due-process-and-fair-trial|TR` — No claim about CPT-due-process-and-fair-trial concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0172 — `concept_jurisdiction:CPT-due-process-and-fair-trial|US` — No claim about CPT-due-process-and-fair-trial concerns US. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- None recorded at this close-out.
