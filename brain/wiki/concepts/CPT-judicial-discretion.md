---
id: CPT-judicial-discretion
status: emergent
concept_type: normative_concern
definition: The scope for subjective, value-laden choice that judges exercise in interpreting and applying legal texts, including the selection of interpretive sources, methods and relevant context, and the trade-off between such discretion and rule-bound consistency.
run_ids: [RUN-2026-09-25-01, RUN-2026-09-28-01]
---

# CPT-judicial-discretion

## What it means

The scope for subjective, value-laden choice that judges exercise in interpreting and applying legal texts, including the selection of interpretive sources, methods and relevant context, and the trade-off between such discretion and rule-bound consistency. Coined as a candidate during the ingest of SRC-0019 and drawn from its claims [CLM-0019-001] [CLM-0019-005] [CLM-0019-007] [CLM-0019-010] [CLM-0019-011]; promoted to emergent at the close-out of RUN-2026-09-28-01, when claims from three independent sources (SRC-0019, SRC-0024, SRC-0026) were mapped to it.

## Claims

### Descriptive

**US**

- Even if judges consistently used a single prompting method, large language models would not remove human subjectivity from determinations of the ordinary meaning of legal text: they shift the source of bias to other parts of the process, such as model developers' design decisions; and in the more likely scenario of no consistent prompting method, using LLMs will not reduce the role of discretionary choices at all. — rests on abstract considerations (SRC-0019). [CLM-0019-001]
- American statutory interpretation lacks an intelligible, generally accepted and consistently applied theory: judges move among theories such as textualism, purposivism and intentionalism; for almost every canon of interpretation there is a counter-canon pointing the opposite way; courts give no stare decisis effect to interpretive methods; and judges can use the various canons and theories to read statutes in almost any way they desire if a majority of the court agrees. — rests on literature (SRC-0024). [CLM-0024-019]

**general**

- Large language models cannot solve a central problem that dogs all legal interpretation — that judges must decide which relevant context to take into account when defining the meaning of words; deciding which context is relevant to interpreting a particular legal term is a normative choice, often undiscussed, and likely to be outcome determinative. — rests on abstract considerations (SRC-0019). [CLM-0019-005]
- To apply general clauses — legal rules deliberately formulated in an imprecise manner using open-textured terms like 'reasonable', 'fair' or 'unconscionable' — AI cannot be a mere legal formalist: an understanding of social norms, ethics and common sense is required; such clauses are especially challenging for LLMs and cannot be solved simply with better information retrieval, as there is no reference material for general clauses in every context, nor by agentic systems, because the open-textured terminology cannot be broken down into well-defined factors. — rests on abstract considerations (SRC-0026). [CLM-0026-009]
- No single AI technique is a panacea for the demands of legal reasoning; a combination of approaches is required to achieve reliability, transparency and fairness in AI-assisted adjudication, and while techniques such as retrieval-augmented generation, multi-agent systems and neuro-symbolic AI can address specific narrow challenges, they fail to solve the more significant ones that remain, particularly in tasks requiring discretion and transparent, justifiable reasoning. — rests on literature (SRC-0026). [CLM-0026-018]
- The current generation of LLMs excels when legal tasks can be distilled into sophisticated information retrieval and pattern recognition, serving best in cases with abundant reference material, clearly defined concepts as opposed to open-textured standards, and decomposability into narrow, sequential sub-tasks; when these conditions are not met, a fundamental barrier remains — the gap between the probabilistic nature of language models and the principled, choice-driven nature of judicial reasoning. — rests on abstract considerations (SRC-0026). [CLM-0026-025]

**general+EU**

- In cross-border disputes, AI must first distinguish between jurisdiction and applicable law and apply international instruments such as the Brussels I Recast Regulation and the Rome I Regulation; while knowledge retrieval systems can find the relevant regulations, AI systems may struggle to interpret the connecting factors that determine jurisdiction, such as a defendant's habitual residence or where the damage occurred, which normally allow for judicial discretion and context-sensitive application, and a multi-agent decomposition of the problem still relies on the agents' ability to interpret the often ambiguous and complex web of logical dependencies correctly. — rests on legal sources (SRC-0026). [CLM-0026-011]

### Interpretative

**US**

- The premise that a tool can identify an objectively correct answer about whether a regulation is unlawful is flawed: in many legal contexts, especially when interpreting ambiguous statutory language, there is no objectively correct answer, and agencies initially, and then judges, must choose among multiple competing values and interests and make policy decisions to interpret ambiguous legal language. — rests on abstract considerations (SRC-0024). [CLM-0024-013]

### Predictive

**US**

- Given the prevalence of AI hype, the use of large language models threatens to exacerbate textualism's 'scientific' quality, suggesting reproducibility and neutrality while obscuring the ever-present normative choices that go into legal interpretation. — rests on abstract considerations (SRC-0019). [CLM-0019-007]
- Prompt engineering and 'LLM shopping' are anticipated to become the new 'dictionary shopping': confirmation bias and politically motivated reasoning is the most likely outcome of increased adoption of large language models for legal interpretation, and empirical research on judges' use of these new interpretive methods is needed. — rests on literature (SRC-0019). [CLM-0019-010]

