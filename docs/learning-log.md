# Learning log

Use one entry per meaningful vertical slice. Keep answers short and concrete; link commits, test
output, manifests, diagrams, or screenshots as evidence.

## Entry template

### Date — version — topic

**What I built**

-

**What I can now explain**

-

**Evidence**

- Command or test:
- Artifact or commit:

**Failure or surprise**

-

**Decision and tradeoff**

- Decision:
- Benefit:
- Cost:
- Revisit when:

**Next experiment**

-

---

## 2026-08-22 — v0.2 — first playable episode

**What I built**

- A local Python pipeline that converted a technical Markdown script into a playable MP3 using
  OpenAI TTS and `ffmpeg`.

**What I can now explain**

- Complete after reading `docs/stage-01-local-pipeline.md` and tracing a real run.

**Evidence**

- The pilot episode generated successfully and sounded good during playback.
- The repository passed six tests and Ruff validation at the initial checkpoint.

**Failure or surprise**

- Add observations from the first listen: pacing, pronunciation, voice, transitions, and volume.

**Decision and tradeoff**

- Local-first generation gave the fastest feedback loop before paying the complexity cost of AWS.

**Next experiment**

- Force a two-chunk interruption and prove that completed chunks resume correctly.

---

## 2026-08-23 — v0.3 — explicit episode job state

**What I built**

- Added an `EpisodeJob` model with a small state machine: `planned`, `synthesizing`, `assembling`,
  `completed`, and `failed`.
- Updated the orchestrator to move through those states and include the final job state in the
  episode manifest.

**What I can now explain**

- A file existing on disk is not the same thing as a job having an explicitly known state.
- A state machine makes valid progress and invalid jumps visible to both code and tests.
- This first slice records final state; it does not yet persist state after an abrupt process exit.

**Evidence**

- Command: `UV_CACHE_DIR=/tmp/commute-podcast-uv-cache make check`
- Result: Ruff passed, 8 tests passed, `plan` and dry-run completed successfully.
- Tests: `tests/test_episode.py` covers the valid lifecycle and invalid transition.

**Failure or surprise**

- The default `uv` cache location was outside the writable workspace in this environment, so the
  check needed a temporary `UV_CACHE_DIR`.

**Decision and tradeoff**

- Decision: Keep the state machine in a small domain model and let the orchestrator own transitions.
- Benefit: Later logging, retries, and cloud job records have a stable vocabulary.
- Cost: The manifest is still written only at the end of the run.
- Revisit when: Incremental persistence and atomic audio validation are implemented.

**Next experiment**

- Persist state transitions incrementally and validate each audio part before treating it as complete.

---

## 2026-08-23 — v0.3 — local pipeline hardening

**What I built**

- Separated planning, synthesis, assembly, and publication into explicit functions.
- Added JSON logs, bounded transient retries, atomic audio replacement, `ffprobe` validation, cost
  metadata, pronunciation replacements, and an opt-in real-API test.

**What I can now explain**

- A retry belongs around the provider operation, while atomic replacement protects the artifact
  boundary.
- Estimated cost can be calculated locally, but actual cost requires usage data from the provider.
- A validation command is a cheap local quality gate and does not need to call the TTS API.

**Evidence**

- Tests: `UV_CACHE_DIR=/tmp/commute-podcast-uv-cache make check`
- Recovery exercises: `docs/v03-recovery-exercises.md`
- Paid integration: skipped unless `RUN_REAL_API_TESTS=1` is set.

**Failure or surprise**

- Existing audio is now reused only after `ffprobe` validation; an invalid part is regenerated.

**Decision and tradeoff**

- Decision: Keep actual provider cost nullable until the `SpeechProvider` contract exposes usage.
- Benefit: The manifest does not present an unverified estimate as a bill.
- Cost: Actual billing is not yet visible locally.
- Revisit when: Provider comparison or cloud billing metadata is added.

**Next experiment**

- Add a second provider and compare quality, latency, cost, and failure behavior in Version 0.4.

---

## 2026-08-23 — v0.3 complete — first recovery-tested episodes

**What I built**

- Completed the local hardening stage and generated the first two episodes.

**What I can now explain**

- The local generator can recover completed chunks, reject invalid audio, and produce a validated
  final MP3 with observable phase transitions.

**Evidence**

- Completed the v0.3 recovery exercises.
- Generated and validated two real episodes in `episodes/`.

**Next experiment**

- Begin Version 0.4 by adding a second TTS provider and comparing it with OpenAI using the same
  evaluation script.

---

## 2026-08-23 — metadata — library-ready episodes

**What I built**

- Embedded ID3v2.3 title, artist, album, album artist, genre, comment, and year metadata during
  FFmpeg assembly.
- Added a regression test and retagged the first two final episodes.

**What I can now explain**

- Audio content and media metadata are separate concerns: TTS creates the sound, while FFmpeg
  packages the finished file for media-library software.

**Evidence**

- `ffprobe` shows metadata on both final MP3 files.

**Next experiment**

- Start Version 0.4 provider comparison with a shared evaluation script.

---

