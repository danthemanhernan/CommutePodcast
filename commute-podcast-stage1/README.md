# Commute Podcast

Turn technical podcast scripts into commute-ready MP3 episodes. Stage 1 is a local-first Python
CLI used directly or through a ChatGPT Work skill. The core is intentionally provider-neutral so
the same workflow can later run behind a remote MCP server and an AWS job queue.

## Stage 1 capabilities

- Configurable OpenAI text-to-speech voice and delivery style
- Paragraph- and sentence-aware script chunking
- Resumable generation with a per-episode working directory
- Deterministic `plan` command that estimates chunks, duration, and API input size without cost
- MP3 concatenation and optional EBU R128 loudness normalization through `ffmpeg`
- Episode manifest containing settings and generated artifacts
- `--dry-run` mode for verifying the entire local workflow without an API call

## Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)
- `ffmpeg`
- An OpenAI API key for real generation

## Setup

```bash
uv sync --extra dev
cp .env.example .env
```

Set `OPENAI_API_KEY` in your shell. The CLI deliberately does not read or print the key itself.

```bash
export OPENAI_API_KEY="your-key"
```

## Try it safely

Inspect how a script will be processed:

```bash
uv run commute-podcast plan examples/pilot.md
```

Exercise the complete pipeline without calling a paid API:

```bash
uv run commute-podcast generate examples/pilot.md --dry-run
```

Generate the real episode:

```bash
uv run commute-podcast generate examples/pilot.md --title "Pilot Episode"
```

Output is written under `episodes/<episode-slug>/`, with the finished MP3 copied to
`episodes/<episode-slug>.mp3`.

## Roadmap

1. Local CLI and ChatGPT Work skill
2. Provider abstraction and ElevenLabs adapter
3. Containerized asynchronous worker
4. AWS SQS, ECS Fargate, S3, DynamoDB, and EventBridge
5. Remote MCP server and private ChatGPT plugin
6. Automated script research and private podcast RSS feed

AI-generated voices should be disclosed to listeners. Only clone or use voices for which you have
the necessary consent and rights.

