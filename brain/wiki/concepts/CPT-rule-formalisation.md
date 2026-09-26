---
id: CPT-rule-formalisation
status: anchor
concept_type: technical_task
definition: The technical task of turning legal or policy text into explicit, machine-operable rules or logic.
run_ids: [RUN-2026-09-25-01]
---

# CPT-rule-formalisation

## What it means

The technical task of turning legal or policy text into explicit, machine-operable rules or logic. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0001-008] [CLM-0007-002] [CLM-0007-010].

## Claims

### Descriptive

**EU**

- Reformulating GDPR articles into concrete, binary-checkable rule statements identifies concrete compliance indicators, permits functional equivalence via references to established security standards, and reduces interpretive ambiguity. — rests on abstract considerations (SRC-0001). [CLM-0001-008]

**MY+AU**

- SIRAC is the first semi-structured IRAC corpus: 50 legal scenarios pertaining to the Contract Act Malaysia and the Australian Social Act, each annotated by senior law students with a complete IRAC analysis codified in a semi-structured language interpretable by both machines and legal professionals. — rests on factual basis (SRC-0015). [CLM-0015-001]

**general**

- In contrast to prior approaches to generating structured rules from policy documents with large language models, which rely on human-designed schemas and helper functions and thereby constrain reasoning to facts explicitly represented in the input, dynamic rule generation from natural language — leveraging finetuned models and symbolic reasoning to automatically extract governing policy language and generate rules — eliminates the need for human-curated schemas and helper functions, with the intent to offer a scalable and cost-effective solution that reduces manual effort and reliance on frequent LLM inference. — rests on literature (SRC-0007). [CLM-0007-012]
- Four fundamental challenges act as roadblocks to making fully automated privacy compliance checking feasible: vague terms with no computational definition, evolving terminology that does not fit predefined categories, exception patterns that appear contradictory to automated tools, and external legal dependencies not defined in the policy text. — rests on abstract considerations (SRC-0013). [CLM-0013-001]
- Privacy policies use terms, such as 'business operations', that have no computational definition; these terms are intentionally flexible to cover future business needs, whereas formal verification requires precise predicates. — rests on abstract considerations (SRC-0013). [CLM-0013-002]
- Real privacy policies address broader concerns than data confidentiality: they encode legal requirements about appropriate data use, business practices, and user expectations that resist simple formalization. — rests on abstract considerations (SRC-0013). [CLM-0013-003]
- Existing automated privacy policy analysis tools rely on fixed categorization schemes that fail when policies mention novel concepts, and attempting to dynamically expand taxonomies risks creating overlapping categories that break the logical consistency needed for formal reasoning. — rests on literature (SRC-0013). [CLM-0013-005]
- Privacy policies state general rules and then carve out specific exceptions, which appear contradictory to automated tools that treat each statement independently; humans understand that the later statement creates a specific exception to the general rule, but current analyzers struggle to recognize the hierarchical relationship where specific rules override general ones, and manual review shows that most apparent contradictions in policies are actually coherent exception patterns. — rests on literature (SRC-0013). [CLM-0013-006]
- Privacy policies reference external context that is not defined within the policy text, such as which laws apply in each jurisdiction or how an application actually implements its settings; formalizing these statements requires information beyond the policy text itself, and even entity-sensitive analysis cannot determine which specific laws trigger sharing in which contexts. — rests on abstract considerations (SRC-0013). [CLM-0013-007]

**undetermined**

