---
id: CPT-user-interface-design
status: candidate
concept_type: technical_task
definition: Designing how a system presents its outputs and communicates with its user — the presentation of answers, alternatives, disclaimers, warnings and explanations.
run_ids: [RUN-2026-09-25-01]
---

# CPT-user-interface-design

## What it means

Designing how a system presents its outputs and communicates with its user — the presentation of answers, alternatives, disclaimers, warnings and explanations. A candidate concept coined during the ingest of SRC-0005 and drawn from its claims [CLM-0005-014] [CLM-0005-015] [CLM-0005-016].

## Claims

### Descriptive

**CN**

- Visually presenting the legal-article basis of each sentence of a large language model's legal-advice response helps users understand the advice and verify its reliability, a sentence lacking any legal basis serving as a warning that it may be incorrect; in a user study the legal article basis of the responses was accurately provided for approximately 95% of queries. — rests on factual basis (SRC-0014). [CLM-0014-004]
- Allowing users to interactively select the legal articles a legal large language model uses improves the accuracy and completeness of its responses: in a user study the top three retrieved legal articles were not entirely correct for an average of 83% of queries, but users successfully received correct responses in 80% of cases by selecting relevant legal articles for the model to regenerate its response. — rests on factual basis (SRC-0014). [CLM-0014-005]
- Retrieving relevant legal cases and highlighting the sentences related to the user's query provides users with comprehensive reference information in legal consultation: in a user study the legal case retrieval module proved beneficial for 77% of queries on average, and all users agreed that highlighting pertinent sentences significantly streamlines reading the cases and improves reading efficiency. — rests on factual basis (SRC-0014). [CLM-0014-006]

### Interpretative

**general**

- The spectrum of user-interface design choices for a legal large language model can be conceptualised along an axis between a single-answer design and a panorama design presenting a range of plausible interpretations, and the choice reflects deeper normative commitments about how legal disagreement should be represented and about who — the designer of the LLM or the user — bears responsibility for taking a decision considering those disagreements. — rests on abstract considerations (SRC-0005). [CLM-0005-014]
- Because hallucinations are an integral part of the operation of a probabilistic tool rather than a marginal phenomenon or a technical problem, and their consequences can be serious in law, the design of the user interface is a promising venue to cabin and mitigate hallucinations. — rests on abstract considerations (SRC-0005). [CLM-0005-015]

### Prescriptive

**general**

- A legal large language model should communicate its different stages of reasoning, including which information is grounded in the retrieval database, and its main interpretative choices; it must be configurable to adapt its explanations to the user's mental model, level of knowledge, abilities and needs; and its interface should use counterfactual logic, identifying interpretative crossroads that lead to different results. — rests on literature (SRC-0005). [CLM-0005-016]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0003 holds “A retrieval-augmented fatwa system's source-based response places substantial weight on the inquirer, leaving source verification and …” [CLM-0003-007]; SRC-0014 holds “Allowing users to interactively select the legal articles a legal large language model uses improves the accuracy and completeness of its …” [CLM-0014-005]. Note: That leaving source relevance and verification to the inquirer's judgment is a weight and a bias risk gives a reason against expecting lay article selection to yield accurate advice.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0005 | 2026 | 3 | 2 interpretative, 1 prescriptive | 2 abstract, 1 literature | general |
| SRC-0014 | unknown | 3 | 3 descriptive | 3 factual | CN |

## Open questions

- Can lay users be relied on to select the sources a legal assistant reasons from?
