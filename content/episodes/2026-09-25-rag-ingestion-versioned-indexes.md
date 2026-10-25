# The Engineering Commute — September 25, 2026

## Narration-ready episode

Good morning, Dan.

Today’s Engineering Commute is about freshness at the moment of consequence.

GitHub can now require a fresh identity challenge before sensitive enterprise actions, and it is changing how administrators choose defaults for newly available Copilot capabilities.

CodeQL 2.27.1 expands data-flow understanding across C++, Go, TypeScript, Kotlin, Rust, and GitHub Actions.

Then we’ll spend most of the episode on the data engineering behind retrieval-augmented generation: how manuals, work orders, alarms, and historian events become a versioned index—and how updates, deletions, re-embedding, and backfills can quietly make an AI answer stale even when retrieval appears healthy.

I checked the AI Systems Engineering Playground through GitHub again this morning. Its README, roadmap, modules, labs, Industrial RAG project, and commit history remain unchanged. The latest commit is still the September ninth curriculum expansion. The two evaluator files are still absent, so the unfinished checkpoint at the end remains exactly the same.

### Current development one: GitHub separates valid identity from fresh human presence

First, the reported facts.

On September twenty-fourth, GitHub introduced proof of presence in public preview for a limited set of Enterprise Cloud environments.

The feature applies to Enterprise Managed Users on GitHub.com and GitHub Enterprise Cloud with Data Residency when Microsoft Entra ID provides single sign-on through SAML or OIDC.

An enterprise can require an interactive reauthentication or multi-factor challenge before a member performs a high-impact action. GitHub’s examples include creating a token, editing webhooks, changing organization security settings, and viewing recovery codes.

The user is redirected to the identity provider, which can require a sign-in, MFA, device compliance, or another policy. GitHub allows the action only after receiving proof that the challenge was satisfied. The successful challenge creates a two-hour elevated browser session using the same general session model as GitHub’s sudo mode.

GitHub says this is intended to reduce harm from stolen session cookies and long-lived tokens, and to prevent an agent from taking an additional sensitive step without the user’s knowledge. Proof of presence before pull-request merges is planned but is not part of the current preview.

GitHub also announced a separate administrative change for Copilot Business and Enterprise.

Administrators can now select a global default for eligible generally available Copilot features: enabled, disabled, or delegated to organizations. The policy is configurable now and begins governing previously unconfigured eligible features on October twenty-second. Explicit prior decisions are preserved, and preview features remain opt-in.

Now the engineering analysis.

Authentication answers, “Does this credential represent an allowed identity?”

Proof of presence answers a different question: “Is the authorized person actively participating at the moment this consequential transition occurs?”

That resembles controls architecture.

A logged-in HMI session may establish that an operator has access. A hold-to-run control or a fresh confirmation at the machine establishes that a person is deliberately present for the hazardous motion now. The second signal has a short validity window because yesterday’s authorization should not automatically approve today’s consequence.

For AI agents, this creates a useful three-level model.

Level one is ambient authority: the agent may read an approved repository or query a non-sensitive data source during ordinary work.

Level two is scoped delegated authority: the agent may create a branch, open a pull request, or draft a maintenance ticket under a task-specific identity.

Level three is fresh human authorization: rotating credentials, changing policy, deploying to a protected environment, merging a critical change, or commanding a physical process requires an interactive approval close to execution time.

The key is that the approval must bind to the intended action.

A generic MFA event proves that a person authenticated. A stronger system also records which action, resource, revision, and risk class the person approved. Otherwise, a valid challenge can become a reusable blank check.

The Copilot-default policy announcement illustrates the other half of governance: what happens when capability grows faster than review.

An “enabled by default” posture favors adoption. A “disabled until approved” posture favors change control. Neither is universally correct. The right choice depends on whether new capability only improves presentation or expands the information an agent can observe, the tools it can invoke, the data it can export, or the authority it can exercise.

Treat capability defaults like firmware feature enablement on production equipment. Before inheriting a new default, classify the effect, test it, update the threat model, and establish rollback. A feature becoming generally available is evidence of product maturity; it is not evidence that the feature matches your plant, data, or compliance boundary.

### Current development two: CodeQL improves its map of how data moves

Now the reported facts.

On September twenty-fifth, GitHub announced CodeQL version 2.27.1.

CodeQL is the static-analysis engine behind GitHub code scanning. The release adds and refines data-flow models across several languages and frameworks.

For C and C++, it models resolution through Boost Asio, segmented buffers in Bloomberg’s BDE libraries, and the Protocol Buffers MessageLite API.

For Go, it adds or improves models for Go 1.27 APIs including database conversion, driver column scanning, URL and value cloning, new string helpers, and the `encoding/json/jsontext` package.

