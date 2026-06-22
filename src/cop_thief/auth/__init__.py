"""Authentication & reporting: OAuth2 desktop flow + Gmail JSON-only sender."""

from .gmail_reporter import DEFAULT_RECIPIENT, GmailReporter

__all__ = ["DEFAULT_RECIPIENT", "GmailReporter"]
