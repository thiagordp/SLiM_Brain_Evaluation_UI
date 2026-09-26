---
id: CPT-reasoning-quality
status: emergent
concept_type: normative_concern
definition: The quality of a model's disclosed reasoning — its grounding in the facts of a case and its fidelity to applicable doctrinal standards — assessed as a property distinct from the accuracy of the model's final prediction.
run_ids: [RUN-2026-09-25-01]
---

# CPT-reasoning-quality

## What it means

The quality of a model's disclosed reasoning — its grounding in the facts of a case and its fidelity to applicable doctrinal standards — assessed as a property distinct from the accuracy of the model's final prediction. An emergent concept coined during the ingest of SRC-0020 and drawn from its claims [CLM-0020-001] [CLM-0020-002] [CLM-0020-003] [CLM-0020-004] [CLM-0020-005] [CLM-0020-009] [CLM-0020-010] [CLM-0020-013] [CLM-0020-014] [CLM-0020-015] [CLM-0020-016]. Promoted from candidate to emergent at this close-out: claims from 5 sources with no shared author are mapped to it (SRC-0015, SRC-0020, SRC-0022, SRC-0023, SRC-0024).

## Claims

### Descriptive

**MY+AU**

- ChatGPT's generated IRAC analyses are fluent, but it does not provide enough information such as references to statutes or precedents in its reasoning paths — of 40 evaluated scenarios only one had an analysis with correct references to statutes and precedents, and only two produced high-quality reasoning paths — and its formulation of the analysis is sometimes very confusing and logically inconsistent. — rests on factual basis (SRC-0015). [CLM-0015-007]
- Although ChatGPT can produce correct conclusions in IRAC analysis of legal scenarios, its analysis in the Application part is mostly not aligned with the analyses of legal professionals, and its references to law and precedents are often missing or incorrect. — rests on factual basis (SRC-0015). [CLM-0015-008]

**MY+AU+US**

- Without IRAC analysis from legal professionals, ChatGPT achieves an average F1 of 0.49 for answering the legal questions of legal scenarios (0.35 on US Internal Revenue Code scenarios, 0.67 on Australian Social Act scenarios, 0.44 on Contract Act Malaysia scenarios), yet fails to produce complete and correct reasoning paths toward the answers for any evaluated scenario, although some of the answers are correct. — rests on factual basis (SRC-0015). [CLM-0015-003]

**NL**

- Adding regulatory text to the prompt improves the quality and perceived helpfulness of LLM-generated legal explanations, but does not consistently improve advertisement detection accuracy: the prompting strategy incorporating the most legal knowledge does not always yield the best classification performance. — rests on factual basis (SRC-0023). [CLM-0023-005]
- In LLM-generated legal explanations for advertisement identification, citation-related errors dominate: the most frequent error is the absence of any legal citation (28.57% of annotated explanations), followed by unclear citations (20.71%), while hallucinations of legal citations (2.62%) and of content (2.38%) are rare and occur almost entirely in prompts providing no legal text, where models fabricate citations due to missing legal context. — rests on factual basis (SRC-0023). [CLM-0023-007]
- Undisclosed (hidden) advertisements exhibit the highest rate of mistaken potential cues in LLM explanations (28.57%) and notable unclear-citation errors, with hallucinations appearing more often than in other content categories; these patterns reflect the difficulty of detecting subtle promotions, where models must infer intent from indirect cues and often misidentify which signals indicate sponsorship. — rests on factual basis (SRC-0023). [CLM-0023-008]
- In an expert case analysis of LLM explanations classifying Instagram posts under the Dutch Advertising Code, neither gpt-5-nano nor gemini-2.5-flash-lite was able to generate a cohesive, well-structured legal explanation: the outputs are an amalgam of statements comparable to a rather poorly performing first-year law student, lack systematic tackling of the conditions of the relevant provisions, and while seeming at first sight to have relevance and accuracy are upon closer examination chaotic, incomplete, or simply inaccurate. — rests on factual basis (SRC-0023). [CLM-0023-011]

**general**

- Recently released large language models often follow different, or even wrong, reasoning paths to obtain correct answers — an issue referred to as a misalignment problem between LLMs and humans — and this problem has not previously been investigated in the legal domain. — rests on literature (SRC-0015). [CLM-0015-014]
- Prior research on evaluating LLM outputs has not extended explanation-evaluation frameworks to complex, domain-specific contexts such as legal interpretation in detecting undisclosed advertisements on social media, which is a key gap in compliance detection; a taxonomy of common errors in LLM-generated legal reasoning for this task is a novel addition to regulatory compliance technology. — rests on literature (SRC-0023). [CLM-0023-003]
- Large language models are word-prediction machines that are not engaging in reasoning in the same way humans do, and are not engaging in legal reasoning or legal analysis as traditionally understood when they evaluate cases, statutes or legal arguments. — rests on literature (SRC-0024). [CLM-0024-003]
- Large language models were not designed to engage in legal reasoning and are notoriously bad at it: studies have found that most models do no better than random guessing when asked to measure the precedential relationship between cases, hallucinate about 75% of the time in answering questions about a court's holding, provide inaccurate information in 40% or more of legal reasoning tasks, and deteriorate as tasks require more nuanced understanding of legal issues or texts. — rests on literature (SRC-0024). [CLM-0024-015]

