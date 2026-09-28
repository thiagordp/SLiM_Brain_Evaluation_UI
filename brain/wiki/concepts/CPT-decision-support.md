---
id: CPT-decision-support
status: anchor
concept_type: legal_task
definition: The legal task of assisting a human decision-maker with retrieval, analysis and preliminary assessment while the decision itself remains human.
run_ids: [RUN-2026-09-25-01]
---

# CPT-decision-support

## What it means

The legal task of assisting a human decision-maker with retrieval, analysis and preliminary assessment while the decision itself remains human. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0003-001] [CLM-0003-008] [CLM-0007-002].

## Claims

### Descriptive

**CN**

- In an A/B test, software IP lawyers using LicenseGPT completed dataset license compliance analyses in an average of 6 seconds per license, compared to 108 seconds without the tool — a 94.44% reduction in time — without compromising accuracy. — rests on factual basis (SRC-0012). [CLM-0012-009]
- Software IP lawyers perceive LicenseGPT as a valuable supplementary tool that enhances efficiency and express willingness to incorporate it into their workflows as an auxiliary resource for initial assessments, while recognizing the need for human oversight and careful validation in complex cases due to limitations in handling complex legal nuances. — rests on factual basis (SRC-0012). [CLM-0012-010]
- Even when legal large language models are combined with legal article retrieval components, the advice given can still be incorrect or baseless: current legal article retrieval models cannot ensure that all relevant legal articles are retrieved and all irrelevant ones left out, and while missed articles reduce the completeness of responses, retrieved irrelevant articles bring noise that leads the models to produce incomplete, incorrect or inconsistent information. — rests on factual basis (SRC-0014). [CLM-0014-001]
- Visually presenting the legal-article basis of each sentence of a large language model's legal-advice response helps users understand the advice and verify its reliability, a sentence lacking any legal basis serving as a warning that it may be incorrect; in a user study the legal article basis of the responses was accurately provided for approximately 95% of queries. — rests on factual basis (SRC-0014). [CLM-0014-004]
- Allowing users to interactively select the legal articles a legal large language model uses improves the accuracy and completeness of its responses: in a user study the top three retrieved legal articles were not entirely correct for an average of 83% of queries, but users successfully received correct responses in 80% of cases by selecting relevant legal articles for the model to regenerate its response. — rests on factual basis (SRC-0014). [CLM-0014-005]
- Retrieving relevant legal cases and highlighting the sentences related to the user's query provides users with comprehensive reference information in legal consultation: in a user study the legal case retrieval module proved beneficial for 77% of queries on average, and all users agreed that highlighting pertinent sentences significantly streamlines reading the cases and improves reading efficiency. — rests on factual basis (SRC-0014). [CLM-0014-006]
- Presenting China's judicial interpretations alongside large language model legal-advice responses can assist users in acquiring a better comprehension of the responses when interpretation is required: in a user study roughly 30% of the provided judicial interpretations served to clarify specific legal terminologies or special cases, while for the remaining 70% users claimed they were already familiar with their content. — rests on factual basis (SRC-0014). [CLM-0014-009]

**general**

