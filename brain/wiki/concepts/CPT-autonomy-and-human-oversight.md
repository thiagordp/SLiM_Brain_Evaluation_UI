---
id: CPT-autonomy-and-human-oversight
status: anchor
concept_type: normative_concern
definition: The concern with how much decision authority stays with humans — supervision, review, the human in the loop — when automated systems take part in legal work.
run_ids: [RUN-2026-09-25-01]
---

# CPT-autonomy-and-human-oversight

## What it means

The concern with how much decision authority stays with humans — supervision, review, the human in the loop — when automated systems take part in legal work. An anchor concept, given in advance in the grid of `schema/concept.md`; the corpus uses it as the claims below show [CLM-0002-009] [CLM-0003-001] [CLM-0003-007].

## Claims

### Descriptive

**CN**

- Software IP lawyers perceive LicenseGPT as a valuable supplementary tool that enhances efficiency and express willingness to incorporate it into their workflows as an auxiliary resource for initial assessments, while recognizing the need for human oversight and careful validation in complex cases due to limitations in handling complex legal nuances. — rests on factual basis (SRC-0012). [CLM-0012-010]
- Allowing users to interactively select the legal articles a legal large language model uses improves the accuracy and completeness of its responses: in a user study the top three retrieved legal articles were not entirely correct for an average of 83% of queries, but users successfully received correct responses in 80% of cases by selecting relevant legal articles for the model to regenerate its response. — rests on factual basis (SRC-0014). [CLM-0014-005]

**US**

- A semi-automated approach in which a large language model induces legal factors from raw opinions with a human in the loop produces factor representations that can predict case outcomes with moderate success, if not yet as well as expert-defined factors can. — rests on factual basis (SRC-0018). [CLM-0018-002]
- Validating generated logical programs and deferring uncertain cases to human experts can substantially reduce tax penalties, underscoring the value of explicit reasoning even when full automation is not feasible. — rests on literature (SRC-0021). [CLM-0021-013]
- Over the past five years several U.S. states, including Ohio, South Carolina and Virginia, have turned to generative AI to identify outdated, duplicative or confusing rules that could be repealed or revised; each initiative was narrowly focused on such rules and each involved human review of the rules identified for potential repeal or amendment. — rests on factual basis (SRC-0024). [CLM-0024-010]

**general**

- A retrieval-augmented fatwa system's source-based response places substantial weight on the inquirer, leaving source verification and relevance to the user's judgment, and inherits biases created by online visibility: websites with more traffic and content, such as Islamweb, are more likely to appear in retrieved results not because they are more authoritative but because they are more visible. — rests on abstract considerations (SRC-0003). [CLM-0003-007]
- Explainable AI techniques for large language models, such as chain-of-thought explanation, cannot supply the passive contextual information a mufti relies on — intention, social conditions, or local custom — but can show which sources shaped a model's answer and how the model weighed them, supporting scholarly oversight of whether the reasoning aligns with accepted interpretive methods. — rests on abstract considerations (SRC-0003). [CLM-0003-014]
- Full 'transmission principles' in the sense of Contextual Integrity - the complex social norms governing when data sharing is appropriate - are not extracted automatically from privacy policies because they require human judgment about social context and significant human interpretation. — rests on literature (SRC-0013). [CLM-0013-010]
- Most users are not familiar with the existence or extent of the limitations of large language models and have a tendency to put much more faith in their output than it deserves; the ease of use of the models contributes to automation bias, a phenomenon where persons place too much trust in automated systems and do not adequately verify or validate the output. — rests on literature (SRC-0024). [CLM-0024-009]

**undetermined**

- A neuro-symbolic system supporting medical coverage policy review does not make coverage determinations: human reviewers maintain full adjudication authority, and the system serves as a support tool that finds support from coverage documents and makes the underlying policy logic interpretable, helping humans make informed judgments while the final decision remains in the hands of the human reviewer. — rests on abstract considerations (SRC-0007). [CLM-0007-013]

### Interpretative

**US**

- Substituting a polling proxy — a panel drawn from the public or a large language model prediction of aggregated public opinion — for a judge's individual reasoning is not the process mandated for legal decisions by the text of the US Constitution and by US legal culture; a judge who handed over her ultimate decision to such a proxy would be violating her duty to decide the case. — rests on legal sources (SRC-0019). [CLM-0019-003]
- Having a human in the loop to review the conclusions reached by a large language model does not make an agency's action reasonable, since the human cannot recreate or verify the reasoning of the model before the agency adopts its conclusions. — rests on abstract considerations (SRC-0024). [CLM-0024-022]

**general**

