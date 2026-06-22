"""Integration tests for the inter-group bonus series and report."""

from __future__ import annotations

import json

from cop_thief.domain.reporting import AgreementReconciler
from cop_thief.sdk import CopThiefSDK


def _sides(config):
    sdk_a = CopThiefSDK(config=config)
    sdk_b = CopThiefSDK(config=config)
    side_a = sdk_a.make_side(
        "Team-Alpha", "https://github.com/alpha/x", "https://a-cop", "https://a-thief", ["Amjad"]
    )
    side_b = sdk_b.make_side(
        "Team-Beta", "https://github.com/beta/y", "https://b-cop", "https://b-thief", ["Naji"]
    )
    return sdk_a, sdk_b, side_a, side_b


def test_series_plays_six_sub_games_split_in_half(small_config):
    sdk_a, _sdk_b, side_a, side_b = _sides(small_config)
    series = sdk_a.run_bonus_series(side_a, side_b)
    assert len(series.first_half) == small_config.num_games // 2
    assert len(series.second_half) == small_config.num_games // 2
    assert set(series.totals_by_group) == {"Team-Alpha", "Team-Beta"}


def test_bonus_report_matches_schema(small_config):
    sdk_a, _sdk_b, side_a, side_b = _sides(small_config)
    series = sdk_a.run_bonus_series(side_a, side_b)
    data = json.loads(sdk_a.build_bonus_report(series, side_a, side_b).to_json())
    assert data["report_type"] == "bonus_game"
    assert data["groups"] == {"group_1": "Team-Alpha", "group_2": "Team-Beta"}
    assert len(data["sub_games"]) == small_config.num_games
    assert set(data["bonus_claim"]) == {"Team-Alpha", "Team-Beta"}
    assert data["mutual_agreement"] is True


def test_both_groups_reports_agree(small_config):
    sdk_a, sdk_b, side_a, side_b = _sides(small_config)
    # Deterministic seed => both sides reproduce the identical series.
    series_a = sdk_a.run_bonus_series(side_a, side_b)
    series_b = sdk_b.run_bonus_series(side_a, side_b)
    report_a = sdk_a.build_bonus_report(series_a, side_a, side_b).to_dict()
    report_b = sdk_b.build_bonus_report(series_b, side_a, side_b).to_dict()
    assert AgreementReconciler().reconcile(report_a, report_b)
