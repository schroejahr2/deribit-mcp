"""FastAPI wrapper for Deribit MCP over HTTP."""

from __future__ import annotations

import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from dashboard.api import router as dashboard_router, static_directory as dashboard_static_directory

from .config import settings
from .events_api import router as events_router
from .news_api import router as news_router
from .lifespan import deribit_lifespan
from .server import build_mcp

app = FastAPI(title="Deribit MCP", version="0.2.0")


@asynccontextmanager
async def fastmcp_passthrough_lifespan(_server):
    """Expose the FastAPI-created AppContext as FastMCP's lifespan_context."""
    yield app.state.deribit


mcp = build_mcp(lifespan=fastmcp_passthrough_lifespan)


@app.get("/health")
async def health():
    return {"ok": True}


@app.middleware("http")
async def mcp_shared_secret_middleware(request: Request, call_next):
    """Protect MCP HTTP transport behind Bifrost's internal shared secret."""
    protected = request.url.path.startswith("/mcp") or request.url.path.startswith("/sse")
    if protected:
        supplied = request.headers.get("X-Deribit-MCP-Secret", "")
        if not secrets.compare_digest(supplied, settings.mcp_shared_secret):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
    if (
        settings.mcp_http_stateless
        and request.method == "GET"
        and request.url.path.startswith("/mcp")
    ):
        # Stateless mode has no server-initiated messages; a hanging GET/SSE
        # stream ties up the client's keep-alive connection and stalls
        # subsequent POSTs (Claude Code bun fetch pool). 405 per MCP spec.
        return JSONResponse({"error": "method not allowed"}, status_code=405)
    return await call_next(request)


json_response = settings.mcp_http_json_response
mcp_app = mcp.http_app(
    path="/",
    transport="streamable-http",
    json_response=json_response,
    stateless_http=settings.mcp_http_stateless,
)


@asynccontextmanager
async def combined_lifespan(fastapi_app: FastAPI):
    async with deribit_lifespan(fastapi_app) as deribit_ctx:
        fastapi_app.state.deribit = deribit_ctx
        async with mcp_app.lifespan(fastapi_app):
            yield


app.router.lifespan_context = combined_lifespan
app.include_router(news_router)
app.include_router(events_router)
app.include_router(dashboard_router)
app.mount(
    "/dashboard/static",
    StaticFiles(directory=dashboard_static_directory),
    name="dashboard-static",
)
app.mount("/mcp", mcp_app)