**undetermined**

- OpenAI GPT-5.4 scores far from ideal in legal reasoning on European Court of Human Rights cases concerning ECHR Article 10: it produces structurally complete but substantively shallow analyses, reliably reproducing the doctrinal structure while its substantive reasoning remains shallow. — rests on factual basis (SRC-0020). [CLM-0020-001]
- When evaluating LLM-generated legal reasoning on ECtHR cases, LLM-as-a-Judge evaluators (GPT-5.5, Claude Opus 4.7 and DeepSeek V4 Pro) are internally consistent yet align only weakly with trained human annotators (judge-judge α = 0.41 versus human-human α = 0.09 on comprehensiveness; judge-human ρ = 0.16-0.33): they are reliable but not a valid substitute for human evaluation. — rests on factual basis (SRC-0020). [CLM-0020-002]
- An expert-curated step-by-step reasoning prompt leads GPT-5.4 to more comprehensive legal reasoning on ECtHR Article 10 cases than guide-based or non-curated prompting — a ranking shared by human annotators and LLM judges — but does not result in more accurate predictions. — rests on factual basis (SRC-0020). [CLM-0020-003]
- On class-imbalanced ECtHR Article 10 judgment forecasting, GPT-5.4's predictive accuracy (77-82%, against an always-violation majority baseline of 0.77) reflects the majority class rather than the substantive legal test, and at case level reasoning comprehensiveness and prediction correctness are essentially uncorrelated (r = 0.08). — rests on factual basis (SRC-0020). [CLM-0020-004]
- In GPT-5.4's assessments of ECtHR Article 10 cases, assessing the lawfulness of the interference (step 2) is the step most frequently missed, and the model's reasoning is poorer overall for the later, harder-to-assess steps of legitimate aim and necessity (steps 3 and 4). — rests on factual basis (SRC-0020). [CLM-0020-009]
- GPT-5.4 grounds its factual references in ECtHR case facts reliably — recall restricted to paragraphs present in the facts is 0.81-0.86 and groundedness is 1.00, with no hallucinated paragraph numbers — but hedges by over-citing, referencing about 21 paragraphs per case versus the Court's about 13, a low precision that keeps the factual-reference F1 near 0.51-0.53. — rests on factual basis (SRC-0020). [CLM-0020-010]
- GPT-5.4's errors on ECtHR Article 10 cases recur in a few forms — vague or non-committal conclusions where the Court is firm, over-reliance on sometimes overturned domestic-court findings, shallow proportionality analysis that misses the Court's practical balancing, a majority-class bias toward predicting a violation, and over-citation of factual paragraphs — of which the first three, concerning substantive legal judgment, are the most consequential. — rests on factual basis (SRC-0020). [CLM-0020-013]
- Trained human annotators evaluating LLM legal reasoning agree strongly in raw terms — disagreeing on step occurrence in only 11 of 240 cases (97% exact agreement) and landing within one point of each other 87-91% of the time on 1-5 criteria — while chance-corrected coefficients are low (κ/α = 0.09-0.14), a known artifact of ratings clustering at the top of the scale. — rests on factual basis (SRC-0020). [CLM-0020-015]
- Across three paradigms — pure LLM classification, LLM reasoning over formal logical representations, and a neuro-symbolic pipeline combining LLM formalization with an SMT solver — evaluated over five large language models on contract entailment, formal structure improves accuracy, but accuracy does not imply faithful reasoning: high-performing models succeed by mimicking legal interpretation, including its implicit assumptions, rather than by reasoning formally. — rests on factual basis (SRC-0022). [CLM-0022-007]
- Three failure modes recur in LLM reasoning over contract entailment: assumption injection, where the reasoning silently bridges gaps with unstated inferences; scope laundering, where the reasoning presents informal conclusions as formally grounded; and implicit constraint blindness, where the reasoning overlooks constraints present in formal representations. — rests on factual basis (SRC-0022). [CLM-0022-009]

### Interpretative

**TR**

- A reading of the divergence between model and Court in Tergek v. Türkiye is that LLMs fail to capture the tacit knowledge the ECtHR applies in proportionality analysis — the Court's understanding of the need for a workable system to ensure security in Turkish prisons, which makes the interference reasonable — and the models score low (2) on the proportionality step. — rests on factual basis (SRC-0020). [CLM-0020-014]

