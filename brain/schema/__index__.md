# Schema — index and version

`schema_version: 0.1.0`

## Changing the schema

Bump the version here and note what changed in `changelog.md`. That is the whole procedure.

There is deliberately no rule about what that means for records already written. `run_ids` tells you which records predate a change; what to do about them is decided when it comes up.

This is the only way a rule changes, and only when the team asks. The rules are CLAUDE.md, `schema/` and `.claude/skills/`. Nothing else adds, drops, tightens or loosens one: not a prompt to a subagent, not a helper script, not your own reading of a step. When you hand a task to a subagent, point it to the files that hold the rules; never restate them, since a paraphrase is a second copy. Likewise, never alter what a subagent hands back: a defect you notice in its results, whether or not the gate rejects it, goes back to the subagent's skill with the reason. Where the rules are silent, or you would want to depart from them, log it in `wiki/log.md` and follow the text as written.

## Files

| File | Defines |
|---|---|
| `run.md` | Run record: schema version, model, corpus, and the `run_ids` every record carries |
| `source.md` | Source node (one per publication) |
| `claim.md` | Claim node |
| `concept.md` | Concept node, statuses, and the six-family concept grid |
| `dataset.md` | Dataset node |
| `edge.md` | The six edge types, their grounding vocabulary, and carried fields |
| `absence.md` | Absence record |
| `hypothesis.md` | Hypothesis record |
| `synthesis.md` | Synthesis record |

