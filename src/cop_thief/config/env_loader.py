"""Zero-dependency ``.env`` autoloader (idempotent, non-overriding).

Loads ``KEY=VALUE`` pairs from the project ``.env`` into ``os.environ`` so the
documented secrets workflow works without volatile shell exports. Existing
environment variables always win (an explicit shell export is never clobbered),
and the file is parsed at most once per process.
"""

from __future__ import annotations

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_LOADED = False


def _apply_env(path: Path) -> None:
    """Parse ``path`` and populate only env vars not already set."""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_env_once(env_path: Path | None = None) -> None:
    """Load the project ``.env`` exactly once (no-op if missing/already loaded)."""
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    path = env_path or (_PROJECT_ROOT / ".env")
    if path.exists():
        _apply_env(path)
