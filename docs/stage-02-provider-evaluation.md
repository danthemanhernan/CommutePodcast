# Stage 2 walkthrough: transcript library and provider evaluation

Version 0.4 extends the local workflow in two directions: transcripts become durable repository
inputs, and TTS providers become comparable implementations behind the same protocol.

## The complete flow

```text
Markdown transcript + front matter
        ↓
Validate title, date, status, and sources
        ↓
Plan one shared script
        ↓
Run the same chunks through each provider
        ↓
Record latency, cost, failures, and metadata
        ↓
Listen to blind samples and score them
        ↓
Choose a default with an ADR
```

## Transcript source of truth

The reviewed file under `content/episodes/` is the canonical script. This removes the fragile loop
of drafting in chat, copying into the repository, and losing the relationship between the final
script and its sources. Git provides history, review, and rollback; the manifest will provide the
exact transcript hash used for an audio run.

## Editorial depth standard

The transcript is designed to teach one topic deeply during a commute, not to summarize a set of
headlines. Aim for 18–22 minutes, approximately 2,700–3,300 words at 150 words per minute. Build
from a motivating problem or story to a mental model, then explain the mechanism, boundaries,
failure modes, worked examples, tradeoffs, and practical takeaways. Descriptive detail should
increase understanding; avoid padding through repeated claims or generic enthusiasm. Use the
`plan` command as a pre-generation quality gate for word count and estimated duration.

## Provider comparison

The existing `SpeechProvider` protocol is the seam. A second adapter should translate its own API
request and response format into the same `synthesize()` behavior without changing the episode
orchestrator. Both providers receive the exact same transcript and voice evaluation script.

Objective measurements include request latency, retries, failures, input characters, estimated cost,
output duration, and audio format. Subjective listening should be blind and score pronunciation,
pacing, expressiveness, technical clarity, and overall commute suitability.

## Suggested task rhythm

1. Add and validate one transcript in `content/episodes/`.
2. Generate a baseline sample with OpenAI.
3. Add the second provider adapter behind `SpeechProvider`.
4. Generate matching samples.
5. Fill out the [evaluation scorecard](v04-evaluation-scorecard.md).
6. Record the provider decision in a new ADR.
