"""Inter-rater agreement coefficients for the Training report (Appendix C).

Pure functions over *units*: one list of answers per item, one answer per rater
(None or "" = no answer). Undefined coefficients (all answers in one category,
so expected disagreement is zero) are returned as None.

    python app/tools/training_report/coefficients.py DATA.json

adds a "coefficients" block to a JSON written by extract.py (in place);
extract.py also calls compute() itself.
"""
from __future__ import annotations

import collections
import itertools
import json
import pathlib
import random
import sys

APP = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(APP))

import spec  # noqa: E402

FAMILIES = ("Claim evaluation", "Schema fields", "Concepts", "Relations", "Dataset")
SMALL_N = 10
REPS = 2000
SEED = 1


# ------------------------------------------------------------------ coefficients
def _clean(units):
    return [[v for v in u if v not in (None, "")] for u in units]


def percent_agreement(units) -> float | None:
    """Mean over units of the share of agreeing rater pairs (= mean pairwise Po without missing data)."""
    shares = []
    for u in _clean(units):
        m = len(u)
        if m < 2:
            continue
        n = collections.Counter(u)
        shares.append(sum(c * (c - 1) for c in n.values()) / (m * (m - 1)))
    return sum(shares) / len(shares) if shares else None


def cohen_kappa(a: list, b: list) -> float | None:
    pairs = [(x, y) for x, y in zip(a, b) if x not in (None, "") and y not in (None, "")]
    n = len(pairs)
    if not n:
        return None
    po = sum(x == y for x, y in pairs) / n
    ca, cb = collections.Counter(x for x, _ in pairs), collections.Counter(y for _, y in pairs)
    pe = sum(ca[k] * cb[k] for k in ca) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def light_kappa(units) -> dict:
    """Cohen's kappa for every rater pair; Light's kappa is their mean."""
    raters = range(max(len(u) for u in units))
    ks = [cohen_kappa([u[i] for u in units], [u[j] for u in units]) for i, j in itertools.combinations(raters, 2)]
    defined = [k for k in ks if k is not None]
    return {"mean": sum(defined) / len(defined) if defined else None,
            "min": min(defined) if defined else None, "max": max(defined) if defined else None,
            "pairs": len(ks), "undefined_pairs": len(ks) - len(defined)}


def fleiss_kappa(units) -> float | None:
    """Fleiss (1971); requires the same number of raters per unit."""
    units = _clean(units)
    m = len(units[0])
    assert all(len(u) == m for u in units), "Fleiss' kappa needs a constant number of raters"
    p_bar = percent_agreement(units)
    pooled = collections.Counter(v for u in units for v in u)
    total = sum(pooled.values())
    pe = sum((c / total) ** 2 for c in pooled.values())
    return None if pe == 1 else (p_bar - pe) / (1 - pe)


def gwet_ac1(units, q: int) -> float | None:
    """Gwet (2008) AC1 for several raters; q = number of categories of the scale."""
    units = _clean(units)
    pa = percent_agreement(units)
    pooled = collections.Counter(v for u in units for v in u)
    total = sum(pooled.values())
    pe = sum((c / total) * (1 - c / total) for c in pooled.values()) / (q - 1)
    return None if pe == 1 else (pa - pe) / (1 - pe)


def nominal(a, b) -> float:
    return 0.0 if a == b else 1.0


def jaccard(a: frozenset, b: frozenset) -> float:
    return 1.0 if not a and not b else len(a & b) / len(a | b)


def masi_distance(a: frozenset, b: frozenset) -> float:
    """Passonneau (2006): 1 - Jaccard x M; M = 1 identical, 2/3 subset, 1/3 overlap, 0 disjoint."""
    if a == b:
        return 0.0
    if a <= b or b <= a:
        m = 2 / 3
    elif a & b:
        m = 1 / 3
    else:
        m = 0.0
    return 1 - jaccard(a, b) * m


def alpha(units, distance=nominal) -> float | None:
    """Krippendorff's alpha = 1 - Do/De over pairable values (units with two or more answers)."""
    units = [u for u in _clean(units) if len(u) >= 2]
    values = [v for u in units for v in u]
    n = len(values)
    if n < 2:
        return None
    if distance is nominal:                              # closed form via category counts
        d_o = sum((len(u) ** 2 - sum(c * c for c in collections.Counter(u).values())) / (len(u) - 1)
                  for u in units) / n
        d_e = (n * n - sum(c * c for c in collections.Counter(values).values())) / (n * (n - 1))
    else:
        d_o = sum(sum(distance(x, y) for x, y in itertools.permutations(u, 2)) / (len(u) - 1)
                  for u in units) / n
        d_e = sum(distance(x, y) for x, y in itertools.permutations(values, 2)) / (n * (n - 1))
    return None if d_e == 0 else 1 - d_o / d_e


