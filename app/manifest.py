"""Runtime configuration: who evaluates what, and which switches are on.

Two sources, one interface. When a workbook is configured, CONFIG / EVALUATORS /
ASSIGNMENTS are the live configuration and the administrator can change a switch
without a redeploy — which matters because the deployed checkout is not writable
between restarts. Without a workbook, ``data/manifest.yaml`` serves the same
data: it is the bootstrap source, the local-development configuration, and the
reproducibility snapshot. Callers cannot tell which is active.

The two halves of the configuration change at very different rates and are
cached separately: a phase switch must take effect within seconds of the
administrator flipping it, while the evaluator and assignment tables are stable
for the length of a round.


The app never infers an assignment. It reads explicit evaluator x paper x phase
rows produced by ``tools/build_assignments.py``, because the labels in
circulation do not line up — Giovanni and Alessandro are called "Group A" in the
allocation email but hold ``AGR-C``. Changing the division means regenerating
the manifest, not editing code.

Three phases:

    training     optional practice, the same two papers for everyone
    agreement    both evaluators of a pair over one shared set
    individual   one evaluator per paper

Each carries its own assignments, open/closed switch and final submission.

They are **not sequential**. All three are open from the start; a phase's
open/closed switch is an operational control, not a methodological gate. Training
is optional: leaving it untouched, half-finished or unsubmitted blocks nothing —
not Agreement, not Individual, not their final submissions, and it is never
reported as a configuration problem. Agreement need not be closed before
Individual is used. An assigned pool
whose paper-by-paper division is still pending — IND-1 — does not hold its phase
closed either; only those particular papers wait.

Secrets are never stored here: the shared password and the admin secret come
from environment variables (or Streamlit secrets), never from the manifest.
"""
from __future__ import annotations

import functools
import hashlib
import json
import os
import pathlib
import threading
import time

import yaml

import sheets

MANIFEST_PATH = pathlib.Path(__file__).resolve().parent / "data" / "manifest.yaml"

#: Seconds a cached read stays fresh. The switches are polled often and must
#: react quickly; the tables are read on nearly every rerun and almost never
#: change, so re-reading them per interaction would be pure cost.
SWITCH_TTL = 15.0
TABLE_TTL = 300.0

ENV_PASSWORD = "HE_APP_PASSWORD"
ENV_ADMIN_SECRET = "HE_ADMIN_SECRET"

#: Set on a deployed run. Streamlit Community Cloud does not guarantee that
#: runtime-generated local files survive, so a SQLite store there can be wiped
#: between restarts. With this set the app stops rather than let evaluators fill
#: in a store that may silently vanish.
ENV_REQUIRE_SHEETS = "HE_REQUIRE_SHEETS"

# Hard rule from the design: every password and credential exists only as an
# environment variable (or Streamlit secrets, which is the same mechanism on
# Community Cloud). No secret value appears in this code or in any committed
# config file, and there is no development fallback — an unset secret fails
# closed rather than silently accepting a value someone could read here.


class _Cache:
    """A tiny time-boxed cache that works in and out of Streamlit.

    ``st.cache_data`` is not used here: this module is also imported by the
    command-line tools, and the invalidation has to be explicit — the
    administrator flipping a switch must not wait for a TTL to lapse.
    """

    def __init__(self, ttl: float) -> None:
        self._ttl = ttl
        self._value = None
        self._at = 0.0
        self._lock = threading.Lock()

    def get(self, loader):
        with self._lock:
            if self._value is None or time.monotonic() - self._at > self._ttl:
                self._value = loader()
                self._at = time.monotonic()
            return self._value

    def clear(self) -> None:
        with self._lock:
            self._value = None
            self._at = 0.0


_SWITCHES = _Cache(SWITCH_TTL)
_TABLES = _Cache(TABLE_TTL)


def invalidate() -> None:
    """Drop every cached read. Called after any configuration write."""
    _SWITCHES.clear()
    _TABLES.clear()
    manifest.cache_clear()


