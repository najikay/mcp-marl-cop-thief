"""Unit tests for bonus scoring and mutual-agreement reconciliation."""

from __future__ import annotations

import pytest

from cop_thief.domain.reporting import AgreementReconciler, average_bonus, compute_bonus_claim


def test_winner_gets_ten_loser_seven():
    claim = compute_bonus_claim({"Alpha": 60, "Beta": 40})
    assert claim == {"Alpha": 10, "Beta": 7}


def test_tie_gives_five_each():
    assert compute_bonus_claim({"Alpha": 50, "Beta": 50}) == {"Alpha": 5, "Beta": 5}


def test_claim_requires_two_groups():
    with pytest.raises(ValueError):
        compute_bonus_claim({"Alpha": 10})


def test_average_over_series():
    assert average_bonus([10, 7]) == 8.5
    assert average_bonus([]) == 0.0


def test_matching_reports_agree():
    a = {"totals_by_group": {"A": 60, "B": 40}, "sub_games": [{"x": 1}]}
    b = {"totals_by_group": {"B": 40, "A": 60}, "sub_games": [{"x": 1}], "extra": "ignored"}
    assert AgreementReconciler().reconcile(a, b)


def test_divergent_reports_do_not_agree():
    a = {"totals_by_group": {"A": 60, "B": 40}, "sub_games": []}
    b = {"totals_by_group": {"A": 55, "B": 45}, "sub_games": []}
    assert not AgreementReconciler().reconcile(a, b)