def specific_agreement(units) -> tuple[float | None, float | None]:
    """Pooled pairwise agreement on defects (positive, True) and on correct outputs (negative, False)."""
    both_d = both_ok = dis = 0
    for u in units:
        for a, b in itertools.combinations([v for v in u if v is not None], 2):
            if a and b:
                both_d += 1
            elif not a and not b:
                both_ok += 1
            else:
                dis += 1
    pos = 2 * both_d / (2 * both_d + dis) if both_d + dis else None
    neg = 2 * both_ok / (2 * both_ok + dis) if both_ok + dis else None
    return pos, neg


def bootstrap_ci(units, fn, reps: int = REPS, seed: int = SEED) -> list | None:
    """95% percentile interval, resampling units with replacement."""
    rng = random.Random(seed)
    stats = []
    for _ in range(reps):
        s = fn([units[rng.randrange(len(units))] for _ in units])
        if s is not None:
            stats.append(s)
    if len(stats) < reps / 2:
        return None
    stats.sort()
    return [stats[int(0.025 * len(stats))], stats[int(0.975 * len(stats)) - 1]]


# ------------------------------------------------------------------ report tables
def _binary_row(units, ci: bool, pairs: bool) -> dict:
    """Defect coding: units of booleans (True = defect recorded)."""
    coded = [["d" if v else "o" for v in u] for u in units]
    pos, neg = specific_agreement(units)
    row = {"n": len(units), "po": percent_agreement(coded), "fleiss": fleiss_kappa(coded),
           "alpha": alpha(coded), "ac1": gwet_ac1(coded, 2), "pos": pos, "neg": neg,
           "defect_share": sum(v for u in units for v in u) / sum(len(u) for u in units)}
    if pairs:
        row["light"] = light_kappa(coded)
    if ci:
        row["alpha_ci"] = bootstrap_ci(coded, alpha)
        row["ac1_ci"] = bootstrap_ci(coded, lambda us: gwet_ac1(us, 2))
    return row


def compute(data: dict) -> dict:
    raters = data["raters"]
    papers = list(data["papers"])
    q_of = {q.key: q for q in spec.QUESTIONS}
    items = {s: data["papers"][s]["items"] for s in papers}
    flags = lambda its: [[bool(i["flags"].get(r)) for r in raters] for i in its]       # noqa: E731

    overall = {s: _binary_row(flags(items[s]), ci=True, pairs=True) for s in papers}
    overall["both"] = _binary_row(flags([i for s in papers for i in items[s]]), ci=True, pairs=True)

    pooled = [i for s in papers for i in items[s]]
    families = {f: _binary_row(flags([i for i in pooled if i["section"] == f]), ci=True, pairs=False)
                for f in FAMILIES if any(i["section"] == f for i in pooled)}

    per_question, omitted = [], []
    for q in spec.QUESTIONS:
        its = [i for i in pooled if i["key"] == q.key]
        if not its or q.part == spec.PART_RECALL:          # one holistic unit per paper
            continue
        if len(its) < 2:
            omitted.append(q.key)
            continue
        units = [[i["answers"][r] for r in raters] for i in its]
        per_question.append({"key": q.key, "title": q.title, "section": its[0]["section"], "n": len(its),
                             "q": len(q.options), "po": percent_agreement(units), "fleiss": fleiss_kappa(units),
                             "alpha": alpha(units), "ac1": gwet_ac1(units, len(q.options)),
                             "small": len(its) < SMALL_N})

    def q14_units(s):
        out = []
        for claim, ev in data["papers"][s]["q14"].items():
            u = []
            for r in raters:
                x = ev[r]
                if not x["state"]:
                    u.append(None)
                    continue
                u.append(frozenset([c["id"] for c in x["selected"]] +
                                   ["new:" + p["name"].strip().lower() for p in x["proposed"]]))
            out.append(u)
        return out

    def set_row(units):
        pairs = [jaccard(a, b) for u in units for a, b in itertools.combinations([v for v in u if v is not None], 2)]
        return {"n": len(units), "alpha_masi": alpha(units, masi_distance),
                "jaccard": sum(pairs) / len(pairs) if pairs else None,
                "identical": sum(len(set(v for v in u if v is not None)) == 1 for u in units)}

    q14 = {s: set_row(q14_units(s)) for s in papers}
    q14["both"] = set_row([u for s in papers for u in q14_units(s)])
    return {"overall": overall, "families": families, "per_question": per_question,
            "omitted_questions": omitted, "q14": q14, "reps": REPS, "seed": SEED, "small_n": SMALL_N}


def main() -> int:
    path = pathlib.Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    data["coefficients"] = compute(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    c = data["coefficients"]
    for k, v in c["overall"].items():
        print(k, {x: (round(y, 3) if isinstance(y, float) else y) for x, y in v.items() if x != "light"},
              "light", {x: (round(y, 3) if isinstance(y, float) else y) for x, y in v["light"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
