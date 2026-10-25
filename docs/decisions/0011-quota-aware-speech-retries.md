# ADR 0011: Stop on exhausted speech credits and use one retry layer

- Status: Accepted
- Date: 2026-10-23
- Stage: Local generation hardening

## Context

The speech API returned HTTP 429 with `credit_balance_exhausted` / `insufficient_quota`.
The pipeline treated every RateLimitError as transient, and the SDK also retried each application
attempt. The batch continued attempting later episodes despite an account-wide billing failure.

## Decision

Classify billing failures by structured error code/type, not HTTP status alone. Never retry quota
exhaustion. Stop the batch and report unattempted scripts as `deferred`. Keep ordinary transient
errors retryable. Disable SDK retries so the configured application attempt limit is authoritative.
Reuse one lazily initialized SDK client per provider for connection pooling.

## Consequences

Resuming skips finished MP3s and reuses validated completed chunks without changing their boundary
settings or voice. Transient failures still use bounded exponential backoff. A timeout after server
processing may still incur cost on retry: the speech API path offers no exactly-once guarantee.
Credits must be replenished externally before a quota-blocked run can proceed. Error classification
and batch deferral have deterministic tests using real SDK error shapes without network access.

References: https://developers.openai.com/api/docs/guides/rate-limits
