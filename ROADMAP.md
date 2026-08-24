# Commute Podcast learning roadmap

This roadmap turns the project into a staged engineering capstone. Each version delivers a usable
vertical slice, teaches a defined set of skills, records important decisions, and has objective
exit criteria. Checkboxes describe repository state, not aspirations.

## How to use this roadmap

For every version:

1. Read the learning objectives before changing code.
2. Complete the smallest runnable vertical slice.
3. Run the verification checklist and preserve evidence.
4. Explain the design in your own words in `docs/learning-log.md`.
5. Record decisions that constrain later stages under `docs/decisions/`.
6. Mark the version complete only when its exit criteria pass.

## Version map

| Version | Stage | Deliverable | Primary learning | Status |
| --- | --- | --- | --- | --- |
| `v0.1` | 1A | Script planning and configuration | Python packaging, CLI design, configuration | Complete |
| `v0.2` | 1B | Local TTS-to-MP3 pipeline | APIs, dependency inversion, file workflows | Complete |
| `v0.3` | 1C | Production-ready local generator | resilience, observability, audio QA | Complete |
| `v0.4` | 2A | Second provider and comparison harness | adapter pattern, evaluation design | Next |
| `v0.5` | 2B | Containerized asynchronous worker | Docker, jobs, idempotency | Planned |
| `v0.6` | 3A | AWS queue-to-object-storage slice | SQS, ECS, S3, IAM, Terraform | Planned |
| `v0.7` | 3B | Cloud status and metadata service | DynamoDB, APIs, observability | Planned |
| `v0.8` | 4 | Remote MCP server and private plugin | MCP tools, schemas, auth, async UX | Planned |
| `v0.9` | 5 | Scheduled research-to-audio workflow | orchestration, evaluation, scheduling | Planned |
| `v1.0` | 6 | Private podcast feed | RSS, distribution, operations, portfolio polish | Planned |

---

## Stage 1 — local generation

### Version 0.1: plan a podcast locally

**User outcome:** inspect a script and understand how it will be generated without spending money.

**Learning objectives**

- Explain how `pyproject.toml` creates an installable Python package and CLI entry point.
- Explain the difference between source code, configuration, generated artifacts, and secrets.
- Use immutable dataclasses to turn raw TOML into typed application configuration.
- Design a CLI command that delegates work instead of containing business logic.
- Write deterministic tests around text-processing boundaries.

**Feature checklist**

- [x] Python 3.12 package managed with `uv`
- [x] `commute-podcast` console entry point
- [x] TOML configuration for show, voice, chunking, output, and loudness
- [x] `plan` command with word, character, duration, chunk, model, and voice summary
- [x] Paragraph-, sentence-, and word-aware chunking
- [x] Unit tests for valid and invalid chunk boundaries
- [x] Example technical podcast script

**Practice checklist**

- [x] Change the target chunk size and predict the result before running `make plan`.
- [x] Add a paragraph that exceeds the maximum and inspect how it is split.
- [x] Explain why a target and a hard maximum are separate settings.
- [x] Trace the `plan` command from shell entry point to JSON output without running it.

**Exit criteria**

- [x] `make plan` succeeds without an API key.
- [x] No returned chunk exceeds `max_chunk_characters`.
- [x] Tests prove paragraph order is preserved.

### Version 0.2: generate a local MP3

**User outcome:** convert a Markdown script into a normalized, playable MP3.

**Learning objectives**

- Explain dependency inversion using `SpeechProvider` and `OpenAITTSProvider`.
- Safely authenticate an SDK with an environment variable.
- Break an expensive workflow into resumable intermediate artifacts.
- Use a subprocess safely to assemble and normalize audio with `ffmpeg`.
- Distinguish a dry run, unit test, integration test, and real production operation.

**Feature checklist**

- [x] Provider protocol independent of OpenAI
- [x] OpenAI `gpt-4o-mini-tts` streaming adapter
- [x] Configurable model, voice, format, and delivery instructions
- [x] Per-chunk text and audio artifacts
- [x] Resume behavior that skips existing audio parts
- [x] MP3 concatenation at 160 kbps
- [x] Optional EBU R128 loudness normalization targeting -16 LUFS
- [x] Episode manifest with reproducibility metadata
- [x] Dry-run path that avoids an API call
- [x] Local ChatGPT Work skill

**Practice checklist**

- [x] Generate and listen to the pilot episode.
- [x] Inspect the manifest and map every field to its source in code.
- [x] Interrupt a multi-chunk generation and verify completed parts are reused.
- [x] Compare normalized and non-normalized output with `ffprobe`.
- [ ] Explain why the provider object is created in the CLI but used by the orchestrator.

**Exit criteria**