**general**

- However the legal world ultimately decides to use large language models, this technology is not going to solve the fundamental issue of trading off between judicial discretion and more rule-bound consistency. — rests on abstract considerations (SRC-0019). [CLM-0019-011]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0019 holds “Prompt engineering and 'LLM shopping' are anticipated to become the new 'dictionary shopping': confirmation bias and politically motivated …” [CLM-0019-010]; SRC-0005 holds “The idea of having one or a few large language models for international law should be abandoned; instead, a variety of LLMs should be …” [CLM-0005-019]. Note: The prediction that choice among models and prompts enables 'LLM shopping', confirmation bias and politically motivated reasoning gives reasons against the prescription to develop a variety of LLMs configurable to distinct sets of data and interpretations of legal norms.
- SRC-0019 holds “Large language models cannot solve a central problem that dogs all legal interpretation — that judges must decide which relevant context to …” [CLM-0019-005]; SRC-0025 holds “Large language models may be the adjudicatory technology that resolves the text-versus-context issue at the practical lawyering scale where …” [CLM-0025-010]. Note: The contention that deciding which context is relevant is a normative, outcome-determinative choice LLMs cannot solve gives reasons against the claim that LLMs may resolve the text-versus-context issue and let judges relax old safeguards.
- SRC-0010 holds “No technical limitation of large language models has yet been found that would convince the community that the models are, in principle, unable to …” [CLM-0010-010]; SRC-0026 holds “The current generation of LLMs excels when legal tasks can be distilled into sophisticated information retrieval and pattern recognition …” [CLM-0026-025]. Note: The claim that no technical limitation has been found showing LLMs in principle unable to perform law-creation and law-interpretation gives reasons against the assertion of a fundamental barrier between probabilistic models and judicial reasoning.
- SRC-0025 holds “Large language models may be the adjudicatory technology that resolves the text-versus-context issue at the practical lawyering scale where it …” [CLM-0025-010]; SRC-0026 holds “The current generation of LLMs excels when legal tasks can be distilled into sophisticated information retrieval and pattern recognition …” [CLM-0026-025]. Note: The claim that LLMs may become the adjudicatory technology resolving the text-versus-context issue at practical scale, letting judges relax old safeguards, gives reasons against a fundamental barrier confining LLMs to retrieval-like legal tasks.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0019 | 2025 | 5 | 2 descriptive, 3 predictive | 4 abstract, 1 literature | US, general |
| SRC-0024 | unknown | 2 | 1 interpretative, 1 descriptive | 1 abstract, 1 literature | US |
| SRC-0026 | 2026 | 4 | 4 descriptive | 2 abstract, 1 legal, 1 literature | general, EU |

## What is missing

Absence records whose key names this concept (12 current and 1 lapsed, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0244 — `concept_jurisdiction:CPT-judicial-discretion|AU` — No claim about CPT-judicial-discretion concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0245 — `concept_jurisdiction:CPT-judicial-discretion|BR` — No claim about CPT-judicial-discretion concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0246 — `concept_jurisdiction:CPT-judicial-discretion|CA` — No claim about CPT-judicial-discretion concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0247 — `concept_jurisdiction:CPT-judicial-discretion|CN` — No claim about CPT-judicial-discretion concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0248 — `concept_jurisdiction:CPT-judicial-discretion|DE` — No claim about CPT-judicial-discretion concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0250 — `concept_jurisdiction:CPT-judicial-discretion|GB` — No claim about CPT-judicial-discretion concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0251 — `concept_jurisdiction:CPT-judicial-discretion|KR` — No claim about CPT-judicial-discretion concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0252 — `concept_jurisdiction:CPT-judicial-discretion|MY` — No claim about CPT-judicial-discretion concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0253 — `concept_jurisdiction:CPT-judicial-discretion|NL` — No claim about CPT-judicial-discretion concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0254 — `concept_jurisdiction:CPT-judicial-discretion|NZ` — No claim about CPT-judicial-discretion concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0255 — `concept_jurisdiction:CPT-judicial-discretion|RU` — No claim about CPT-judicial-discretion concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0256 — `concept_jurisdiction:CPT-judicial-discretion|TR` — No claim about CPT-judicial-discretion concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

### Lapsed

- ABS-0249 — `concept_jurisdiction:CPT-judicial-discretion|EU` — No claim about CPT-judicial-discretion concerns EU. Lapsed 2026-09-28 (RUN-2026-09-28-01): CLM-0026-011 now concerns EU. A lapsed absence is never un-lapsed.

## Open questions

- Does a plurality of legal LLMs enable representativity, or license model shopping and motivated reasoning?
- Can LLMs resolve the choice of relevant context in interpretation, or only relocate it?