- The traceability of a symbolic rule-based coverage system — showing which rule fired and which attribute conditions matched — allows a human reviewer to see exactly which factors contributed to a decision, providing transparency and context; direct prompting of a large language model does not offer this level of traceability and is more prone to hallucinations, making it less reliable for such a task. — rests on factual basis (SRC-0007). [CLM-0007-011]
- Large language models may be sensitive to input perturbation, so that legal consultation responses can be contradictory when inputs differ only slightly, or even when an identical question is asked in a new conversation; this inconsistency can potentially confuse users and result in a lower-quality consultation. — rests on literature (SRC-0014). [CLM-0014-002]
- Relevant legal cases can offer users more in-depth reference information when large language models fail to produce coherent and complete responses, yet a legal case retrieval module has rarely been integrated into existing legal-domain large language models in civil law systems. — rests on literature (SRC-0014). [CLM-0014-003]
- Legal terminology may sometimes be embedded in large language models' legal-advice responses without sufficient explanations, posing potential understanding difficulties for users without domain knowledge. — rests on literature (SRC-0014). [CLM-0014-008]
- For AI to function reliably in judicial decision-making, it must overcome a set of core challenges: selecting the correct legal framework across jurisdictions, generating sound arguments based on the doctrine of the sources of law, distinguishing ratio decidendi from obiter dicta in case law, resolving ambiguity arising from general clauses such as 'reasonableness', managing conflicting legal provisions, and applying the burden of proof correctly. — rests on abstract considerations (SRC-0026). [CLM-0026-002]
- While AI can be a powerful tool in the initial issue-discovery phase of legal reasoning, its greatest challenges and potential lie in the two demanding phases of selecting the correct rule and applying it to the facts of the case, where the highest standards of judicial reasoning are required. — rests on abstract considerations (SRC-0026). [CLM-0026-004]
- Establishing the relevant facts of a case is a precondition for identifying the legal issue and determining the applicable law; issues of evidence and law may be intertwined, evidence presented during court proceedings can lead to a situation where the applicable rules change, and there is thus a continuous interaction between the facts and rules that can be difficult for AI to follow. — rests on abstract considerations (SRC-0026). [CLM-0026-016]

**undetermined**

- A hybrid system that pairs a coverage-aware retriever with symbolic rule-based reasoning to surface relevant medical coverage policy language, organize it into explicit facts and rules, and generate auditable rationales minimizes the number of LLM inferences required, achieving a 44% reduction in inference cost alongside a 4.5% improvement in F1 score. — rests on factual basis (SRC-0007). [CLM-0007-002]
- A neuro-symbolic system supporting medical coverage policy review does not make coverage determinations: human reviewers maintain full adjudication authority, and the system serves as a support tool that finds support from coverage documents and makes the underlying policy logic interpretable, helping humans make informed judgments while the final decision remains in the hands of the human reviewer. — rests on abstract considerations (SRC-0007). [CLM-0007-013]

### Interpretative

**EU**

- LEGAL-BERT may be considered the best model for Judicial Interpretative Formula extraction: it is the most stable and has the best macro F1 score and the best F1 score on the positive class, and its near-best recall on the positive class is particularly relevant for tools intended for legal practitioners, since the presence of additional JIFs is preferable to the absence of fundamental ones — users can easily discard a few irrelevant paragraphs, but cannot know if a crucial JIF is missing. — rests on factual basis (SRC-0009). [CLM-0009-011]

**general**

- Large language models occupy an intermediate position in Islamic legal reasoning: they assist juristic research through retrieval, organization, and structured reasoning, yet they cannot assume the epistemic or ethical responsibilities that shape Islamic legal judgment, and therefore cannot take the role of a mufti or a mujtahid. — rests on literature (SRC-0003). [CLM-0003-001]
- A neuro-symbolic system is a feasible approach to resolving high-volume, low-complexity disputes such as consumer product-defect small claims: an LLM layer operates as an observation engine that reads unstructured inputs and proposes structured facts, while a symbolic layer performs the determinative legal reasoning by handling curated rules and decision tables, a division that delivers both coverage over unstructured inputs and transparent, auditable decisions aligned with core legal maxims. — rests on abstract considerations (SRC-0026). [CLM-0026-021]
- The most effective current role for AI in law can be understood through a dual-application model: as a high-volume assistant for simple cases — where, with only a few points to consider, LLMs can already work well with today's techniques — and as a sophisticated 'sparring partner' for experts in complex matters, where the LLM is not an adjudicator but an invaluable collaborator for the human lawyer or judge, helping to stress-test arguments and enhance the coherence of a legal strategy. — rests on abstract considerations (SRC-0026). [CLM-0026-023]

### Prescriptive

**general**