- [x] The user successfully generated and played an episode.
- [x] `make check` passes locally.
- [ ] A two-chunk real generation resumes correctly after interruption.
- [ ] `ffprobe` confirms the finished MP3 is valid and the loudness target is reasonable.

### Version 0.3: harden the local vertical slice

**User outcome:** trust the local pipeline for repeated 5–15 minute episodes.

**Learning objectives**

- Design explicit job state rather than inferring all state from file existence.
- Implement bounded retries, backoff, and failure classification.
- Add structured logs and correlation IDs suitable for later cloud aggregation.
- Measure duration, latency, characters, cost estimates, and provider failures.
- Build integration tests without making the normal test suite depend on a paid API.

**Implementation checklist**

- [x] Define an `EpisodeJob` model and explicit statuses.
- [x] Separate planning, synthesis, assembly, and publication steps.
- [x] Add structured JSON logging with episode and chunk identifiers.
- [x] Add bounded retry/backoff for transient provider failures.
- [x] Write atomically to temporary audio files before marking chunks complete.
- [x] Add a `validate` command using `ffprobe`.
- [x] Add estimated and actual cost fields to the manifest.
- [x] Add configurable pronunciation replacements.
- [x] Add an opt-in real-API integration test.
- [x] Document failure injection and recovery exercises.

**Exit criteria**

- [ ] A forced mid-generation failure resumes without duplicate API calls for completed chunks.
- [ ] Invalid or partial audio is not mistaken for a completed chunk.
- [ ] Logs trace one episode across every processing step.
- [ ] A 15-minute episode passes automated validation.

**Completed slice evidence**

- `EpisodeJob` now records `planned`, `synthesizing`, `assembling`, `completed`, and `failed`
  states in the episode manifest.
- Unit tests cover the valid forward path and rejection of an invalid transition.
- The recovery exercise was completed and two real episodes were generated and validated.

---

## Stage 2 — provider evaluation and containerized jobs

### Version 0.4: compare TTS providers

**User outcome:** maintain a durable transcript library and select a TTS provider from evidence
rather than intuition.

**Learning objectives**

- Apply the adapter pattern to APIs with different request and response shapes.
- Create repeatable human listening evaluations.
- Separate objective metrics from subjective voice-quality judgments.
- Compare cost, latency, pronunciation, expressiveness, and operational complexity.
- Keep transcripts, source citations, and editorial status in the repository as the source of truth.

**Implementation checklist**

- [ ] Add a dated `content/episodes/` Markdown transcript format with front matter.
- [ ] Add transcript validation and a CLI path that generates from the content library.
- [ ] Preserve source URLs, editorial status, and transcript hashes in episode manifests.
- [ ] Add ElevenLabs or another provider adapter without changing orchestration.
- [ ] Create a fixed evaluation script containing technical terms and transitions.
- [ ] Capture latency, cost, failures, and output metadata per provider.
- [ ] Create a blind listening scorecard.
- [ ] Record the selected default in an ADR.

**Exit criteria**

- [ ] One command generates comparable samples from two providers from the same transcript.
- [ ] A transcript can be reviewed, corrected, and regenerated without copying text through chat.
- [ ] Provider selection is documented with evidence and tradeoffs.

### Version 0.5: run generation as a containerized job

**User outcome:** submit work to a repeatable worker process independent of the laptop environment.

**Learning objectives**

- Build small, reproducible container images.
- Model work as immutable job input plus durable output.
- Understand idempotency, retries, health checks, and graceful shutdown.
- Keep secrets and generated data outside the container image.

**Implementation checklist**

- [ ] Add a multi-stage Dockerfile and non-root runtime user.
- [ ] Define a versioned job-request schema.
- [ ] Create one local queue-to-worker-to-output vertical slice.
- [ ] Mount scripts/output and inject credentials at runtime.
- [ ] Handle termination without corrupting job state.
- [ ] Add container build and smoke tests to CI.

**Exit criteria**

- [ ] A fresh machine can build the image and complete a dry-run job.
- [ ] Replaying the same job does not create conflicting episode state.

---

## Stage 3 — AWS production pipeline

### Version 0.6: SQS to ECS to S3

**User outcome:** submit a podcast job and receive a durable cloud-hosted MP3 without the Mac on.

**Learning objectives**

- Explain queue visibility timeouts, redrive policies, and dead-letter queues.
- Use IAM least privilege between producer, worker, and storage.
- Deploy an ECS Fargate task and understand its networking and lifecycle.
- Provision reproducible infrastructure with Terraform.
- Design S3 keys and metadata for idempotent job output.

**Implementation checklist**

- [ ] Provision SQS, DLQ, S3, ECR, ECS, logs, networking, and IAM with Terraform.
- [ ] Push the worker image through GitHub Actions.
- [ ] Consume one job, generate one episode, and upload one MP3 plus manifest.
- [ ] Configure timeouts and retries from measured local generation behavior.
- [ ] Add failure alarms and a cost budget.

