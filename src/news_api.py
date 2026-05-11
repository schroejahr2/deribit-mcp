"""FastAPI routes for stored news items."""

from __future__ import annotations

import secrets
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from .config import settings
from .news import compact_news_row, push_news
from .notifications import validate_channel_name
from .persistence import VALID_NEWS_STATUSES

router = APIRouter(prefix="/news", tags=["news"])


class PushNewsRequest(BaseModel):
    notification_channel: str = "outbox"


class SaveNewsRequest(BaseModel):
    headline: str
    summary: Optional[str] = None
    source: Optional[str] = None
    instrument: Optional[str] = None
    url: Optional[str] = None
    score: Optional[float] = None
    dedupe_key: Optional[str] = None
    content: Optional[dict[str, Any]] = None
    context: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None
    model: Optional[str] = None
    status: str = "processed"
    notification_channel: Optional[str] = None
    push: bool = True
    error: Optional[str] = None


def _bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    return authorization.split(" ", 1)[1]


def _require_admin_token(authorization: Optional[str]) -> None:
    if not settings.deribit_event_admin_token:
        raise HTTPException(status_code=503, detail="DERIBIT_EVENT_ADMIN_TOKEN is not configured")
    token = _bearer_token(authorization)
    if not secrets.compare_digest(token, settings.deribit_event_admin_token):
        raise HTTPException(status_code=401, detail="Invalid admin token")


def _ctx(request: Request):
    ctx = getattr(request.app.state, "deribit", None)
    if not ctx:
        raise HTTPException(status_code=503, detail="Deribit context is not ready")
    return ctx


def _validate_channel(channel: str) -> None:
    try:
        validate_channel_name(channel)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("")
async def save_news(
    request: Request,
    payload: SaveNewsRequest,
    authorization: Optional[str] = Header(default=None),
):
    _require_admin_token(authorization)
    if payload.status not in VALID_NEWS_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {payload.status}. Valid: {sorted(VALID_NEWS_STATUSES)}",
        )
    if payload.notification_channel:
        _validate_channel(payload.notification_channel)

    ctx = _ctx(request)
    news_id = str(uuid.uuid4())
    try:
        stored_id, created = await ctx.news_repo.create(
            news_id=news_id,
            headline=payload.headline,
            summary=payload.summary,
            source=payload.source,
            instrument=payload.instrument,
            url=payload.url,
            score=payload.score,
            dedupe_key=payload.dedupe_key,
            content=payload.content,
            context=payload.context,
            tags=payload.tags,
            model=payload.model,
            status=payload.status,
            notification_channel=payload.notification_channel,
            error=payload.error,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    row = await ctx.news_repo.get(stored_id)
    if row is None:
        raise HTTPException(status_code=500, detail="Failed to reload saved news")

    pushed = False
    pushed_channel: Optional[str] = None
    if payload.push and created:
        pushed_channel = payload.notification_channel or "outbox"
        _validate_channel(pushed_channel)
        try:
            pushed = await push_news(ctx, row, pushed_channel)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        row = await ctx.news_repo.get(stored_id) or row

    return {
        "news": compact_news_row(row, include_full=True),
        "pushed": pushed,
        "duplicate": not created,
        "notification_channel": pushed_channel,
    }


@router.get("")
async def list_news(
    request: Request,
    limit: int = 10,
    source: Optional[str] = None,
    instrument: Optional[str] = None,
    status: Optional[str] = None,
    include_full: bool = False,
):
    ctx = _ctx(request)
    try:
        rows = await ctx.news_repo.list(
            limit=limit, source=source, instrument=instrument, status=status
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "news": [compact_news_row(row, include_full=include_full) for row in rows],
        "count": len(rows),
    }


@router.get("/{news_id}")
async def get_news(
    news_id: str,
    request: Request,
    include_full: bool = True,
):
    ctx = _ctx(request)
    row = await ctx.news_repo.get(news_id)
    if not row:
        raise HTTPException(status_code=404, detail="News not found")
    return {"news": compact_news_row(row, include_full=include_full)}


@router.post("/{news_id}/push")
async def push_news_route(
    news_id: str,
    request: Request,
    payload: Optional[PushNewsRequest] = None,
    authorization: Optional[str] = Header(default=None),
):
    _require_admin_token(authorization)
    channel = payload.notification_channel if payload else "outbox"
    _validate_channel(channel)
    ctx = _ctx(request)
    row = await ctx.news_repo.get(news_id)
    if not row:
        raise HTTPException(status_code=404, detail="News not found")
    try:
        pushed = await push_news(ctx, row, channel)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    updated = await ctx.news_repo.get(news_id) or row
    return {
        "ok": pushed,
        "news": compact_news_row(updated, include_full=True),
        "notification_channel": channel,
    }
