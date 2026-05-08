"""In-memory store for uploaded workbook. Single-process; swap with Redis/DB for multi-worker."""
from __future__ import annotations
from threading import RLock
from typing import Any
import pandas as pd


class WorkbookStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._sheets: dict[str, pd.DataFrame] = {}
        self._filename: str | None = None
        self._uploaded_at: str | None = None

    def set(self, filename: str, sheets: dict[str, pd.DataFrame], uploaded_at: str) -> None:
        with self._lock:
            self._sheets = sheets
            self._filename = filename
            self._uploaded_at = uploaded_at

    def clear(self) -> None:
        with self._lock:
            self._sheets = {}
            self._filename = None
            self._uploaded_at = None

    @property
    def has_data(self) -> bool:
        return bool(self._sheets)

    @property
    def sheet_names(self) -> list[str]:
        return list(self._sheets.keys())

    def get_sheet(self, name: str) -> pd.DataFrame | None:
        return self._sheets.get(name)

    def meta(self) -> dict[str, Any]:
        return {
            "filename": self._filename,
            "uploaded_at": self._uploaded_at,
            "sheets": self.sheet_names,
        }

    def all_sheets(self) -> dict[str, pd.DataFrame]:
        return dict(self._sheets)


store = WorkbookStore()
