# ADR 0003: Preserve numbered chunk artifacts for recovery and inspection

- Status: Accepted
- Date: 2026-08-22
- Stage: v0.2

## Context

Long episodes require several paid TTS calls. A failure near the end should not force regeneration
of valid earlier work, and chunk boundaries must remain inspectable during quality review.

## Decision

Write numbered text and audio parts inside a per-episode working directory and skip completed audio
parts on rerun.

## Consequences

Local recovery is simple and API waste is reduced. File existence alone is not sufficient proof of
valid completion, so Version 0.3 must add atomic writes, validation, checksums, and explicit state.

## Revisit when

The worker moves to object storage and a durable cloud job-state model.