- Large language models should be deployed in Islamic legal settings as supervised accelerators and synthesizers — assisting retrieval, classification, and preliminary analysis — with domain experts setting the frame, checking the steps, and making the rulings, leaving authoritative judgments to qualified jurists. — rests on abstract considerations (SRC-0003). [CLM-0003-008]
- LLM systems in legal settings should support, not replace, human legal judgment, and automated evaluation of legal reasoning should be validated against, not substituted for, expert assessment. — rests on factual basis (SRC-0020). [CLM-0020-020]
- AI-assisted adjudication must include system-design features for procedural fairness: audit trails recording all inputs, outputs and intermediate reasoning steps of the AI as a discoverable record — a legal necessity if AI outputs are to be contestable evidence in court; clear disclosure to the parties of an AI system's role in judicial decisions; and contestability with human oversight, so that there is always an avenue for a human decision-maker to review and, if necessary, override the AI's output. — rests on abstract considerations (SRC-0026). [CLM-0026-019]
- A framework for judicial AI should organize requirements into four categories — normative and procedural values; doctrinal and reasoning constraints; fact-finding and evidential requirements; and system-level technical properties — scope them to concrete legal domains, specify an operational design obligation for each requirement, and make those obligations testable through benchmark tasks and metrics, with deployment acceptable only if minimum thresholds are met on a bundle of doctrinal, transparency, evidential and procedural metrics. — rests on abstract considerations (SRC-0026). [CLM-0026-022]
- Adoption of AI in adjudication should be staged: first capturing efficiency in simple cases with technology already available today, and thereafter sustaining long-term investment in new methods that handle hierarchy, temporality, and other requirements of legally sound reasoning, thus enabling expansion to complex adjudication in the future; the successful automation of high-volume, procedurally simple cases has the potential to free up significant human resources for more complex legal challenges. — rests on abstract considerations (SRC-0026). [CLM-0026-024]

### Predictive

**general**

- A foundation model fine-tuned for dataset license compliance has the potential to assist AI software developers in managing preliminary license checks before involving legal counsel; by providing timely and accurate guidance on dataset constraints, it can foster effective collaboration between technical and legal teams and prevent costly late-stage rework. — rests on abstract considerations (SRC-0012). [CLM-0012-014]

**undetermined**

- A model's tendency to default to the majority outcome could, if deployed for forecasting freedom-of-expression cases, systematically misjudge the minority of cases where restrictions on expression are in fact justified. — rests on factual basis (SRC-0020). [CLM-0020-022]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0007 holds “The traceability of a symbolic rule-based coverage system — showing which rule fired and which attribute conditions matched — allows a …” [CLM-0007-011]; SRC-0001 holds “Carefully designed prompts can serve as the primary mechanism for guiding legal reasoning in LLM-based systems, offering a scalable, …” [CLM-0001-013]. Note: The contention that direct prompting offers no comparable traceability and is more prone to hallucinations gives reasons against treating carefully designed prompts as a scalable, explainable primary mechanism for guiding legal reasoning in LLM-based systems.
- SRC-0003 holds “A retrieval-augmented fatwa system's source-based response places substantial weight on the inquirer, leaving source verification and …” [CLM-0003-007]; SRC-0014 holds “Allowing users to interactively select the legal articles a legal large language model uses improves the accuracy and completeness of its …” [CLM-0014-005]. Note: That leaving source relevance and verification to the inquirer's judgment is a weight and a bias risk gives a reason against expecting lay article selection to yield accurate advice.
- SRC-0014 holds “Even when legal large language models are combined with legal article retrieval components, the advice given can still be incorrect or …” [CLM-0014-001]; SRC-0016 holds “A retrieval-augmented generation method that preserves the structure of legal texts — dividing a legal document into its pre-defined …” [CLM-0016-006]. Note: The finding that legal article retrieval cannot ensure all relevant articles are retrieved and that retrieved noise leads models to incomplete or incorrect responses gives reasons against the claim that a retrieval-augmented method ensures accurate retrieval and interpretation of relevant provisions.
- SRC-0021 holds “Monolithic large language models are relatively robust to linguistic variation in legal case descriptions: paraphrasing tax cases while …” [CLM-0021-007]; SRC-0014 holds “Large language models may be sensitive to input perturbation, so that legal consultation responses can be contradictory when inputs differ …” [CLM-0014-002]. Note: The finding that monolithic LLMs remain stable under semantics-preserving paraphrases of legal case descriptions gives a reason against the contention that slightly differing inputs make LLM legal responses contradictory, at least for purely linguistic variation.
- SRC-0024 holds “Having a human in the loop to review the conclusions reached by a large language model does not make an agency's action reasonable, since the human …” [CLM-0024-022]; SRC-0026 holds “AI-assisted adjudication must include system-design features for procedural fairness: audit trails recording all inputs, outputs and intermediate …” [CLM-0026-019]. Note: The claim that a human in the loop cannot recreate or verify a model's reasoning and so does not make reliance on it reasonable gives reasons against human review and override sufficing as a procedural-fairness safeguard.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0003 | 2026 | 2 | 1 interpretative, 1 prescriptive | 1 literature, 1 abstract | general |
| SRC-0007 | 2026 | 3 | 3 descriptive | 2 factual, 1 abstract | undetermined, general |
| SRC-0009 | 2025 | 1 | 1 interpretative | 1 factual | EU |
| SRC-0012 | 2025 | 3 | 2 descriptive, 1 predictive | 2 factual, 1 abstract | CN, general |
| SRC-0014 | unknown | 8 | 8 descriptive | 5 factual, 3 literature | CN, general |
| SRC-0020 | 2025 | 2 | 1 prescriptive, 1 predictive | 2 factual | general, undetermined |
| SRC-0026 | 2026 | 8 | 3 descriptive, 3 prescriptive, 2 interpretative | 8 abstract | general |

