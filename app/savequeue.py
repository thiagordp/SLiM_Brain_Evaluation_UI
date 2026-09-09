"""Asynchronous save queue.

The design fixes the semantics, not the backend:

* changing an answer updates the UI immediately and queues the write;
* repeated edits to the same response collapse to the latest pending value,
  because writes are keyed by the deterministic response key;
* writes that arrive together go out together;
* normal navigation never waits for storage;
* **a write is never lost.** Retries that exhaust their attempts move to a
  failed registry and keep being retried, rather than being dropped with a red
  status nobody can act on;
* **completion and submission are the exception** — they flush every pending
  write and refuse while anything is unresolved.

A single background worker thread owns the writes, so the store still sees one
writer per process and rows are never interleaved mid-update.
"""
from __future__ import annotations

import threading
import time

IDLE, SAVING, SAVED = "idle", "saving", "saved"
FAILED, RETRYING, CONFLICT = "failed", "retrying", "conflict"

#: Attempts before a write moves from "being written" to "failed but retained".
MAX_ATTEMPTS = 3
RETRY_SECONDS = 1.0

#: How long a failed write waits before the queue tries it again. It is retried
#: for as long as the session lives: a lost answer is worse than a slow one.
FAILED_RETRY_SECONDS = 20.0

#: Writes that arrive together go out together. An evaluator answering quickly,
#: or a page that settles several answers at once, otherwise costs one request
#: each — and the Sheets quota is counted in requests.
BATCH_MAX = 25