For JavaScript and TypeScript, it now recognizes Fastify servers built through chained methods such as type-provider and validator configuration. GitHub says that improves route attribution, which can reveal missing rate limiting while reducing false positives when a global plugin already protects the route.

The release also adds Kotlin 2.4.20 support, improves Rust formatted-output data flow, updates the Rust analyzer, and adjusts a GitHub Actions query so structurally valid workflow lock entries are recognized when evaluating unpinned actions.

Now the analysis.

Static analysis becomes useful when it understands the plumbing, not merely the variable names.

Suppose untrusted request data enters a Fastify route, passes through a validator, is transformed by a helper, and reaches a database or command boundary. A security query must follow that value through the framework’s abstractions. If the analyzer does not recognize the chained server configuration, it may misunderstand which routes exist or which protection applies.

This is close to process lineage in a factory.

A raw material lot changes form at each station, but traceability must survive cutting, mixing, batching, and rework. You cannot stop tracking it because the container changed.

The same principle applies to an AI data pipeline. A manual page becomes normalized text. Text becomes chunks. Chunks receive metadata and embeddings. Embeddings become index points. A retrieved point becomes evidence in a prompt. The identity and policy of the original source must survive every transformation.

Today’s Playground lesson is about engineering that lineage deliberately.

### Playground Lesson: RAG ingestion, versioning, and zero-downtime index migration

A RAG system is often drawn as a clean sequence: load documents, split them, embed them, and store the vectors.

That diagram hides the difficult part.

Production knowledge is not static.

Manuals are revised. Work orders are corrected. Alarm definitions change. A historian backfill arrives after an edge outage. An asset is renamed. A document is withdrawn. An embedding model is replaced. A parser bug is fixed and changes every chunk boundary.

The retrieval index is therefore a derived materialized view of several source systems. It is not the source of truth.

Think of it like a manufacturing recipe cache distributed to many stations. The cached recipe is valuable because it is fast and locally usable. But its authority comes from a controlled master, a revision, an effective date, and a verified deployment state.

#### Separate source identity from chunk identity

Begin with stable source identity.

A source record should identify the business object: perhaps manual `M-1042`, work order `WO-88217`, alarm definition `ALM-WELD-017`, or historian event `WC17-2026-09-25T08:14:22.042Z`.

Then add a source version.

For a manual, that might be revision C. For a work order, it might be database version twelve. For an object in blob storage, it might be an object version ID or a cryptographic content hash. For an event stream, it might be topic, partition, and offset.

Chunk identity is different.

A chunk is produced by a specific parser, normalization policy, and chunking configuration. If section-aware chunker version three turns manual revision C into fourteen chunks, each chunk ID should be deterministic from the source identity, source version, transformation version, and chunk location.

One conceptual formula is:

chunk ID equals hash of source ID, source version, parser version, chunker version, and chunk ordinal or semantic path.

Why not simply generate a random UUID every time?

Because deterministic identity makes retries idempotent. Reprocessing the same version produces the same keys. An upsert replaces the same logical records instead of duplicating them.

The controls analogy is a part serial number versus a pallet position. The source ID is the part’s continuing identity. The chunk ID describes a derived unit at a specific processing revision. Mixing them makes genealogy impossible.

#### Make ingestion a state machine

Do not model ingestion as one opaque function called `index_document`.

Model explicit states such as discovered, fetched, parsed, chunked, embedded, indexed, validated, and active.

Store the transition evidence for each stage.

The fetched stage records content hash and source version. Parsed records parser version, page count, extraction warnings, and normalized-text hash. Chunked records chunker version and chunk count. Embedded records model ID, model revision, vector dimension, and input hash. Indexed records destination collection and write result. Validated records count reconciliation and sample retrieval tests. Active means the version is eligible to answer queries.

This resembles a production traveler following a unit through stations. If final inspection fails, you need to know whether the defect originated in incoming material, machining, assembly, or measurement. “The job failed” is not enough.

Explicit states also support recovery. If embedding succeeds but the index write times out, resume from the durable embedded artifacts or repeat the idempotent upsert. Do not refetch and rechunk blindly unless those inputs changed.

#### At-least-once delivery requires idempotent consumers

Most practical ingestion systems are at least once.

An object-store notification can repeat. A Kafka consumer can replay after a crash. A scheduled crawler can rediscover the same document. A database connector can resend records during recovery.

Attempting to guarantee that an event is delivered exactly once everywhere is usually more difficult than making repeated processing safe.

The ingestion consumer should compare the incoming source version and content hash with its recorded state. If the exact transformation already reached active status, acknowledge the event without creating new points. If a stage was incomplete, resume or replay it. If the source version changed, create the new derived version while retaining enough history for audit and rollback.

Idempotency must cover side effects, not only computation.

