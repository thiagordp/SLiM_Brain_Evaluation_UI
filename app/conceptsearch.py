"""Local, deterministic Concept search for Question 14.

The evaluator types free words; Concepts are ranked by how well their name, id
and family match — the shared vocabulary itself. Generated Concept definitions
are deliberately not read: they are neither search evidence nor ranking
evidence. No query word is mandatory: a Concept matching some of the words
still appears, below those that match more or match in the name. The same query
always gives the same order.
"""
from __future__ import annotations

import re
import unicodedata

STOPWORDS = frozenset({"a", "an", "and", "the", "of", "in", "on", "to", "for", "or",
                       "by", "with", "is", "are", "as", "at", "its"})

# Weights: a word in the name counts far more than one in the id or the family.
NAME_WORD, NAME_PREFIX = 10, 6
ID_WORD = 4
FAMILY_WORD = 2
NAME_PHRASE, NAME_EXACT = 30, 100


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def words(text: str) -> list[str]:
    return [w for w in normalise(text).split() if w and w not in STOPWORDS]


def score(query: str, entry: dict) -> int:
    """Relevance of one Concept (`label`, `id`, `family`) to a query."""
    q_words = words(query)
    if not q_words:
        return 0
    name = normalise(entry.get("label", ""))
    name_words = set(name.split())
    id_words = set(normalise(entry.get("id", "").removeprefix("CPT-")).split())
    family_words = set(normalise(entry.get("family", "")).split())
    total = 0
    phrase = " ".join(q_words)
    if name == normalise(query):
        total += NAME_EXACT
    elif phrase and phrase in name:
        total += NAME_PHRASE
    for word in q_words:
        if word in name_words:
            total += NAME_WORD
        elif any(w.startswith(word) for w in name_words) and len(word) >= 3:
            total += NAME_PREFIX
        if word in id_words:
            total += ID_WORD
        if word in family_words:
            total += FAMILY_WORD
    return total


def search(query: str, entries: list[dict]) -> list[dict]:
    """Matching entries, most relevant first; all entries when the query is empty."""
    if not words(query):
        return sorted(entries, key=lambda e: e.get("label", "").lower())
    ranked = [(score(query, e), e) for e in entries]
    ranked = [(s, e) for s, e in ranked if s > 0]
    ranked.sort(key=lambda pair: (-pair[0], pair[1].get("label", "").lower()))
    return [e for _, e in ranked]