class SaveQueue:
    def __init__(self) -> None:
        self._pending: dict[str, tuple] = {}   # key -> (function, args, kwargs, done)
        self._failed: dict[str, tuple] = {}    # the same, awaiting another attempt
        self._errors: dict[str, str] = {}      # key -> why it last failed
        self._retry_at = 0.0
        self._lock = threading.Lock()
        self._wake = threading.Condition(self._lock)
        self._state = IDLE
        self._error = ""
        self._worker: threading.Thread | None = None
        self._stop = False
        self._batch_of = None
        self._write_many = None
        self._fatal: tuple[type[BaseException], ...] = ()
        self._conflicts: dict[str, str] = {}

    # ---------------------------------------------------------- public API
    def submit(self, key: str, function, *args, on_success=None, **kwargs) -> None:
        """Queue a write. A newer edit to the same key replaces the older one."""
        with self._wake:
            self._pending[key] = (function, args, kwargs, on_success)
            self._failed.pop(key, None)        # superseded by a fresher value
            self._errors.pop(key, None)
            self._state = SAVING
            self._wake.notify()
        self._ensure_worker()

    def set_fatal(self, *exception_types) -> None:
        """Failures that must not be retried.

        A conflict is not a transient error. The write was refused because the
        row had already moved on, and retrying re-sends the same stale
        expectation — so it would fail identically for ever, hold the queue
        unresolved, and block completion on a paper nothing is wrong with. It is
        reported to the evaluator instead, and the stored value stands.
        """
        self._fatal = tuple(exception_types)

    def set_batch_writer(self, batch_of, write_many) -> None:
        """Teach the queue to coalesce one kind of write.

        ``batch_of(function, args, kwargs)`` returns a record when that write can
        travel with others, or None; ``write_many(records)`` sends them as one
        request and returns one result per record, in order. Anything
        unrecognised keeps going out on its own.
        """
        self._batch_of = batch_of
        self._write_many = write_many

    def flush(self, timeout: float = 30.0) -> bool:
        """Block until everything is written. Used only before submission.

        Returns False while anything is unresolved — including a write that has
        exhausted its attempts and is waiting to be retried. A caller that
        treated that as "nothing left to do" would mark a paper complete whose
        last answer never reached storage.
        """
        self._ensure_worker()
        with self._wake:
            self._retry_at = 0.0               # try failed writes again, now
            self._wake.notify()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if not self._pending and not self._failed:
                    return True
            time.sleep(0.05)
        with self._lock:
            return not self._pending and not self._failed

    def retry_now(self) -> None:
        """Ask the worker to reattempt failed writes immediately."""
        with self._wake:
            self._retry_at = 0.0
            self._wake.notify()
        self._ensure_worker()

    @property
    def state(self) -> tuple[str, str, int]:
        with self._lock:
            return self._state, self._error, len(self._pending) + len(self._failed)

    @property
    def unresolved(self) -> int:
        """Writes not yet in storage: queued, being retried, or failed."""
        with self._lock:
            return len(self._pending) + len(self._failed)

    @property
    def failures(self) -> dict[str, str]:
        with self._lock:
            return dict(self._errors)

    @property
    def conflicts(self) -> dict[str, str]:
        """Edits refused because the row had changed elsewhere."""
        with self._lock:
            return dict(self._conflicts)

    def clear_conflicts(self) -> None:
        with self._lock:
            self._conflicts.clear()
            if self._state == CONFLICT:
                self._state = SAVED if not self._pending and not self._failed else SAVING

    def stop(self) -> None:
        with self._wake:
            self._stop = True
            self._wake.notify()

    # -------------------------------------------------------------- worker
    def _ensure_worker(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._stop = False
        self._worker = threading.Thread(target=self._run, daemon=True,
                                        name="he-save-queue")
        self._worker.start()

    def _take(self):
        """The next batch of work: fresh writes first, then anything failed."""
        with self._wake:
            while not self._pending and not self._stop:
                if self._failed and time.monotonic() >= self._retry_at:
                    break
                self._wake.wait(timeout=0.5)
            if self._stop and not self._pending and not self._failed:
                return None
            if self._pending:
                items = list(self._pending.items())
            elif self._failed and time.monotonic() >= self._retry_at:
                self._state = RETRYING
                items = list(self._failed.items())
            else:
                return []

        if self._batch_of is None:
            return [items[0]]
        batch = []
        for key, call in items:
            if self._batch_of(*call[:3]) is None:
                return [(key, call)] if not batch else batch
            batch.append((key, call))
            if len(batch) >= BATCH_MAX:
                break
        return batch or [items[0]]

    def _write(self, batch) -> list:
        if len(batch) == 1 or self._write_many is None:
            return [function(*args, **kwargs)
                    for _, (function, args, kwargs, _done) in batch]
        return list(self._write_many([self._batch_of(*call[:3])
                                      for _, call in batch]))

    def _run(self) -> None:
        while True:
            batch = self._take()
            if batch is None:
                return
            if not batch:
                continue

            error, results, refused = "", [], False
            for attempt in range(MAX_ATTEMPTS):
                try:
                    results = self._write(batch)
                    error = ""
                    break
                except self._fatal as failure:
                    error, refused = str(failure), True
                    break
                except Exception as failure:
                    error = str(failure)
                    if attempt + 1 < MAX_ATTEMPTS:
                        time.sleep(RETRY_SECONDS * (attempt + 1))

            with self._lock:
                for index, (key, call) in enumerate(batch):
                    superseded = (self._pending.get(key) not in (None, call))
                    if not superseded:
                        self._pending.pop(key, None)
                    if refused:
                        # Not retried, not retained: the stored value stands and
                        # the evaluator is told their edit was not applied.
                        self._conflicts[key] = error
                        self._failed.pop(key, None)
                        self._errors.pop(key, None)
                    elif error:
                        if not superseded:
                            # Retained, not dropped: it is the evaluator's answer.
                            self._failed[key] = call
                            self._errors[key] = error
                    else:
                        self._failed.pop(key, None)
                        self._errors.pop(key, None)
                        done = call[3]
                        if done is not None and index < len(results):
                            try:
                                done(results[index])
                            except Exception:      # a callback must not lose a write
                                pass
                if error and not refused:
                    self._state, self._error = FAILED, error
                    self._retry_at = time.monotonic() + FAILED_RETRY_SECONDS
                elif self._pending or self._failed:
                    self._state, self._error = SAVING, ""
                elif self._conflicts:
                    self._state, self._error = CONFLICT, error
                else:
                    self._state, self._error = SAVED, ""
