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

## Editorial standard

Each episode is a learning podcast rather than a news briefing. Target 18–22 minutes of spoken
audio, or approximately 2,700–3,300 words at the planning rate of 150 words per minute. A shorter
script is acceptable only when the topic genuinely cannot support a useful deep dive.

A strong episode should usually include:

1. A motivating problem or story that makes the topic concrete.
2. A plain-language mental model before introducing product or implementation details.
3. A descriptive deep dive into how the system works, including boundaries, state, and failure
   modes.
4. At least one worked example, operational scenario, or controls/data-engineering analogy.
5. Tradeoffs, alternatives, and the conditions under which the design is or is not appropriate.
6. A short recap that connects the lesson back to decisions the listener can make.

Use narrative and repetition strategically for understanding, but do not restate the same point
without adding a new angle, example, or implication. Before generation, run `plan` and confirm the
word count and estimated duration are in range.
