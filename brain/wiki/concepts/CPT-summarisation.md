---
id: CPT-summarisation
status: anchor
concept_type: technical_task
definition: The technical task of condensing legal documents while preserving what matters in them.
run_ids: [RUN-2026-09-25-01]
---

# CPT-summarisation

## What it means

The technical task of condensing legal documents while preserving what matters in them. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0004-005] [CLM-0004-006] [CLM-0004-007].

## Claims

### Descriptive

**KR**

- Incorporating a high-level community summary consisting of legal provision titles improves the robustness of long-context-window large language model provision retrieval to prompt variations, narrowing the accuracy gap between prompt variants from 5.27 to 1.17 percentage points, but it does not yield the highest performance: its primary effect is to ensure consistency in search results rather than directly enhancing accuracy. — rests on factual basis (SRC-0004). [CLM-0004-005]
- Providing a high-level community summary of provision titles reduces the navigation effort of a long-context-window large language model during exhaustive legal provision search: the average number of referenced provisions per inquiry fell from 10.70 to 7.62 and the average longest multi-hop sequence from 3.35 to 2.91 hops, suggesting that the summary helps minimize unnecessary navigation and exploration across different documents. — rests on factual basis (SRC-0004). [CLM-0004-006]
- Using a high-level community summary significantly increases the execution time of long-context-window large language model provision search - by a factor of 1.24 for exhaustive search - even though token usage is only 1.02 times higher; this may be attributed to the model repeatedly referencing the entire summary for each hop. — rests on factual basis (SRC-0004). [CLM-0004-007]

**US**

- Generative AI can be used effectively in the rulemaking process for tasks such as preparing summaries or plain-English versions of rulemaking documents, organizing and summarizing public comments, identifying trends in scientific studies or petitions for rules, and some minor drafting tasks, but it is a poor tool for tasks that require legal analysis, such as identifying 'unlawful' regulations. — rests on literature (SRC-0024). [CLM-0024-001]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0024 holds “Generative AI can be used effectively in the rulemaking process for tasks such as preparing summaries or plain-English versions of …” [CLM-0024-001]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: The contention that LLMs are a poor tool for tasks requiring legal analysis gives reasons against the contention that LLMs are uniquely suited for legal tasks where rule interpretation, justification and flexible reasoning are essential.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0004 | unknown | 3 | 3 descriptive | 3 factual | KR |
| SRC-0024 | unknown | 1 | 1 descriptive | 1 literature | US |

## Open questions

- Which side of the boundary between clerical assistance and legal analysis do current LLM deployments actually sit on?
