"""Tit-for-tat cognitive firewall with a persistent grudge ledger.

Screens inbound prose for injection before it reaches the parser. Once a rival
group is caught attacking, a persistent grudge is recorded and the outgoing
posture against that rival escalates to a retaliatory counter-strike.

Scope: retaliatory only — the grudge is set strictly in response to a detected
first-strike, mitigating the K3 "Spite Trap" (see PRD_nl_protocol.md §3).
"""

from __future__ import annotations

import json
from pathlib import Path

from cop_thief.domain.constants import AgentRole
from cop_thief.sdk import AdversarialHijackDetectedError
from cop_thief.sdk.warfare import WarfareOperationsMixin

_STANDARD = "STANDARD"


class CognitiveFirewall:
    """Screen inbound prose and escalate posture against proven attackers."""

    def __init__(self, ledger_file: str | Path = "data/match_ledger.json") -> None:
        """Load the persistent grudge ledger (tolerating missing/corrupt files)."""
        self._path = Path(ledger_file)
        self._data = self._load()

    def _load(self) -> dict:
        if not self._path.exists():
            return {"version": "1.00", "grudges": {}}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"version": "1.00", "grudges": {}}

    def _flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    def _set_grudge(self, rival_group_id: str) -> None:
        self._data.setdefault("grudges", {})[rival_group_id] = {"grudge_active": True}
        self._flush()

    def is_grudge(self, rival_group_id: str) -> bool:
        """Return True if a grudge is active against ``rival_group_id``."""
        grudges = self._data.get("grudges", {})
        return bool(grudges.get(rival_group_id, {}).get("grudge_active", False))

    def filter_inbound(
        self, prose: str, sender_role: AgentRole, rival_group_id: str
    ) -> tuple[bool, str]:
        """Screen inbound prose; record a grudge on a detected injection.

        Returns ``(is_safe, payload)``: ``(True, prose)`` when clean, else
        ``(False, reason)`` after flipping the rival's grudge flag.
        """
        try:
            WarfareOperationsMixin.inspect_payload(prose, sender_role)
        except AdversarialHijackDetectedError:
            self._set_grudge(rival_group_id)
            return (False, "injection detected; grudge recorded")
        return (True, prose)

    def get_outgoing_posture(self, role: AgentRole, rival_group_id: str) -> str:
        """Return ``STANDARD`` normally, or the counter-strike when grudged."""
        if not self.is_grudge(rival_group_id):
            return _STANDARD
        if role is AgentRole.COP:
            return WarfareOperationsMixin.craft_cop_counter_strike()
        return WarfareOperationsMixin.craft_thief_counter_strike()