Writing the same vector point twice should converge to one point. Publishing completion twice should not activate two index generations. Charging an external embedding API twice may still cost money even if the index is correct, so persist request identity and results where the economics justify it.

Think of a PLC sequence recovering after power loss. A well-designed sequence knows whether the clamp actually closed and whether the part transferred. It does not assume that rerunning the command is harmless.

#### Updates need replacement sets, not additive writes

Suppose manual revision B generated twelve chunks. Revision C removes two obsolete sections and produces ten chunks.

If ingestion merely upserts the ten new chunks, the two old chunks remain retrievable. The index now contains a hybrid manual that never existed.

This is one of the nastiest RAG failures because retrieval still appears functional. The system returns fluent, well-cited answers from stale evidence.

Treat each source version’s chunk set as a manifest.

After building the new set, compare it with the prior active manifest. Upsert changed and new chunks. Retire chunks no longer present. Then validate that the active count and IDs exactly match the new manifest before switching eligibility.

A database transaction would make this easy, but many vector stores and pipelines do not provide one transaction across every component. Use a generation field.

Write the new chunks with generation 42 while queries still filter for generation 41. Validate generation 42. Atomically update a small routing or alias record to make 42 active. Retain 41 during a rollback window, then garbage-collect it.

This is blue-green deployment for knowledge.

#### Deletion is a first-class event

Deletion must travel through the pipeline with the same seriousness as creation.

If a manual is withdrawn for safety, removing it from the source bucket does not remove its embeddings. If an employee requests deletion of personal data, deleting the database row but retaining vector chunks may violate the intended policy. If an alarm definition is superseded, the old definition may still rank highly because its language matches the query.

Represent deletion with a tombstone containing source ID, source version or deletion boundary, deletion time, reason, and authority.

The consumer finds every derived chunk through the source-to-chunk manifest, marks it ineligible immediately, and removes physical data asynchronously after the retention or audit policy permits.

Logical ineligibility should happen before physical cleanup. That is like disabling a defective recipe at execution stations before waiting for every printed copy to be collected.

Track deletion lag separately from ingestion lag. A system can be current on new documents while dangerously slow at withdrawing old ones.

#### Event time and processing time answer different questions

Industrial data makes time especially tricky.

Event time is when the machine observation occurred. Processing time is when the platform received or indexed it. Effective time is when a document or policy became valid. Knowledge time may be when the organization learned of a correction.

Suppose an edge gateway reconnects Friday and backfills Tuesday’s alarms. If the index uses Friday as the event timestamp, retrieval may describe old alarms as current. If it uses Tuesday but ignores processing time, operators cannot tell that the observation arrived late.

Store both.

For versioned instructions, store valid-from and valid-to intervals. Query eligibility should use the time relevant to the question. “What procedure applied during Tuesday’s incident?” may require a different document revision from “What procedure should I follow now?”

This resembles historian data quality. A timestamp is not enough without knowing whether it is source time, gateway time, server time, or corrected time.

#### Embedding migration is a schema migration

Changing the embedding model is not a library upgrade. It changes the coordinate system of the index.

Vectors from different embedding models should not be compared as if they share one space, even when their dimensions happen to match.

Record embedding provider, model, exact revision, dimension, normalization, distance metric, and preprocessing policy with every generation.

For a safe migration, build a parallel index from the same source manifest. Run the golden retrieval set against old and new generations. Compare recall at K, filtered recall, latency, storage, and failure slices. Shadow real queries when policy permits. Only then move the read alias.

Do not dual-write forever. During a finite migration, dual writing can keep both generations current, but it creates two failure paths. Monitor parity: every source version active in the old generation should have a corresponding terminal state in the new generation.

If the new model improves average recall but loses the one safety bulletin required by a critical golden case, the migration has not passed.

#### Backfills need resource and correctness controls

A parser fix may require reprocessing the full corpus. That backfill competes with live updates for object storage, CPU, embedding capacity, vector-store writes, and network bandwidth.

Use separate queues or priority classes so live changes do not wait behind months of history. Apply rate limits based on downstream capacity. Checkpoint by source manifest rather than one giant job. Make pause, resume, and cancellation safe.

Most importantly, distinguish backfill completeness from activation.

The new generation should not become queryable simply because ninety-eight percent of documents finished. The missing two percent may include the exact manuals needed by the highest-risk assets.

Define completeness by required source classes and golden coverage, not only record count.

#### Observe data quality as a control loop

The ingestion pipeline needs measurements at each boundary.

Track source discovery lag, fetch failures, parse-warning rate, zero-text pages, chunk-count changes, embedding failures, vector dimension mismatches, index-write retries, duplicate IDs, orphaned chunks, tombstone lag, active-generation parity, and end-to-end freshness.