**Exit criteria**

- [ ] The complete cloud slice works while the Mac is off.
- [ ] A poisoned message reaches the DLQ after the intended retry count.
- [ ] The worker can access only its required queue, objects, secret, and logs.

### Version 0.7: status, metadata, and observability

**User outcome:** query job status and retrieve a completed episode safely.

**Learning objectives**

- Model asynchronous state transitions in DynamoDB.
- Build APIs around eventual completion rather than long blocking requests.
- Use correlation IDs, metrics, dashboards, traces, and alarms.
- Generate time-limited download access instead of public buckets.

**Implementation checklist**

- [ ] Persist job state and conditional transitions in DynamoDB.
- [ ] Expose submit, status, list, and download-link operations.
- [ ] Add presigned S3 URLs with short expiration.
- [ ] Add CloudWatch metrics, dashboards, and alarms.
- [ ] Measure end-to-end latency and cost per episode.

**Exit criteria**

- [ ] Clients can distinguish queued, running, completed, and failed jobs.
- [ ] Episode objects remain private while approved users can play them.

---

## Stage 4 — ChatGPT MCP and plugin

### Version 0.8: remote MCP server

**User outcome:** ask ChatGPT Work to generate an episode and receive its status and playable link.

**Learning objectives**

- Design focused MCP tools with stable input/output schemas.
- Separate model-readable results from user-facing resources.
- Handle authentication, authorization, asynchronous jobs, and safe error messages.
- Evaluate direct and indirect tool selection from realistic prompts.

**Implementation checklist**

- [ ] Implement `generate_podcast`.
- [ ] Implement `get_podcast_status`.
- [ ] Implement `get_podcast_episode`.
- [ ] Implement `list_podcast_voices`.
- [ ] Deploy a secured HTTPS `/mcp` endpoint.
- [ ] Connect it as a private ChatGPT plugin.
- [ ] Add tool-selection and schema-contract evaluations.

**Exit criteria**

- [ ] ChatGPT invokes the correct tool from natural requests.
- [ ] Long jobs return quickly with a job ID and can be checked later.
- [ ] Unauthorized users cannot access episode metadata or audio.

---

## Stage 5 — autonomous research and publishing

### Version 0.9: scheduled research-to-audio workflow

**User outcome:** receive a useful personalized technical episode on a schedule.

**Learning objectives**

- Orchestrate research, synthesis, editorial QA, TTS, and publication as separate steps.
- Evaluate freshness, factual accuracy, topic diversity, and listener relevance.
- Design human approval boundaries and safe retry behavior.
- Prevent repeated stories and preserve source provenance.

**Implementation checklist**

- [ ] Define topic-selection preferences and exclusions.
- [ ] Collect current primary sources and retain citations.
- [ ] Generate a structured script with an editorial rubric.
- [ ] Add factual and pronunciation QA gates.
- [ ] Trigger the pipeline with EventBridge.
- [ ] Notify only when an episode is successfully published.

**Exit criteria**

- [ ] Five scheduled episodes complete without manual machine uptime.
- [ ] Every factual segment retains traceable sources.
- [ ] Repetition and relevance scores meet the documented rubric.

### Version 1.0: private podcast product

**User outcome:** episodes automatically appear in a private feed suitable for commuting.

**Learning objectives**

- Implement valid RSS podcast metadata and secure distribution.
- Operate deployment, rollback, retention, cost, security, and incident workflows.
- Present architecture, tradeoffs, measurements, and demos as a professional portfolio case study.

**Implementation checklist**

- [ ] Generate a standards-compliant private RSS feed.
- [ ] Add episode retention and cleanup policies.
- [ ] Add authentication or unguessable subscriber access.
- [ ] Create operational runbooks and recovery tests.
- [ ] Add architecture diagrams, cost model, demo, and portfolio narrative.
- [ ] Tag `v1.0.0` after all acceptance criteria pass.

**Exit criteria**

- [ ] A podcast client automatically receives new episodes.
- [ ] Restore, rollback, and key-rotation exercises are documented and tested.
- [ ] The repository clearly demonstrates Python, API, data, cloud, IaC, CI/CD, MCP, security, and
  observability skills.

---

## Ongoing engineering checklist

Apply this to every pull request:

- [ ] The change maps to one roadmap objective.
- [ ] The smallest useful vertical slice works.
- [ ] Automated tests cover important behavior and failure paths.
- [ ] No secret or generated audio is committed.
- [ ] Documentation matches current behavior.
- [ ] A new durable architectural choice has an ADR.
- [ ] `make check` passes.
- [ ] The learning log contains evidence and a short reflection.
