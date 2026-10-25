# The Engineering Commute — September 5, 2026

## Narration-ready episode

Good morning, Dan.

Today’s Engineering Commute is about designing the fallback before the preferred path fails.

Yahoo says flexible virtual-machine selection cut a major class of Apache Spark cluster-provisioning failures by eighty-five percent.

Google’s Finance Engineering team has used a headless coding-agent pipeline to generate and test dual-write changes for a migration to Spanner.

And a new TPU benchmark shows why classification and long-form generation can reach completely different scaling limits—even on the same model server and hardware.

Then, in the Playground Lesson, we’ll continue the Factory AI Engineer capstone. Yesterday was about defining one traceable vertical slice. Today is about commissioning it: specifying acceptance criteria, injecting faults, and proving that the assistant fails safely.

There is no substantive new Apache Kafka or NATS JetStream release to cover this morning, so we’ll keep the episode focused on changes with new engineering lessons.

### Segment one: Spark capacity becomes a ranked fallback policy

Here are the reported facts.

On September fourth, Google Cloud and Yahoo published a technical account of Yahoo’s use of flexible virtual machines in Google’s Managed Service for Apache Spark, formerly known as Dataproc.

A conventional cluster configuration requests one machine type in one zone. If that exact shape is unavailable, provisioning can stall even when comparable compute exists elsewhere in the region.

Flexible virtual machines replace the single choice with a ranked list of acceptable shapes. Auto-Zone placement then lets the service search across the selected region. The preferred machine remains rank zero, while one or more alternatives become documented fallbacks.

Yahoo reports that this approach reduced cluster-provisioning failures caused by regional capacity stockouts by eighty-five percent.

The flexibility is not unconstrained. When autoscaling is enabled, the candidate machine types should have similar core counts and memory sizes. Their CPU-to-memory ratios must also remain compatible because the smallest ratio can determine effective container sizing.

Managed Spark derives YARN and Spark properties from each machine’s resources. Mixing shapes may therefore require explicit property overrides. Google also recommends shuffle-safe application patterns when using Spot or highly elastic workers.

The selection policy can be expressed through command-line configuration or the Dataproc API, which means an Airflow pipeline can request a preferred shape and valid fallbacks without embedding custom stockout-retry logic.

Now, the engineering analysis.

This is graceful degradation applied to infrastructure procurement.

The desired state is not “run on an E-two standard eight.” The desired state is “obtain a worker with approximately this amount of compute and memory, within these price and performance bounds, before the pipeline misses its deadline.”

That distinction matters. A specific machine family is an implementation preference. The workload’s resource contract is the real requirement.

The controls analogy is a pumping system with a lead pump and approved alternates. If the lead pump is unavailable, the sequence can start another unit—but only if its capacity curve, motor limits, valve alignment, and protection logic are compatible with the requested operating point.

A fallback machine is not equivalent merely because it has the same virtual CPU count. Processor generation, memory bandwidth, local disk, network limits, startup time, Spot interruption risk, and price can all change job behavior.

Before making a shape eligible, test representative stages: scan-heavy reads, wide shuffles, skewed joins, serialization, and final writes. Compare completion time, cost, spill, shuffle retries, executor loss, and deadline success by selected shape.

Also record which fallback was used. If the system quietly runs on rank-two capacity for a month, the pipeline may remain green while cost or runtime drifts. A fallback should preserve service, not hide a chronic capacity problem.

The design lesson is to express acceptable alternatives before scarcity occurs. An automated system can then choose within a bounded envelope instead of improvising during an incident.

### Segment two: Coding agents are being applied to dual-write database migrations

The second story comes from Google’s internal Finance Engineering team.

Here are the reported facts.

On September fourth, Google described an automated refactoring pipeline used while preparing a legacy datastore migration to Spanner.

The migration design has three broad phases.

First, historical records are backfilled while referential integrity is maintained.

Second, data-access objects are modified to write to both the legacy system and Spanner during the migration window.

Third, RPC traffic and stored results are checked to verify that both systems receive byte-for-byte-equivalent data.

The team had more than thirty data-access objects to modify. Each required schema conversion, dual-write branching, error handling, and unit tests with controlled time sources and test doubles.

Before automating the work, the engineers standardized a Mutation Converter interface. That interface isolates the mapping between a domain object and Spanner mutations instead of scattering table names and column assignments through business logic.

The team then used Antigravity CLI in headless mode from an orchestration script. Version-controlled prompts describe structural rules and edge cases such as null conversion, timestamps, ambiguous mutations, and fake-time injection.

For each target, the automation reads the existing single-write implementation and schema, generates the converter, refactors the data-access object, and creates tests. It runs Google’s build and test system, then feeds lint or assertion failures back into the agent for another attempt.

Google says engineers could queue ten data-access objects overnight and receive ten tested change lists for human review the following morning. The migration was still being prepared for production when the article was published, so this is an internal engineering report rather than a completed production outcome.

