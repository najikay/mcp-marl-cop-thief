# PRD (Per-Mechanism) — OAuth2 Desktop Client & Gmail JSON Reporter
## `marl-cop-thief` · Mechanism: Secure Automated Result Reporting

| Field | Value |
|-------|-------|
| Mechanism ID | `MECH-GMAIL-OAUTH` |
| Document version | 1.00 |
| Parent docs | [`PRD.md`](./PRD.md) · [`PLAN.md`](./PLAN.md) · [`TODO.md`](./TODO.md) (Task #300, Phase 8) |
| Source modules | `auth/oauth_flow.py`, `auth/gmail_reporter.py`, `domain/reporting/*` |
| Source guide | Dr. Segal *"Integrating Google APIs: Client & Token Setup for Gmail & Calendar"* |
| Standard | Dr. Segal *Guidelines v3.00* (§7.4 secrets, §2.3, §11) |
| Status | Draft — approve before implementing Phase 8 |

> **Mandate.** At the end of every full game, the **Cop** agent autonomously sends a **single,
> JSON-only** email to `rmisegal+uoh26b@gmail.com` via the **Gmail API** (Google API Client). Both
> agents must reach **byte-identical mutual agreement** on that report (KPI **K3**). Authentication is
> **OAuth2 token-based with zero passwords**.

---

## 1. Theoretical & Mathematical Background

### 1.1 Why tokens, not passwords (zero-tolerance security)
A stored password is a **long-lived, full-scope, reusable** secret: on breach it grants total account
access. An OAuth2 token is **short-lived, narrowly-scoped, and revocable**. We request only the
`gmail.modify` scope (read/search/label/draft/send/manage Gmail messages) — the minimum needed to
send the report — embodying **least privilege** (Guidelines §7.4). Even if the access token leaks, it
expires quickly and is bound to a single scope, and can be revoked from the Google console.

### 1.2 OAuth2 Authorization-Code flow (Desktop application)
The Desktop OAuth client uses the **authorization-code grant**:
```
credentials.json (client_id, client_secret)         [bootstrap secret, git-ignored]
        │
        ▼  build flow → open browser → user consents (Test User)
authorization code  ──exchange──▶  access_token (short-lived) + refresh_token (long-lived)
        │
        ▼  persisted to token.json (git-ignored)
access_token expires  ──refresh_token──▶  new access_token   [silent, automated]
refresh_token revoked/expired  ──────────▶  graceful re-auth (reopen consent)
```

### 1.3 Byte-identical agreement as a hash-equality proof
Mutual agreement (K3) is reduced to a **cryptographic equality check** over a canonical record.
Define a deterministic serialization `canon(·)` and digest `H = SHA-256(canon(record))`. Two agents
agree iff `H_cop == H_thief`. Canonicalisation removes all non-determinism (key order, whitespace,
float formatting, timezone normalisation), so equal *facts* ⇒ equal *bytes* ⇒ equal *hash*.

---

## 2. Token Lifecycle (detailed)

| Phase | Trigger | Action | Artifact |
|-------|---------|--------|----------|
| **Bootstrap** | First run, no `token.json` | Load `credentials.json` (Desktop client), build `InstalledAppFlow`, scopes `[gmail.modify]`. | `credentials.json` (input) |
| **Consent** | Bootstrap | Open local browser; user (registered **Test User**) approves. | authorization code |
| **Token mint** | Consent granted | Exchange code → access + refresh tokens. | `token.json` (written, git-ignored) |
| **Reuse** | Subsequent runs | Load `token.json`; if access token valid, use it. | — |
| **Auto-refresh** | Access token expired, refresh valid | Refresh silently; rewrite `token.json`. | refreshed `token.json` |
| **Graceful re-auth** | Refresh token revoked/expired | Detect refresh error → delete stale `token.json` → re-run consent. | new `token.json` |
| **Revoke** | Security incident | Revoke from Google console / programmatic revoke; next run re-bootstraps. | — |

### 2.1 Google Cloud one-time setup (documented in README/`assets/`)
1. Create project → Google Auth Platform. 2. Audience = **External**; add the sending Gmail as a
**Test User**. 3. **Enable Gmail API**. 4. Data access → add scope `https://www.googleapis.com/auth/gmail.modify`
(the guide also lists `calendar`; **unused** here). 5. Create **OAuth client → Desktop** → Download
JSON → rename to `credentials.json` in project root. 6. Confirm `credentials.json`/`token.json` are
git-ignored.

---

## 3. The Gmail JSON Reporter

### 3.1 Send contract
`send_report(report: BaseReport) -> SendResult` builds a MIME message whose **body is JSON only** (no
free text, no signatures, no HTML) and sends it via `users().messages().send` through the **Gatekeeper**
(`service="gmail"`).

### 3.2 Single-send guard & JSON-only enforcement
- **Exactly one** email per full game (idempotency guard keyed on game id) — re-trigger is a no-op.
- Pre-send validation asserts: body parses as JSON, matches the report schema, and contains **no**
  non-JSON characters before the opening `{` or after the closing `}`. Free text ⇒ **reject** (raise
  before send) so the examiner's automated parser never sees prose.
- Recipient `rmisegal+uoh26b@gmail.com` and subject template are **config-sourced**.

### 3.3 Technical-loss interplay
The reporter is invoked by `orchestrator/report_trigger.py` **only after 6 valid sub-games** exist
(void sub-games re-run first, `PRD.md F-06/K4`). The Cop is the designated sender.

---

## 4. Internal Game JSON Report Builder & Mutual-Agreement Hashing (K3)

### 4.1 Internal report schema (built by `domain/reporting/internal_report.py`)
```json
{
  "group_name": "Team-Alpha",
  "students": [],
  "github_repo": "https://github.com/team-alpha/marl-cop-thief",
  "cop_mcp_url": "https://cop-mcp-alpha.trycloudflare.com/mcp/",
  "thief_mcp_url": "https://thief-mcp-alpha.trycloudflare.com/mcp/",
  "timezone": "Asia/Jerusalem",
  "sub_games": [],
  "totals": { "cop": 90, "thief": 40 },
  "telemetry": { "input_accumulated": 0, "output_accumulated": 0,
                 "estimated_cost_usd": 0.0, "status": "OK" }
}
```
> The `telemetry` block is injected by the SDK from the TokenTracker (see `PRD_token_budget.md §3`).
> It is part of the agreed record (and therefore part of the hash) — see §4.3 for exclusion policy.

### 4.2 Canonical serialization `canon(record)`
- `json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.
- Floats formatted with fixed precision (`round(x, 6)`); timezone normalised to `Asia/Jerusalem`;
  `sub_games` ordered by index; sets serialised as sorted lists.

### 4.3 Agreement digest
```
H = SHA-256( canon(agreement_view(record)) )
```
`agreement_view` projects the record onto the **mutually-observable facts** (per-sub-game outcomes,
move logs, totals). **Telemetry is each side's own measurement** and is **excluded** from
`agreement_view` (the two groups legitimately consume different token counts), so it never causes a
spurious K3 failure — while still being reported in each email's `telemetry` block.

### 4.4 Reconciliation (`domain/reporting/agreement.py`)
Cop and Thief each compute `H`; the `agree_on_report` MCP tool exchanges digests. `mutual_agreement =
(H_cop == H_thief)`. On equality → send. On mismatch → Diplomat reconciliation
(`PRD_nl_protocol.md §3`); if still unequal after `max_rounds`, file with `mutual_agreement=false` and
attach full logs (and in the bonus, the series scores 0/0).

### 4.5 Bonus report
`domain/reporting/bonus_report.py` builds the inter-group schema (`report_type`, `groups`, two
`github_repo_*`, four `mcp_url_*`, `students_group_*`, `sub_games`, `totals_by_group`, `bonus_claim`,
`mutual_agreement`, plus per-group `telemetry`). Each group sends its **own** email with the **same**
`agreement_view` hash.

---

## 5. Functional Requirements, I/O Contracts & Metrics

### 5.1 Functional requirements
| ID | Requirement |
|----|-------------|
| GO-F1 | OAuth2 Desktop flow, scope `gmail.modify` only, **zero passwords**. |
| GO-F2 | Token lifecycle: bootstrap → consent → `token.json` → auto-refresh → graceful re-auth → revoke. |
| GO-F3 | Secrets git-ignored (`credentials.json`, `token.json`, `.env`); `.env-example` committed. |
| GO-F4 | Reporter sends via Gmail API through the Gatekeeper (`service="gmail"`). |
| GO-F5 | Body is **JSON only**; free text rejected pre-send. |
| GO-F6 | **Exactly one** email per full game (idempotent). |
| GO-F7 | Internal + bonus report builders match the mandated schemas. |
| GO-F8 | Byte-identical agreement via canonical-serialization SHA-256 (telemetry excluded from `agreement_view`). |
| GO-F9 | Cop is the designated sender; fires only after 6 valid sub-games. |

### 5.2 I/O contracts
**`oauth_flow.get_credentials()`** — In: `credentials.json` (+ optional `token.json`) · Out: valid
`Credentials` (refreshed/re-auth as needed).
**`send_report(report)`** — In: validated `BaseReport` · Out: `SendResult{message_id, status}`; raises
`ReportValidationError` on non-JSON/ schema-invalid body before any send.
**`agreement.compute_digest(record)`** — In: report dict · Out: hex SHA-256 of `agreement_view`.

### 5.3 Performance metrics
| Metric | Target |
|--------|--------|
| Passwords in code/config | **0** |
| Secrets committed to git | **0** |
| Emails per full game | exactly **1** |
| Non-JSON bytes in body | **0** |
| K3 false-mismatch from telemetry | **0** (telemetry excluded from hash) |
| Refresh success without user prompt (valid refresh token) | 100 % |

---

## 6. Hard Constraints, Edge Cases, Alternatives, Rationale

### 6.1 Hard constraints
- No passwords anywhere; OAuth tokens only.
- `credentials.json` / `token.json` never committed.
- Body JSON-only; one send per game.
- All sends through the Gatekeeper; files ≤150 LOC.

### 6.2 Edge cases
| Case | Behaviour |
|------|-----------|
| `token.json` missing | Bootstrap consent flow. |
| Access token expired, refresh valid | Silent refresh; rewrite token. |
| Refresh token revoked/expired | Delete stale token; graceful re-auth. |
| Account not a Test User | Consent blocked → clear actionable error in logs/README. |
| Body would contain prose | Reject with `ReportValidationError` (never send prose). |
| Re-trigger of report | Idempotent no-op (single-send guard). |
| Gmail transient 5xx | Gatekeeper retries (`service="gmail"`). |
| Hash mismatch | Diplomat reconcile; else `mutual_agreement=false` + logs. |

### 6.3 Alternatives considered
| Alternative | Verdict | Rationale |
|-------------|---------|-----------|
| SMTP + app password | **Rejected** | Password secret; brittle mail servers; brief mandates Gmail API + tokens. |
| Service account | Rejected | Domain-wide setup overhead; Desktop OAuth matches the provided guide. |
| Broad `https://mail.google.com/` scope | Rejected | Over-privileged; `gmail.modify` is least-privilege sufficient. |
| Hash full record incl. telemetry | **Rejected** | Telemetry differs per group → spurious K3 failures; excluded from `agreement_view`. |

### 6.4 Technical rationale
Token-over-password + least-privilege scope minimises blast radius; canonical-serialization hashing
turns "do the reports agree?" into a single deterministic equality, and excluding self-measured
telemetry from the hash prevents legitimate per-group token differences from breaking agreement.

---

## 7. Acceptance Criteria
- [ ] Desktop OAuth mints `token.json` from `credentials.json` with `gmail.modify` only.
- [ ] Expired access token auto-refreshes; revoked refresh triggers graceful re-auth.
- [ ] No passwords/secrets in repo (secret scan clean); secrets git-ignored.
- [ ] Reporter sends exactly one JSON-only email via the Gatekeeper; prose rejected.
- [ ] Identical facts ⇒ identical `agreement_view` hash on both sides; telemetry differences don't break it.
- [ ] Coverage ≥85 % for `auth/*` + `domain/reporting/*`; `ruff` clean.

## 8. Step-by-Step Test Scenarios
1. **Bootstrap (mocked Google libs):** no `token.json` ⇒ flow built with scope `gmail.modify`; `token.json` written.
2. **Reuse:** valid `token.json` ⇒ no consent; credentials returned.
3. **Refresh:** expired access + valid refresh ⇒ silent refresh; token rewritten; no prompt.
4. **Re-auth:** revoked refresh ⇒ stale token deleted; consent re-invoked.
5. **JSON-only guard:** report with a trailing free-text line ⇒ `ReportValidationError`, **no** send call.
6. **Single-send:** trigger report twice ⇒ exactly one `messages().send`.
7. **Gatekeeper path:** assert send invoked `gatekeeper.execute(service="gmail")`.
8. **Agreement equal:** two records with identical facts but different `telemetry` ⇒ same hash ⇒ `mutual_agreement=true`.
9. **Agreement mismatch:** differing sub-game outcome ⇒ different hash ⇒ reconcile path; on failure `false` + logs.
10. **Secret scan:** grep repo ⇒ zero keys/passwords; `credentials.json`/`token.json` git-ignored.

*End of `PRD_gmail_oauth.md`.*
