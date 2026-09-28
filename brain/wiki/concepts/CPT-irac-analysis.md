---
id: CPT-irac-analysis
status: candidate
concept_type: legal_task
definition: The structured method of legal analysis proceeding through Issue, Rule, Application and Conclusion, used by legal professionals and law schools to organise the analysis of a legal scenario.
run_ids: [RUN-2026-09-25-01]
---

# CPT-irac-analysis

## What it means

The structured method of legal analysis proceeding through Issue, Rule, Application and Conclusion, used by legal professionals and law schools to organise the analysis of a legal scenario. A candidate concept coined during the ingest of SRC-0015 and drawn from its claims [CLM-0015-001] [CLM-0015-003] [CLM-0015-005] [CLM-0015-008] [CLM-0015-011].

## Claims

### Descriptive

**MY+AU**

- SIRAC is the first semi-structured IRAC corpus: 50 legal scenarios pertaining to the Contract Act Malaysia and the Australian Social Act, each annotated by senior law students with a complete IRAC analysis codified in a semi-structured language interpretable by both machines and legal professionals. — rests on factual basis (SRC-0015). [CLM-0015-001]
- ChatGPT benefits from adding similar example scenarios with IRAC analysis to the prompt during in-context learning only if similar scenarios can be found: with the most similar example added, the quality of its reasoning paths improved by 27.5%, especially for Australian Social Act scenarios, and the F1 score on the analysis part changed from 0.34 to 0.66. — rests on factual basis (SRC-0015). [CLM-0015-005]
- Although ChatGPT can produce correct conclusions in IRAC analysis of legal scenarios, its analysis in the Application part is mostly not aligned with the analyses of legal professionals, and its references to law and precedents are often missing or incorrect. — rests on factual basis (SRC-0015). [CLM-0015-008]

**MY+AU+US**

- Without IRAC analysis from legal professionals, ChatGPT achieves an average F1 of 0.49 for answering the legal questions of legal scenarios (0.35 on US Internal Revenue Code scenarios, 0.67 on Australian Social Act scenarios, 0.44 on Contract Act Malaysia scenarios), yet fails to produce complete and correct reasoning paths toward the answers for any evaluated scenario, although some of the answers are correct. — rests on factual basis (SRC-0015). [CLM-0015-003]

**general**

- IRAC — standing for Issue, Rule, Application and Conclusion — is the most popular legal analysis methodology used by legal professionals and law schools, applied for solving legal problems in a systematic manner. — rests on literature (SRC-0015). [CLM-0015-011]
- While AI can be a powerful tool in the initial issue-discovery phase of legal reasoning, its greatest challenges and potential lie in the two demanding phases of selecting the correct rule and applying it to the facts of the case, where the highest standards of judicial reasoning are required. — rests on abstract considerations (SRC-0026). [CLM-0026-004]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0015 | unknown | 5 | 5 descriptive | 4 factual, 1 literature | MY, AU, US, general |
| SRC-0026 | 2026 | 1 | 1 descriptive | 1 abstract | general |

## What is missing

Absence records whose key names this concept (16, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0601 — `concept_pair:CPT-irac-analysis|CPT-agentic-systems` — No claim links CPT-irac-analysis to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0602 — `concept_pair:CPT-irac-analysis|CPT-context-granularity` — No claim links CPT-irac-analysis to CPT-context-granularity. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0603 — `concept_pair:CPT-irac-analysis|CPT-deep-learning` — No claim links CPT-irac-analysis to CPT-deep-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0604 — `concept_pair:CPT-irac-analysis|CPT-defeasible-reasoning` — No claim links CPT-irac-analysis to CPT-defeasible-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0605 — `concept_pair:CPT-irac-analysis|CPT-fine-tuning` — No claim links CPT-irac-analysis to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0606 — `concept_pair:CPT-irac-analysis|CPT-human-reinforcement-learning` — No claim links CPT-irac-analysis to CPT-human-reinforcement-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0607 — `concept_pair:CPT-irac-analysis|CPT-llm-as-a-judge` — No claim links CPT-irac-analysis to CPT-llm-as-a-judge. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0608 — `concept_pair:CPT-irac-analysis|CPT-llm-based-annotation` — No claim links CPT-irac-analysis to CPT-llm-based-annotation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0609 — `concept_pair:CPT-irac-analysis|CPT-machine-learning` — No claim links CPT-irac-analysis to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0610 — `concept_pair:CPT-irac-analysis|CPT-neuro-symbolic-hybrid` — No claim links CPT-irac-analysis to CPT-neuro-symbolic-hybrid. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0611 — `concept_pair:CPT-irac-analysis|CPT-prompt-engineering` — No claim links CPT-irac-analysis to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0612 — `concept_pair:CPT-irac-analysis|CPT-question-decomposition` — No claim links CPT-irac-analysis to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0613 — `concept_pair:CPT-irac-analysis|CPT-retrieval-augmented-generation` — No claim links CPT-irac-analysis to CPT-retrieval-augmented-generation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0614 — `concept_pair:CPT-irac-analysis|CPT-syllogistic-reasoning` — No claim links CPT-irac-analysis to CPT-syllogistic-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0615 — `concept_pair:CPT-irac-analysis|CPT-symbolic-rule-based` — No claim links CPT-irac-analysis to CPT-symbolic-rule-based. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0616 — `concept_pair:CPT-irac-analysis|CPT-zero-shot-learning` — No claim links CPT-irac-analysis to CPT-zero-shot-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- None recorded at this close-out.
