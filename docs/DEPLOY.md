# Deployment & Token Auth

How to take the two MCP servers from `localhost` to public, token-protected URLs
and drive a game against them. Each group needs **two** public URLs (Cop, Thief).

## 1. Tokens (revocable bearer auth)

Each server requires a bearer token when `MCP_TOKEN` is set; calls without a valid
`Authorization: Bearer <token>` are rejected. **To revoke, rotate the token**
(restart the server with a new value) — old tokens stop working immediately.

```powershell
# generate a token (example)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set it per server before launching:

```powershell
$env:MCP_TOKEN = "<cop-token>";   uv run cop-server   --host 0.0.0.0 --port 8001
$env:MCP_TOKEN = "<thief-token>"; uv run thief-server --host 0.0.0.0 --port 8002
```

The orchestrator sends tokens when driving remote servers:

```powershell
uv run cop-thief-match `
  --cop-url   https://<cop-host>/mcp/   --cop-token   <cop-token> `
  --thief-url https://<thief-host>/mcp/ --thief-token <thief-token>
```

(`MCP_COP_TOKEN` / `MCP_THIEF_TOKEN` env vars are picked up as defaults.)

## 2. Going public — pick one

### Option A — ngrok (fastest for a dry-run)
```powershell
uv run cop-server --host 127.0.0.1 --port 8001    # terminal 1
ngrok http 8001                                    # terminal 2 -> https URL
```
Repeat for the Thief on 8002. Use the two `https://*.ngrok-free.app/mcp/` URLs.
Add ngrok Basic Auth / a Traffic Policy for a second layer if desired.

### Option B — Docker + any host (Prefect Cloud, a VM, Render, Fly.io)
```powershell
docker build -t cop-thief .
docker run -e MCP_TOKEN=<cop-token>   -p 8001:8001 cop-thief cop-server   --host 0.0.0.0 --port 8001
docker run -e MCP_TOKEN=<thief-token> -p 8002:8002 cop-thief thief-server --host 0.0.0.0 --port 8002
```

### Option C — Nginx reverse proxy (full SSL)
Terminate TLS at Nginx (Certbot/Let's Encrypt), `proxy_pass` to the local server
port, and firewall the raw port (UFW/nftables). See the lecture §7 notes.

## 3. Security checklist (PRD §N-02)

- [ ] Both servers require a bearer token (`MCP_TOKEN` set); no open public ports.
- [ ] Tokens are not committed — `.env` only (`.env-example` documents the names).
- [ ] HTTPS in front of every public URL.
- [ ] Token rotation tested (old token rejected after restart).
- [ ] The MCP path is `/mcp/` (FastMCP default) — include it in the URL.

## 4. Bonus match wiring

Drive your Cop + the other group's Thief (and vice-versa) with the four URLs and
their tokens; see `docs/BONUS.md` §2 for the tool contract and §5 for the
report-agreement checklist before either group emails its report.
