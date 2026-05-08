from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    filename: str
    uploaded_at: str
    sheets: list[str]
    rows_per_sheet: dict[str, int]
    warnings: list[str] = Field(default_factory=list)


class SheetMeta(BaseModel):
    name: str
    rows: int
    columns: list[dict[str, str]]  # [{name, dtype, kind}]


class SheetSummary(BaseModel):
    sheet: str
    rows: int
    cards: list[dict[str, Any]]
    charts: list[dict[str, Any]]


class TableQuery(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)
    search: str | None = None
    sort_by: str | None = None
    sort_dir: Literal["asc", "desc"] = "asc"
    filters: dict[str, Any] = Field(default_factory=dict)


class TableResponse(BaseModel):
    sheet: str
    page: int
    page_size: int
    total: int
    columns: list[dict[str, str]]
    rows: list[dict[str, Any]]


class ChatRequest(BaseModel):
    message: str
    sheet: str | None = None  # context sheet
    history: list[dict[str, str]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    provider: str
    model: str
    context_sheet: str | None = None
