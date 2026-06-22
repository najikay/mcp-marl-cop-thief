"""BaseReport — shared serialization with a version stamp.

Every report carries an explicit ``version`` so a grader can tell which schema
generation produced it. Subclasses implement :meth:`to_dict`.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

from ... import __version__


class BaseReport(ABC):
    """Abstract report with canonical JSON serialization."""

    version: str = __version__

    @abstractmethod
    def to_dict(self) -> dict:
        """Return the report as a plain, JSON-serialisable mapping."""
        raise NotImplementedError

    def to_json(self) -> str:
        """Canonical, stable JSON (sorted keys) so two sides can byte-compare."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False)
