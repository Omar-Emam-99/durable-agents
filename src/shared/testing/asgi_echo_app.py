"""Local Starlette ASGI app for offline HTTP client demos and tests."""

from __future__ import annotations

from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route


def create_echo_app() -> Starlette:
    """
    Build an in-process ASGI app that exercises auth, retry, and deserialization.

    Routes
    ------
    GET  /echo          – echo headers and query
    GET  /items/{id}    – JSON item for response_model parsing
    POST /items         – echo JSON body
    GET  /secure        – 401 until Authorization is Bearer fresh-token
    GET  /flaky         – 500 once, then 200
    POST /oauth/token   – fake OAuth2 client-credentials token
    """
    state: dict[str, Any] = {
        "flaky_hits": 0,
        "token_counter": 0,
    }

    async def echo(request: Request) -> JSONResponse:
        return JSONResponse(
            {
                "headers": dict(request.headers),
                "query": dict(request.query_params),
                "method": request.method,
                "path": request.url.path,
            }
        )

    async def get_item(request: Request) -> JSONResponse:
        item_id = request.path_params["id"]
        return JSONResponse({"id": item_id, "name": f"item-{item_id}"})

    async def post_item(request: Request) -> JSONResponse:
        body = await request.json()
        return JSONResponse({"created": True, "body": body}, status_code=201)

    async def secure(request: Request) -> Response:
        auth = request.headers.get("authorization", "")
        if auth == "Bearer fresh-token":
            return JSONResponse({"ok": True, "auth": auth})
        return JSONResponse({"detail": "unauthorized"}, status_code=401)

    async def flaky(request: Request) -> Response:
        state["flaky_hits"] += 1
        if state["flaky_hits"] == 1:
            return JSONResponse({"detail": "server error"}, status_code=500)
        return JSONResponse({"ok": True, "hits": state["flaky_hits"]})

    async def oauth_token(request: Request) -> JSONResponse:
        from urllib.parse import parse_qs

        raw = (await request.body()).decode()
        form = {k: v[0] for k, v in parse_qs(raw).items()}
        if form.get("grant_type") != "client_credentials":
            return JSONResponse({"error": "unsupported_grant"}, status_code=400)
        state["token_counter"] += 1
        token = f"oauth-token-{state['token_counter']}"
        return JSONResponse(
            {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": 3600,
            }
        )

    return Starlette(
        routes=[
            Route("/echo", echo, methods=["GET"]),
            Route("/items/{id}", get_item, methods=["GET"]),
            Route("/items", post_item, methods=["POST"]),
            Route("/secure", secure, methods=["GET"]),
            Route("/flaky", flaky, methods=["GET"]),
            Route("/oauth/token", oauth_token, methods=["POST"]),
        ]
    )
