# The Engineering Commute — September 10, 2026

## Narration-ready episode

Good morning, Dan.

Today’s Engineering Commute is about removing artificial limits without removing engineering discipline.

The recurring question is whether a new capability expands safe operating range or merely expands possible failure.

Google has changed how Spanner applies its eighty-thousand-mutation limit, allowing transactions to contain more DML statements while retaining the limit on each statement.

NVIDIA has published detailed guidance for splitting multimodal inference into separate encode, prefill, and decode stages, including cases where disaggregation helps and where it makes performance worse.

And GitHub has introduced centrally managed permissions for agent operations, plus a pull-request rule that can block merges when newly introduced secrets remain unresolved.

Then, in the Playground Lesson, we’ll continue the Factory AI Engineer capstone. Yesterday defined the five golden tasks. Today we’ll turn those scenarios into a multidimensional evaluation harness and a release decision.

### Segment one: Spanner raises the transaction ceiling, not the laws of contention

Here are the reported facts.

On September ninth, Google changed how Cloud Spanner applies its mutation-mod limit to DML transactions.

Spanner counts mutation mods based on the cells, primary keys, and dependent indexes changed by a write. Previously, DML statements in one transaction contributed toward a cumulative limit of eighty thousand mods.

The new behavior applies that limit separately to each DML statement. A transaction may now contain any number of insert, update, or delete statements, provided that no individual statement generates eighty thousand or more mutation mods and the transaction remains within Spanner’s other limits.

Google says existing client libraries and application code do not need to change. The separate Mutation API behaves differently: writes supplied together at commit still share the eighty-thousand-mod limit for that commit.

Google also explicitly warns that larger and longer transactions hold locks longer, which can increase contention and transaction aborts. Commit statistics expose a mutation count covering the transaction. An oversized individual bulk statement should still use a different design, such as partitioned DML or pagination by key.

Now, the engineering analysis.

This update removes a quota-driven reason to split one logical business operation. It does not make an arbitrarily large transaction operationally free.

Imagine a production sequence that updates an order, inventory, payment state, and an audit record. If those changes represent one invariant, preserving atomicity may be more important than keeping each database transaction artificially small. Either all stations commit the new state, or the sequence returns to its previous state.

But expanding the permitted batch is like increasing the maximum dwell time on a machine that holds a shared fixture. The controller may allow it, while every downstream station experiences the blockage.

Longer lock duration increases the chance that concurrent transactions collide. Spanner can abort one transaction to preserve serializable behavior, which means the application still needs safe retries. Those retries must rerun the entire transaction function without duplicating effects outside Spanner.

Do not send an email, publish a non-idempotent command, or charge an external payment service from inside a retriable transaction body unless that side effect is coordinated through an outbox, idempotency key, or post-commit workflow.

The important measurements are transaction duration, total mutation count, lock contention, abort rate, retry count, and high-percentile latency by transaction type. Compare those before and after consolidating statements.

The right boundary follows the business invariant, then gets tested under concurrency. A higher limit is capacity, not permission to ignore queueing behavior.

### Segment two: Multimodal serving gets a third scheduling domain

The second development comes from NVIDIA’s open-source Dynamo inference framework.

Here are the reported facts.

On September ninth, NVIDIA published benchmarks and design guidance for encode-prefill-decode disaggregation, or EPD.

A multimodal request performs media download and preprocessing, runs a vision encoder to create embeddings, performs language-model prefill over the resulting input, and then decodes output tokens.

In an aggregated worker, vision encoding, prefill, and decode share one GPU worker and one scheduling domain. EPD separates the encoder workers from the workers responsible for prefill and decode. Vision embeddings move between those roles through NVIDIA’s inference-transfer library.

NVIDIA describes three topologies.

Aggregated serving keeps the entire request together.

Colocated EPD runs separate encoder and language-model workers on the same GPUs, allowing separate queues and batches without dedicating a full accelerator to the lighter encoder.

Heterogeneous EPD places encoders on a lower-cost GPU tier and reserves premium GPUs for prefill and decode.

In NVIDIA’s selected test environment, with a quantized mixture-of-experts model on four GB200 GPUs, plus RTX 6000D GPUs for the heterogeneous configuration, EPD produced large gains for image-heavy requests. For a ten-image request with a one-thousand-twenty-four-token output, colocated encoding reduced mean time to first token by fifty-eight percent. The heterogeneous topology served seventy percent more traffic at the same inter-token-latency objective.

The benefit did not apply universally. With light image input and a two-thousand-forty-eight-token output, colocated EPD was two-and-a-half percent slower end to end. In a model-size comparison, the relative goodput benefit fell as the dense language model grew and its work dominated the encoder.

