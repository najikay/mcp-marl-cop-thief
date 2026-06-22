"""Architecture guard: consumers import only the SDK (PRD §E3)."""

from __future__ import annotations

from pathlib import Path

_MAIN = Path(__file__).resolve().parents[2] / "src" / "cop_thief" / "main.py"
_FORBIDDEN = (
    "from .domain",
    "from .infra",
    "from .orchestrator",
    "import cop_thief.domain",
)


def test_cli_imports_only_the_sdk():
    source = _MAIN.read_text(encoding="utf-8")
    leaks = [fragment for fragment in _FORBIDDEN if fragment in source]
    assert not leaks, f"main.py bypasses the SDK boundary: {leaks}"
