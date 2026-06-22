"""Unit tests for the RetryPolicy."""

from __future__ import annotations

import pytest

from cop_thief.infra.errors import PermanentError, TransientError
from cop_thief.infra.retry import RetryPolicy


def _policy(max_retries: int) -> RetryPolicy:
    return RetryPolicy(max_retries, retry_after_seconds=0, sleeper=lambda _s: None)


def test_succeeds_first_try():
    assert _policy(3).run(lambda: 42) == 42


def test_succeeds_after_transient_failure():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise TransientError("temporary")
        return "ok"

    assert _policy(3).run(flaky) == "ok"
    assert calls["n"] == 2


def test_exhausts_retries():
    def always_fails():
        raise TransientError("nope")

    with pytest.raises(TransientError):
        _policy(2).run(always_fails)


def test_permanent_error_not_retried():
    calls = {"n": 0}

    def perm():
        calls["n"] += 1
        raise PermanentError("bad request")

    with pytest.raises(PermanentError):
        _policy(3).run(perm)
    assert calls["n"] == 1
