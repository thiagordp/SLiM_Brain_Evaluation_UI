"""An in-memory Google Sheets workbook for tests. Never a runtime store.

It mirrors the behaviour the application depends on: row 1 is the header, data
starts at row 2, appends go after the last non-empty row, a batched read is one
request, and a tab the workbook lacks is an error rather than an empty result.
Every request is counted, so tests can assert what a page costs.
"""
from __future__ import annotations

import collections
import threading

import sheets


class FakeWorkbook:
    def __init__(self, default_tab: str | None = "Sheet1") -> None:
        self.sheet_id = f"fake-{id(self)}"
        self.tabs: dict[str, list[list[str]]] = {}
        self.requests = collections.Counter()
        self._lock = threading.RLock()
        if default_tab:
            self.tabs[default_tab] = []

    # ------------------------------------------------------------ structure
    def tab_titles(self) -> list[str]:
        self.requests["list"] += 1
        return list(self.tabs)

    def is_blank(self, title: str) -> bool:
        self.requests["read"] += 1
        return not any(str(c).strip() for row in self.tabs[title] for c in row)

    def create_tab(self, tab: str) -> None:
        self.requests["write"] += 1
        if tab in self.tabs:
            raise sheets.StorageError(f"tab {tab} exists")
        self.tabs[tab] = []

    def delete_tab(self, title: str) -> None:
        self.requests["write"] += 1
        if len(self.tabs) == 1 and title in self.tabs:
            raise sheets.StorageError("a workbook must keep one tab")
        self.tabs.pop(title, None)

    def write_header(self, tab: str) -> None:
        self.requests["write"] += 1
        rows = self._tab(tab)
        header = list(sheets.COLUMNS[tab])
        if rows:
            rows[0] = header
        else:
            rows.append(header)

    def headers(self, tabs) -> dict[str, list[str]]:
        self.requests["read"] += 1
        return {t: list(self.tabs[t][0]) if self.tabs.get(t) else [] for t in tabs}

    def _tab(self, tab: str) -> list[list[str]]:
        if tab not in self.tabs:
            raise sheets.StorageError(f"The workbook has no {tab} tab.")
        return self.tabs[tab]

    # ---------------------------------------------------------------- reads
    def _rows(self, tab: str, first: int | None, last: int | None) -> list[dict]:
        rows = self._tab(tab)
        if first is None:
            body = rows[1:]
        else:
            body = rows[first - 1:last]
        while body and not any(body[-1]):
            body = body[:-1]
        return [sheets.as_row(tab, raw) for raw in body]

    def read_tab(self, tab: str) -> list[dict[str, str]]:
        with self._lock:
            self.requests["read"] += 1
            return self._rows(tab, None, None)

    def read_range(self, tab: str, first: int, last: int) -> list[dict[str, str]]:
        with self._lock:
            self.requests["read"] += 1
            return self._rows(tab, first, last) if last >= first else []

    def read_ranges(self, requests) -> list[list[dict[str, str]]]:
        with self._lock:
            self.requests["read"] += 1
            return [self._rows(tab, first, last) for tab, first, last in requests]

    # --------------------------------------------------------------- writes
    def append_rows(self, tab: str, rows) -> int:
        with self._lock:
            rows = list(rows)
            if not rows:
                return 0
            self.requests["write"] += 1
            target = self._tab(tab)
            while len(target) > 1 and not any(target[-1]):
                target.pop()
            for row in rows:
                target.append([str(v) for v in sheets.ordered(tab, row)])
            return len(rows)

    def update_rows(self, tab: str, updates) -> None:
        with self._lock:
            updates = list(updates)
            if not updates:
                return
            self.requests["write"] += 1
            target = self._tab(tab)
            for number, values in updates:
                index = number - 1
                if not 0 < index < len(target):
                    raise sheets.StorageError(f"{tab} has no row {number}")
                target[index] = [str(v) for v in sheets.ordered(tab, values)]

    # ---------------------------------------------------------------- tests
    def count(self, tab: str) -> int:
        return max(len(self.tabs.get(tab, [])) - 1, 0)