## What is missing

Absence records whose key names this concept (13, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0571 — `concept_pair:CPT-decision-support|CPT-agentic-systems` — No claim links CPT-decision-support to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0572 — `concept_pair:CPT-decision-support|CPT-context-granularity` — No claim links CPT-decision-support to CPT-context-granularity. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0573 — `concept_pair:CPT-decision-support|CPT-defeasible-reasoning` — No claim links CPT-decision-support to CPT-defeasible-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0574 — `concept_pair:CPT-decision-support|CPT-explicit-reasoning` — No claim links CPT-decision-support to CPT-explicit-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0575 — `concept_pair:CPT-decision-support|CPT-fine-tuning` — No claim links CPT-decision-support to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0576 — `concept_pair:CPT-decision-support|CPT-human-reinforcement-learning` — No claim links CPT-decision-support to CPT-human-reinforcement-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0577 — `concept_pair:CPT-decision-support|CPT-in-context-learning` — No claim links CPT-decision-support to CPT-in-context-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0578 — `concept_pair:CPT-decision-support|CPT-llm-based-annotation` — No claim links CPT-decision-support to CPT-llm-based-annotation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0579 — `concept_pair:CPT-decision-support|CPT-machine-learning` — No claim links CPT-decision-support to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0580 — `concept_pair:CPT-decision-support|CPT-prompt-engineering` — No claim links CPT-decision-support to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0581 — `concept_pair:CPT-decision-support|CPT-question-decomposition` — No claim links CPT-decision-support to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0582 — `concept_pair:CPT-decision-support|CPT-syllogistic-reasoning` — No claim links CPT-decision-support to CPT-syllogistic-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0583 — `concept_pair:CPT-decision-support|CPT-zero-shot-learning` — No claim links CPT-decision-support to CPT-zero-shot-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Can prompt-driven LLM pipelines reach the traceability that symbolic rules offer a human reviewer?
- Can lay users be relied on to select the sources a legal assistant reasons from?
- Does structure-aware retrieval actually remove the retrieval noise that misleads legal RAG systems?
- How sensitive are LLMs to legally irrelevant input variation, and does paraphrase robustness generalize beyond entailment tasks?
