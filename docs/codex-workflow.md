# Continue the project in Codex

The repository is the durable project context. Codex reads the root `AGENTS.md` before work, while
the roadmap, walkthroughs, tests, and decision records preserve the context that previously lived
only in chat.

## Recommended progression

### Now: Codex Local

Use Local while Stage 1 depends on the Mac's `ffmpeg`, local files, and `OPENAI_API_KEY`.

1. Put the repository in a permanent development folder.
2. Open the ChatGPT desktop app.
3. Choose **Codex**.
4. Open the repository folder.
5. Start a **Local** chat.
6. Ask Codex to summarize `AGENTS.md`, `ROADMAP.md`, and the current Git status before editing.

Suggested first prompt:

> Orient me to this repository using AGENTS.md and ROADMAP.md. Verify the Stage 1 checks, walk me
> through the current code path, and then help me complete the first unchecked Version 0.3 task as
> a small vertical slice. Explain the lesson and update the roadmap, learning log, decision records,
> and tests with the change.

### During implementation: Codex Worktree

Use a Worktree chat when developing an isolated feature or experiment that should not modify the
main checkout until reviewed. Good examples include the second provider adapter, structured job
model, or `ffprobe` validator.

### After GitHub and cloud environment setup: Codex Cloud

Use Cloud when the repository has a remote and the task can run with configured dependencies and
approved network access. Cloud work is appropriate for tests, refactors, Terraform, CI/CD, and MCP
development. Real TTS integration tests should remain explicitly opt-in because they use secrets
and incur provider cost.

## Suggested Codex task rhythm

For each task, ask Codex to:

1. State the roadmap item and acceptance criteria.
2. Explain the concept before implementation.
3. Make the smallest complete change.
4. Run focused tests, then `make check`.
5. Show the diff and explain important lines.
6. Update the checklist and learning log.
7. Create an ADR only when the decision is durable and architectural.

## Git workflow

Use one branch or worktree per roadmap task:

```text
feature/v0.3-job-state
feature/v0.3-structured-logging
feature/v0.3-audio-validation
```

Commit messages should describe the capability:

```text
Add explicit episode job state
Validate generated chunks before resume
Record actual audio duration in manifest
```

Do not commit `.env`, API keys, generated audio, episode working directories, or local Codex logs.
