# PRD — OAuth2 Desktop Client & Gmail JSON Reporter

| Field | Value |
|-------|-------|
| Mechanism | End-of-game JSON-only report email via the Gmail API |
| Implements | PRD §F-15, §N-01, KPI K6, PLAN Phase 8 |
| Code | [`auth/oauth_flow.py`](../src/cop_thief/auth/oauth_flow.py), [`auth/gmail_reporter.py`](../src/cop_thief/auth/gmail_reporter.py) |
| Version | 1.0.0 |

## 1. Purpose
At game end the Cop emails a **JSON-only** report to the examiner. Access uses an
**OAuth2 token, never a password** (N-01): tokens are short-lived, scoped and
revocable; a stored password would be exposed on breach.

## 2. Requirements
| ID | Requirement |
|----|-------------|
| M-1 | Desktop OAuth2 flow: `credentials.json` → `token.json`, with refresh; both git-ignored. |
| M-2 | Scope limited to `gmail.modify` (least privilege). |
| M-3 | Email **body is valid JSON only** — free text is rejected (K6). |
| M-4 | Exactly **one** email is sent per game (a re-send is blocked). |
| M-5 | The send is routed through the gatekeeper under the `gmail` budget. |
| M-6 | No secrets in source; recipient configurable via env (`REPORT_RECIPIENT`). |

## 3. Design
- **`oauth_flow.py`** — `load_credentials()` reuses/refreshes `token.json` or runs
  the desktop consent flow; `build_gmail_service()` returns the API client. Google
  libraries are imported lazily (offline-safe); excluded from coverage (interactive).
- **`GmailReporter`** — validates the JSON body, builds a MIME message, and sends
  via the **injected** Gmail service through `gatekeeper.execute("gmail", …)`; a
  `_sent` flag enforces single-send. The injected service makes it fully mockable.
- **`SDK.send_report(report, gmail_service)`** wires it to a played report.

## 4. Setup (per the Google guide)
Create a Google Cloud project → OAuth client of type **Desktop** → add the test
account as a **Test User** → enable the Gmail API → download `credentials.json`
into the repo root (git-ignored). First send opens consent and writes `token.json`.

## 5. Acceptance criteria
- A JSON body sends once; a second send raises (`test_gmail_reporter`).
- A free-text body is rejected with `ValueError`.
- Transient failures are retried via the gatekeeper (mocked service).
- `SDK.send_report` emits a played report's JSON (mocked service).
