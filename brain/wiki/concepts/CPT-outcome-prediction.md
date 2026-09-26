---
id: CPT-outcome-prediction
status: anchor
concept_type: technical_task
definition: The technical task of forecasting the legal outcome of a case or question.
run_ids: [RUN-2026-09-25-01]
---

# CPT-outcome-prediction

## What it means

The technical task of forecasting the legal outcome of a case or question. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0008-015] [CLM-0018-002] [CLM-0018-003].

## Claims

### Descriptive

**US**

- A semi-automated approach in which a large language model induces legal factors from raw opinions with a human in the loop produces factor representations that can predict case outcomes with moderate success, if not yet as well as expert-defined factors can. — rests on factual basis (SRC-0018). [CLM-0018-002]
- Attempts to fully automate the production of a factor representation of a legal domain from raw opinions using a large language model result in weak to moderate predictive performance; an entirely automated pipeline from raw opinions to a refined factor representation would need improvement and so far performs better with human involvement. — rests on factual basis (SRC-0018). [CLM-0018-003]
- Outcome predictions based on factor sets identified by a large language model using an expert-defined canonical factor representation can come very close in quality to predictions from gold-standard expert annotations, which suggests that the canonical factor representation is robust across annotators. — rests on factual basis (SRC-0018). [CLM-0018-005]
- A large language model will not be able to predict when a statute expressly delegates authority to an agency as envisioned by the Loper Bright majority, because that question has been addressed by only a few courts; even a model trained on all federal court decisions could not pattern-match an answer to a question that few courts have resolved. — rests on legal sources (SRC-0024). [CLM-0024-018]

**general**

- LLM reasoning has been substantially benchmarked in domains like logic, math and code, but its application and quality in demanding legal-oriented tasks, such as legal case forecasting, remain heavily understudied. — rests on literature (SRC-0020). [CLM-0020-018]

**undetermined**

- OpenAI GPT-5.4 scores far from ideal in legal reasoning on European Court of Human Rights cases concerning ECHR Article 10: it produces structurally complete but substantively shallow analyses, reliably reproducing the doctrinal structure while its substantive reasoning remains shallow. — rests on factual basis (SRC-0020). [CLM-0020-001]
- An expert-curated step-by-step reasoning prompt leads GPT-5.4 to more comprehensive legal reasoning on ECtHR Article 10 cases than guide-based or non-curated prompting — a ranking shared by human annotators and LLM judges — but does not result in more accurate predictions. — rests on factual basis (SRC-0020). [CLM-0020-003]
- On class-imbalanced ECtHR Article 10 judgment forecasting, GPT-5.4's predictive accuracy (77-82%, against an always-violation majority baseline of 0.77) reflects the majority class rather than the substantive legal test, and at case level reasoning comprehensiveness and prediction correctness are essentially uncorrelated (r = 0.08). — rests on factual basis (SRC-0020). [CLM-0020-004]
- A dataset of 30 recent European Court of Human Rights cases on ECHR Article 10, officially published in the HUDOC database from April 2025 onwards, together with the results of human and LLM-based evaluations, is released to assess LLMs' capabilities in legal judgment forecasting and reasoning. — rests on factual basis (SRC-0020). [CLM-0020-006]
- GPT-5.4's errors on ECtHR Article 10 cases recur in a few forms — vague or non-committal conclusions where the Court is firm, over-reliance on sometimes overturned domestic-court findings, shallow proportionality analysis that misses the Court's practical balancing, a majority-class bias toward predicting a violation, and over-citation of factual paragraphs — of which the first three, concerning substantive legal judgment, are the most consequential. — rests on factual basis (SRC-0020). [CLM-0020-013]
- A judgment-forecasting setup whose input includes the relevant legal framework and which requests the model's assessment (reasoning) as a part of supporting the model's decision is the closest to the real judicial process followed by the ECtHR, compared to the prior legal judgment prediction literature. — rests on literature (SRC-0020). [CLM-0020-017]

### Interpretative

**general**

- In legal case forecasting, model reasoning is not merely a path to better predictive accuracy but a lens into the model's decision-making — an explainability factor beyond brute-force pattern matching. — rests on abstract considerations (SRC-0020). [CLM-0020-019]

### Predictive

**general**

- Identifying the stable discursive patterns that constitute the logic of legal court decision texts will facilitate the construction of reasoning datasets in legal and other non-STEM domains, and lays a foundation for improving the explainability of large language models in legal decision prediction; the identified function chains can serve as building blocks enabling the automatized reconstruction of court decisions. — rests on abstract considerations (SRC-0008). [CLM-0008-015]

**undetermined**

- A model's tendency to default to the majority outcome could, if deployed for forecasting freedom-of-expression cases, systematically misjudge the minority of cases where restrictions on expression are in fact justified. — rests on factual basis (SRC-0020). [CLM-0020-022]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0020 holds “OpenAI GPT-5.4 scores far from ideal in legal reasoning on European Court of Human Rights cases concerning ECHR Article 10: it produces …” [CLM-0020-001]; SRC-0011 holds “Although existing large language models can generate responses to legal questions, they fail to perform explicit syllogistic reasoning, …” [CLM-0011-002]. Note: The finding that a recent top-tier LLM reliably reproduces a structurally complete doctrinal analysis gives reasons against the claim that existing LLMs produce implicit and unstructured answers lacking explicit reasoning steps.
- SRC-0020 holds “An expert-curated step-by-step reasoning prompt leads GPT-5.4 to more comprehensive legal reasoning on ECtHR Article 10 cases than …” [CLM-0020-003]; SRC-0015 holds “Providing ChatGPT with correct human-written intermediate reasoning paths progressively improves its final answers to legal scenario …” [CLM-0015-004]. Note: The finding that an expert-curated reasoning strategy yields more comprehensive reasoning but no gain in predictive accuracy gives reasons against expecting expert-provided reasoning guidance to improve an LLM's final answers, as found with human-written IRAC reasoning paths.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0008 | 2026 | 1 | 1 predictive | 1 abstract | general |
| SRC-0018 | 2024 | 3 | 3 descriptive | 3 factual | US |
| SRC-0020 | 2025 | 9 | 7 descriptive, 1 interpretative, 1 predictive | 6 factual, 2 literature, 1 abstract | general, undetermined |
| SRC-0024 | unknown | 1 | 1 descriptive | 1 legal | US |

## Open questions

- Have newer models overtaken the finding that LLM legal answers lack explicit doctrinal structure?
- Does supplying better reasoning paths improve conclusions, or only the reasoning's appearance?