- A hybrid system that pairs a coverage-aware retriever with symbolic rule-based reasoning to surface relevant medical coverage policy language, organize it into explicit facts and rules, and generate auditable rationales minimizes the number of LLM inferences required, achieving a 44% reduction in inference cost alongside a 4.5% improvement in F1 score. — rests on factual basis (SRC-0007). [CLM-0007-002]
- Most failures of LLM-generated symbolic coverage rules stem from two factors: in 73.5% of incorrect cases the correct attribute is not incorporated into the rule creation process — often because when the attribute list is lengthy the model overlooks or 'forgets' attributes appearing later in the input sequence — and in the remaining 26.5% the model fails to generate a sufficient set of rules, so no rule is triggered; careful attribute selection and prompt engineering are therefore important when constructing symbolic rules from complex policy language. — rests on factual basis (SRC-0007). [CLM-0007-010]
- Embedding-based semantic search reduces each verification query over a privacy policy's extracted data practice edges to a small relevant subset - on average 6.4 edges for the TikTok policy and 18.5 for the Meta policy, a 99.38% and 99.50% reduction in the verification problem - enabling tractable formal reasoning by an SMT solver: 23 queries of varying complexity achieved zero timeouts with average query times of 3.39s and 3.91s, and although the Meta policy is 3.9 times larger than the TikTok policy, query times increased by only 1.15 times, demonstrating sub-linear scaling behavior. — rests on factual basis (SRC-0013). [CLM-0013-012]
- The first-order logic formulas produced from full privacy policies remain too complex for SMT solvers: without a semantic search phase reducing the search space, a query would require the SMT solver to reason about thousands of disjunctive clauses, which leads to exponential complexity. — rests on factual basis (SRC-0013). [CLM-0013-013]

### Interpretative

**general**

- Empirical results on statutory tax reasoning suggest that large language models are more reliable as translators of natural language into formal logic than as standalone reasoners, especially as task complexity increases, supporting a principled role for them as translators between natural language and formal representations. — rests on factual basis (SRC-0021). [CLM-0021-005]
- The complexity of the minimal axiom set needed to ground an entailment classification is diagnostic: many or complex axioms signal genuine interpretive difficulty, while few and simple axioms suggest confident automated classification. — rests on abstract considerations (SRC-0022). [CLM-0022-012]

### Prescriptive

**general**

- Privacy policy formalization should embrace rather than abstract away the limitations of legal language: a large language model can identify six key elements of each policy statement - the data sender, receiver, data subject, data type, action performed, and any conditions - and the extracted elements can be encoded as first-order logic, while vague terms are preserved as uninterpreted predicates rather than defined, making the ambiguity explicit for human review. — rests on abstract considerations (SRC-0013). [CLM-0013-009]
- Formalizing legal privacy policy text shows both promise and fundamental limits; rather than attempting full automation, privacy policy analysis should be structured so that formal methods identify clear-cut issues while human expertise resolves genuine ambiguities. — rests on abstract considerations (SRC-0013). [CLM-0013-014]
- A neutral entailment classification need not be a dead end: a system can compute the minimal set of additional axioms sufficient to shift the classification to ENTAILMENT or CONTRADICTION and present them to a legal reviewer with a targeted question, so that whether the lawyer validates the implicit norm or confirms the case is genuinely underspecified, legal expertise is applied precisely where formal methods reach their limit. — rests on abstract considerations (SRC-0022). [CLM-0022-011]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0013 holds “Four fundamental challenges act as roadblocks to making fully automated privacy compliance checking feasible: vague terms with no …” [CLM-0013-001]; SRC-0016 holds “By integrating a compliance assistant into the AI development process, companies can proactively ensure that their models and data …” [CLM-0016-008]. Note: The four roadblocks to fully automated privacy compliance checking — vague terms, evolving terminology, exception patterns, and external legal dependencies — give reasons against the claim that an automated compliance assistant can proactively ensure models and data pipelines comply with complex regulations.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0001 | unknown | 1 | 1 descriptive | 1 abstract | EU |
| SRC-0007 | 2026 | 3 | 3 descriptive | 2 factual, 1 literature | general, undetermined |
| SRC-0013 | 2025 | 10 | 8 descriptive, 2 prescriptive | 6 abstract, 2 literature, 2 factual | general, undetermined |
| SRC-0015 | unknown | 1 | 1 descriptive | 1 factual | MY+AU |
| SRC-0021 | unknown | 1 | 1 interpretative | 1 factual | general |
| SRC-0022 | unknown | 2 | 1 prescriptive, 1 interpretative | 2 abstract | general |

## Open questions

- How far can compliance checking be automated when vague terms, exceptions and external references resist formalization?
