"""RetryPolicy — retry transient failures with a bounded backoff.

Only :class:`TransientError` is retried; :class:`PermanentError` (and any other
exception) surfaces immediately. The sleeper is injectable for fast tests.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from .errors import TransientError

T = TypeVar("T")


class RetryPolicy:
    """Run a callable, retrying transient failures up to ``max_retries`` times."""

    def __init__(
        self,
        max_retries: int,
        retry_after_seconds: float,
        sleeper: Callable[[float], None],
    ) -> None:
        self._max_retries = max_retries
        self._retry_after = retry_after_seconds
        self._sleeper = sleeper

    def run(self, func: Callable[[], T]) -> T:
        """Execute ``func``; on :class:`TransientError`, back off and retry."""
        attempts = 0
        while True:
            try:
                return func()
            except TransientError:
                attempts += 1
                if attempts > self._max_retries:
                    raise
                self._sleeper(self._retry_after)
