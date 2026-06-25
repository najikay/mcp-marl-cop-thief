"""TDD unit tests for the API Gatekeeper (fully mocked — no real network).

Scenarios:
1. Happy-path DeepSeek 200 OK -> text returned, token tracker accumulates.
2. DeepSeek 502 -> instant failover returns the mocked Anthropic response.
3. Queue overflow -> BackpressureOverflowError fires.

(TokenTracker ledger math + corrupt-file recovery live in ``test_token_tracker.py``.)
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import httpx
import pytest

from cop_thief.config import ConfigManager
from cop_thief.config.rate_limit_models import RateLimitConfig
from cop_thief.infra.gatekeeper import (
    ApiGatekeeper,
    BackpressureOverflowError,
    ProviderUpstreamError,
    TokenTracker,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REAL_CONFIG_DIR = PROJECT_ROOT / "config"


def _env(key: str, default: str = "") -> str:
    """Stub env reader returning a fixed token for tests."""
    return "test-key"


def _ok(payload: dict) -> mock.Mock:
    resp = mock.Mock()
    resp.raise_for_status = mock.Mock()
    resp.json = mock.Mock(return_value=payload)
    return resp


def _http_error(status: int) -> mock.Mock:
    resp = mock.Mock()
    resp.raise_for_status = mock.Mock(
        side_effect=httpx.HTTPStatusError(
            f"{status}", request=mock.Mock(), response=mock.Mock(status_code=status)
        )
    )
    return resp


def _deepseek_body(text: str, p: int, c: int) -> dict:
    return {"choices": [{"message": {"content": text}}],
            "usage": {"prompt_tokens": p, "completion_tokens": c}}


def _anthropic_body(text: str, i: int, o: int) -> dict:
    return {"content": [{"text": text}], "usage": {"input_tokens": i, "output_tokens": o}}


def _build_gatekeeper(client: mock.Mock, tmp_path: Path) -> ApiGatekeeper:
    cfg = ConfigManager(config_dir=REAL_CONFIG_DIR)
    tracker = TokenTracker(usage_file=tmp_path / "token_usage.json")
    return ApiGatekeeper(cfg.rate_limits, cfg.setup.llm_routing,
                         token_tracker=tracker, client=client, get_env=_env)


def test_happy_path_deepseek_accumulates(tmp_path: Path) -> None:
    """DeepSeek 200 -> text returned and tracker records the usage."""
    client = mock.Mock()
    client.post = mock.Mock(return_value=_ok(_deepseek_body("MOVE north", 850, 90)))
    gk = _build_gatekeeper(client, tmp_path)

    text, usage = gk.execute_llm_call("where are you?", "you are the cop")

    assert text == "MOVE north"
    assert usage["provider"] == "DEEPSEEK"
    assert usage["input_tokens"] == 850
    econ = gk._tracker.get_current_economics()
    assert econ["input_accumulated"] == 850
    assert econ["output_accumulated"] == 90
    assert client.post.call_count == 1


def test_failover_to_anthropic_on_502(tmp_path: Path) -> None:
    """DeepSeek 502 -> gatekeeper instantly returns the Anthropic fallback."""
    client = mock.Mock()
    client.post = mock.Mock(side_effect=[_http_error(502),
                                         _ok(_anthropic_body("FLEE south", 120, 40))])
    gk = _build_gatekeeper(client, tmp_path)

    text, usage = gk.execute_llm_call("closing in", "you are the thief")

    assert text == "FLEE south"
    assert usage["provider"] == "ANTHROPIC"
    assert client.post.call_count == 2
    assert gk._tracker.get_current_economics()["input_accumulated"] == 120


def test_backpressure_overflow_raises(tmp_path: Path) -> None:
    """A saturated FIFO queue raises BackpressureOverflowError, no crash."""
    tiny = RateLimitConfig(
        version="1.00",
        rate_limits={"services": {"default": {
            "requests_per_minute": 1, "concurrent_max": 1,
            "retry_after_seconds": 1, "max_retries": 1, "queue_max_depth": 1}}},
    )
    cfg = ConfigManager(config_dir=REAL_CONFIG_DIR)
    gk = ApiGatekeeper(tiny, cfg.setup.llm_routing,
                       token_tracker=TokenTracker(usage_file=tmp_path / "u.json"),
                       client=mock.Mock(), get_env=_env)
    gk._queue.put_nowait(1)  # pre-saturate the single slot
    with pytest.raises(BackpressureOverflowError):
        gk.execute_llm_call("prompt", "system")


def test_dual_provider_failure_raises(tmp_path: Path) -> None:
    """Both providers down (502 then 503) -> ProviderUpstreamError, no crash."""
    client = mock.Mock()
    client.post = mock.Mock(side_effect=[_http_error(502), _http_error(503)])
    gk = _build_gatekeeper(client, tmp_path)

    with pytest.raises(ProviderUpstreamError):
        gk.execute_llm_call("prompt", "system")
    assert client.post.call_count == 2


def test_generic_execute_passthrough(tmp_path: Path) -> None:
    """The generic execute() chokepoint runs an arbitrary callable and returns it."""
    gk = _build_gatekeeper(mock.Mock(), tmp_path)
    result = gk.execute(lambda value: {"sent": value}, "payload", service="gmail")
    assert result == {"sent": "payload"}
    assert gk._queue.qsize() == 0  # slot acquired then released