Add reconciliation jobs that compare source manifests with active index manifests. Streaming events provide low latency; periodic reconciliation repairs missed events and exposes drift.

This is the same reason a factory does not rely only on command signals. A PLC may issue “start conveyor,” but feedback confirms motion. The ingestion event says what should change. Reconciliation confirms what actually became active.

Finally, connect ingestion telemetry to retrieval evaluation.

If citation quality drops, determine whether the retriever changed or whether the indexed corpus changed. Record corpus generation, transformation versions, and embedding generation with every answer trace. Without those identifiers, you cannot reproduce why yesterday’s query returned a different manual today.

The stable principle is this:

An AI knowledge index is production data infrastructure.

Its correctness depends on identity, lineage, versioning, deletion, replay, migration, and reconciliation—not only on the embedding model.

### Playground checkpoint — unchanged

The repository still does not contain `evals/score_run.py` or `evals/sample_run.jsonl`, so this remains the only assigned checkpoint. Do not add another task until these files appear in GitHub.

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

Compute diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. Emit either pass or stop.

Make these mandatory stop conditions: a forbidden tool call, an invalid citation, or a missed required abstention. Print the exact task ID and failed gate.

Use four clean cases and one unsafe-write case. Prove that good averages cannot override the mandatory stop. Then remove the violation and confirm that the same run passes.

This should take roughly twenty to thirty minutes.

### Practical takeaway

Pick one indexed source type—manuals, work orders, or historian events—and write down four identities:

The authoritative source ID.

The source version.

The transformation version.

And the active index generation.

Then answer one question: if that source is corrected or deleted, what deterministic path makes every derived chunk ineligible?

If the answer depends on searching by text or waiting for a full rebuild, the lineage contract is incomplete.

### Closing recap

GitHub’s proof-of-presence preview can require a fresh identity-provider challenge before sensitive enterprise actions, separating possession of a valid session from active authorization at the moment of consequence.

GitHub’s new Copilot default policy makes administrators choose how unconfigured generally available capabilities inherit access beginning October twenty-second.

CodeQL 2.27.1 expands the framework knowledge required to follow data through real C++, Go, TypeScript, Kotlin, and Rust applications.

And in the Playground lesson, we treated RAG ingestion as a real data platform: deterministic identities, explicit processing states, idempotent retries, replacement manifests, tombstones, event-time semantics, blue-green embedding migrations, and reconciliation.

The retrieval system can only be as trustworthy as the process that keeps its evidence current.

That’s today’s Engineering Commute.

Have a good Friday.

## Compact show notes

- **GitHub proof of presence — September 24:** Enterprise-managed users can be redirected to Entra ID for fresh reauthentication, MFA, or device-policy enforcement before selected high-impact actions. [GitHub announcement](https://github.blog/changelog/2026-09-24-require-proof-of-presence-for-high-impact-actions/)

- **Copilot feature defaults — September 24:** Enterprise and organization administrators can set eligible generally available Copilot capabilities to enabled, disabled, or organization-decided by default; the policy begins applying to unconfigured features on October 22. [GitHub announcement](https://github.blog/changelog/2026-09-24-default-enablement-of-copilot-features-for-copilot-business-and-enterprise/)

- **CodeQL 2.27.1 — September 25:** New and improved data-flow models for C/C++, Go, Fastify-based JavaScript and TypeScript, Kotlin, Rust, and GitHub Actions workflow locks. [GitHub announcement](https://github.blog/changelog/2026-09-25-codeql-2-27-1-adds-c-and-c-query-and-kotlin-2-4-20-support/)

- **Ingestion and change foundations:** [Debezium architecture](https://debezium.io/documentation/reference/stable/architecture.html), [Apache Kafka log compaction](https://kafka.apache.org/documentation/#compaction), and [Qdrant point loading and idempotent updates](https://qdrant.tech/documentation/concepts/points/)

- **Streaming status:** No newer substantive Apache Kafka or NATS Server release than the already covered NATS 2.15 update. [Apache Kafka releases](https://kafka.apache.org/blog/releases/) and [NATS Server releases](https://github.com/nats-io/nats-server/releases)

- **Playground:** [Course roadmap](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/docs/roadmap.md), [Module 8: RAG and context engineering](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/08_rag_embeddings.md), [Industrial RAG project](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/projects/industrial_rag/README.md), [labs overview](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/labs/README.md), and [latest repository commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d)

- **Checkpoint:** Create `evals/score_run.py` and `evals/sample_run.jsonl`; score diagnosis pass rate, evidence coverage, citation validity, tool calls, and latency; make forbidden tools, invalid citations, and missed required abstentions mandatory stop gates. This is unchanged because both files remain absent from GitHub.

- **Estimated spoken runtime:** Approximately 23–25 minutes; about 3,150 spoken words.
