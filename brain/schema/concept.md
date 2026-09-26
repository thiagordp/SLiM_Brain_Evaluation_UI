# Node: Concept

A concept is a notion that claims are about. A notion that nearly every paper in the corpus would trigger discriminates nothing, and is not a concept.

## Fields

- **`id`** — kebab-case, stable, prefixed `CPT-`. Example: `CPT-outcome-prediction`.

- **`status`** — one of:
  - `anchor`: given in advance, listed in the grid below;
  - `candidate`: created during extraction (`map-concepts`);
  - `emergent`: a candidate promoted (`map-concepts`).

- **`concept_type`** — the concept's family: `legal_task` | `technical_task` | `technique_class` | `normative_concern` | `interpretation_object_type` | `interpretation_canon`. 

- **`definition`** — brief definition of the concept as understood within the corpus domain; the definition is inferred and continuously refined according to connected extracted claims. Each refinement appends an entry to `wiki/log.md` giving the concept id, the run id, and the replaced definition verbatim;

- **`run_ids`** — `schema/run.md`.

## Anchor concepts: the grid

```yaml
legal_task:
  - CPT-legal-drafting
  - CPT-review-and-due-diligence
  - CPT-legal-discovery
  - CPT-compliance-and-monitoring
  - CPT-decision-support
  - CPT-legal-education

technical_task:
  - CPT-information-retrieval
  - CPT-question-answering
  - CPT-summarisation
  - CPT-outcome-prediction
  - CPT-argument-mining
  - CPT-information-extraction
  - CPT-rule-formalisation

technique_class:
  - CPT-symbolic-rule-based
  - CPT-case-based-reasoning
  - CPT-machine-learning
  - CPT-computational-argumentation
  - CPT-deep-learning
  - CPT-large-language-models
  - CPT-retrieval-augmented-generation
  - CPT-agentic-systems
  - CPT-neuro-symbolic-hybrid

normative_concern:
  - CPT-accuracy-and-reliability
  - CPT-explainability-and-transparency
  - CPT-fairness-and-non-discrimination
  - CPT-due-process-and-fair-trial
  - CPT-accountability-and-liability
  - CPT-privacy-and-data-protection
  - CPT-professional-responsibility
  - CPT-autonomy-and-human-oversight
  - CPT-access-to-justice
  - CPT-rule-of-law
  - CPT-environmental-cost
  - CPT-security-and-misuse

interpretation_object_type:
  - CPT-statutory-interpretation
  - CPT-contractual-interpretation
  - CPT-judgment-interpretation
  - CPT-treaty-interpretation
  - CPT-other-instrument-interpretation

interpretation_canon:
  - CPT-ordinary-meaning
  - CPT-technical-meaning
  - CPT-contextual-harmonization
  - CPT-precedent
  - CPT-statutory-analogy
  - CPT-legal-concept
  - CPT-general-principle
  - CPT-history
  - CPT-purpose
  - CPT-substantive-reasons
  - CPT-intention
```
