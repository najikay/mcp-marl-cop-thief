"""Tests for the parser's LLM path and SDK.parse_message integration."""

from __future__ import annotations

from cop_thief.domain.nl import NLParser
from cop_thief.infra import MockLLMClient
from cop_thief.sdk import CopThiefSDK


class _JsonLLM:
    """A fake LLM that returns a structured JSON belief."""

    def complete(self, prompt: str) -> str:
        return '{"region_row": "south", "region_col": "east", "confidence": 0.9}'


def test_parser_uses_llm_json_when_available():
    belief = NLParser(llm=_JsonLLM()).parse("anything")
    assert belief.region_row == "south"
    assert belief.region_col == "east"
    assert belief.confidence == 0.9


def test_parser_falls_back_when_llm_not_json():
    # MockLLMClient echoes non-JSON, so the heuristic must take over.
    belief = NLParser(llm=MockLLMClient()).parse("I'm in the northern flank")
    assert belief.region_row == "north"


def test_sdk_parse_message_returns_belief(small_config):
    sdk = CopThiefSDK(config=small_config)
    belief = sdk.parse_message("slipping through the south-east area")
    assert belief.region_row == "south"
    assert belief.region_col == "east"
