# ADR 0004: Use ffmpeg for assembly and loudness normalization

- Status: Accepted
- Date: 2026-08-22
- Stage: v0.2

## Context

The TTS API returns individual audio parts, but the user needs one consistently playable episode.
Audio concatenation and loudness processing are mature media concerns outside the provider API.

## Decision

Use the `ffmpeg` executable for concatenation, MP3 encoding, and EBU R128 loudness normalization.
Invoke it with an argument list and without a shell.

## Consequences

The project uses a proven media tool and avoids implementing codecs. `ffmpeg` becomes a required
local and container dependency, and its output needs integration-level validation.

## Revisit when

Measured cold-start or container-size costs make a different media-processing approach preferable.
