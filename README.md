# CFB DFS Analytics — MCP connector source

A read-only MCP server that fetches CollegeFootballData API data for ChatGPT. No credentials are included.

## Deploy
1. Host this folder on a Python-capable service with an HTTPS public endpoint.
2. Set the `CFBD_API_KEY` secret in the hosting provider's secret/environment settings. Never paste it into chat or source files.
3. Install dependencies with `pip install -r requirements.txt` and start with `python server.py`.
4. Connect ChatGPT to the resulting HTTPS MCP endpoint, typically `/mcp`.
5. Restrict access to the MCP endpoint with hosting-level authentication before exposing it publicly. CFBD's API key authenticates upstream CFBD requests, **not** callers of this MCP server.

## Scope
Read-only CFBD data: game schedule, season and game player stats, team advanced statistics, player usage, SP+/CORE ratings and betting lines. Availability varies by plan and season. This is source code, not a deployed service. Check CFBD API docs for current endpoint parameter requirements.

## DFS methodology
Use the latest four completed weeks where available, season baselines, opponent-adjusted efficiency, positional usage, defensive vulnerabilities and game-script robustness. Do not use projection systems as the primary decision criterion. Separate data-backed observations from inference. Never label a player cash or tournament unless asked. Be mindful of API quota; reuse results within a session.
