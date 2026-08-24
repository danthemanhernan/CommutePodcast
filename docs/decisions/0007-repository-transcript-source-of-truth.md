# ADR 0007: Keep reviewed transcripts in the repository

- Status: Accepted
- Date: 2026-08-24
- Stage: v0.4

## Context

Daily transcript drafting currently requires moving between ChatGPT and the repository. That makes
it easy to lose source citations, revise the wrong copy, or generate audio from text that was not
reviewed or preserved.

## Decision

Store reviewed episode transcripts as dated Markdown files under `content/episodes/`, with front
matter for title, date, status, topics, and sources. The transcript path and content hash will be
recorded in the episode manifest when the generator consumes it.

## Consequences

Git provides history, review, and rollback. Provider comparisons can use exactly the same script,
and future scheduled workflows have a clear input/output boundary. The repository gains editorial
content that needs review, and a validator must reject incomplete metadata before generation.

## Revisit when

Transcripts move to a dedicated content database or CMS, or the scheduled research workflow needs
multi-user editorial collaboration beyond Git review.
