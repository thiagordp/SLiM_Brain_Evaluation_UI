"""Check the calibration content model against its sources. Exits 1 on any failure.

    python app/tools/calibration_guide/validate.py BUILD_DIR

BUILD_DIR holds register.json (extract_register.py). The checks:
* every quotation in policies.py occurs verbatim (after normalising quotes,
  dashes and whitespace) in the source it is attributed to;
* every source key resolves (meeting timestamps exist, comments and Final cells exist);
* AGREED rests on a meeting or on Thiago's calibration notes (E08T);
* every example Claim exists in the register, every linked id exists;
* no OPEN item has a Differs list, and Differs is recomputed independently;
* every open question and consistency point of the earlier summary is kept;
* open Finals (??, No?, To be discussed, yellow Final cell) are never CONFIRMED-and-not-OPEN.
"""
from __future__ import annotations

import ast
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

import policies as pol  # noqa: E402
from report_docx import EVALUATORS, squash  # noqa: E402

EMAIL = ROOT / "Calibration" / "email-conversation.txt"
M28 = ROOT / "meetings" / "SLiM Brain calibration meeting-28-09.docx"
M07 = ROOT / "meetings" / "Brain_meeting_07-10-Transcript.docx"
SPEC = ROOT / "app" / "spec.py"
DEFS = ROOT / "app" / "data" / "definitions_v4.json"

# Each email in the thread, located by a line that only it contains.
EMAIL_MARKERS = {
    "E13A": "Sent: 13 October 2026 17:41", "E13V": "13 Ottobre, 2026 12:23",
    "E12T": "Sent: 12 October 2026 15:14", "E11S": "Sent: 11 October 2026 18:46",
    "E09V": "vendredi, 9 octobre 2026", "E09T": "Sent: 09 October 2026 07:41",
    "E08A": "Sent: 08 October 2026 13:00", "E08T": "08 Ottobre, 2026 12:01",
}


def transcript(path: pathlib.Path) -> str:
    return subprocess.run(["pandoc", "-t", "plain", "--wrap=none", str(path)], capture_output=True,
                          text=True, check=True).stdout


def emails() -> dict[str, str]:
    text = EMAIL.read_text(encoding="utf-8")
    pos = sorted((text.index(m), k) for k, m in EMAIL_MARKERS.items())
    out = {}
    for i, (start, key) in enumerate(pos):
        end = pos[i + 1][0] if i + 1 < len(pos) else len(text)
        out[key] = text[start:end]
    return out