Now, the analysis.

This is a queueing problem disguised as a model-serving feature.

Picture a mixed line where some parts require machine vision inspection before assembly, while ordinary parts go directly to assembly. If inspection and assembly share one station and one queue, an image-heavy part can block ordinary parts that never needed inspection.

Separating the vision stage creates two service centers. Text requests bypass the encoder queue. Image requests can be batched with similar work. Each stage can scale according to its own arrival rate and service time.

But disaggregation adds transport, coordination, buffering, and another failure boundary. If vision work is small, the handoff costs more than the isolation saves. If decode dominates a long response, accelerating the beginning barely changes completion time.

Choose architecture from a workload matrix, not a headline speedup.

Measure the distribution of images or video per request, visual tokens, input tokens, output tokens, model type, precision, cache reuse, and text-to-multimodal mix. Then record stage-level queue time, service time, transfer time, time to first token, inter-token latency, end-to-end latency, and same-SLO goodput.

Also decide what happens when the encoder tier is unavailable. A text-only request should not fail merely because an unrelated vision pool is down. A multimodal request may degrade to a clear unavailable state, route to an aggregated fallback, or enter a bounded queue. It should not silently discard the image and answer as if it had seen it.

The deeper lesson is that independently scalable stages are valuable only when their workloads and failure policies are independently understood.

### Segment three: Agent permissions and secret findings become enforced states

The third story combines two GitHub changes published September ninth.

Here are the reported facts.

GitHub Copilot Business and Enterprise administrators can now centrally classify agent operations as blocked, requiring human approval, or allowed without a prompt.

The managed permissions cover shell commands, file reads and edits, and network domains. They are generally available in the Copilot app, Copilot command-line interface, and Visual Studio Code sessions using Agent Host.

The enterprise restriction takes precedence over user settings, workspace settings, automatic approval, and previously saved approvals. Policies can differ by enterprise team.

Separately, GitHub repository rulesets can now require pull-request secret-scanning alerts to be resolved before merge. The rule verifies that a scan completed for the head commit and that no applicable secret alerts introduced by the pull request remain open.

Provider patterns are included by default. Administrators can also select custom or generic secret patterns. The rule is in public preview for customers with Secret Protection or GitHub Advanced Security, and it complements push protection rather than replacing it.

Now, the analysis.

Yesterday’s JetBrains sandbox established the physical cell around a local coding agent. Today’s managed permissions define the transitions allowed inside that cell.

A sandbox may permit access to the repository and a shell. The operation policy can still say that tests run automatically, dependency installation requires approval, production configuration is unreadable, and network calls are limited to approved domains.

This resembles separating a machine guard from its sequence permissives. The fence limits where motion can occur. The PLC logic decides which motion is legal in the current state.

The secret-scanning rule applies the same principle to delivery. A scanner finding is information. A ruleset turns selected findings into a merge-state constraint.

Design the exceptions with as much care as the default. A bypass should identify the person, reason, secret type, affected repository, expiration, and remediation owner. Otherwise, the gate may become ceremonial under schedule pressure.

Test negative paths. Ask an agent to read a denied file through a shell command, edit it through another tool, or send its content to an unapproved domain. Push a synthetic test credential and confirm that the scan completes and the pull request remains blocked. Then rotate or revoke the test credential and remove it safely.

Policy should produce auditable state transitions: proposed, allowed, approved, denied, bypassed, and completed. A prompt saying “be careful” is not a control system.

### Playground Lesson: turn golden tasks into a release gate

I inspected the AI Systems Engineering Playground through GitHub today, including its README, module sequence, labs, roadmap, capstone, and recent commits.

The latest commit remains the September-ninth curriculum expansion. Module Thirteen defines five golden scenarios and asks the capstone to record accuracy, citation validity, tool-call count, p95 latency, and estimated cost.

Yesterday’s checkpoint created the task contract. The next step is to separate three kinds of evaluation.

First, correctness metrics ask whether the diagnosis is acceptable and grounded in the simulator’s authoritative state.

Second, process metrics ask whether the agent gathered required evidence, cited valid source identifiers, stayed within its tool budget, and reached an explicit terminal status.

Third, safety gates ask whether it attempted a forbidden action, invented evidence, concealed conflicting signals, or produced an actionable conclusion when required data was missing.

Do not average all of these into one comforting score.

Suppose the agent diagnoses four of five scenarios correctly, cites evidence in four, and attempts one prohibited write. A weighted average might still exceed eighty percent. Operationally, the release should fail.

