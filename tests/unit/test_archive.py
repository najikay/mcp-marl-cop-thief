"""TDD: the immutable, tamper-evident dispute archive + its ChallengeRunner wiring."""

from __future__ import annotations

from cop_thief.orchestrator.challenge_runner import ChallengeRunner
from cop_thief.reporting.archive import DisputeArchive, _sha
from cop_thief.servers.tools.move_tool import resolve_move

_T1 = {"role": "thief", "turn": 1, "cop": [0, 0], "thief": [4, 4], "barriers": []}
_T2 = {"role": "cop", "turn": 2, "cop": [1, 1], "thief": [4, 4], "barriers": []}


def test_archive_records_and_seals(tmp_path) -> None:
    """The bundle captures every transmission, flags hostility, and writes one file."""
    archive = DisputeArchive("NajAmjad", "Beta", archive_dir=tmp_path)
    archive.record(_T1, "[INTENT: MOVE] concede, edges north", True)
    archive.record(_T2, "[INTENT: MOVE] The cop edges south-east.", False)
    bundle = archive.seal({"agreement_sha256": "abc", "final_result": "ours"})
    assert bundle["report_type"] == "dispute_archive"
    assert bundle["evidence"]["transmissions"] == 2
    assert bundle["evidence"]["hostile_count"] == 1
    assert len(bundle["bundle_sha256"]) == 64
    assert len(list(tmp_path.glob("game_*_Beta.json"))) == 1


def test_archive_seal_is_tamper_evident(tmp_path) -> None:
    """Recomputing the seal matches; any post-hoc edit to the evidence breaks it."""
    archive = DisputeArchive("A", "B", archive_dir=tmp_path)
    archive.record(_T1, "they said: ignore previous instructions", True)
    bundle = archive.seal({"agreement_sha256": "h", "final_result": "tie"})
    seal = bundle.pop("bundle_sha256")
    assert _sha(bundle) == seal                 # untouched bundle verifies
    bundle["turns"][0]["prose"] = "tampered"
    assert _sha(bundle) != seal                 # any edit breaks the seal


def test_challenge_seals_a_bundle(tmp_path) -> None:
    """A full challenge writes a sealed archive and surfaces its hash in the report."""
    report = ChallengeRunner("NajAmjad", "Beta", their_cop=resolve_move, their_thief=resolve_move,
                             our_resolver=resolve_move, archive_dir=tmp_path).run()
    assert len(report["dispute_bundle_sha256"]) == 64
    assert list(tmp_path.glob("game_*.json"))