def calibration_texts() -> str:
    tree = ast.parse(SPEC.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "CALIBRATION":
            d = ast.literal_eval(node.value)
            return "\n".join(" ".join(v) for v in d.values())
    raise SystemExit("CALIBRATION not found in spec.py")


def all_strings(obj) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in all_strings(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in all_strings(v)]
    return []


class Sources:
    def __init__(self, reg: dict):
        self.reg = reg
        self.meet = {"M28": transcript(M28), "M07": transcript(M07)}
        self.mail = emails()
        self.spec = calibration_texts()
        self.defs = "\n".join(all_strings(json.loads(DEFS.read_text(encoding="utf-8"))))

    def rows(self, ref: str) -> list[dict]:
        """F:/EC: references -> matching register rows."""
        parts = ref.split(":", 1)[1].split("/")
        claim, qid = parts[0], parts[1]
        target = parts[2] if len(parts) > 2 and parts[2].startswith("CLM-") else None
        return [r for r in self.reg["rows"] if r["id"] == claim and r["qid"] == qid
                and (target is None or target in r["assigned"])]

    def text(self, key: str) -> str | None:
        if key in ("M28", "M07"):
            return self.meet[key]
        if key in self.mail:
            return self.mail[key]
        if key.startswith("RC#"):
            c = self.reg["comments"].get(key[3:])
            return c["text"] if c else None
        if key.startswith("F:"):
            rows = self.rows(key)
            return "\n".join(r["final"] for r in rows) if rows else None
        if key.startswith("EC:"):
            evaluator = key.rsplit("/", 1)[1]
            rows = self.rows(key.rsplit("/", 1)[0])
            return "\n".join(r["evaluators"][evaluator]["comment"] for r in rows) if rows else None
        if key == "DEF":
            return self.defs
        if key.startswith("SPEC"):
            return self.spec
        return None

    def key_exists(self, key: str) -> bool:
        m = re.match(r"^(M28|M07) (\d+:\d\d(?::\d\d)?)$", key)
        if m:
            return re.search(r" %s\s*$" % re.escape(m.group(2)), self.meet[m.group(1)], re.M) is not None
        if key in ("SUM", "REP", "DEF", "SPEC:code") or key.startswith("SPEC:"):
            return True
        return self.text(key) is not None


def recompute_differs(r: dict) -> list[str]:
    if r["status"] == "OPEN" or r["final_category"] not in ("CONFIRMED", "REPLACEMENT"):
        return []
    return [e for e in EVALUATORS if e not in r["gated"] and r["answers"][e] and r["answers"][e] != r["final_value"]]


# House style for the prose we write (quotations are exempt): no rule or decision
# ids inside sentences (they appear only as tags), no em dashes, no stock phrases.
PROSE_IDS = re.compile(r"\b(?:(?:GEN|CL|GR|FD|CO|RE|RC|CC)-\d+|D\d{1,2})\b")
BANNED = re.compile(r"\b(explicitly|substantively|crucial|ensure|robust|leverage|delve|note that|it is worth)\b", re.I)
BRIEF_MAX = 130


def prose_fields():
    """(owner, text) for every hand-written prose string of the content model."""
    for p in pol.POLICIES:
        for k in ("title", "brief", "rule", "apply", "basis", "limits"):
            yield f'{p["id"]}.{k}', p.get(k, "")
    for d in pol.OPEN_DECISIONS:
        for k in ("title", "brief", "readings", "meanwhile", "question", "why", "decide"):
            yield f'{d["id"]}.{k}', d.get(k, "")
        for n, s in enumerate(d["interpretations"], 1):
            yield f'{d["id"]}.reading{n}', s
    for c in pol.CONSISTENCY_CHECKS:
        yield f'{c["id"]}.point', c["point"]
    for b in pol.BASELINE:
        yield f'BASELINE {b["field"]} {b["value"]}.reading', b["reading"]
    yield from ((f"STATUS_RULES.{k}", v) for k, v in pol.STATUS_RULES.items())


def builder_strings():
    """Literal strings of 30+ characters in the two document builders."""
    for name in ("build_guide.py", "build_annex.py"):
        tree = ast.parse((HERE / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) >= 30:
                yield f"{name}:{node.lineno}", node.value


def style_errors() -> list[str]:
    errors = []
    for p in pol.POLICIES:
        if p.get("group") not in dict(pol.GROUPS):
            errors.append(f'{p["id"]}: missing or unknown group')
    for owner, s in list(prose_fields()):
        key = owner.rsplit(".", 1)[-1]
        if key in ("brief", "title", "readings", "meanwhile") and not s:
            errors.append(f"{owner}: empty")
        if key == "brief" and len(s) > BRIEF_MAX:
            errors.append(f"{owner}: longer than {BRIEF_MAX} characters")
        if PROSE_IDS.search(s):
            errors.append(f"{owner}: rule or decision id inside prose: {PROSE_IDS.search(s).group(0)}")
    for owner, s in list(prose_fields()) + list(builder_strings()):
        if "—" in s:
            errors.append(f"{owner}: em dash in prose")
        if BANNED.search(s):
            errors.append(f"{owner}: stock phrase “{BANNED.search(s).group(0)}”")
    return errors


def main(build: pathlib.Path) -> int:
    reg = json.loads((build / "register.json").read_text(encoding="utf-8"))
    src = Sources(reg)
    errors, notes = [], []
    claims = {r["id"] for r in reg["rows"]}
    ids = {p["id"] for p in pol.POLICIES} | {c["id"] for c in pol.CONSISTENCY_CHECKS}

    for p in pol.POLICIES:
        if not p["sources"]:
            errors.append(f'{p["id"]}: no source')
        if p["status"] == pol.AGREED and not any(s.split()[0] in ("M28", "M07", "E08T") for s in p["sources"]):
            errors.append(f'{p["id"]}: AGREED without a meeting or E08T source')
        for s in p["sources"]:
            if not src.key_exists(s):
                errors.append(f'{p["id"]}: source key does not resolve: {s}')
        for c in p["examples"]:
            if c not in claims:
                errors.append(f'{p["id"]}: example {c} is not in the register')
    quoted = [(p["id"], k, q) for p in pol.POLICIES for k, q in p["quotes"]]
    quoted += [(c["id"], k, q) for c in pol.CONSISTENCY_CHECKS for k, q in c["evidence"]]
    quoted += [(f'BASELINE {b["field"]} {b["value"]}', "DEF", b["schema"]) for b in pol.BASELINE]
    quoted += [(f'BASELINE {b["field"]} {b["value"]}', "SPEC", b["calibration"]) for b in pol.BASELINE if b["calibration"]]
    for owner, key, q in quoted:
        text = src.text(key)
        if text is None:
            errors.append(f"{owner}: quote source missing: {key}")
        elif squash(q) not in squash(text):
            errors.append(f"{owner}: quote not found in {key}: {q!r}")
    for d in pol.OPEN_DECISIONS:
        for i in d["policies"]:
            if i not in ids:
                errors.append(f'{d["id"]}: unknown policy {i}')
        for c in d["examples"]:
            if c not in claims:
                errors.append(f'{d["id"]}: example {c} not in register')
    for c in pol.CONSISTENCY_CHECKS:
        for i in c["policies"]:
            if i not in ids:
                errors.append(f'{c["id"]}: unknown policy {i}')
        for x in c["items"]:
            if x not in claims:
                errors.append(f'{c["id"]}: item {x} not in register')
    for _c, _q, _t, links in pol.ITEM_POLICY:
        for i in links:
            if i not in ids:
                errors.append(f"ITEM_POLICY: unknown id {i}")
    if sorted(pol.SUM_OPEN_QUESTIONS) != list(range(1, 12)):
        errors.append("Not every open question of the earlier summary (Section 8, 1–11) is mapped")
    sum9 = [c for c in pol.CONSISTENCY_CHECKS if c["origin"].startswith("SUM §9")]
    if len(sum9) != 5:
        errors.append(f"Expected the 5 consistency points of the earlier summary, found {len(sum9)}")

    for r in reg["rows"]:
        tag = f'{r["id"]} {r["question"]} {r["assigned"]}'
        if r["status"] == "OPEN" and r["differs"]:
            errors.append(f"{tag}: OPEN item has a Differs list")
        if sorted(recompute_differs(r)) != sorted(r["differs"]):
            errors.append(f"{tag}: Differs does not match the recomputation")
        f = r["final"].lower()
        if ("??" in f or re.match(r"^\s*no\?", f) or "to be discussed" in f) and r["status"] != "OPEN":
            errors.append(f"{tag}: tentative Final not OPEN")
        if "Final" in r["manual_yellow_cells"] and r["status"] == "PROVISIONAL":
            errors.append(f"{tag}: Final cell marked yellow but item not OPEN")
        if r["final_category"] == "REPLACEMENT" and r["final_value"] != "No":
            errors.append(f"{tag}: replacement Final without evaluation No")
    errors += style_errors()

    for p in reg["proposals"]:
        if p["disposition"] == "CONSIDERED_REASONABLE" and p["status"] == "AGREED":
            errors.append(f'{p["claim"]} {p["concept"]}: \u201creasonable\u201d read as agreed')
        if not p["split_exact"]:
            notes.append(f'{p["claim"]} {p["evaluator"]}: Missing-Concept cell split inexactly: {p["cell"]!r}')

    for n in notes:
        print("NOTE ", n)
    for e in errors:
        print("ERROR", e)
    print(f"{len(errors)} errors, {len(notes)} notes; {len(quoted)} quotations checked; "
          f"{len(pol.POLICIES)} policies, {len(pol.OPEN_DECISIONS)} open decisions, {len(pol.CONSISTENCY_CHECKS)} checks")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(pathlib.Path(sys.argv[1])))