- Large language models occupy an intermediate position in Islamic legal reasoning: they assist juristic research through retrieval, organization, and structured reasoning, yet they cannot assume the epistemic or ethical responsibilities that shape Islamic legal judgment, and therefore cannot take the role of a mufti or a mujtahid. — rests on literature (SRC-0003). [CLM-0003-001]
- Mapped onto the principal tiers of Islamic juristic competence, large language models neither fit a single juristic rank nor fully replicate any human role: they occupy an intermediate space, partially simulating analytical tasks while lacking the deeper judgment, context-sensitivity, and ethical responsibility that underpin genuine ijtihād and fatwa issuance, and while far exceeding the lay interpreter (muqallid) in information retrieval and recall, their outputs remain dependent and non-independent. — rests on abstract considerations (SRC-0003). [CLM-0003-013]
- Understanding where and why current legal AI systems break is not a limitation but the foundation of an agenda for trustworthy AI legal reasoning: only by honestly characterizing failure modes can it be identified where AI assistance can be responsibly applied, and systems be built that proactively surface interpretive uncertainty rather than asking lawyers to verify conclusions after the fact. — rests on abstract considerations (SRC-0022). [CLM-0022-019]

### Prescriptive

**US**

- Large language models should be thought of as no more definitive than other sources of 'evidence' of ordinary meaning, such as dictionaries, must only be used with an understanding of their limits, their tendencies to hallucinate and their sensitivity to context and priming, and must never be used to decide the core interpretive questions at issue in a case. — rests on abstract considerations (SRC-0019). [CLM-0019-008]

**general**

- Because different large language models produce varying responses, there is a need to create and use standardized evaluation benchmarks across model families, and human oversight and domain-specific fine-tuning remain crucial in applications where consistency is essential, such as the legal domain. — rests on factual basis (SRC-0002). [CLM-0002-009]
- Large language models should be deployed in Islamic legal settings as supervised accelerators and synthesizers — assisting retrieval, classification, and preliminary analysis — with domain experts setting the frame, checking the steps, and making the rulings, leaving authoritative judgments to qualified jurists. — rests on abstract considerations (SRC-0003). [CLM-0003-008]
- Privacy policy formalization should embrace rather than abstract away the limitations of legal language: a large language model can identify six key elements of each policy statement - the data sender, receiver, data subject, data type, action performed, and any conditions - and the extracted elements can be encoded as first-order logic, while vague terms are preserved as uninterpreted predicates rather than defined, making the ambiguity explicit for human review. — rests on abstract considerations (SRC-0013). [CLM-0013-009]
- Formalizing legal privacy policy text shows both promise and fundamental limits; rather than attempting full automation, privacy policy analysis should be structured so that formal methods identify clear-cut issues while human expertise resolves genuine ambiguities. — rests on abstract considerations (SRC-0013). [CLM-0013-014]
- Large language models should not be used for inherently normative tasks such as judging: normative values are always present in the legal process, and it is better to be explicit and choose socially desirable values than to accept without question the hidden and often harmful normative values forced on us by technology companies. — rests on abstract considerations (SRC-0019). [CLM-0019-009]
- LLM systems in legal settings should support, not replace, human legal judgment, and automated evaluation of legal reasoning should be validated against, not substituted for, expert assessment. — rests on factual basis (SRC-0020). [CLM-0020-020]
- A neutral entailment classification need not be a dead end: a system can compute the minimal set of additional axioms sufficient to shift the classification to ENTAILMENT or CONTRADICTION and present them to a legal reviewer with a targeted question, so that whether the lawyer validates the implicit norm or confirms the case is genuinely underspecified, legal expertise is applied precisely where formal methods reach their limit. — rests on abstract considerations (SRC-0022). [CLM-0022-011]
- Rather than using LLM judges or human preferences as feedback, a formal verification tool can be used as a reward signal in training, teaching a model to distinguish formally supportable inferences from assumption-laden ones; when the solver flags an insufficiently grounded claim it also computes the minimal axioms required to ground it, feeding directly into targeted human review at the points where legal interpretation and formal grounding diverge. — rests on abstract considerations (SRC-0022). [CLM-0022-018]

### Predictive

**general**

