# ADR 0013: Correct episode dates and publish readable narration scripts

- Status: Accepted
- Date: 2026-10-25
- Stage: Podcast distribution

## Context

MP3 modification time describes artifact generation/copying, not an episode's editorial date.
Existing catalog records preserved those incorrect dates. No transcripts were included in RSS.
Apple's native transcript UI is unavailable for episodes distributed only through private feeds.

## Decision

Infer dates from ISO dates in filenames, then English dates in filenames/titles; use 08:00
America/Los_Angeles. Correct dated catalog entries without changing GUIDs or immutable audio URLs.
Keep original dates for undated episodes. Sort RSS newest first with a deterministic filename tie.
Do not attempt to override the listener's episode-order preference.

Use saved synthesis text (bounded by manifest chunk count) or an explicit adjacent
`.transcript.txt` sidecar for imported recordings. Publish escaped HTML under a content hash with
an RSS transcript tag and an episode-description link. Do not silently use newer repository drafts
or invent timestamps. Missing scripts produce no transcript claim. Scripts may differ from speech.
Host pages under `media/transcripts/` using existing media-prefix permissions.
Upload transcript pages before RSS and never upload unrelated local working files.

## Consequences

Previously subscribed clients can refresh corrected dates without duplicate episode IDs. Private
Apple Podcasts listeners can read a linked page, but native synchronized transcripts remain an
Apple platform limitation. The existing media-prefix grant also covers transcript-path access.
Undated imports and same-day episodes need explicit editorial metadata if finer ordering is desired.

References: https://podcasters.apple.com/support/5316-transcripts-on-apple-podcasts
https://podcasters.apple.com/support/3143-how-to-set-the-order-of-podcast-episodes
https://podcasting2.org/docs/podcast-namespace/tags/transcript
