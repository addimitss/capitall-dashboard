from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from ..services.auth import require_user
from ..services import insights_service as ins
from ..state import store

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/overview")
async def overview(_: dict = Depends(require_user)) -> dict:
    if not store.has_data:
        raise HTTPException(400, "No workbook uploaded.")
    return ins.overview(store.all_sheets())


@router.get("/mismatches")
async def mismatches(_: dict = Depends(require_user)) -> dict:
    if not store.has_data:
        raise HTTPException(400, "No workbook uploaded.")
    return ins.mismatches(store.all_sheets())
