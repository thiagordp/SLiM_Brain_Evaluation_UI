---
id: CPT-legal-factor-discovery
status: candidate
concept_type: technical_task
definition: Inducing a set of legal factors and their definitions for a legal domain from raw case texts, without relying on a pre-existing factor list — as distinct from annotating cases with factors from a canonical list.
run_ids: [RUN-2026-09-25-01]
---

# CPT-legal-factor-discovery

## What it means

Inducing a set of legal factors and their definitions for a legal domain from raw case texts, without relying on a pre-existing factor list — as distinct from annotating cases with factors from a canonical list. A candidate concept coined during the ingest of SRC-0018 and drawn from its claims [CLM-0018-001] [CLM-0018-002] [CLM-0018-003] [CLM-0018-006] [CLM-0018-007] [CLM-0018-008] [CLM-0018-009] [CLM-0018-011].

## Claims

### Descriptive

**US**

- A methodology that leverages large language models can take raw court opinions as input and produce a set of legal factors and associated definitions that effectively represent a legal domain, without using a pre-existing factor list. — rests on factual basis (SRC-0018). [CLM-0018-001]
- A semi-automated approach in which a large language model induces legal factors from raw opinions with a human in the loop produces factor representations that can predict case outcomes with moderate success, if not yet as well as expert-defined factors can. — rests on factual basis (SRC-0018). [CLM-0018-002]
- Attempts to fully automate the production of a factor representation of a legal domain from raw opinions using a large language model result in weak to moderate predictive performance; an entirely automated pipeline from raw opinions to a refined factor representation would need improvement and so far performs better with human involvement. — rests on factual basis (SRC-0018). [CLM-0018-003]
- Legal factors refined entirely by large language models are sometimes too specific and other times too abstract compared to human-refined factors, and these mismatches and varying levels of generality seem to explain the poor quality of the LLM-refined factor representation and its commensurately poor predictive power. — rests on factual basis (SRC-0018). [CLM-0018-006]
- Both humans and large language models tasked with inducing legal factors from court opinions return some factors that are not legally meaningful — such as an officer's training and experience, the duration of a traffic stop, or a canine alert — and the failure of large language models to discount frequently appearing language that is contrary to basic legal knowledge highlights their limitations in the legal domain. — rests on factual basis (SRC-0018). [CLM-0018-007]
- Inducing factors from raw court opinions with large language models shows promise in identifying new factors for pre-defined factor lists: the procedure yielded a plausible candidate — a driver's use of disguise or deception — that could reasonably be categorized as a new factor not on a predefined expert list, or at least as a sub-factor augmenting an existing factor. — rests on factual basis (SRC-0018). [CLM-0018-009]

### Prescriptive

**US**

- There is a need to incorporate fundamental legal knowledge into large language model prompting for more accurate and relevant discovery of legal factors. — rests on factual basis (SRC-0018). [CLM-0018-008]

### Predictive

**general**

- In the absence of predefined factors from courts or legislative bodies, legal scholars manually analyze hundreds of cases to identify factors, a process that is highly time-consuming and costly; large-language-model-based factor discovery could enable a more efficient process of identifying factor representations of legal domain cases. — rests on abstract considerations (SRC-0018). [CLM-0018-011]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0023 holds “Adding regulatory text to the prompt improves the quality and perceived helpfulness of LLM-generated legal explanations, but does not …” [CLM-0023-005]; SRC-0018 holds “There is a need to incorporate fundamental legal knowledge into large language model prompting for more accurate and relevant discovery of …” [CLM-0018-008]. Note: The finding that incorporating legal knowledge into the prompt improves explanations but not detection accuracy gives a reason against expecting accuracy gains from adding fundamental legal knowledge to LLM prompting.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0018 | 2024 | 8 | 6 descriptive, 1 prescriptive, 1 predictive | 7 factual, 1 abstract | US, general |

## Open questions

- Does injecting legal knowledge into prompts improve legal accuracy, or only the plausibility of explanations?