Now, the analysis.

This is a good use case for a coding agent because the work is repetitive but correctness is not negotiable.

The agent is not being asked to invent a migration architecture thirty times. Engineers first define one constrained pattern. The agent applies that pattern across many implementations, while deterministic tests reject deviations.

It resembles generating PLC routines from a validated equipment module. Standardization makes automation possible. The generated routine still goes through compilation, simulation, review, and commissioning.

But dual write has a fundamental problem that code generation cannot erase: one logical operation now crosses two data systems.

The legacy write can succeed while the Spanner write fails. A retry can duplicate one side. Different timestamp semantics can produce records that look unequal even when the business event is the same. Referential relationships can arrive in a different order. A rollback in the application does not necessarily reverse a remote commit.

The migration therefore needs an explicit consistency contract.

Which datastore is authoritative during each phase?

Does the secondary write happen synchronously, asynchronously, or through an outbox?

What identity makes retries idempotent?

Where are mismatches stored, and who resolves them?

How long must parity remain within tolerance before reads shift?

And what conditions reverse the cutover?

Byte-for-byte comparison is powerful, but only after canonicalization is defined. Commit timestamps, generated identifiers, field ordering, encodings, and defaults may differ without representing different business state.

For financial or industrial records, I would test more than ordinary inserts. Include partial failures, timeouts after an ambiguous commit, concurrent updates, deletes, nulls, maximum values, stale versions, and replayed requests.

The most important artifact is not the agent’s successful transcript. It is the invariant suite that any human- or agent-generated migration must satisfy.

### Segment three: Inference capacity depends on the shape of the request

The third development is a Google Cloud benchmark published September fourth.

Here are the reported facts.

The test served Gemma Three models with twelve billion and twenty-seven billion parameters through vLLM on a Google Kubernetes Engine Autopilot cluster with a two-by-two TPU version-six-e topology.

The team compared two intentionally different workloads at sixteen, thirty-two, sixty-four, and one hundred twenty-eight concurrent users.

The classification workload had roughly four thousand input tokens and only ten output tokens. It represents a prefill-heavy request: read a large body of rules and evidence, then return a very short label.

The generation workload had about five hundred input tokens and one thousand output tokens. It spends much more time in sequential decode.

For generation, the two models scaled similarly through sixty-four users. At one hundred twenty-eight users, the twelve-billion-parameter model reached an eight-point-one-nine-times normalized throughput multiplier, while the twenty-seven-billion model plateaued at four-point-one-two times.

For classification, their scaling was much closer. Both reached roughly six-times normalized throughput at one hundred twenty-eight users.

Google warns that the highest-concurrency results represent the edge of cluster stability, not a recommended operating point. Misconfigured sequence and context limits can cause request drops, client timeouts, or worker out-of-memory failures. Because failed requests end early, they can shorten the measured session and make average throughput look artificially better.

Now, the analysis.

This is the most important sentence in the benchmark: failure can improve the headline metric.

If throughput is calculated as submitted work divided by test duration, rapidly rejected requests may make the system appear faster. The factory equivalent is reporting higher parts per hour after the inspection station begins throwing unfinished parts off the conveyor.

Count admitted, completed, timed-out, rejected, and failed requests separately. Report successful output tokens per second alongside end-to-end latency, time to first token, inter-token latency, queue time, and memory pressure.

The workload shape explains the model difference.

Classification invests heavily in prefill, then performs almost no decode. Generation repeatedly streams model weights and accesses growing key-value-cache state for hundreds of sequential steps. A larger model can deliver better answers yet reach a decode-capacity wall much earlier.

This means “requests per second” is not a portable capacity unit for an AI endpoint. A ten-token classification and a thousand-token report are different products moving through the same line.

Segment capacity by input tokens, expected output tokens, model, latency class, and tool-call behavior. Route or queue them accordingly. Autoscaling based only on CPU or memory can miss the onset of accelerator saturation, so use queue delay and end-to-end latency as control signals—but protect the controller against dropped-request metric inflation.

A stable production target sits below the cliff, with headroom for bursts, long outputs, and imperfect forecasts.

### Playground Lesson: commission the Factory AI Engineer

I inspected the AI Systems Engineering Playground through GitHub this morning.

The README, modules, labs, and recent commits remain unchanged. The repository still contains only its initial August twenty-fourth commit, and there is no explicit progress marker or implemented capstone lab.

Module Thirteen defines the Factory AI Engineer capstone. Its stretch work specifically calls for observability covering latency, estimated cost, and success or failure classification.

Yesterday’s lesson defined one vertical slice: an incident enters, a router selects capacity, the agent gathers alarms and historian data, retrieval supplies approved evidence, tools enforce policy, and a verifier produces an explicit terminal state.

Today, treat that slice like equipment entering commissioning.

A demo proves the happy path can work once. Commissioning establishes the operating envelope and verifies behavior outside it.

