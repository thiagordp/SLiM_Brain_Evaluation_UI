"""Runtime configuration: which round this is, who evaluates what, which switches are on.

At runtime everything comes from the round workbook — ROUND, CONFIG, EVALUATORS
and ASSIGNMENTS — so the administrator can pause a phase or activate a
reservation without a redeploy. `data/manifest.yaml` is the generated input
that `tools/bootstrap_round.py` writes into a fresh workbook, and the
reproducibility record of what was bootstrapped; the app never falls back to it.

The app never infers an assignment. It reads explicit evaluator x Source x phase
rows, generated from the allocation file by `tools/build_assignments.py`.

Three phases, all open from the start, none gating another:

    training     optional practice, the same papers for everyone
    agreement    both evaluators of a pair over one shared set
    individual   one evaluator per paper

Secrets never live here: the shared password and the admin secret come from
environment variables or Streamlit secrets.
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

DATA = pathlib.Path(__file__).resolve().parent / "data"
ROUND_CONFIG_PATH = DATA / "round.yaml"

SWITCH_TTL = 15.0
TABLE_TTL = 300.0

ENV_PASSWORD = "HE_APP_PASSWORD"
ENV_ADMIN_SECRET = "HE_ADMIN_SECRET"
ENV_ROUND_ID = "HE_ROUND_ID"


class _Cache:
    """A small time-boxed cache that works in and out of Streamlit."""

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


# ------------------------------------------------------------- the round
@functools.lru_cache(maxsize=1)
def round_config() -> dict:
    return yaml.safe_load(ROUND_CONFIG_PATH.read_text(encoding="utf-8")) or {}


def round_id() -> str:
    """The configured round. The workbook must say the same, or nothing starts."""
    return os.environ.get(ENV_ROUND_ID) or str(round_config().get("round_id") or "")


def allocation_path() -> pathlib.Path:
    return DATA / str(round_config().get("allocation"))


def manifest_path() -> pathlib.Path:
    return DATA / str(round_config().get("manifest") or "manifest.yaml")


def load_manifest_file() -> dict:
    """The generated manifest. Bootstrap input only — never a runtime source."""
    return yaml.safe_load(manifest_path().read_text(encoding="utf-8")) or {}


def round_metadata() -> dict[str, str]:
    import store

    return store.round_metadata()


# -------------------------------------------------------------- secrets
def _secrets():
    try:
        import streamlit as st

        return st.secrets
    except Exception:
        return {}


def _secret(name: str) -> str:
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


# ----------------------------------------------------------- live tables
def _workbook():
    import store

    return store.workbook()


def _truthy(value) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _load_switches() -> dict:
    rows = _workbook().read_tab(sheets.CONFIG)
    return {r["key"]: r["value"] for r in rows if r.get("key")}


def _load_tables() -> dict:
    book = _workbook()
    evaluators, assignments = book.read_ranges(
        [(sheets.EVALUATORS, None, None), (sheets.ASSIGNMENTS, None, None)])
    return {
        "evaluators": [{**r, "is_admin": _truthy(r.get("is_admin")),
                        "pair_id": r.get("pair_id") or None} for r in evaluators],
        "assignments": [{**r, "assignment_order": int(r["assignment_order"])
                         if str(r.get("assignment_order") or "").isdigit() else 0,
                         "assignment_state": state_of(r)} for r in assignments],
    }


def config() -> dict:
    return _SWITCHES.get(_load_switches)


def _tables() -> dict:
    return _TABLES.get(_load_tables)


# ------------------------------------------------------------------ phases
TRAINING, AGREEMENT, INDIVIDUAL = "training", "agreement", "individual"
PHASES = (TRAINING, AGREEMENT, INDIVIDUAL)
PHASE_LABEL = {TRAINING: "Training", AGREEMENT: "Agreement", INDIVIDUAL: "Individual"}

#: Training is practice: never required, and never reported as a problem.
OPTIONAL_PHASES = (TRAINING,)


def is_phase(phase_id: str) -> bool:
    return phase_id in PHASES


def is_optional(phase_id: str) -> bool:
    return phase_id in OPTIONAL_PHASES


ASSIGNED = "assigned"
#: Preallocated storage for a decision not yet taken: invisible to the
#: evaluator and counted toward nothing until activated.
RESERVED = "reserved"
ASSIGNMENT_STATES = (ASSIGNED, RESERVED)


def state_of(row: dict) -> str:
    return str(row.get("assignment_state") or ASSIGNED)


def phase_open(phase_id: str) -> bool:
    value = config().get(f"{phase_id}_open", "")
    return _truthy(value) if isinstance(value, str) else bool(value)


def open_phases() -> list[str]:
    return [phase for phase in PHASES if phase_open(phase)]


#: The ROUND keys that say what the experiment is. Phase switches are not among
#: them: closing a phase changes what people can do next, not what an answer means.
EXPERIMENT_KEYS = ("round_id", "eval_spec_version", "brain_snapshot_id",
                   "definitions_id", "allocation_id")


def config_version() -> str:
    """A stable digest of the experimental configuration, recorded on reviews."""
    metadata = round_metadata()
    payload = {
        "experiment": {k: str(metadata.get(k, "")) for k in EXPERIMENT_KEYS},
        "evaluators": sorted(
            (str(e.get("evaluator_id")), str(e.get("name")), bool(e.get("is_admin")),
             str(e.get("agreement_split") or ""), str(e.get("individual_split") or ""))
            for e in evaluators()),
        "assignments": sorted(
            (str(a.get("assignment_key")), str(a.get("evaluator_id") or ""),
             str(a.get("phase_id")), str(a.get("split_id")), str(a.get("source_id")),
             state_of(a))
            for a in assignments()),
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------------------- immutability
def assignment_key(phase_id: str, evaluator_id: str, source_id: str) -> str:
    return f"{phase_id}|{evaluator_id}|{source_id}"


def has_activity(review: dict) -> bool:
    """Durable evidence a person worked on a review. A preallocated row is not."""
    status = (review.get("status") or "").strip()
    if status and status != "not_started":
        return True
    return bool((review.get("started_at") or "").strip()
                or (review.get("last_saved_at") or "").strip())


def active_assignment_keys(reviews) -> set[str]:
    return {r.get("assignment_key") or assignment_key(
                r.get("phase_id", ""), r.get("evaluator_id", ""), r.get("source_id", ""))
            for r in reviews if has_activity(r)}


def set_setting(key: str, value) -> None:
    book = _workbook()
    rows = book.read_tab(sheets.CONFIG)
    index = sheets.row_index(rows, sheets.CONFIG)
    payload = {"key": key, "value": str(value)}
    if key in index:
        book.update_rows(sheets.CONFIG, [(index[key], payload)])
    else:
        book.append_rows(sheets.CONFIG, [payload])
    invalidate()


def set_phase(phase_id: str, is_open: bool) -> None:
    if not is_phase(phase_id):
        raise ValueError(f"unknown phase {phase_id!r}")
    set_setting(f"{phase_id}_open", "true" if is_open else "false")


def set_assignment_state(key: str, state: str) -> None:
    """Activate a reservation, or return an assignment to reserved.

    Its storage was preallocated with the rest, so this is a one-field edit, safe
    until somebody starts work — after which the admin page locks the row.
    """
    if state not in ASSIGNMENT_STATES:
        raise ValueError(f"unknown assignment state {state!r}")
    book = _workbook()
    rows = book.read_tab(sheets.ASSIGNMENTS)
    index = sheets.row_index(rows, sheets.ASSIGNMENTS)
    if key not in index:
        raise KeyError(key)
    row = next(r for r in rows if r.get("assignment_key") == key)
    book.update_rows(sheets.ASSIGNMENTS, [(index[key], {**row, "assignment_state": state})])
    invalidate()


# -------------------------------------------------------------- evaluators
def evaluators() -> list[dict]:
    return list(_tables()["evaluators"])


def evaluator_names() -> list[str]:
    return [e["name"] for e in evaluators()]


def evaluator_by_name(name: str) -> dict | None:
    return next((e for e in evaluators() if e.get("name") == name), None)


def evaluator(evaluator_id: str) -> dict | None:
    return next((e for e in evaluators() if e.get("evaluator_id") == evaluator_id), None)


def pair_of(evaluator_id: str) -> str | None:
    """Internal only. Evaluators are shown split ids, never a pair letter."""
    return (evaluator(evaluator_id) or {}).get("pair_id")


def splits_of(evaluator_id: str) -> dict[str, str]:
    entry = evaluator(evaluator_id) or {}
    return {AGREEMENT: str(entry.get("agreement_split") or ""),
            INDIVIDUAL: str(entry.get("individual_split") or "")}


def is_admin(evaluator_id: str) -> bool:
    return bool((evaluator(evaluator_id) or {}).get("is_admin"))


# ------------------------------------------------------------- assignments
def assignments() -> list[dict]:
    return list(_tables()["assignments"])


def assigned(evaluator_id: str, phase_id: str) -> list[dict]:
    rows = [row for row in assignments()
            if row.get("evaluator_id") == evaluator_id
            and row.get("phase_id") == phase_id and state_of(row) == ASSIGNED]
    return sorted(rows, key=lambda r: (r.get("split_id") or "",
                                       int(r.get("assignment_order") or 0)))


def assigned_source_ids(evaluator_id: str, phase_id: str) -> list[str]:
    return [row["source_id"] for row in assigned(evaluator_id, phase_id)]


def is_assigned(evaluator_id: str, phase_id: str, source_id: str) -> bool:
    return source_id in assigned_source_ids(evaluator_id, phase_id)


def assignment(phase_id: str, evaluator_id: str, source_id: str) -> dict:
    key = assignment_key(phase_id, evaluator_id, source_id)
    return next((a for a in assignments() if a.get("assignment_key") == key), {})


def reserved(phase_id: str | None = None) -> list[dict]:
    return [row for row in assignments() if state_of(row) == RESERVED
            and (phase_id is None or row.get("phase_id") == phase_id)]


def reserved_sources(phase_id: str | None = None) -> list[str]:
    return sorted({row["source_id"] for row in reserved(phase_id)})


def reservations_for(source_id: str) -> list[dict]:
    return [row for row in reserved() if row.get("source_id") == source_id]


def with_current_state(reviews) -> list[dict]:
    """Reviews with today's assignment state beside the one recorded at start."""
    current = {row.get("assignment_key"): state_of(row) for row in assignments()}
    return [{**review, "current_assignment_state":
             current.get(review.get("assignment_key"), "")} for review in reviews]


# -------------------------------------------------------------- validation
def validate(known_source_ids: set[str], reviews=None) -> list[str]:
    """Configuration problems for the administrator. Reported, not raised."""
    problems: list[str] = []
    keys = {a.get("assignment_key") for a in assignments()}
    if reviews is not None:
        for key in sorted(active_assignment_keys(reviews) - keys):
            problems.append(f"{key} has answers against it but no assignment row")
        active = active_assignment_keys(reviews)
        for row in reserved():
            if row.get("assignment_key") in active:
                problems.append(f"{row['assignment_key']} is reserved but has activity")
    for row in assignments():
        if row.get("source_id") not in known_source_ids:
            problems.append(f"assignment {row.get('assignment_key')} names a Source "
                            f"not in the Brain")
    holders: dict[str, set] = {}
    for row in assignments():
        if row.get("phase_id") == INDIVIDUAL and state_of(row) == ASSIGNED:
            holders.setdefault(row["source_id"], set()).add(row.get("evaluator_id"))
    for source_id, names in sorted(holders.items()):
        if len(names) > 1:
            problems.append(f"{source_id} is assigned to {len(names)} evaluators in "
                            f"the individual phase")
    for name in missing_secrets():
        problems.append(f"{name} is not set")
    return problems
