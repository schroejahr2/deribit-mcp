"""FastAPI routes for the Deribit event outbox stream."""

from __future__ import annotations

import asyncio
import json
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .config import settings

router = APIRouter(prefix="/events", tags=["events"])


class RegisterConsumerRequest(BaseModel):
    consumer_id: Optional[str] = None
    display_name: str


def _bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    return authorization.split(" ", 1)[1]


async def _event_repo(request: Request):
    ctx = getattr(request.app.state, "deribit", None)
    if not ctx:
        raise HTTPException(status_code=503, detail="Deribit context is not ready")
    return ctx.event_outbox_repo


def _require_admin_token(authorization: Optional[str]) -> None:
    if not settings.deribit_event_admin_token:
        raise HTTPException(status_code=503, detail="DERIBIT_EVENT_ADMIN_TOKEN is not configured")
    token = _bearer_token(authorization)
    if not secrets.compare_digest(token, settings.deribit_event_admin_token):
        raise HTTPException(status_code=401, detail="Invalid admin token")


@router.post("/register")
async def register_consumer(
    payload: RegisterConsumerRequest,
    authorization: Optional[str] = Header(default=None),
    repo=Depends(_event_repo),
):
    """Register or rotate a consumer token."""
    _require_admin_token(authorization)
    return await repo.register_consumer(payload.consumer_id, payload.display_name)


@router.get("/stream")
async def stream_events(
    consumer_id: str,
    authorization: Optional[str] = Header(default=None),
    repo=Depends(_event_repo),
):
    """Stream pending events as newline-delimited JSON."""
    token = _bearer_token(authorization)
    if not await repo.authenticate_consumer(consumer_id, token):
        raise HTTPException(status_code=401, detail="Invalid consumer token")
    if not await repo.claim_stream(consumer_id, settings.deribit_event_stream_claim_seconds):
        raise HTTPException(status_code=409, detail="Consumer already has an active stream")

    async def event_generator():
        try:
            while True:
                await repo.renew_stream(consumer_id, settings.deribit_event_stream_claim_seconds)
                events = await repo.pending_events(consumer_id)
                for event in events:
                    yield json.dumps(event, sort_keys=True, default=str) + "\n"
                await asyncio.sleep(1)
        finally:
            await repo.release_stream(consumer_id)

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@router.post("/{event_id}/ack")
async def ack_event(
    event_id: str,
    consumer_id: str,
    authorization: Optional[str] = Header(default=None),
    repo=Depends(_event_repo),
):
    """Acknowledge successful processing of one event for one consumer."""
    token = _bearer_token(authorization)
    if not await repo.authenticate_consumer(consumer_id, token):
        raise HTTPException(status_code=401, detail="Invalid consumer token")
    await repo.ack(consumer_id, event_id)
    return {"ok": True}


@router.post("/heartbeat")
async def heartbeat(
    consumer_id: str,
    authorization: Optional[str] = Header(default=None),
    repo=Depends(_event_repo),
):
    """Update consumer liveness without opening the stream."""
    token = _bearer_token(authorization)
    if not await repo.authenticate_consumer(consumer_id, token):
        raise HTTPException(status_code=401, detail="Invalid consumer token")
    await repo.heartbeat(consumer_id)
    return {"ok": True}
