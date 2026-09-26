---
id: CPT-multi-hop-search
status: candidate
concept_type: technical_task
definition: Retrieving the information needed to answer an inquiry through successive logical steps (hops) applied to the provided documents, whether within a single document (intra-document hops) or across multiple documents (cross-document hops), as required by cross-referenced legal corpora.
run_ids: [RUN-2026-09-25-01]
---

# CPT-multi-hop-search

## What it means

Retrieving the information needed to answer an inquiry through successive logical steps (hops) applied to the provided documents, whether within a single document (intra-document hops) or across multiple documents (cross-document hops), as required by cross-referenced legal corpora. A candidate concept coined during the ingest of SRC-0004 and drawn from its claims [CLM-0004-006] [CLM-0004-010].

## Claims

### Descriptive

**KR**

- Providing a high-level community summary of provision titles reduces the navigation effort of a long-context-window large language model during exhaustive legal provision search: the average number of referenced provisions per inquiry fell from 10.70 to 7.62 and the average longest multi-hop sequence from 3.35 to 2.91 hops, suggesting that the summary helps minimize unnecessary navigation and exploration across different documents. — rests on factual basis (SRC-0004). [CLM-0004-006]

### Predictive

**KR**

- Because a long-context-window large language model typically requires fewer than three hops to locate relevant legal provisions, predefining the top three related provisions could help reduce token costs while maintaining high accuracy in legal interpretation tasks. — rests on factual basis (SRC-0004). [CLM-0004-010]

## Where papers disagree

No ATTACKS edge touches the claims mapped to this concept.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0004 | unknown | 2 | 1 descriptive, 1 predictive | 2 factual | KR |

## Open questions

- None recorded at this close-out.
