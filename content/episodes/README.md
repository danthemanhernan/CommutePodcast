# Episode transcript library

This directory is the source of truth for episode scripts. ChatGPT, Codex, or another research
workflow may draft a transcript, but the reviewed Markdown file is the durable input to generation.

## Naming

Use a UTC date followed by a URL-safe slug:

```text
YYYY-MM-DD-topic-slug.md
```

## Front matter

Every transcript should begin with:

```yaml
---
title: Streaming Data Is the Nervous System, Not the Brain
date: 2026-08-24
status: draft
topics:
  - streaming systems
  - data architecture
sources:
  - https://example.com/source
---
```

Use `draft`, `review`, `ready`, or `published` for `status`. Keep source URLs with the transcript so
future research and editorial review remain reproducible.

The Version 0.4 validator will check required fields, dates, statuses, and non-empty body text. The
generator will record the transcript path and content hash in the episode manifest.
