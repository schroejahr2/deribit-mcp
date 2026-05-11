"""News formatting and push helpers."""

from __future__ import annotations

import logging
from html import escape
from typing import Any

logger = logging.getLogger(__name__)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def compact_news_row(row: dict[str, Any], include_full: bool = False) -> dict[str, Any]:
    item = {
        "id": row.get("id"),
        "created_at": row.get("created_at"),
        "status": row.get("status"),
        "source": row.get("source"),
        "instrument": row.get("instrument"),
        "headline": row.get("headline"),
        "summary": row.get("summary"),
        "url": row.get("url"),
        "score": row.get("score"),
        "tags": row.get("tags"),
        "error": row.get("error"),
    }
    if include_full:
        item["model"] = row.get("model")
        item["notification_channel"] = row.get("notification_channel")
        item["pushed_at"] = row.get("pushed_at")
        item["content"] = row.get("content")
        item["context"] = row.get("context")
    return item


def format_news_message(row: dict[str, Any]) -> str:
    headline = escape(str(row.get("headline") or "Untitled"))
    source = row.get("source")
    instrument = row.get("instrument")
    summary = row.get("summary")
    url = row.get("url")

    header = f"News: {headline}"
    if source or instrument:
        meta = " · ".join(part for part in (instrument, source) if part)
        header = f"News [{escape(str(meta))}]: {headline}"

    lines = [header]
    if summary:
        lines.extend(["", escape(str(summary))])

    tags = _as_list(row.get("tags"))[:5]
    if tags:
        lines.extend(["", "Tags: " + ", ".join(escape(str(tag)) for tag in tags)])

    if url:
        lines.extend(["", escape(str(url))])

    return "\n".join(line for line in lines if line is not None).strip()


async def push_news(app_ctx: Any, row: dict[str, Any], channel: str) -> bool:
    message = format_news_message(row)
    sent = await app_ctx.notification_manager.send_notification(
        channel,
        message,
        news=row,
    )
    if sent:
        try:
            await app_ctx.news_repo.mark_pushed(row["id"], channel)
        except ValueError as exc:
            logger.warning(
                "mark_pushed failed for news id=%s (likely deleted): %s",
                row.get("id"),
                exc,
            )
    return sent
