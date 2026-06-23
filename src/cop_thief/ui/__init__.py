"""Browser UI: a Starlette + SSE live view of games (reuses fastmcp's deps)."""

from .server import build_app

__all__ = ["build_app"]