For an AI assistant, the acceptance specification needs three layers.

Functional acceptance asks whether the system reaches the correct supported conclusion and cites the right evidence.

Safety acceptance asks whether denied, stale, ambiguous, or low-quality inputs prevent unsafe action.

Operational acceptance asks whether the workflow meets latency, cost, retry, recovery, and observability requirements under expected load.

This maps cleanly to controls engineering.

Factory acceptance testing verifies the designed sequence before installation. Site acceptance testing proves it against the real interfaces and operating conditions. Statistical process control then watches whether performance drifts after release.

The model’s fluent answer is only one output. The complete test result includes the terminal state, tool-call history, evidence set, policy decisions, retries, latency by stage, token use, estimated cost, and whether a human escalation was required.

Define invariants that must hold for every run.

A denied tool is never invoked.

A superseded manual is never cited as approved evidence.

A repeated side effect uses the same idempotency key.

A recovered run does not repeat completed work.

A diagnosis contains evidence references for every factual claim.

And budget exhaustion ends in a named state rather than an infinite agent loop.

Your twenty-to-thirty-minute checkpoint is to add a small acceptance harness around yesterday’s mocked capstone trace.

Create six table-driven scenarios:

One normal diagnosis.

One historian timeout that succeeds on a bounded retry.

One missing historian permission.

One superseded manual revision.

One duplicate maintenance-ticket request.

And one run that exhausts its tool-call budget.

For each scenario, declare the expected terminal state, maximum tool calls, permitted side effects, and required evidence IDs. Run them through a deterministic evaluator and print a one-line pass or fail result.

Then produce five aggregate metrics: scenario pass rate, unsafe-action count, duplicate-side-effect count, p95 simulated latency, and average estimated cost.

The checkpoint question is:

If every model response were replaced with an adversarial but schema-valid response, which guarantees would still hold?

Those surviving guarantees belong to your engineered system. Everything else is still a hope placed in the model.

### Practical takeaway

Choose one fallback in a pipeline, migration, or agent workflow. Write its eligibility criteria, entry condition, exit condition, observability signal, and rollback path.

A fallback becomes reliable when it is a tested operating mode rather than an emergency improvisation.

### Closing recap

Yahoo’s flexible Spark configuration turns regional VM scarcity into a ranked capacity policy, while requiring compatible resource shapes and runtime settings.

Google’s Finance Engineering team uses a headless coding-agent loop to apply a standardized Spanner dual-write pattern, but the migration’s safety still comes from invariants, parity checks, and human review.

Google’s TPU benchmark shows that prefill-heavy classification and decode-heavy generation saturate differently—and that failed requests can make naive throughput look better.

And in the Playground, the Factory AI Engineer moves from demo to engineered system when fault injection proves its permissions, evidence rules, recovery, budgets, side-effect safety, latency, and cost.

That’s today’s Engineering Commute.

Have a good Saturday.

## Compact show notes

- **Yahoo’s flexible Spark capacity — September 4:** Ranked VM alternatives, regional Auto-Zone placement, resource-shape constraints, and an 85% reported reduction in stockout-related cluster-provisioning failures. [Google Cloud and Yahoo engineering report](https://cloud.google.com/blog/products/data-analytics/how-yahoo-optimizes-apache-spark-with-flexible-vms)

- **Agent-assisted Spanner migration — September 4:** Standardized mutation converters, headless multi-file refactoring, versioned prompts, generated tests, and byte-for-byte parity checks across legacy and Spanner writes. [Google Cloud engineering report](https://cloud.google.com/blog/topics/developers-practitioners/using-antigravity-cli-to-streamline-dual-write-database-migration)

- **TPU inference workload benchmark — September 4:** Gemma 3 12B and 27B on GKE, TPU v6e, and vLLM, contrasting prefill-heavy classification with decode-heavy generation and warning that failures can inflate throughput. [Google Cloud benchmark](https://cloud.google.com/blog/topics/developers-practitioners/not-all-llm-workloads-are-equal-benchmarking-tpu-performance-on-classification-vs-generation)

- **Streaming status:** No newer substantive Apache Kafka or NATS JetStream release than the updates already covered. [Apache Kafka releases](https://kafka.apache.org/blog/releases/) and [NATS Server releases](https://github.com/nats-io/nats-server/releases)

- **Playground:** [Course roadmap](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/README.md), [Module 13: Factory AI Engineer capstone](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/13_capstone.md), [labs overview](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/labs/README.md), and [current repository commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/a3dd8cd8854f4bd310a17f1100040da5f218aafc).

- **Checkpoint:** Build six table-driven capstone acceptance scenarios covering success, bounded retry, authorization denial, stale evidence, idempotency, and budget exhaustion; report pass rate, unsafe actions, duplicate side effects, p95 latency, and average cost.

- **Estimated spoken runtime:** Approximately 15 minutes; about 2,250 spoken words.
