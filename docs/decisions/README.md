# Architectural decision records

ADRs preserve important context for future Codex chats and portfolio reviewers. Create an ADR when
a choice materially constrains architecture, operations, security, cost, or future implementation.
Do not create one for trivial formatting or easily reversible local refactors.

## Status values

- `Proposed`: under active evaluation
- `Accepted`: current direction
- `Superseded`: replaced by a newer ADR
- `Deprecated`: intentionally retained only for compatibility

## Index

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-local-first-vertical-slice.md) | Build a complete local vertical slice before cloud infrastructure | Accepted |
| [0002](0002-provider-protocol.md) | Isolate TTS vendors behind a structural protocol | Accepted |
| [0003](0003-resumable-chunk-artifacts.md) | Preserve numbered chunk artifacts for recovery and inspection | Accepted |
| [0004](0004-ffmpeg-audio-processing.md) | Use `ffmpeg` for assembly and loudness normalization | Accepted |
| [0005](0005-explicit-episode-job-state.md) | Represent episode progress with explicit job state | Accepted |
| [0006](0006-embed-episode-metadata.md) | Embed episode metadata in generated MP3s | Accepted |
| [0007](0007-repository-transcript-source-of-truth.md) | Keep reviewed transcripts in the repository | Accepted |

## Template

```markdown
# ADR NNNN: Decision title

- Status: Proposed
- Date: YYYY-MM-DD
- Stage: vX.Y

## Context

What problem or constraint requires a durable choice?

## Decision

What will we do?

## Consequences

What becomes easier, harder, more expensive, or constrained?

## Revisit when

What measurable condition would justify reconsideration?
```
