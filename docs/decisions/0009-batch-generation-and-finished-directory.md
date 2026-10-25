# ADR 0009: Batch generation skips published transcripts

- Status: Accepted
- Date: 2026-09-08
- Stage: v0.4

## Context

Reviewed transcripts are added over time to `content/episodes/`. Requiring a separate CLI
invocation for every file makes the normal daily workflow tedious, while rerunning all files risks
duplicating paid TTS work.

## Decision

Add `commute-podcast generate-all` and the `scripts/generate-pending-episodes.sh` wrapper. The
batch command discovers only top-level, date-prefixed Markdown files, derives each title from its
first H1. It recognizes both the transcript filename (`episodes/finished/<source-stem>.mp3`) and
the title slug (`episodes/finished/<title-slug>.mp3`) as publication/idempotency markers.
Pending files use the existing episode orchestrator with `episodes/` as the working directory and
`episodes/finished/` as the publication directory. Failures are collected so other episodes can
proceed, and the process exits non-zero if any failed.

## Consequences

Daily use is a single command and completed episodes are not regenerated. Working chunks and
manifests live in `episodes/<slug>/`, leaving `episodes/finished/` clean for published MP3s.
Renaming a
transcript or changing its H1 creates a new slug and is treated as a new publication; content-hash
based invalidation is intentionally deferred.
