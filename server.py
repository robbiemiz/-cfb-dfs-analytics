"""CFBD read-only MCP bridge. Set CFBD_API_KEY in hosting secrets."""
import os
import httpx
from fastmcp import FastMCP

mcp = FastMCP('CFB DFS Analytics')
BASE = 'https://api.collegefootballdata.com'
ALLOWED = {
    'games': '/games',
    'schedule': '/games/schedule',
    'team_advanced': '/stats/season/advanced',
    'team_weekly': '/stats/season',
    'player_season': '/stats/player/season',
    'player_games': '/stats/player/game',
    'player_usage': '/player/usage',
    'team_talent': '/talent',
    'ratings_sp': '/ratings/sp',
    'ratings_core': '/ratings/core',
    'betting_lines': '/lines',
}

@mcp.tool()
async def cfbd_query(dataset: str, year: int = 2026, week: int | None = None,
                     team: str | None = None, conference: str | None = None,
                     season_type: str | None = None, category: str | None = None) -> dict:
    """Read CFBD datasets for college football DFS. Use supported dataset keys; never infer missing stats as zero."""
    if dataset not in ALLOWED:
        return {'error': 'Unsupported dataset', 'supported': sorted(ALLOWED)}
    key = os.environ.get('CFBD_API_KEY')
    if not key:
        return {'error': 'CFBD_API_KEY must be configured in hosting secrets'}
    params = {'year': year}
    for k, v in [('week',week),('team',team),('conference',conference),('seasonType',season_type),('category',category)]:
        if v is not None:
            params[k] = v
    async with httpx.AsyncClient(timeout=25) as client:
        try:
            r = await client.get(BASE + ALLOWED[dataset], params=params,
                                 headers={'Authorization': f'Bearer {key}'})
            r.raise_for_status()
            data = r.json()
            return {'dataset':dataset,'filters':params,'data':data}
        except httpx.HTTPStatusError as e:
            return {'error':'CFBD request failed','status':e.response.status_code,'detail':e.response.text[:400]}
        except httpx.RequestError:
            return {'error':'CFBD network request failed'}

if __name__ == '__main__':
    mcp.run(transport='http', host='0.0.0.0', port=int(os.getenv('PORT','8000')))
