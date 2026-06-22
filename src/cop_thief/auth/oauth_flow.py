"""OAuth2 desktop flow for the Gmail API (PRD §N-01: tokens, never passwords).

``credentials.json`` (downloaded from the Google Cloud OAuth client) and the
resulting ``token.json`` are both git-ignored. Google libraries are imported
lazily so the rest of the package — and the whole test suite — runs without
network access or an interactive browser. This module is excluded from coverage
because its real path requires interactive consent.
"""

from __future__ import annotations

from pathlib import Path

# Gmail send/modify is all the reporter needs; calendar (per the guide) is unused.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def load_credentials(
    credentials_file: str = "credentials.json",
    token_file: str = "token.json",
):  # pragma: no cover - interactive OAuth / external libs
    """Return valid OAuth credentials, refreshing or running consent as needed."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if Path(token_file).exists():
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        Path(token_file).write_text(creds.to_json(), encoding="utf-8")
    return creds


def build_gmail_service(creds=None):  # pragma: no cover - external libs / network
    """Build an authenticated Gmail API service object."""
    from googleapiclient.discovery import build

    return build("gmail", "v1", credentials=creds or load_credentials())
