"""Unit tests for the LLM client factory and offline mock."""

from __future__ import annotations

import pytest

from cop_thief.infra.llm_client import MockLLMClient, make_llm_client


def test_mock_is_deterministic():
    client = MockLLMClient()
    assert client.complete("hello") == client.complete("hello")
    assert "hello" in client.complete("hello")


def test_factory_defaults_to_mock():
    assert isinstance(make_llm_client(), MockLLMClient)
    assert isinstance(make_llm_client("mock"), MockLLMClient)


def test_factory_rejects_unknown_provider():
    with pytest.raises(ValueError):
        make_llm_client("banana")


def test_factory_unwired_provider_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        make_llm_client("cloud")
