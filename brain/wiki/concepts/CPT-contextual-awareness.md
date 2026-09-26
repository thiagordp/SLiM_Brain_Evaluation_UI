---
id: CPT-contextual-awareness
status: candidate
concept_type: normative_concern
definition: The capacity to take account of the situational factors surrounding a legal question — the questioner's intention, prevailing custom, social conditions, and the foreseeable consequences of a ruling — treated as a requirement of sound legal judgment and as a limitation of automated systems.
run_ids: [RUN-2026-09-25-01]
---

# CPT-contextual-awareness

## What it means

The capacity to take account of the situational factors surrounding a legal question — the questioner's intention, prevailing custom, social conditions, and the foreseeable consequences of a ruling — treated as a requirement of sound legal judgment and as a limitation of automated systems. A candidate concept coined during the ingest of SRC-0003 and drawn from its claims [CLM-0003-003] [CLM-0003-013] [CLM-0003-014].

## Claims

### Descriptive

**general**

- Large language models cannot access the passive contextual element of Islamic juristic reasoning — awareness of the questioner's intention, social custom, social conditions, and the consequences of a ruling — on which the dispensing of fatwa depends, unless such information is fed to them explicitly as prompting caveats. — rests on abstract considerations (SRC-0003). [CLM-0003-003]
- Explainable AI techniques for large language models, such as chain-of-thought explanation, cannot supply the passive contextual information a mufti relies on — intention, social conditions, or local custom — but can show which sources shaped a model's answer and how the model weighed them, supporting scholarly oversight of whether the reasoning aligns with accepted interpretive methods. — rests on abstract considerations (SRC-0003). [CLM-0003-014]
- A retrieval-augmented generation method that preserves the structure of legal texts — dividing a legal document into its pre-defined articles and paragraphs and segmenting each paragraph into overlapping passages for dense retrieval — ensures accurate retrieval and interpretation of relevant provisions and more accurate, contextually aware reasoning. — rests on abstract considerations (SRC-0016). [CLM-0016-006]

### Interpretative

**general**

- Mapped onto the principal tiers of Islamic juristic competence, large language models neither fit a single juristic rank nor fully replicate any human role: they occupy an intermediate space, partially simulating analytical tasks while lacking the deeper judgment, context-sensitivity, and ethical responsibility that underpin genuine ijtihād and fatwa issuance, and while far exceeding the lay interpreter (muqallid) in information retrieval and recall, their outputs remain dependent and non-independent. — rests on abstract considerations (SRC-0003). [CLM-0003-013]

## Where papers disagree

No extracted disagreement is recorded: every ATTACKS edge touching these claims is inferred.

### Inferred

- SRC-0014 holds “Even when legal large language models are combined with legal article retrieval components, the advice given can still be incorrect or …” [CLM-0014-001]; SRC-0016 holds “A retrieval-augmented generation method that preserves the structure of legal texts — dividing a legal document into its pre-defined …” [CLM-0016-006]. Note: The finding that legal article retrieval cannot ensure all relevant articles are retrieved and that retrieved noise leads models to incomplete or incorrect responses gives reasons against the claim that a retrieval-augmented method ensures accurate retrieval and interpretation of relevant provisions.
- SRC-0007 holds “Standard semantic search is ill-suited for retrieving the policy language that governs a procedure code's coverage, because the signals …” [CLM-0007-004]; SRC-0016 holds “A retrieval-augmented generation method that preserves the structure of legal texts — dividing a legal document into its pre-defined …” [CLM-0016-006]. Note: The argument that similarity-based semantic search often misses the governing clause because relevance signals are orthogonal to thematic content counts against the claim that dense similarity retrieval over structured passages ensures accurate retrieval of the relevant provisions.

## The spread

| paper | year | claims | by type | by basis | jurisdictions |
|---|---|---|---|---|---|
| SRC-0003 | 2026 | 3 | 2 descriptive, 1 interpretative | 3 abstract | general |
| SRC-0016 | 2024 | 1 | 1 descriptive | 1 abstract | general |

## What is missing

Absence records whose key names this concept (14, computed by `tools/absences.py`). Each is `unresolved` between its three readings — `gap_in_literature` (nobody in the field has written it), `extraction_shadow` (somebody has, and this corpus or extraction missed it), `tacit_link` (so obvious to the field that nobody states it) — which only a person may resolve.

- ABS-0095 — `concept_jurisdiction:CPT-contextual-awareness|AU` — No claim about CPT-contextual-awareness concerns AU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0096 — `concept_jurisdiction:CPT-contextual-awareness|BR` — No claim about CPT-contextual-awareness concerns BR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0097 — `concept_jurisdiction:CPT-contextual-awareness|CA` — No claim about CPT-contextual-awareness concerns CA. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0098 — `concept_jurisdiction:CPT-contextual-awareness|CN` — No claim about CPT-contextual-awareness concerns CN. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0099 — `concept_jurisdiction:CPT-contextual-awareness|DE` — No claim about CPT-contextual-awareness concerns DE. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0100 — `concept_jurisdiction:CPT-contextual-awareness|EU` — No claim about CPT-contextual-awareness concerns EU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0101 — `concept_jurisdiction:CPT-contextual-awareness|GB` — No claim about CPT-contextual-awareness concerns GB. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0102 — `concept_jurisdiction:CPT-contextual-awareness|KR` — No claim about CPT-contextual-awareness concerns KR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0103 — `concept_jurisdiction:CPT-contextual-awareness|MY` — No claim about CPT-contextual-awareness concerns MY. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0104 — `concept_jurisdiction:CPT-contextual-awareness|NL` — No claim about CPT-contextual-awareness concerns NL. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0105 — `concept_jurisdiction:CPT-contextual-awareness|NZ` — No claim about CPT-contextual-awareness concerns NZ. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0106 — `concept_jurisdiction:CPT-contextual-awareness|RU` — No claim about CPT-contextual-awareness concerns RU. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0107 — `concept_jurisdiction:CPT-contextual-awareness|TR` — No claim about CPT-contextual-awareness concerns TR. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)
- ABS-0108 — `concept_jurisdiction:CPT-contextual-awareness|US` — No claim about CPT-contextual-awareness concerns US. (reading: unresolved — gap_in_literature | extraction_shadow | tacit_link)

## Open questions

- Does structure-aware retrieval actually remove the retrieval noise that misleads legal RAG systems?
- Do the signals that govern legal relevance defeat similarity-based retrieval even when document structure is preserved?
