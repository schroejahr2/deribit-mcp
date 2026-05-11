"""Transport switch entry point for the Deribit MCP package."""

from __future__ import annotations

import logging

import uvicorn

from .config import settings

logger = logging.getLogger(__name__)


def main() -> None:
    if settings.mcp_transport.lower() == "http":
        uvicorn.run("src.http_app:app", host="0.0.0.0", port=8000, proxy_headers=True)
        return

    from .server import build_mcp

    build_mcp().run(transport="stdio")


if __name__ == "__main__":
    main()
