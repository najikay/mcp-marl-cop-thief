"""TDD unit tests for the Cloudflare switchboard URL extraction + injection."""

from __future__ import annotations

import json
from pathlib import Path

from cop_thief.infra.network.switchboard import extract_url, inject_urls


def test_extract_url_traps_cloudflare_stderr() -> None:
    """The regex traps the allocated URL out of a realistic stderr line."""
    line = (
        "2026-06-23T10:00:00Z INF +--------------------------------------------+\n"
        "2026-06-23T10:00:00Z INF |  https://brave-otter-42x.trycloudflare.com  |"
    )
    assert extract_url(line) == "https://brave-otter-42x.trycloudflare.com"


def test_extract_url_none_when_absent() -> None:
    """A line with no allocated https URL yields None."""
    assert extract_url("INF Requesting new quick Tunnel on trycloudflare.com...") is None


def test_inject_urls_writes_network_block(tmp_path: Path) -> None:
    """Captured URLs are persisted into the network.team_alpha_* keys."""
    cfg = tmp_path / "setup.json"
    cfg.write_text(
        json.dumps({"network": {"team_alpha_cop_url": "", "team_alpha_thief_url": ""}}),
        encoding="utf-8",
    )
    inject_urls(
        "https://cop-node.trycloudflare.com",
        "https://thief-node.trycloudflare.com",
        config_path=cfg,
    )
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["network"]["team_alpha_cop_url"] == "https://cop-node.trycloudflare.com"
    assert data["network"]["team_alpha_thief_url"] == "https://thief-node.trycloudflare.com"
