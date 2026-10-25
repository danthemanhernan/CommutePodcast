# ADR 0008: Target 18–22 minute learning episodes

- Status: Accepted
- Date: 2026-09-04
- Stage: v0.4

## Context

The first transcript-library episodes were roughly five minutes long. They communicated recent
changes efficiently, but they did not leave enough time to build a durable mental model or explain
how a controls, software, or data engineer could apply the ideas.

## Decision

Treat each episode as a focused teaching session targeting 18–22 minutes of spoken audio, or about
2,700–3,300 words at 150 words per minute. Scripts should move from a motivating problem or story
through a mental model, mechanism, examples, failure modes, tradeoffs, and a practical recap.
Descriptive detail is encouraged when it teaches; repetition and generic filler are not.

Use the `plan` command before generation to check duration and word count. Exceptions are allowed
when the subject cannot support a responsible deep dive, but the transcript should explain that
editorial choice during review.

## Consequences

Longer scripts require more research, editorial review, and paid TTS calls. They also make chunk
resumption and audio validation more valuable. The listener gets enough narrative and technical
context to understand why a design exists, how it behaves, and when its tradeoffs matter.

## Revisit when

Listening evaluations show that episodes consistently feel rushed, padded, or materially too long,
or when completion data indicates that a different commute-length target better serves listeners.