- The trust placed in large language models by users — especially models developed by authoritative entities — has the potential to redefine what and how people consider international law; if users rely on these models as definitive interpretative machines, the influence of their design choices will ripple across legal systems and international decision-making processes. — rests on abstract considerations (SRC-0005). [CLM-0005-017]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0002 holds “Because different large language models produce varying responses, there is a need to create and use standardized evaluation benchmarks …” [CLM-0002-009]; SRC-0001 holds “Because large language models can incorporate broader textual segments such as full paragraphs into their reasoning and can follow …” [CLM-0001-006]. Note: The assertion that human oversight and domain-specific fine-tuning remain crucial in the legal domain because different LLMs produce varying responses gives reasons against the contention that zero-shot operation without domain-specific fine-tuning highlights LLMs' potential for scalable legal compliance checking.
- SRC-0003 holds “A retrieval-augmented fatwa system's source-based response places substantial weight on the inquirer, leaving source verification and …” [CLM-0003-007]; SRC-0014 holds “Allowing users to interactively select the legal articles a legal large language model uses improves the accuracy and completeness of its …” [CLM-0014-005]. Note: That leaving source relevance and verification to the inquirer's judgment is a weight and a bias risk gives a reason against expecting lay article selection to yield accurate advice.
- SRC-0019 holds “Substituting a polling proxy — a panel drawn from the public or a large language model prediction of aggregated public opinion — for a …” [CLM-0019-003]; SRC-0025 holds “The third party who observes and understands the objective manifestations of contractual agreement can be a large language model, even …” [CLM-0025-008]. Note: The contention that substituting an LLM proxy for a judge's individual reasoning violates the duty to decide gives reasons against the claim that the third-party interpreter of contractual agreement can be a large language model.
- SRC-0019 holds “Large language models should not be used for inherently normative tasks such as judging: normative values are always present in the legal …” [CLM-0019-009]; SRC-0025 holds “The third party who observes and understands the objective manifestations of contractual agreement can be a large language model, even …” [CLM-0025-008]. Note: The contention that LLMs should not be used for inherently normative tasks such as judging gives reasons against the claim that an LLM can serve as the third party deciding contract interpretation disputes with a more satisfying result than a coin flip.
- SRC-0019 holds “Large language models should be thought of as no more definitive than other sources of 'evidence' of ordinary meaning, such as …” [CLM-0019-008]; SRC-0025 holds “Large language models may be the adjudicatory technology that resolves the text-versus-context issue at the practical lawyering scale where …” [CLM-0025-010]. Note: The contention that LLMs are no more definitive than dictionaries and must never decide core interpretive questions gives reasons against the claim that LLMs may be the adjudicatory technology that resolves the text-versus-context issue.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0002 | unknown | 1 | 1 prescriptive | 1 factual | general |
| SRC-0003 | 2026 | 5 | 2 interpretative, 2 descriptive, 1 prescriptive | 1 literature, 4 abstract | general |
| SRC-0005 | 2026 | 1 | 1 predictive | 1 abstract | general |
| SRC-0007 | 2026 | 1 | 1 descriptive | 1 abstract | undetermined |
| SRC-0012 | 2025 | 1 | 1 descriptive | 1 factual | CN |
| SRC-0013 | 2025 | 3 | 2 prescriptive, 1 descriptive | 2 abstract, 1 literature | general |
| SRC-0014 | unknown | 1 | 1 descriptive | 1 factual | CN |
| SRC-0018 | 2024 | 1 | 1 descriptive | 1 factual | US |
| SRC-0019 | 2025 | 3 | 1 interpretative, 2 prescriptive | 1 legal, 2 abstract | US, general |
| SRC-0020 | 2025 | 1 | 1 prescriptive | 1 factual | general |
| SRC-0021 | unknown | 1 | 1 descriptive | 1 literature | US |
| SRC-0022 | unknown | 3 | 2 prescriptive, 1 interpretative | 3 abstract | general |
| SRC-0024 | unknown | 3 | 2 descriptive, 1 interpretative | 1 literature, 1 factual, 1 abstract | US, general |

## What is missing

Absence records whose key names this concept (12, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0070 — `concept_jurisdiction:CPT-autonomy-and-human-oversight|AU` — No claim about CPT-autonomy-and-human-oversight concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0071 — `concept_jurisdiction:CPT-autonomy-and-human-oversight|BR` — No claim about CPT-autonomy-and-human-oversight concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0072 — `concept_jurisdiction:CPT-autonomy-and-human-oversight|CA` — No claim about CPT-autonomy-and-human-oversight concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0073 — `concept_jurisdiction:CPT-autonomy-and-human-oversight|DE` — No claim about CPT-autonomy-and-human-oversight concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0074 — `concept_jurisdiction:CPT-autonomy-and-human-oversight|EU` — No claim about CPT-autonomy-and-human-oversight concerns EU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0075 — `concept_jurisdiction:CPT-autonomy-and-human-oversight|GB` — No claim about CPT-autonomy-and-human-oversight concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0076 — `concept_jurisdiction:CPT-autonomy-and-human-oversight|KR` — No claim about CPT-autonomy-and-human-oversight concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0077 — `concept_jurisdiction:CPT-autonomy-and-human-oversight|MY` — No claim about CPT-autonomy-and-human-oversight concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0078 — `concept_jurisdiction:CPT-autonomy-and-human-oversight|NL` — No claim about CPT-autonomy-and-human-oversight concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0079 — `concept_jurisdiction:CPT-autonomy-and-human-oversight|NZ` — No claim about CPT-autonomy-and-human-oversight concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0080 — `concept_jurisdiction:CPT-autonomy-and-human-oversight|RU` — No claim about CPT-autonomy-and-human-oversight concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0081 — `concept_jurisdiction:CPT-autonomy-and-human-oversight|TR` — No claim about CPT-autonomy-and-human-oversight concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Can zero-shot LLM deployment be reconciled with the demand for human oversight and domain-specific fine-tuning where consistency is essential?
- Can lay users be relied on to select the sources a legal assistant reasons from?
- May an adjudicator delegate the observer's role in interpretation to a model without violating the duty to decide?
- Are interpretive determinations inherently normative tasks that models should not perform?
- Should model outputs ever outrank other evidence of meaning, such as dictionaries, in interpretation?
