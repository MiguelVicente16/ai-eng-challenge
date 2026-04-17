"""Admin API: list and fetch call summaries."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.agents.summary.store import get_summary_store

router = APIRouter()


@router.get("/summaries")
async def list_summaries(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sentiment: str | None = None,
    resolved: bool | None = None,
    q: str | None = None,
    from_: str | None = Query(None, alias="from"),
    to: str | None = None,
) -> dict:
    filters: dict = {}
    if sentiment:
        filters["sentiment"] = sentiment
    if resolved is not None:
        filters["resolved"] = resolved
    if q:
        filters["q"] = q
    if from_:
        filters["from"] = from_
    if to:
        filters["to"] = to

    store = get_summary_store()
    skip = (page - 1) * size
    items, total = await store.list(filters, skip, size)
    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/summaries/{session_id}")
async def get_summary(session_id: str) -> dict:
    store = get_summary_store()
    record = await store.get(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="summary not found")
    return record