@functools.lru_cache(maxsize=1)
def manifest() -> dict:
    """The file configuration: bootstrap source, local default, snapshot."""
    return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8")) or {}


def _workbook():
    """The live workbook, or None when the file configuration is in use."""
    import store

    return store.workbook()


def using_workbook() -> bool:
    return _workbook() is not None


def source_name() -> str:
    return "google-sheets" if using_workbook() else "manifest.yaml"


def _read_tab(tab: str) -> list[dict]:
    book = _workbook()
    return book.read_tab(tab) if book is not None else []


def _load_switches() -> dict:
    """CONFIG as a mapping. Falls back to the file when the tab is empty."""
    if using_workbook():
        rows = _read_tab(sheets.CONFIG)
        if rows:
            return {r["key"]: r["value"] for r in rows if r.get("key")}
    return dict(manifest().get("config", {}) or {})


def _load_tables() -> dict:
    if using_workbook():
        evaluators = _read_tab(sheets.EVALUATORS)
        assignments = _read_tab(sheets.ASSIGNMENTS)
        if evaluators and assignments:
            return {"evaluators": [_normalise_evaluator(r) for r in evaluators],
                    "assignments": [_normalise_assignment(r) for r in assignments]}
    data = manifest()
    return {"evaluators": list(data.get("evaluators", []) or []),
            "assignments": list(data.get("assignments", []) or [])}


def _truthy(value) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _normalise_evaluator(row: dict) -> dict:
    """A workbook row is all strings; the rest of the app expects real types."""
    return {**row,
            "is_admin": _truthy(row.get("is_admin")),
            "pair_id": row.get("pair_id") or None}


def _normalise_assignment(row: dict) -> dict:
    order = str(row.get("assignment_order") or "").strip()
    return {**row,
            "assignment_order": int(order) if order.isdigit() else 0,
            "assignment_state": state_of(row)}


def _secrets():
    """Streamlit secrets when running under Streamlit, otherwise nothing.

    Split out so it can be stubbed: a real .streamlit/secrets.toml in the working
    tree would otherwise leak into anything that asks whether a secret is set.
    """
    try:
        import streamlit as st

        return st.secrets
    except Exception:
        return {}


def _secret(name: str) -> str:
    """Environment variable, then Streamlit secrets. Never a literal."""
    if os.environ.get(name):
        return os.environ[name]
    secrets = _secrets()
    try:
        if name in secrets:
            return str(secrets[name])
    except Exception:
        pass
    return ""


def password() -> str:
    return _secret(ENV_PASSWORD)


def admin_secret() -> str:
    return _secret(ENV_ADMIN_SECRET)


def missing_secrets() -> list[str]:
    return [name for name in (ENV_PASSWORD, ENV_ADMIN_SECRET) if not _secret(name)]


def require_sheets() -> bool:
    value = _secret(ENV_REQUIRE_SHEETS).strip().lower()
    return value in ("1", "true", "yes", "on")


# ------------------------------------------------------------------ config
def config() -> dict:
    return _SWITCHES.get(_load_switches)


def _tables() -> dict:
    return _TABLES.get(_load_tables)


def brain_snapshot_id() -> str:
    return str(config().get("brain_snapshot_id", ""))


def eval_spec_version() -> str:
    return str(config().get("eval_spec_version", ""))


def split_version() -> str:
    return str(config().get("split_version", ""))


# ------------------------------------------------------------------ phases
TRAINING, AGREEMENT, INDIVIDUAL = "training", "agreement", "individual"

#: Display order only. Not a sequence: none of them gates another.
PHASES = (TRAINING, AGREEMENT, INDIVIDUAL)

PHASE_LABEL = {
    TRAINING: "Training",
    AGREEMENT: "Agreement",
    INDIVIDUAL: "Individual",
}


