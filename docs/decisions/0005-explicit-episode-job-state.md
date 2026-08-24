# ADR 0005: Represent episode progress with explicit job state

- Status: Accepted
- Date: 2026-08-23
- Stage: v0.3

## Context

The v0.2 generator inferred progress mostly from whether numbered audio files existed. That is
useful for reusing completed chunks, but it cannot distinguish a planned job, active synthesis,
assembly, successful completion, or failure. File existence also does not prove that a file is
valid.

## Decision

Introduce an `EpisodeJob` model with explicit `JobStatus` values: `planned`, `synthesizing`,
`assembling`, `completed`, and `failed`. The orchestrator controls transitions and records the
current state in the episode manifest.

## Consequences

Progress is visible and invalid state jumps are rejected, creating a stable seam for future logs,
retries, and cloud job records. The first slice still writes the manifest at the end of the run, so
failure state is not yet durable after an abrupt process exit; atomic artifacts and incremental
state persistence remain follow-up work.

## Revisit when

Version 0.3 adds incremental manifest writes, atomic audio files, and validation of completed parts.