This is the difference between a quality score and a safety interlock.

An assembly cell may tolerate a small cycle-time regression. It does not average an open guard door against high throughput and declare the machine healthy.

For the capstone, define hard gates first:

Zero forbidden tool calls.

Zero unsupported citations.

Required abstention when critical evidence is unavailable.

And explicit escalation when signals conflict beyond the defined rule.

Only after those pass should you compare softer performance metrics such as diagnosis accuracy, tool efficiency, p95 latency, and estimated cost.

Be careful with p95 on five tasks. One run per scenario is not enough to estimate a tail. Repeat each scenario several times or initially report every observed latency plus the maximum. As the run count grows, p95 becomes more meaningful.

Store an evaluation record with the task version, simulator fixture, corpus revision, tool-server version, model and routing policy, evaluator version, random seed where supported, raw observations, and final scores. That record is the equivalent of a signed commissioning sheet: it tells you what was tested, against which configuration, and why it passed.

Your twenty-to-thirty-minute checkpoint is to create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

The scorer should calculate diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. It should then emit one of two release states: pass or stop.

Make stop mandatory if any record contains a forbidden tool call, invalid citation, or missing required abstention. Print the exact task ID and violated gate.

Use mock results first: four clean cases and one unsafe-action case containing a prohibited write attempt. Confirm that excellent average metrics cannot override the stop decision. Then remove the violation and confirm the same scorer passes the run.

The checkpoint question is:

Which single observed behavior would make you stop deployment even if every aggregate dashboard remained green?

Write that answer as executable policy.

### Practical takeaway

For one system change, write both statements:

The new capability allows us to do what?

And the independent gate stops us under which condition?

Capacity and permission are different design decisions.

### Closing recap

Spanner now permits more DML statements inside one transaction, but lock duration, contention, aborts, and retry-safe side effects still define the useful boundary.

NVIDIA’s EPD design separates vision encoding from language-model prefill and decode when media load, traffic mix, and hardware justify another scheduling domain.

GitHub can centrally control agent operations and prevent pull requests with unresolved secrets from merging.

And in the Playground, golden tasks become an engineering release gate only when safety failures can stop deployment regardless of average performance.

That’s today’s Engineering Commute.

Have a good Thursday.

## Compact show notes

- **Spanner DML transaction limits — September 9:** The 80,000 mutation-mod limit now applies to each DML statement instead of accumulating across the transaction; other limits, lock contention, and Mutation API behavior remain relevant. [Google Cloud announcement](https://cloud.google.com/blog/products/databases/spanner-removes-dml-mutation-limits) and [Spanner quotas](https://cloud.google.com/spanner/quotas).

- **Encode-prefill-decode disaggregation — September 9:** NVIDIA Dynamo separates multimodal encoding from prefill and decode, with aggregated, colocated, and heterogeneous placement options plus workload-specific benchmark results. [NVIDIA technical report](https://developer.nvidia.com/blog/when-to-use-encode-prefill-decode-disaggregation-to-accelerate-multimodal-model-serving/) and [NVIDIA Dynamo repository](https://github.com/ai-dynamo/dynamo).

- **Managed Copilot agent permissions — September 9:** Enterprise policy can block, approve, or automatically allow shell commands, file operations, and network domains across supported Copilot agent clients. [GitHub changelog](https://github.blog/changelog/2026-09-09-enterprise-managed-permissions-for-github-copilot-agent-operations/).

- **Secret-scanning merge gate — September 9:** Repository rulesets can require a completed secret scan and resolution of applicable alerts introduced by a pull request. [GitHub changelog](https://github.blog/changelog/2026-09-09-block-pull-requests-with-exposed-secrets-from-merging/).

- **Streaming status:** No substantive Apache Kafka or NATS JetStream release newer than the JetStream 2.15 release candidate covered on September 8. [Apache Kafka releases](https://kafka.apache.org/blog/releases/) and [NATS Server releases](https://github.com/nats-io/nats-server/releases).

- **Playground:** The repository remains at the September 9 curriculum expansion. [Current commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d), [roadmap](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/docs/roadmap.md), [Module 13](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/13_capstone.md), [capstone project](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/projects/capstone_factory_ai_engineer/README.md), and [labs contract](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/labs/README.md).

- **Checkpoint:** Score mock golden-task runs, report correctness and process metrics, and enforce a non-averaged stop gate for forbidden tool calls, invalid citations, or failure to abstain when required.

- **Estimated spoken runtime:** Approximately 15 minutes; narration target 2,100–2,300 words.
