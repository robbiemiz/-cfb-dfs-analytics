"""Private, read-only CollegeFootballData MCP server for Render.

Required Render environment variables:
  CFBD_API_KEY   CollegeFootballData API key (never put in GitHub)
  MCP_AUTH_TOKEN Long random secret for clients (never put in GitHub)
"""
import os
import secrets
import httpx
import uvicorn
from fastmcp import FastMCP

mcp = FastMCP("CFB DFS Analytics")
BASE = "https://api.collegefootballdata.com"
ALLOWED = {
    "games": "/games",
    "schedule": "/games/schedule",
    "team_advanced": "/stats/season/advanced",
    "team_weekly": "/stats/season",
    "player_season": "/stats/player/season",
    "player_games": "/stats/player/game",
    "player_usage": "/player/usage",
    "team_talent": "/talent",
    "ratings_sp": "/ratings/sp",
    "ratings_core": "/ratings/core",
    "betting_lines": "/lines",
}

@mcp.tool()
async def cfbd_query(dataset: str, year: int = 2026, week: int | None = None,
                     team: str | None = None, conference: str | None = None,
                     season_type: str | None = None, category: str | None = None) -> dict:
    """Fetch a supported CFBD dataset. Do not treat missing data as zero."""
    if dataset not in ALLOWED:
        return {"error": "Unsupported dataset", "supported": sorted(ALLOWED)}
    api_key = os.environ.get("CFBD_API_KEY")
    if not api_key:
        return {"error": "CFBD_API_KEY is not configured"}
    params = {"year": year}
    for name, value in (("week", week), ("team", team), ("conference", conference),
                        ("seasonType", season_type), ("category", category)):
        if value is not None:
            params[name] = value
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.get(
                BASE + ALLOWED[dataset], params=params,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            return {"dataset": dataset, "filters": params, "data": response.json()}
    except httpx.HTTPStatusError as exc:
        return {"error": "CFBD request failed", "status": exc.response.status_code}
    except (httpx.RequestError, ValueError):
        return {"error": "CFBD request failed or returned invalid data"}

# Check bearer authentication BEFORE requests reach the MCP server.
# Only a non-sensitive health check is public.
class AuthenticatedMCP:
    def __init__(self, app, token: str):
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        if path == "/health":
            body = b"ok"
            await send({"type": "http.response.start", "status": 200,
                        "headers": [(b"content-type", b"text/plain"),
                                    (b"content-length", str(len(body)).encode())]})
            await send({"type": "http.response.body", "body": body})
            return
        headers = dict(scope.get("headers", []))
        authorization = headers.get(b"authorization", b"").decode("utf-8", "replace")
        expected = "Bearer " + self.token
        if not secrets.compare_digest(authorization, expected):
            body = b"Unauthorized"
            await send({"type": "http.response.start", "status": 401,
                        "headers": [(b"content-type", b"text/plain"),
                                    (b"www-authenticate", b"Bearer"),
                                    (b"content-length", str(len(body)).encode())]})
            await send({"type": "http.response.body", "body": body})
            return
        await self.app(scope, receive, send)

if __name__ == "__main__":
    token = os.environ.get("MCP_AUTH_TOKEN", "")
    if len(token) < 32:
        raise RuntimeError("MCP_AUTH_TOKEN must be configured with at least 32 characters")
    if not os.environ.get("CFBD_API_KEY"):
        raise RuntimeError("CFBD_API_KEY must be configured")
    app = AuthenticatedMCP(mcp.http_app(), token)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")),
                proxy_headers=True)