## 2026-08-24 — v0.4 kickoff — transcript source of truth

**What I built**

- Added the Version 0.4 task list, provider-evaluation walkthrough, blind listening scorecard, and
  repository-backed `content/episodes/` transcript format.

**What I can now explain**

- ChatGPT can remain a drafting interface while Git-backed Markdown remains the durable reviewed
  input for generation.
- Provider comparisons are only meaningful when every provider receives the same transcript and
  evaluation settings.

**Evidence**

- [Version 0.4 walkthrough](stage-02-provider-evaluation.md)
- [Evaluation scorecard](v04-evaluation-scorecard.md)
- [Transcript library format](../content/episodes/README.md)

**Next experiment**

- Add transcript validation and generate one episode from `content/episodes/` before adding the
  second provider adapter.

---

## 2026-09-04 — v0.4 — teaching-episode depth standard

**What I built**

- Defined a target of 18–22 minutes, approximately 2,700–3,300 spoken words, for new episodes.
- Added a rubric requiring mental models, mechanisms, stories or worked examples, failure modes,
  tradeoffs, and a practical recap without filler.

**What I can now explain**

- A news summary and a learning episode optimize for different outcomes: the latter needs enough
  narrative and technical detail to build a transferable mental model.
- Word count is a useful pre-generation proxy for depth, but editorial review must still judge
  whether the additional words teach rather than repeat.

**Evidence**

- [Editorial standard](../content/episodes/README.md)
- [ADR 0008](decisions/0008-teaching-episode-depth.md)

**Next experiment**

- Write and review the next transcript against the rubric before generating its audio.

## 2026-10-22: Early Apple Podcasts distribution slice

Implemented portable RSS generation without changing TTS orchestration. Deterministic tests
exercise stable GUIDs and dates, XML escaping, content-addressed media, and preservation of the
previous feed on invalid audio. Hosting and device playback remain unverified. Reproduce the
walkthrough in `docs/apple-podcasts.md` and explain why the catalog is durable local state and
why an unlisted feed URL is a bearer credential.

Verification: `make check` passed (24 tests passed, one paid integration test skipped). Built the
portable feed twice from 26 existing finished episodes using an explicitly nonfunctional
`example.invalid` rehearsal URL; all 26 passed ffprobe validation. Generated output and local
catalog remain ignored by Git. No speech API calls or hosting resources were used.

## 2026-10-23: Speech quota recovery

The preceding real batch generated 10 additional episodes before exhausting prepaid API credits.
Quota failures were retried and the batch continued through later scripts. Added structured billing
error classification, batch deferral, a single retry layer, and connection reuse. Preserve chunk
boundaries and completed artifacts during continuation. Tests exercise the actual SDK error shape
without paid calls. The character-based cost estimate remains a legacy heuristic, not API billing.

Verification: `make check` passed with 28 tests passed and one paid test skipped. The authorized
real continuation reused September 24 chunk 1, successfully generated chunk 2, and validated it
with ffprobe. The remaining batch continues in `episodes/batch-resume.*.log`; completion is pending.

## 2026-10-25: Automatic S3 publication

Added a Boto3 publisher and made the pending-generation shell script select `--publish`. The
publisher validates hashed local media, skips matching existing objects, and uploads RSS last.
Failed generation skips publication; failed publication can be retried without TTS. Tests use fake
S3 clients, including HEAD permission errors, transfer failures, and dry-run network exclusion.
README now covers AWS login, .env variables, bucket/CloudFront setup, publication, and subscribing.
Learn to explain the feed-last commit point and the distinction between local and hosted durability.

Verification: `make check` passed (44 tests passed, one paid integration test skipped), and the shell
script passed `bash -n`. A real local `publish --dry-run` rebuilt and verified 65 referenced MP3s
with the configured hosting settings and uploaded zero objects. No paid TTS or live AWS requests
were made during verification. Hosted playback and a real publication remain operator acceptance.

## 2026-10-25: Transcript access and chronological dates

Root cause: RSS publication dates used MP3 modification times, so regenerated/copied recordings
sorted by artifact activity rather than episode date. Corrected dated catalog records while
preserving GUIDs and media URLs. Narration text now becomes escaped HTML with standard transcript
tags and links in episode notes. Apple documents that native transcripts are unavailable for private
RSS feeds, so the readable linked page is the supported fallback.

`make check` passed (48 passed, one paid test skipped). Local and hosted feed checks confirm 65
episodes with descending dates and 64 transcript links. Published all 64 pages while skipping all
65 existing audio objects; no speech API calls. The first attempt exposed an AccessDenied on a new
top-level transcript path. Hosting under `media/transcripts/` uses the existing media-prefix grant
without expanding IAM permissions. CloudFront returned HTTP 200 with text/html for a transcript.
One imported `engineering-commute-2026-08-25-hyperpod.mp3` has no saved script; its transcript
remains unavailable pending verified source text or an explicitly authorized transcription workflow.
Device-native transcript UI remains unsupported by Apple for private feeds; iPhone refresh and the
listener's preferred episode sort remain device acceptance steps.