#: Training is practice. It is offered to everyone and never required: an
#: evaluator may leave it untouched, half-finished or unsubmitted and still work
#: on — and finally submit — Agreement and Individual. Nothing may report it as a
#: problem, only as optional and incomplete.
OPTIONAL_PHASES = (TRAINING,)


def is_phase(phase_id: str) -> bool:
    return phase_id in PHASES


def is_optional(phase_id: str) -> bool:
    return phase_id in OPTIONAL_PHASES


# ------------------------------------------------------- assignment states
#: A real assignment: it appears in the evaluator's paper list, counts toward
#: progress, completion and phase submission, and is an evaluated paper in the
#: exported data.
ASSIGNED = "assigned"

#: A technical reservation: a preallocated possibility, not an assignment. It is
#: invisible to the evaluator and counts toward nothing. IND-1 carries one per
#: evaluator per paper, so settling the Thiago/Francesca division later is a
#: one-field edit rather than a round of row creation. Activate only one
#: evaluator per paper — activating both would make the pool a second agreement
#: set.
RESERVED = "reserved"

ASSIGNMENT_STATES = (ASSIGNED, RESERVED)


def state_of(row: dict) -> str:
    """A row with no state recorded is an assignment; reservation is explicit."""
    return str(row.get("assignment_state") or ASSIGNED)


def phase_open(phase_id: str) -> bool:
    value = config().get(f"{phase_id}_open", False)
    return _truthy(value) if isinstance(value, str) else bool(value)


def open_phases() -> list[str]:
    return [phase for phase in PHASES if phase_open(phase)]


#: Settings that describe the experiment. Everything else in CONFIG — the phase
#: switches — is operational, and deliberately excluded from `config_version`:
#: closing Agreement must not look like the assignments changed.
EXPERIMENT_KEYS = ("brain_snapshot_id", "eval_spec_version", "split_version")


