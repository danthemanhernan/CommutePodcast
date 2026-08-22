# Architecture and evolution

The local CLI, future worker, and future MCP server must depend on `podcast_core` behavior rather
than duplicating it. Provider implementations sit behind the `SpeechProvider` protocol.

## Stage 1 — local

`script -> chunker -> TTS provider -> ffmpeg -> MP3 + manifest`

## Stage 2 — cloud worker

`SQS job -> container worker -> TTS provider -> S3 object + DynamoDB status`

## Stage 3 — MCP

The remote server should expose `generate_podcast`, `get_podcast_status`, `get_podcast_episode`,
and `list_podcast_voices`. Generation must be asynchronous; the MCP request returns a job ID rather
than holding a connection open for an entire episode.

## Stage 4 — automation

EventBridge schedules research and script generation. A completed episode updates a private RSS
feed distributed through CloudFront or time-limited S3 URLs.

