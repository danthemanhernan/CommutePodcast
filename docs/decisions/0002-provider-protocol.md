# ADR 0002: Isolate TTS vendors behind a structural protocol

- Status: Accepted
- Date: 2026-08-22
- Stage: v0.2

## Context

The first implementation uses OpenAI TTS, but voice quality, pricing, control, and availability may
justify comparing other providers. Vendor-specific SDK calls must not control the episode workflow.

## Decision

Make orchestration depend on the small `SpeechProvider` protocol. Put SDK translation and
authentication inside provider adapters.

## Consequences

Providers can be substituted and tested with fakes. Configuration differences still require a
careful common model, and lowest-common-denominator abstractions must be avoided.

## Revisit when

A second provider reveals capabilities that do not fit the current synthesis contract.
