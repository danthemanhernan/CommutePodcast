# Commute Podcast project guidance

## Product goal

Build a production-quality system that turns curated technical scripts into commute-ready podcast
episodes. Evolve it through complete vertical slices: local CLI, containerized worker, AWS job
pipeline, remote MCP server, and autonomous private podcast feed.

## Learning goal

Treat every stage as a capstone lesson, not only a feature delivery. Explain important concepts at
the level of an experienced controls and data engineer. When behavior or architecture changes:

- update `ROADMAP.md` progress and exit criteria;
- update the relevant walkthrough under `docs/`;
- record a durable architectural choice under `docs/decisions/`;
- add or update tests that demonstrate the behavior;
- identify what the learner should be able to explain and reproduce afterward.

Prefer a runnable vertical slice before advanced abstractions. Do not introduce infrastructure or
frameworks until the current stage's exit criteria pass.

## Engineering agreements

- Use Python 3.12+, `uv`, type hints, small modules, and explicit dependency boundaries.
- Keep TTS providers behind the `SpeechProvider` protocol.
- Keep orchestration independent of CLI, future HTTP/MCP transport, and cloud infrastructure.
- Never print, commit, or request API keys in chat. Use environment variables or managed secrets.
- Preserve completed audio chunks when a generation fails so work can resume safely.
- Use structured logs and correlation IDs before adding asynchronous or distributed execution.
- Favor deterministic tests and dry runs; paid API calls are opt-in integration tests.
- Keep generated audio and episode working directories out of Git.

## Required checks

Run before committing:

```bash
make check
```

For changes to the real audio path, also run a short approved sample and validate it with
`ffprobe`. Do not incur API cost unless the user asked for real generation.

## Documentation map

- `README.md`: quick start and project orientation
- `ROADMAP.md`: versions, objectives, checklists, and exit criteria
- `docs/stage-01-local-pipeline.md`: current code walkthrough
- `docs/learning-log.md`: reflection and evidence template
- `docs/decisions/`: architectural decision records
- `docs/codex-workflow.md`: how to continue the project in Codex

## Code review rules

- Flag transport-specific logic leaking into `episode.py` or provider details leaking into the CLI.
- Flag any secret handling that could expose credentials through source, logs, shell history, or
  generated manifests.
- Flag generated audio committed to Git.
- Flag retry behavior that could silently duplicate or overwrite completed episode parts.
- Require tests for chunk-boundary behavior and every new provider adapter.