**general**

- In legal judgment forecasting, appropriate legal reasoning prevails over predictive accuracy: a wrong prediction can arise from genuine ambiguity, narrative complexity, lack of context or subjectivity, whereas appropriate reasoning is the legally meaningful virtue that legitimises juridical bodies in democratic societies. — rests on abstract considerations (SRC-0020). [CLM-0020-016]

### Prescriptive

**general**

- The research community should not rely solely on automated LLM-based evaluation of legal reasoning, and should not treat task accuracy as a proxy for reasoning quality. — rests on factual basis (SRC-0020). [CLM-0020-005]
- Not all errors in LLM-generated explanations are equally harmful for content moderation: vague reasoning may be tolerable, but fabricated citations or misapplied provisions threaten procedural fairness, and integrating severity-sensitive auditing into compliance monitoring would allow regulators to triage high-risk cases while ensuring that enforcement remains both effective and legitimate. — rests on abstract considerations (SRC-0023). [CLM-0023-014]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0020 holds “OpenAI GPT-5.4 scores far from ideal in legal reasoning on European Court of Human Rights cases concerning ECHR Article 10: it produces …” [CLM-0020-001]; SRC-0011 holds “Although existing large language models can generate responses to legal questions, they fail to perform explicit syllogistic reasoning, …” [CLM-0011-002]. Note: The finding that a recent top-tier LLM reliably reproduces a structurally complete doctrinal analysis gives reasons against the claim that existing LLMs produce implicit and unstructured answers lacking explicit reasoning steps.
- SRC-0020 holds “An expert-curated step-by-step reasoning prompt leads GPT-5.4 to more comprehensive legal reasoning on ECtHR Article 10 cases than …” [CLM-0020-003]; SRC-0015 holds “Providing ChatGPT with correct human-written intermediate reasoning paths progressively improves its final answers to legal scenario …” [CLM-0015-004]. Note: The finding that an expert-curated reasoning strategy yields more comprehensive reasoning but no gain in predictive accuracy gives reasons against expecting expert-provided reasoning guidance to improve an LLM's final answers, as found with human-written IRAC reasoning paths.
- SRC-0023 holds “Adding regulatory text to the prompt improves the quality and perceived helpfulness of LLM-generated legal explanations, but does not …” [CLM-0023-005]; SRC-0018 holds “There is a need to incorporate fundamental legal knowledge into large language model prompting for more accurate and relevant discovery of …” [CLM-0018-008]. Note: The finding that incorporating legal knowledge into the prompt improves explanations but not detection accuracy gives a reason against expecting accuracy gains from adding fundamental legal knowledge to LLM prompting.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0015 | unknown | 4 | 4 descriptive | 3 factual, 1 literature | MY+AU, MY+AU+US, general |
| SRC-0020 | 2025 | 11 | 8 descriptive, 1 prescriptive, 2 interpretative | 10 factual, 1 abstract | TR, general, undetermined |
| SRC-0022 | unknown | 2 | 2 descriptive | 2 factual | undetermined |
| SRC-0023 | unknown | 6 | 5 descriptive, 1 prescriptive | 1 literature, 4 factual, 1 abstract | NL, general |
| SRC-0024 | unknown | 2 | 2 descriptive | 2 literature | general |

## What is missing

Absence records whose key names this concept (9, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0457 — `concept_jurisdiction:CPT-reasoning-quality|BR` — No claim about CPT-reasoning-quality concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0458 — `concept_jurisdiction:CPT-reasoning-quality|CA` — No claim about CPT-reasoning-quality concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0459 — `concept_jurisdiction:CPT-reasoning-quality|CN` — No claim about CPT-reasoning-quality concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0460 — `concept_jurisdiction:CPT-reasoning-quality|DE` — No claim about CPT-reasoning-quality concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0461 — `concept_jurisdiction:CPT-reasoning-quality|EU` — No claim about CPT-reasoning-quality concerns EU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0462 — `concept_jurisdiction:CPT-reasoning-quality|GB` — No claim about CPT-reasoning-quality concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0463 — `concept_jurisdiction:CPT-reasoning-quality|KR` — No claim about CPT-reasoning-quality concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0464 — `concept_jurisdiction:CPT-reasoning-quality|NZ` — No claim about CPT-reasoning-quality concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0465 — `concept_jurisdiction:CPT-reasoning-quality|RU` — No claim about CPT-reasoning-quality concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Have newer models overtaken the finding that LLM legal answers lack explicit doctrinal structure?
- Does supplying better reasoning paths improve conclusions, or only the reasoning's appearance?
- Does injecting legal knowledge into prompts improve legal accuracy, or only the plausibility of explanations?
