"""Automated Cloudflare tunnel switchboard for the public two-URL matrix.

Launches two non-root ``cloudflared`` child processes (Cop :8001, Thief :8002),
traps their allocated ``*.trycloudflare.com`` URLs from stderr, injects them into
``config/setup.json`` (``network.team_alpha_*``), prints a double-bordered table,
and holds both tunnels open until Ctrl+C.

Run: ``uv run python -m cop_thief.infra.network.switchboard``
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_CLOUDFLARED = _ROOT / "bin" / "cloudflared"
_CONFIG = _ROOT / "config" / "setup.json"
_PORT_COP = 8001
_PORT_THIEF = 8002
_URL_RE = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")


def extract_url(text: str) -> str | None:
    """Return the first ``*.trycloudflare.com`` URL found in ``text``, else None."""
    match = _URL_RE.search(text)
    return match.group(0) if match else None


def inject_urls(cop_url: str, thief_url: str, config_path: Path = _CONFIG) -> None:
    """Persist the two public URLs into ``network.team_alpha_*`` (clean JSON)."""
    data = json.loads(config_path.read_text(encoding="utf-8"))
    network = data.setdefault("network", {})
    network["team_alpha_cop_url"] = cop_url
    network["team_alpha_thief_url"] = thief_url
    config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _print_table(cop_url: str, thief_url: str) -> None:
    """Print a double-bordered ASCII table of the live public endpoints."""
    rows = [(f"COP   (:{_PORT_COP})", cop_url), (f"THIEF (:{_PORT_THIEF})", thief_url)]
    width = max(len(f"{label}  {url}") for label, url in rows) + 2
    bar = "═" * width
    print(f"╔{bar}╗")
    print(f"║ {'LIVE PUBLIC MATRIX (Team Alpha)'.ljust(width - 1)}║")
    print(f"╠{bar}╣")
    for label, url in rows:
        print(f"║ {f'{label}  {url}'.ljust(width - 1)}║")
    print(f"╚{bar}╝")


async def _spawn(port: int) -> asyncio.subprocess.Process:
    """Launch a cloudflared quick tunnel for ``port`` with stderr piped."""
    return await asyncio.create_subprocess_exec(
        str(_CLOUDFLARED), "tunnel", "--url", f"http://127.0.0.1:{port}",
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE,
    )


async def _capture(proc: asyncio.subprocess.Process) -> str:
    """Read ``proc`` stderr until Cloudflare allocates its public URL."""
    while proc.stderr is not None:
        line = await proc.stderr.readline()
        if not line:
            break
        url = extract_url(line.decode(errors="ignore"))
        if url:
            return url
    raise RuntimeError("cloudflared exited before allocating a URL")


async def _drain(stream) -> None:
    """Keep draining stderr so the child never blocks on a full pipe."""
    while await stream.readline():
        pass


async def run_switchboard() -> None:
    """Launch both tunnels, capture + persist URLs, then hold open until Ctrl+C."""
    procs = [await _spawn(_PORT_COP), await _spawn(_PORT_THIEF)]
    try:
        cop_url, thief_url = await asyncio.gather(_capture(procs[0]), _capture(procs[1]))
        inject_urls(cop_url, thief_url)
        _print_table(cop_url, thief_url)
        print("Tunnels live and written to config/setup.json. Press Ctrl+C to terminate.")
        await asyncio.gather(*(_drain(p.stderr) for p in procs))
    finally:
        for proc in procs:
            with contextlib.suppress(ProcessLookupError):
                proc.terminate()
        await asyncio.gather(*(p.wait() for p in procs), return_exceptions=True)


def main() -> None:
    """Run the switchboard until interrupted."""
    try:
        asyncio.run(run_switchboard())
    except KeyboardInterrupt:
        print("\nSwitchboard shut down; both tunnels terminated.")


if __name__ == "__main__":
    main()
