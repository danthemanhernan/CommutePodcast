# ADR 0001: Build a complete local vertical slice before cloud infrastructure

- Status: Accepted
- Date: 2026-08-22
- Stage: v0.1–v0.3

## Context

Voice quality, pacing, chunk boundaries, file formats, and the useful episode workflow needed fast
feedback. Starting with AWS, queues, databases, and MCP would multiply moving parts before proving
that the core output was worth operating.

## Decision

Complete and harden a local script-to-MP3 vertical slice before building remote infrastructure.
Retain clean boundaries so the core can later run inside a worker without a rewrite.

## Consequences

The project delivers useful audio early and failures are easy to inspect. Cloud availability is
delayed, and temporary local assumptions must be identified before containerization.

## Revisit when

Version 0.3 exit criteria pass for repeated 5–15 minute episodes.
