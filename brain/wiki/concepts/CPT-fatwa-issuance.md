---
id: CPT-fatwa-issuance
status: candidate
concept_type: legal_task
definition: The issuing of a fatwa — an Islamic legal opinion answering a questioner — as a legal task that depends on textual evidence, school methodology, and the situational circumstances of the questioner.
run_ids: [RUN-2026-09-25-01]
---

# CPT-fatwa-issuance

## What it means

The issuing of a fatwa — an Islamic legal opinion answering a questioner — as a legal task that depends on textual evidence, school methodology, and the situational circumstances of the questioner. A candidate concept coined during the ingest of SRC-0003 and drawn from its claims [CLM-0003-001] [CLM-0003-003] [CLM-0003-006] [CLM-0003-007] [CLM-0003-008] [CLM-0003-013].

## Claims

### Descriptive

**general**

- Large language models cannot access the passive contextual element of Islamic juristic reasoning — awareness of the questioner's intention, social custom, social conditions, and the consequences of a ruling — on which the dispensing of fatwa depends, unless such information is fed to them explicitly as prompting caveats. — rests on abstract considerations (SRC-0003). [CLM-0003-003]
- Retrieval-augmented generation stabilizes answers and reduces unsupported claims in Islamic-domain question answering: anchoring responses in authoritative sources such as Dar al-Iftāʾ archives yields measurable reductions in hallucinations and improvements in answer stability, and creates a workflow in which scholars can trace an answer back to recognized sources and flag unsupported steps. — rests on literature (SRC-0003). [CLM-0003-006]
- A retrieval-augmented fatwa system's source-based response places substantial weight on the inquirer, leaving source verification and relevance to the user's judgment, and inherits biases created by online visibility: websites with more traffic and content, such as Islamweb, are more likely to appear in retrieved results not because they are more authoritative but because they are more visible. — rests on abstract considerations (SRC-0003). [CLM-0003-007]

### Interpretative

**general**

- Large language models occupy an intermediate position in Islamic legal reasoning: they assist juristic research through retrieval, organization, and structured reasoning, yet they cannot assume the epistemic or ethical responsibilities that shape Islamic legal judgment, and therefore cannot take the role of a mufti or a mujtahid. — rests on literature (SRC-0003). [CLM-0003-001]
- Mapped onto the principal tiers of Islamic juristic competence, large language models neither fit a single juristic rank nor fully replicate any human role: they occupy an intermediate space, partially simulating analytical tasks while lacking the deeper judgment, context-sensitivity, and ethical responsibility that underpin genuine ijtihād and fatwa issuance, and while far exceeding the lay interpreter (muqallid) in information retrieval and recall, their outputs remain dependent and non-independent. — rests on abstract considerations (SRC-0003). [CLM-0003-013]

### Prescriptive

**general**

- Large language models should be deployed in Islamic legal settings as supervised accelerators and synthesizers — assisting retrieval, classification, and preliminary analysis — with domain experts setting the frame, checking the steps, and making the rulings, leaving authoritative judgments to qualified jurists. — rests on abstract considerations (SRC-0003). [CLM-0003-008]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0004 holds “Retrieval-augmented generation approaches to supplying legal information to large language models lose contextual information because data …” [CLM-0004-002]; SRC-0003 holds “Retrieval-augmented generation stabilizes answers and reduces unsupported claims in Islamic-domain question answering: anchoring responses …” [CLM-0003-006]. Note: The claim that similarity-based retrieval can surface passages whose keywords appear in unrelated or misleading contexts gives reasons against RAG reliably stabilizing and grounding legal question answering.
- SRC-0003 holds “A retrieval-augmented fatwa system's source-based response places substantial weight on the inquirer, leaving source verification and …” [CLM-0003-007]; SRC-0014 holds “Allowing users to interactively select the legal articles a legal large language model uses improves the accuracy and completeness of its …” [CLM-0014-005]. Note: That leaving source relevance and verification to the inquirer's judgment is a weight and a bias risk gives a reason against expecting lay article selection to yield accurate advice.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0003 | 2026 | 6 | 2 interpretative, 3 descriptive, 1 prescriptive | 2 literature, 4 abstract | general |

## What is missing

Absence records whose key names this concept (17, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0584 — `concept_pair:CPT-fatwa-issuance|CPT-agentic-systems` — No claim links CPT-fatwa-issuance to CPT-agentic-systems. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0585 — `concept_pair:CPT-fatwa-issuance|CPT-context-granularity` — No claim links CPT-fatwa-issuance to CPT-context-granularity. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0586 — `concept_pair:CPT-fatwa-issuance|CPT-deep-learning` — No claim links CPT-fatwa-issuance to CPT-deep-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0587 — `concept_pair:CPT-fatwa-issuance|CPT-defeasible-reasoning` — No claim links CPT-fatwa-issuance to CPT-defeasible-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0588 — `concept_pair:CPT-fatwa-issuance|CPT-explicit-reasoning` — No claim links CPT-fatwa-issuance to CPT-explicit-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0589 — `concept_pair:CPT-fatwa-issuance|CPT-fine-tuning` — No claim links CPT-fatwa-issuance to CPT-fine-tuning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0590 — `concept_pair:CPT-fatwa-issuance|CPT-human-reinforcement-learning` — No claim links CPT-fatwa-issuance to CPT-human-reinforcement-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0591 — `concept_pair:CPT-fatwa-issuance|CPT-in-context-learning` — No claim links CPT-fatwa-issuance to CPT-in-context-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0592 — `concept_pair:CPT-fatwa-issuance|CPT-llm-as-a-judge` — No claim links CPT-fatwa-issuance to CPT-llm-as-a-judge. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0593 — `concept_pair:CPT-fatwa-issuance|CPT-llm-based-annotation` — No claim links CPT-fatwa-issuance to CPT-llm-based-annotation. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0594 — `concept_pair:CPT-fatwa-issuance|CPT-machine-learning` — No claim links CPT-fatwa-issuance to CPT-machine-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0595 — `concept_pair:CPT-fatwa-issuance|CPT-neuro-symbolic-hybrid` — No claim links CPT-fatwa-issuance to CPT-neuro-symbolic-hybrid. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0596 — `concept_pair:CPT-fatwa-issuance|CPT-prompt-engineering` — No claim links CPT-fatwa-issuance to CPT-prompt-engineering. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0597 — `concept_pair:CPT-fatwa-issuance|CPT-question-decomposition` — No claim links CPT-fatwa-issuance to CPT-question-decomposition. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0598 — `concept_pair:CPT-fatwa-issuance|CPT-syllogistic-reasoning` — No claim links CPT-fatwa-issuance to CPT-syllogistic-reasoning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0599 — `concept_pair:CPT-fatwa-issuance|CPT-symbolic-rule-based` — No claim links CPT-fatwa-issuance to CPT-symbolic-rule-based. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0600 — `concept_pair:CPT-fatwa-issuance|CPT-zero-shot-learning` — No claim links CPT-fatwa-issuance to CPT-zero-shot-learning. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Does RAG's dependence on chunked, similarity-based retrieval undermine the answer stability it is credited with?
- Can lay users be relied on to select the sources a legal assistant reasons from?
