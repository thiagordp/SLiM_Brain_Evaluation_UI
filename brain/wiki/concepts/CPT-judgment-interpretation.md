---
id: CPT-judgment-interpretation
status: anchor
concept_type: interpretation_object_type
definition: Interpretation whose object is a judicial decision.
run_ids: [RUN-2026-09-25-01]
---

# CPT-judgment-interpretation

## What it means

Interpretation whose object is a judicial decision. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0009-002] [CLM-0017-001] [CLM-0017-002].

## Claims

### Descriptive

**DE**

- In zero-shot extraction of normative sentences related to § 6 StVO from German court decisions with GPT-4o, Chain-of-Instructions prompting achieved superior Recall and F2 scores compared to Standard, Chain-of-Thought and Layer-of-Thoughts prompting, extracting 108 of 125 gold normative sentences against 99, 102 and 103 respectively. — rests on factual basis (SRC-0017). [CLM-0017-006]
- The complexity and nuance of legal language in court rulings makes it challenging for GPT-4o to consistently identify and extract the most relevant normative statements: the model occasionally extracts normative statements beyond the intended scope or includes irrelevant details, and even well-designed standard prompts have not consistently enabled it to interpret the content accurately. — rests on factual basis (SRC-0017). [CLM-0017-007]

**general**

- Explicit traffic rules such as speed limits and right-of-way regulations can be directly programmed into automated driving systems, but implicit traffic rules — which emerge from judicial decisions and may not be formally written in statutes — are crucial for autonomous vehicles to navigate ambiguous or unusual driving scenarios. — rests on abstract considerations (SRC-0017). [CLM-0017-001]
- Manual review of court decisions by legal experts to identify and extract normative statements related to specific traffic rules ensures high accuracy but is highly time-consuming and labor-intensive, and as the number of court decisions grows there is an urgent need for more efficient methods of extracting the implicit rules they contain. — rests on literature (SRC-0017). [CLM-0017-002]

### Interpretative

**EU**

- The Court of Justice of the European Union adopts an argumentative style with broad interpretative statements — Judicial Interpretative Formulas, legal texts or standards the CJEU develops over time through self-citation — whose value extends beyond specific issues as they are progressively cited and integrated into EU law; these differ from ratio decidendi in that they are not limited to the elements necessary to reach the Court's conclusion. — rests on literature (SRC-0009). [CLM-0009-002]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0017 holds “In zero-shot extraction of normative sentences related to § 6 StVO from German court decisions with GPT-4o, Chain-of-Instructions prompting …” [CLM-0017-006]; SRC-0004 holds “When a long-context-window large language model retrieves provisions of the Korean Building Act and its subordinate regulations for legal …” [CLM-0004-004]. Note: The finding that detailed step-by-step Chain-of-Instructions prompts outperformed less structured prompts in zero-shot legal extraction gives reasons against the finding that less prompt guidance leads to higher accuracy in LLM-based legal provision retrieval.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0009 | 2025 | 1 | 1 interpretative | 1 literature | EU |
| SRC-0017 | 2024 | 4 | 4 descriptive | 1 abstract, 1 literature, 2 factual | DE, general |

## Open questions

- Does less prompt guidance help or hurt legal extraction — and does the answer depend on the task?
