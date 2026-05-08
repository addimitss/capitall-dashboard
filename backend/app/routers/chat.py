from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException
from ..models.schemas import ChatRequest, ChatResponse
from ..services.auth import require_user
from ..services.excel_service import build_chat_context
from ..services.insights_service import mismatches
from ..services.llm.base import ChatMessage
from ..services.llm.factory import get_llm
from ..state import store

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

SYSTEM_PROMPT = (
    "You are an AML/risk analytics assistant for an enterprise dashboard. "
    "You answer business-friendly, concise questions strictly grounded in the supplied workbook context. "
    "If the answer is not in the context, say so. Use Indian Rupee (₹) when amounts are present. "
    "Prefer short paragraphs and small bullet lists. Cite sheet names when useful."
)

_MISMATCH_KEYWORDS = ("mismatch", "discrepan", "reconcil", "variance", "differ", "inconsist")


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, _: dict = Depends(require_user)) -> ChatResponse:
    if not store.has_data:
        raise HTTPException(400, "No workbook uploaded. Upload an Excel file first.")
    if not req.message.strip():
        raise HTTPException(400, "Empty message.")

    sheets = store.all_sheets()
    context = build_chat_context(sheets, req.sheet)

    # If user asks about mismatches/reconciliation, inject computed mismatch report
    if any(k in req.message.lower() for k in _MISMATCH_KEYWORDS):
        mm = mismatches(sheets)
        if mm["count"]:
            context += (
                f"\n\nMISMATCH_REPORT (Risk Rating Summary vs Aggregation Check):\n"
                f"customers_with_mismatches={mm['count']}, fields_checked={mm['fields']}\n"
                f"sample_issues={mm['rows'][:10]}"
            )

    messages: list[ChatMessage] = [
        ChatMessage("system", SYSTEM_PROMPT),
        ChatMessage("system", f"WORKBOOK CONTEXT:\n{context}"),
    ]
    for h in req.history[-8:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append(ChatMessage(h["role"], h["content"]))
    messages.append(ChatMessage("user", req.message))

    try:
        llm = get_llm()
        answer = await llm.chat(messages)
    except NotImplementedError as e:
        raise HTTPException(501, str(e)) from e
    except Exception as e:
        log.exception("LLM error")
        raise HTTPException(502, f"LLM error: {e}") from e

    return ChatResponse(answer=answer, provider=llm.name, model=llm.model, context_sheet=req.sheet)
