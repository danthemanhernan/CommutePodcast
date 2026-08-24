# Commute Podcast

Turn technical podcast scripts into commute-ready MP3 episodes. Stage 1 is a local-first Python
CLI used directly or through a ChatGPT Work skill. The core is intentionally provider-neutral so
the same workflow can later run behind a remote MCP server and an AWS job queue.

## Learn while building

This repository is organized as an engineering capstone, with complete vertical slices and explicit
learning evidence:

- [Learning roadmap](ROADMAP.md): versions, objectives, task checklists, and exit criteria
- [Stage 1 code walkthrough](docs/stage-01-local-pipeline.md): what every current module does
- [Stage 2 provider evaluation](docs/stage-02-provider-evaluation.md): transcript library and comparison workflow
- [Version 0.4 scorecard](docs/v04-evaluation-scorecard.md): objective and listening evaluation template
- [Learning log](docs/learning-log.md): reflection and evidence after each slice
- [Architecture decisions](docs/decisions/README.md): durable choices and their tradeoffs
- [Codex workflow](docs/codex-workflow.md): continue locally, in worktrees, and eventually in cloud
- [Architecture evolution](docs/architecture.md): local-to-MCP system shape

## Stage 1 capabilities

- Configurable OpenAI text-to-speech voice and delivery style
- Paragraph- and sentence-aware script chunking
- Resumable generation with a per-episode working directory
- Deterministic `plan` command that estimates chunks, duration, and API input size without cost
- MP3 concatenation and optional EBU R128 loudness normalization through `ffmpeg`
- Episode manifest containing settings and generated artifacts
- Repository-backed transcript library for repeatable episode generation
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

Set `OPENAI_API_KEY` in `.env`. The CLI loads that file automatically and never
prints the key.

You can also set the key in your shell:

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

Run every local quality check:

```bash
make check
```

## Roadmap summary

The project progresses from a local CLI through provider evaluation, containerized jobs, an AWS
pipeline, a remote MCP plugin, scheduled research, and a private RSS feed. See [ROADMAP.md](ROADMAP.md)
for versioned feature lists, learning objectives, implementation checklists, and acceptance tests.

AI-generated voices should be disclosed to listeners. Only clone or use voices for which you have
the necessary consent and rights.
