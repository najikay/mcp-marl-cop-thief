"""Unit tests for the Gmail JSON-only reporter (mocked Gmail service)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cop_thief.auth import DEFAULT_RECIPIENT, GmailReporter
from cop_thief.infra import ApiGatekeeper
from cop_thief.infra.errors import TransientError
from cop_thief.sdk import CopThiefSDK


def _fast_gatekeeper() -> ApiGatekeeper:
    """A gatekeeper that never really sleeps, so retry tests stay fast."""
    return ApiGatekeeper(clock=lambda: 0.0, sleeper=lambda _s: None)


def _service():
    """A mock Gmail service whose send() records the call and returns an id."""
    service = MagicMock()
    service.users.return_value.messages.return_value.send.return_value.execute.return_value = {
        "id": "msg-1"
    }
    return service


def test_sends_json_body_once():
    service = _service()
    reporter = GmailReporter(service)
    result = reporter.send_report('{"totals": {"cop": 90}}')
    assert result == {"id": "msg-1"}
    service.users.return_value.messages.return_value.send.assert_called_once()


def test_second_send_is_blocked():
    reporter = GmailReporter(_service())
    reporter.send_report('{"ok": true}')
    with pytest.raises(RuntimeError):
        reporter.send_report('{"ok": true}')


def test_free_text_body_rejected():
    reporter = GmailReporter(_service())
    with pytest.raises(ValueError):
        reporter.send_report("hello examiner, here are our results")


def test_default_recipient_used():
    service = _service()
    GmailReporter(service).send_report('{"a": 1}')
    sent_body = service.users.return_value.messages.return_value.send.call_args.kwargs["body"]
    assert "raw" in sent_body  # base64 MIME payload was built
    assert DEFAULT_RECIPIENT.endswith("@gmail.com")


def test_transient_failure_is_retried_via_gatekeeper():
    service = _service()
    send = service.users.return_value.messages.return_value.send
    send.return_value.execute.side_effect = [TransientError("503"), {"id": "msg-2"}]
    reporter = GmailReporter(service, gatekeeper=_fast_gatekeeper())
    assert reporter.send_report('{"a": 1}') == {"id": "msg-2"}
    assert send.return_value.execute.call_count == 2


def test_sdk_send_report_emits_report_json(small_config):
    sdk = CopThiefSDK(config=small_config)
    report = sdk.build_internal_report(
        sdk.play_game(), "Team-Alpha", "https://repo", "https://cop", "https://thief"
    )
    assert sdk.send_report(report, _service()) == {"id": "msg-1"}
