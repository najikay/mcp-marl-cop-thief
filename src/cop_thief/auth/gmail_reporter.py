"""GmailReporter — send the end-of-game report as a JSON-only email.

Enforces the brief's rules: the body must be valid JSON (no free text, KPI K6)
and exactly one email is sent per game. The send is routed through the gatekeeper
under the ``gmail`` service budget. The Gmail service object is injected, so the
reporter is fully testable with a mock (no Google libraries or network needed).
"""

from __future__ import annotations

import base64
import json
import os
from email.message import EmailMessage

from ..infra import ApiGatekeeper

DEFAULT_RECIPIENT = "rmisegal+uoh26b@gmail.com"


class GmailReporter:
    """Send a single JSON-only report email via the Gmail API."""

    def __init__(
        self,
        service,
        gatekeeper: ApiGatekeeper | None = None,
        recipient: str | None = None,
    ) -> None:
        self._service = service
        self._gatekeeper = gatekeeper or ApiGatekeeper()
        self._recipient = recipient or os.environ.get("REPORT_RECIPIENT", DEFAULT_RECIPIENT)
        self._sent = False

    def send_report(self, json_body: str, subject: str = "Cop & Thief game report") -> dict:
        """Validate the JSON body and send exactly one email (gatekeeper-routed)."""
        json.loads(json_body)  # reject any non-JSON / free-text body (K6)
        if self._sent:
            raise RuntimeError("report already sent for this game (one email only)")
        raw = self._encode(json_body, subject)
        body = {"raw": raw}
        result = self._gatekeeper.execute(
            "gmail", lambda: self._service.users().messages().send(userId="me", body=body).execute()
        )
        self._sent = True
        return result

    def _encode(self, json_body: str, subject: str) -> str:
        message = EmailMessage()
        message["To"] = self._recipient
        message["Subject"] = subject
        message.set_content(json_body)
        return base64.urlsafe_b64encode(message.as_bytes()).decode()