def config_version() -> str:
    """A stable digest of the experimental configuration.

    Recorded on every review, so an answer can always be traced to the exact
    Brain, instrument and assignment set it was given under. Phase switches are
    not part of it: opening or closing a phase changes what people can do next,
    not what any existing answer means.
    """
    switches = config()
    payload = {
        "experiment": {k: str(switches.get(k, "")) for k in EXPERIMENT_KEYS},
        "evaluators": sorted(
            (str(e.get("evaluator_id")), str(e.get("name")), bool(e.get("is_admin")),
             str(e.get("agreement_split") or ""), str(e.get("individual_split") or ""))
            for e in evaluators()
        ),
        "assignments": sorted(
            (str(a.get("assignment_key")), str(a.get("evaluator_id") or ""),
             str(a.get("phase_id")), str(a.get("split_id")), str(a.get("source_id")),
             state_of(a))
            for a in assignments()
        ),
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------------------- immutability
def assignment_key(phase_id: str, evaluator_id: str, source_id: str) -> str:
    return f"{phase_id}|{evaluator_id}|{source_id}"


def has_activity(review: dict) -> bool:
    """Whether an evaluator has actually done something to this review.

    **The existence of a REVIEWS row is not activity.** Rows are preallocated for
    every assigned paper before anyone opens the application, so treating a row
    as evidence of work would lock the entire configuration the moment the
    workbook was prepared — including the IND-1 pool that must stay assignable.

    Activity is durable evidence left by a person: a status past `not_started`,
    the moment they confirmed reading the paper, or a write against the review.
    """
    status = (review.get("status") or "").strip()
    if status and status != "not_started":
        return True
    return bool((review.get("started_at") or "").strip()
                or (review.get("last_saved_at") or "").strip())


def active_assignment_keys(reviews) -> set[str]:
    """Assignments an evaluator has actually started work against.

    Keyed to the individual assignment rather than to the phase: every phase is
    open from the start, so "frozen once the phase opens" would freeze the whole
    configuration immediately and leave an undivided pool unassignable.
    """
    return {
        assignment_key(r.get("phase_id", ""), r.get("evaluator_id", ""),
                       r.get("source_id", ""))
        for r in reviews
        if has_activity(r)
    }


def is_locked(key: str, reviews) -> bool:
    return key in active_assignment_keys(reviews)


def orphaned(reviews) -> list[str]:
    """Worked-on reviews whose assignment row is gone or has been reassigned.

    Adding an assignment, or naming the evaluator on a pending one, is always
    safe — it creates work rather than invalidating any. Removing or reassigning
    a row that already carries answers strands them, and nothing downstream
    could tell that had happened, so it is surfaced as a configuration problem.
    """
    keys = {a.get("assignment_key") for a in assignments()}
    return sorted(key for key in active_assignment_keys(reviews) if key not in keys)


def set_phase(phase_id: str, is_open: bool) -> None:
    """Admin control. Writes the manifest back, preserving everything else.

    Closing a phase is an operational measure — pausing work, or freezing a set
    before it is analysed — not a stage in a sequence. The default for all three
    is open.

    Note this does not persist on Streamlit Community Cloud, where the checkout
    is not writable between restarts. The switches move into the workbook in the
    step that makes Sheets the live configuration.
    """
    if not is_phase(phase_id):
        raise ValueError(f"unknown phase {phase_id!r}")
    set_setting(f"{phase_id}_open", is_open)


def set_setting(key: str, value) -> None:
    """Write one CONFIG setting to whichever configuration is live.

    On the workbook this is a one-row update, so it survives the restart that
    would discard a file written into the deployed checkout.
    """
    book = _workbook()
    if book is not None:
        rows = book.read_tab(sheets.CONFIG)
        index = sheets.row_index(rows, sheets.CONFIG)
        payload = {"key": key, "value": str(value)}
        if key in index:
            book.update_row(sheets.CONFIG, index[key], payload)
        else:
            book.append_rows(sheets.CONFIG, [payload])
    else:
        data = manifest()
        data.setdefault("config", {})[key] = value
        header = "\n".join(
            line for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines()
            if line.startswith("#")
        )
        MANIFEST_PATH.write_text(
            header + "\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    invalidate()


# -------------------------------------------------------------- evaluators
def evaluators() -> list[dict]:
    return list(_tables()["evaluators"])


def evaluator_names() -> list[str]:
    """Selectable names, in manifest order. Admin-only identities included."""
    return [e["name"] for e in evaluators()]


def evaluator_by_name(name: str) -> dict | None:
    for entry in evaluators():
        if entry.get("name") == name:
            return entry
    return None


def evaluator(evaluator_id: str) -> dict | None:
    for entry in evaluators():
        if entry.get("evaluator_id") == evaluator_id:
            return entry
    return None


def pair_of(evaluator_id: str) -> str | None:
    """Internal only. Evaluators are shown their split ids, never a pair letter.

    The allocation email's "Group A/B/C" labels contradict the AGR split names,
    so showing either to an evaluator is worse than showing nothing.
    """
    entry = evaluator(evaluator_id)
    return (entry or {}).get("pair_id")


def agreement_split(evaluator_id: str) -> str:
    return str((evaluator(evaluator_id) or {}).get("agreement_split") or "")


def individual_split(evaluator_id: str) -> str:
    return str((evaluator(evaluator_id) or {}).get("individual_split") or "")


PENDING_SPLIT = "pending assignment"


def splits_of(evaluator_id: str) -> dict[str, str]:
    """What to show the evaluator when they confirm their identity.

    An evaluator whose individual papers are still reserved — the IND-1 pool,
    whose division is not settled — has no split id to show. Saying nothing
    reads as "you have no individual phase", which is false: they have papers
    held for them and a decision outstanding. So the phase is named as pending
    instead. The reserved papers themselves stay invisible; announcing which
    papers someone might be asked to read would pre-empt the decision.
    """
    splits = {AGREEMENT: agreement_split(evaluator_id),
              INDIVIDUAL: individual_split(evaluator_id)}
    for phase, split in splits.items():
        if not split and holds_reservations(evaluator_id, phase):
            splits[phase] = PENDING_SPLIT
    return splits


def holds_reservations(evaluator_id: str, phase_id: str) -> bool:
    """Are papers being held for this evaluator in a phase not yet divided?"""
    return any(row.get("evaluator_id") == evaluator_id
               for row in reserved(phase_id))


def is_admin(evaluator_id: str) -> bool:
    return bool((evaluator(evaluator_id) or {}).get("is_admin"))


# ------------------------------------------------------------- assignments
def assignments() -> list[dict]:
    return list(_tables()["assignments"])


def assigned(evaluator_id: str, phase_id: str) -> list[dict]:
    """Papers actually assigned to this evaluator in this phase.

    Reservations are deliberately excluded: they are storage prepared in advance
    for a decision nobody has taken, and showing one would put a paper in front
    of an evaluator who may never be asked to read it.
    """
    rows = [
        row for row in assignments()
        if row.get("evaluator_id") == evaluator_id
        and row.get("phase_id") == phase_id
        and state_of(row) == ASSIGNED
    ]
    return sorted(rows, key=lambda r: (r.get("split_id") or "",
                                       int(r.get("assignment_order") or 0)))


def assigned_source_ids(evaluator_id: str, phase_id: str) -> list[str]:
    return [row["source_id"] for row in assigned(evaluator_id, phase_id)]


def is_assigned(evaluator_id: str, phase_id: str, source_id: str) -> bool:
    return source_id in assigned_source_ids(evaluator_id, phase_id)


def training_source_ids() -> list[str]:
    return sorted({
        row["source_id"] for row in assignments() if row.get("phase_id") == TRAINING
    })


def reserved(phase_id: str | None = None) -> list[dict]:
    """Preallocated possibilities awaiting a decision."""
    return [row for row in assignments()
            if state_of(row) == RESERVED
            and (phase_id is None or row.get("phase_id") == phase_id)]


def reserved_sources(phase_id: str | None = None) -> list[str]:
    """The distinct papers a reservation covers, each held for several people."""
    return sorted({row["source_id"] for row in reserved(phase_id)})


def reservations_for(source_id: str) -> list[dict]:
    return [row for row in reserved() if row.get("source_id") == source_id]


def with_current_state(reviews) -> list[dict]:
    """Reviews with today's assignment state added beside the recorded one.

    `assignment_state` on the row is history: what the review was when its
    evaluator began. `current_assignment_state` is context: what the
    configuration says now. They are separate on purpose — reading only the
    current table would let a later change silently reinterpret a finished
    evaluation, and reading only the recorded one would hide that the
    configuration has since moved.

    A review nobody has started has no recorded state, so only the current one
    is meaningful for it.
    """
    current = {row.get("assignment_key"): state_of(row) for row in assignments()}
    out = []
    for review in reviews:
        key = review.get("assignment_key") or assignment_key(
            review.get("phase_id", ""), review.get("evaluator_id", ""),
            review.get("source_id", ""))
        out.append({**review, "assignment_key": key,
                    "current_assignment_state": current.get(key, "")})
    return out


def assignment_state(key: str) -> str:
    for row in assignments():
        if row.get("assignment_key") == key:
            return state_of(row)
    return ""


def set_assignment_state(key: str, state: str) -> None:
    """Activate a reservation, or return an assignment to reserved.

    The whole point of preallocating both possibilities is that this is a
    one-field edit: no review, response, edge row or row range is created or
    destroyed, so it is safe to take, reverse and retake until somebody starts
    work — after which `has_activity` locks the row.
    """
    if state not in ASSIGNMENT_STATES:
        raise ValueError(f"unknown assignment state {state!r}")
    book = _workbook()
    if book is not None:
        rows = book.read_tab(sheets.ASSIGNMENTS)
        index = sheets.row_index(rows, sheets.ASSIGNMENTS)
        if key not in index:
            raise KeyError(key)
        row = next(r for r in rows if r.get("assignment_key") == key)
        book.update_row(sheets.ASSIGNMENTS, index[key],
                        {**row, "assignment_state": state})
    else:
        data = manifest()
        for row in data.get("assignments", []):
            if row.get("assignment_key") == key:
                row["assignment_state"] = state
                break
        else:
            raise KeyError(key)
        header = "\n".join(
            line for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines()
            if line.startswith("#")
        )
        MANIFEST_PATH.write_text(
            header + "\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    invalidate()


# -------------------------------------------------------------- validation
def snapshot_matches(snapshot_id: str) -> bool:
    """The Brain on disk is the one this split was accepted against."""
    configured = brain_snapshot_id()
    if not configured:
        return True
    return snapshot_id in (configured, configured[:16]) or configured.startswith(snapshot_id)


def validate(known_source_ids: set[str], snapshot_id: str,
             reviews=None) -> list[str]:
    """Problems worth surfacing before anyone evaluates. Reported, not raised."""
    problems: list[str] = []

    if reviews is not None:
        for key in orphaned(reviews):
            problems.append(
                f"{key} has answers against it but no assignment row — an active "
                f"assignment was removed or reassigned"
            )

    training = set(training_source_ids())
    seen_splits: dict[str, str] = {}
    for row in assignments():
        source_id = row.get("source_id")
        phase_id = row.get("phase_id")
        if source_id not in known_source_ids:
            problems.append(f"assignment {source_id} is not in the Brain")
        if not is_phase(phase_id):
            problems.append(f"assignment {row.get('assignment_key')} has "
                            f"unknown phase {phase_id!r}")
        if phase_id in (AGREEMENT, INDIVIDUAL):
            if source_id in training:
                problems.append(
                    f"{source_id} is assigned for {phase_id} but is also a training paper"
                )
            split = row.get("split_id")
            if source_id in seen_splits and seen_splits[source_id] != split:
                problems.append(
                    f"{source_id} is in split {seen_splits[source_id]} and split {split}"
                )
            seen_splits[source_id] = split

    keys = [r.get("assignment_key") for r in assignments()]
    duplicates = {k for k in keys if k and keys.count(k) > 1}
    if duplicates:
        problems.append(f"duplicate assignment_key: {sorted(duplicates)}")

    for row in assignments():
        if state_of(row) not in ASSIGNMENT_STATES:
            problems.append(f"{row.get('assignment_key')} has unknown state "
                            f"{row.get('assignment_state')!r}")

    # Activating both reservations on one paper would quietly turn an individual
    # pool into a second agreement set, which is a different experiment.
    holders: dict[str, list[str]] = {}
    for row in assignments():
        if row.get("phase_id") == INDIVIDUAL and state_of(row) == ASSIGNED:
            holders.setdefault(row["source_id"], []).append(row.get("evaluator_id", ""))
    for source_id, names in sorted(holders.items()):
        if len(names) > 1:
            problems.append(
                f"{source_id} is assigned to {len(names)} evaluators in the "
                f"individual phase ({', '.join(sorted(names))}) — an individual "
                f"paper is evaluated once"
            )

    if reviews is not None:
        active = active_assignment_keys(reviews)
        for row in reserved():
            if row.get("assignment_key") in active:
                problems.append(
                    f"{row['assignment_key']} is reserved but has activity against "
                    f"it — a reservation should never have been evaluated"
                )

    ids = [e.get("evaluator_id") for e in evaluators()]
    if len(ids) != len(set(ids)):
        problems.append("duplicate evaluator_id in the manifest")
    for entry in evaluators():
        if not entry.get("agreement_split"):
            problems.append(f"evaluator {entry.get('name')} has no agreement split")

    for name in missing_secrets():
        problems.append(f"{name} is not set — export it before anyone signs in")
    return problems
