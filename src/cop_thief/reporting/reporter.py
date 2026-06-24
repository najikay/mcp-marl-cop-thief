"""Gmail-API JSON reporter behind the SEC-03 safety guard and API gatekeeper.

Delegation order (enforced): guard -> build canonical JSON (K3 SHA-256 + token
telemetry) -> dispatch through the ApiGatekeeper chokepoint.
"""

from __future__ import annotations

import base64
import hashlib
import json
from email.mime.text import MIMEText
from pathlib import Path

from cop_thief.domain.state import DecPomdpGameState
from cop_thief.infra.gatekeeper import build_default_gatekeeper
from cop_thief.reporting.guard import SubmissionSafetyGuard

_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
_ZERO_ECON = {"input_accumulated": 0, "output_accumulated": 0, "estimated_cost_usd": 0.0}


class GmailApiReporter:
    """Build and dispatch the end-game JSON handshake via the Gmail API."""

    def __init__(
        self,
        guard: SubmissionSafetyGuard | None = None,
        gatekeeper=None,
        service=None,
        token_tracker=None,
        sender: str = "mcp.marl.telemetry@gmail.com",
        credentials_path: str = "credentials.json",
        token_path: str = "token.json",
    ) -> None:
        """Wire the guard, gatekeeper, optional Gmail service and tracker."""
        self._guard = guard or SubmissionSafetyGuard()
        self._gatekeeper = gatekeeper or build_default_gatekeeper()
        self._service = service
        self._tracker = token_tracker
        self._sender = sender
        self._cred_path = Path(credentials_path)
        self._token_path = Path(token_path)

    def bootstrap_oauth(self):
        """Run the OAuth2 Desktop flow (gmail.modify), persisting token.json."""
        from google.auth.exceptions import RefreshError
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        creds = None
        if self._token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self._token_path), _SCOPES)
        if not creds or not creds.valid:
            try:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    raise RefreshError("interactive consent required")
            except RefreshError:  # stale/revoked token (e.g. disabled_client) -> re-consent
                flow = InstalledAppFlow.from_client_secrets_file(str(self._cred_path), _SCOPES)
                creds = flow.run_local_server(port=0)
            self._token_path.write_text(creds.to_json(), encoding="utf-8")
        self._service = build("gmail", "v1", credentials=creds)
        return self._service

    @staticmethod
    def _agreement_hash(facts: dict) -> str:
        """Compute the K3 byte-identical SHA-256 over canonical facts."""
        canon = json.dumps(facts, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()

    def _build_report(self, state: DecPomdpGameState) -> dict:
        """Formulate the canonical end-game JSON handshake."""
        facts = {
            "cop_pos": list(state.cop_pos),
            "thief_pos": list(state.thief_pos),
            "turn_counter": state.turn_counter,
            "barriers": sorted(list(cell) for cell in state.grid.barriers),
        }
        econ = self._tracker.get_current_economics() if self._tracker else dict(_ZERO_ECON)
        telemetry = {k: econ.get(k, _ZERO_ECON[k]) for k in _ZERO_ECON}
        telemetry["status"] = "OK"
        return {"report_type": "internal_game", "facts": facts,
                "agreement_sha256": self._agreement_hash(facts), "telemetry": telemetry}

    def _encode_message(self, recipient: str, body: str, subject: str = "marl-cop-thief game report") -> dict:
        """Encode a JSON-only MIME message for the Gmail API."""
        message = MIMEText(body, "plain", "utf-8")
        message["to"] = recipient
        message["from"] = self._sender
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        return {"raw": raw}

    def _send(self, message: dict) -> dict:
        """Low-level Gmail send (always routed via the gatekeeper)."""
        return self._service.users().messages().send(userId="me", body=message).execute()

    def dispatch_game_report(self, state: DecPomdpGameState, recipient_email: str) -> dict:
        """Guard the recipient, build the JSON handshake, then dispatch it."""
        self._guard.verify_safe_recipient(recipient_email)
        report = self._build_report(state)
        message = self._encode_message(recipient_email, json.dumps(report))
        report["_delivery"] = self._gatekeeper.execute(self._send, message, service="gmail")
        return report

    def dispatch_payload(self, report: dict, recipient_email: str) -> dict:
        """Guard + dispatch a JSON report; carry ``groups.ours`` into the subject line."""
        self._guard.verify_safe_recipient(recipient_email)
        group = report.get("groups", {}).get("ours", "")
        subject = f"marl-cop-thief game report: {group}".rstrip(": ")
        message = self._encode_message(recipient_email, json.dumps(report), subject)
        report["_delivery"] = self._gatekeeper.execute(self._send, message, service="gmail")
        return report
