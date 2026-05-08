from __future__ import annotations
from datetime import datetime
import logging
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Body
from ..config import settings
from ..models.schemas import (
    UploadResponse, SheetMeta, SheetSummary, TableQuery, TableResponse,
)
from ..services import excel_service as svc
from ..services import schema as schema_svc
from ..services.auth import require_user
from ..state import store

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["excel"])


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...), user: dict = Depends(require_user)) -> UploadResponse:
    if user.get("role") == "viewer":
        raise HTTPException(403, "Viewers cannot upload data.")
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Please upload an .xlsx or .xlsm file.")
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB limit.")
    try:
        sheets = svc.parse_workbook(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        log.exception("Upload parse failure")
        raise HTTPException(status_code=500, detail=f"Failed to parse workbook: {e}") from e

    try:
        validation = schema_svc.validate(sheets, strict=settings.STRICT_SCHEMA)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Schema validation failed: {e}") from e

    uploaded_at = datetime.utcnow().isoformat() + "Z"
    store.set(file.filename, sheets, uploaded_at)
    return UploadResponse(
        filename=file.filename,
        uploaded_at=uploaded_at,
        sheets=list(sheets.keys()),
        rows_per_sheet={n: len(d) for n, d in sheets.items()},
        warnings=validation.get("warnings", []),
    )


@router.get("/workbook")
async def workbook_meta(_: dict = Depends(require_user)) -> dict:
    return store.meta()


@router.delete("/workbook")
async def clear_workbook(user: dict = Depends(require_user)) -> dict:
    if user.get("role") == "viewer":
        raise HTTPException(403, "Viewers cannot clear data.")
    store.clear()
    return {"cleared": True}


@router.get("/sheets/{name}/meta", response_model=SheetMeta)
async def sheet_meta(name: str, _: dict = Depends(require_user)) -> SheetMeta:
    df = store.get_sheet(name)
    if df is None:
        raise HTTPException(404, "Sheet not found.")
    return SheetMeta(name=name, rows=len(df), columns=svc.column_meta(df))


@router.get("/sheets/{name}/summary", response_model=SheetSummary)
async def sheet_summary(name: str, _: dict = Depends(require_user)) -> SheetSummary:
    df = store.get_sheet(name)
    if df is None:
        raise HTTPException(404, "Sheet not found.")
    return SheetSummary(**svc.build_summary(name, df))


@router.post("/sheets/{name}/data", response_model=TableResponse)
async def sheet_data(name: str, q: TableQuery = Body(...), _: dict = Depends(require_user)) -> TableResponse:
    df = store.get_sheet(name)
    if df is None:
        raise HTTPException(404, "Sheet not found.")
    sub, total = svc.apply_query(
        df, q.search, q.sort_by, q.sort_dir, q.filters, q.page, q.page_size,
    )
    return TableResponse(
        sheet=name,
        page=q.page,
        page_size=q.page_size,
        total=total,
        columns=svc.column_meta(df),
        rows=svc.df_to_records(sub),
    )
