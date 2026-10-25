# The Engineering Commute — September 18, 2026

## Narration-ready episode

Good morning, Dan.

Today’s Engineering Commute is about systems that stay useful while the workload keeps changing.

NATS Server two-point-fifteen introduces a desired-state reconciliation engine for JetStream, along with safer asset moves, server evacuation, disaster recovery, and a new backup format.

GitHub Actions now has generally available workflow-execution protections that can restrict who may start a workflow, which events may start it, and which workflow files a rule applies to.

Then we’ll spend most of the commute on the next inference-systems lesson: prefill, decode, the KV cache, continuous batching, queueing delay, backpressure, and the difference between making a GPU busy and making a service good.

I checked the AI Systems Engineering Playground before recording. The latest commit is still the September ninth curriculum expansion, and the current evaluator checkpoint is not present. So today adds no new assignment. The same checkpoint is repeated unchanged near the end.

### Current development one: JetStream moves from imperative operations toward reconciliation

First, the reported facts.

NATS Server two-point-fifteen was released on September seventeenth.

Its largest JetStream change is a desired-state metalayer and reconciliation engine for streams and consumers. NATS says this substantially improves the safety and reliability of asset moves and scaling operations.

With the new design, operators can more safely change placement or replication while an earlier move is still underway. They can cancel an in-flight stream move and return the asset to its original placement. They can also evacuate all streams and associated consumers from a server, or evacuate a particular peer from a stream, while transferring data and state.

For disaster recovery, a new metalayer rescue endpoint can temporarily lower the quorum required by the metadata layer when nodes have been permanently lost and quorum can no longer be reached. That is a recovery mechanism, not an ordinary availability setting.

The release also introduces a second-generation stream backup format. Instead of reading snapshots per storage block, it reads per message, and it includes non-replicated consumers located on follower nodes.

Source and mirror state also receives attention. JetStream now persists source indices so restarts and leader changes can avoid expensive backward scans. The server can detect when a source stream has been recreated and restart sourcing from the beginning.

There is one notable default change. Streams now default to at most one thousand consumers unless the stream or account configuration says otherwise. Existing consumers are not deleted, but creation beyond the limit is prevented. Teams that intentionally use more must configure that capacity.

Now the engineering analysis.

The theme is the difference between issuing a command and maintaining an invariant.

An imperative move says, “Put this stream over there.” If the operator changes their mind halfway through, a node fails, or leadership changes, the system must reconstruct what partially happened.

A reconciler says, “This is the state we want. Compare it with the state that exists, then take safe, repeatable steps until they match.”

That resembles a closed-loop controller. A command is the setpoint. The observed cluster is the process variable. The reconciler repeatedly measures error and applies bounded corrections. The hard part is not calculating the difference. It is making every transition recoverable when the actuator is interrupted halfway through.

For an industrial event platform, server evacuation is operationally important. Maintenance should be a planned state transfer, not a collection of peer removals performed while watching replicas and hoping no state is stranded.

But safer APIs do not eliminate preparation. Before adopting two-point-fifteen, read the upgrade guide, inventory streams near the new consumer limit, test move cancellation, verify snapshots by restoring them, and define who may invoke rescue. A quorum-rescue endpoint is like a maintenance bypass around a safety permissive: essential in the right emergency, dangerous as a routine shortcut.

### Current development two: GitHub Actions adds an execution interlock

Here are the reported facts.

On September seventeenth, GitHub made workflow-execution protections generally available for GitHub Enterprise, organizations, and repositories.

The protections evaluate both actor rules and event rules before an Actions run starts. In other words, policy can restrict who is allowed to trigger a workflow and which trigger events are allowed.

General availability adds workflow-file targeting. A repository can apply strict rules to a deployment workflow while allowing a broader set of contributors to run ordinary continuous integration.

GitHub also added insights showing how rules are evaluated and enforced, plus REST API support for managing execution-protection policy at enterprise, organization, and repository scope.

Now the analysis.

This is not a replacement for branch protection, environment approval, least-privilege tokens, or pinned dependencies. It is an earlier gate.

Think of a deployment workflow as a machine sequence. Branch protection verifies that the recipe was approved. Environment protection governs access to the production cell. Token permissions limit what the sequence may actuate. Execution protection is the permissive that determines whether the sequence may start at all.

Workflow-file targeting matters because risk is uneven. A pull-request test that compiles code has a different blast radius from `deploy-production.yml`, a database migration, or an infrastructure-destroy workflow.

The REST API also makes policy measurable. Treat protection rules as versioned configuration. Begin in observation where possible, inspect blocked and allowed attempts, then enforce. A rule that exists only in a web interface is harder to reproduce and audit across hundreds of repositories.

For the Factory AI Engineer, the deployment workflow and evaluation workflow should have different execution contracts. Many contributors may safely run offline evaluation against fixtures. Promotion of a new model, tool manifest, or production policy should be limited to trusted actors and approved events.

### Playground Lesson: continuous batching and the queue inside an AI service

Yesterday we discussed quantization: reducing model precision to save memory and bandwidth while preserving the behavioral contract.

Today we assume the model fits and ask a different question.

What happens when many requests arrive at different times, have different prompt lengths, and generate different numbers of output tokens?

This is where an AI model becomes a queueing system.

#### One request has two computational phases

An autoregressive language-model request has two visibly different phases: prefill and decode.

During prefill, the server processes the input prompt. If the request contains a manual excerpt, alarm history, tool schema, and conversation context totaling four thousand tokens, the model evaluates those tokens and constructs attention state for every layer.

Prefill can process many prompt tokens in parallel. It usually creates large matrix operations and can use accelerator compute efficiently. Longer prompts increase prefill work and delay the first output token.

During decode, the model generates one next token, appends it to the sequence, then repeats. Within one sequence, token number two-hundred cannot be generated before token one-hundred-ninety-nine. That dependency limits parallelism across time.

Decode can still batch many independent sequences together, but each active request normally contributes only one new token to a decode step.

The production analogy is a changeover followed by repetitive cycles.

Prefill is recipe loading, fixture setup, and inspecting the incoming job. Decode is the machine producing one part per cycle until that job is complete.

A long setup does not necessarily imply a long cycle time. A short prompt can still request a long answer. These phases therefore need separate metrics.

Time to first token includes queueing plus prefill plus initial scheduling.

Inter-token latency describes how quickly later tokens arrive during decode.

End-to-end latency includes both and depends strongly on generated length.

If you report only total tokens per second, an interactive service can look excellent while users wait several seconds before anything appears.

#### What the KV cache stores

Attention compares the current token with earlier tokens. Without caching, the model would repeatedly recompute the keys and values for the entire history at every decode step.

The KV cache stores those key and value tensors for each transformer layer. Prefill populates the cache for the prompt. Every decode step adds entries for the new token.

The cache is like a prepared work-in-process rack beside every station. The line does not remanufacture every previous part each cycle. It keeps the intermediate state needed for the next operation.

That saves compute, but it consumes accelerator memory.

KV-cache size grows with the number of layers, cached tokens, key-value head geometry, datatype size, and number of active sequences. Long contexts and high concurrency can therefore exhaust memory even when the model weights fit comfortably.

This explains why quantizing an eight-billion-parameter model does not automatically solve capacity. Four-bit weights might save many gigabytes, but hundreds of active long-context sessions can consume the recovered space through their caches.

The cache also turns admission into a commitment. Accepting a request with a maximum context and output budget reserves potential future state. If the scheduler admits too many optimistic requests, it may later run out of memory as their outputs grow.

Production servers manage this with token budgets, paged allocation, prefix reuse, preemption, or swapping. The general principle is identical to material control: do not release more work to the line than the constrained buffer can hold.

#### Why ordinary batching wastes capacity

Suppose four requests arrive together. They need ten, twenty, sixty, and one-hundred output tokens.

With static batching, the server groups them and advances them together. The ten-token request finishes first, but its position may remain unused until the entire batch completes. Then the twenty-token request finishes, leaving another empty position. The batch proceeds at the pace of its longest member.

This resembles loading four parts onto a fixture that cannot be opened until all four processes finish. Three positions may sit empty while the slowest part completes.

Static batching works well when shapes and durations are predictable. Generative inference is highly variable.

Continuous batching changes membership between decoding iterations. When one request finishes, the scheduler can insert another waiting request into the freed capacity. The accelerator operates on a changing set of active sequences.

This improves utilization because short jobs no longer leave permanent holes.

But it does not make scheduling free. New prefill work competes with active decode work. Sequences have different lengths. Memory blocks fragment. Some requests use cached prefixes. Some have priority. Some are close to their deadline.

The server is effectively solving a real-time production-scheduling problem every iteration.

#### Throughput and latency are not the same objective

Larger batches often improve throughput because the accelerator processes more work per operation. Kernel-launch overhead and weight movement are amortized across requests.

But larger batches can increase queueing delay. A request may wait while the scheduler accumulates enough work, or active batches may occupy memory and compute for longer.

Imagine a heat-treatment furnace. Filling every rack maximizes parts per furnace cycle. Waiting to fill the last rack, however, may violate the due date of the first part. A hot urgent repair job may deserve immediate processing even if the furnace is not full.

Inference serving has the same conflict.

Offline summarization may optimize total tokens per second and dollars per million tokens.

An operator asking why Line Four is stopped cares about time to first useful answer and tail latency.

An autonomous tool loop cares about the latency of several sequential model turns, because each tool decision blocks the next action.

The correct objective is not “maximize GPU utilization.” It is “meet workload-specific service objectives at acceptable cost.”

A GPU can be one-hundred percent busy doing work that has already missed its deadline.

#### Queueing delay and utilization

Queueing systems become nonlinear near saturation.

At low utilization, a new request usually finds available capacity. As average utilization rises, bursts increasingly arrive while the server is already occupied. The queue grows, and tail latency rises much faster than average service time.

This is why running at ninety-nine percent steady utilization is a poor target for an interactive service. There is no room for arrival variance, long prompts, long generations, cache misses, or noisy neighbors.

Controls engineers see the same behavior in surge capacity. A pump sized exactly to average inflow cannot absorb disturbances. The vessel level rises during every positive deviation because there is no excess removal capacity.

Headroom is not necessarily waste. It is the capacity that closes the loop after a disturbance.

Track arrival rate, admitted token rate, queued requests, queued input tokens, active sequences, KV-cache occupancy, prefill tokens per second, decode tokens per second, time to first token, inter-token latency, and p50, p95, and p99 end-to-end latency.

Request count alone is misleading. One request may contain fifty prompt tokens; another may contain fifty thousand.

#### Backpressure is part of correctness

If incoming work exceeds sustainable service capacity, the system has only a few honest options.

Queue it within a bounded limit.

Reject it.

Defer it.

Route it elsewhere.

Reduce its permitted context or output.

Or degrade to a cheaper model or simpler workflow.

An unbounded queue does not create capacity. It hides overload until memory, deadlines, and retries fail together.

This is similar to allowing unlimited work orders onto a production line. The line may look fully utilized, but lead time becomes unpredictable, priorities lose meaning, and operators expedite everything.

Backpressure should activate before failure. Useful signals include queue age, predicted completion time, KV-cache occupancy, accelerator memory headroom, admission-token budget, and recent tail latency.

A request can be rejected with a clear retry-after response. An asynchronous task can be placed on a durable queue. A low-priority batch can pause. An operator request can preempt background work.

The response must match the workload. Silently accepting a safety-relevant request that will wait three minutes is worse than immediately declaring that the service is overloaded and invoking a fallback.

#### Scheduling policies encode business priority

First-in, first-out is easy to understand, but it can create head-of-line blocking when one enormous prefill sits ahead of many small requests.

Shortest-job-first can reduce average latency, but output length is not known with certainty. It can also starve long requests.

Priority queues protect urgent classes, but a priority label must be authenticated and bounded. Otherwise every client marks itself critical.

Deadline-aware scheduling can consider remaining service time and service objectives. Fair-share scheduling prevents one tenant from consuming every decode slot or all KV memory.

For the Factory AI Engineer, I would define at least three classes.

Interactive operator diagnosis receives a tight time-to-first-token objective and a bounded response length.

Agent tool steps receive moderate priority but strict per-incident budgets, because one incident can generate many sequential calls.

Offline indexing, summarization, and evaluation use spare capacity or a separate queue.

Do not mix these classes and hope the scheduler infers intent from prompt text. Priority is an authorization and product decision, not a model decision.

#### Prefill and decode may deserve separate capacity

Prefill and decode stress hardware differently.

Prefill has substantial parallel computation over many input tokens. Decode often moves weights and cache data for comparatively little work per active sequence.

At sufficient scale, platforms may disaggregate these phases. One worker group handles prefill and transfers the resulting KV state to decode workers. Decode workers remain optimized for steady token generation.

This resembles separating a setup cell from the production line. Specialized setup resources prepare the job, then hand it to a high-throughput repetitive process.

Disaggregation can improve independent scaling and reduce interference, but the KV transfer becomes a new dependency. Network bandwidth, state serialization, routing, placement, failure recovery, and cache ownership now matter.

If prefill succeeds but the decode worker disappears after receiving only part of the cache, can the request resume? If routing retries, will two decode workers produce duplicate streams? What is the timeout? Who owns cleanup?

Architecture creates failure modes along with capacity.

Do not disaggregate a small service merely because the pattern is fashionable. Begin with measurements. Separate phases when their scaling needs and interference justify the added state transfer.

#### Prefix caching and repeated industrial context

Many requests share prefixes: the same system prompt, tool definitions, safety policy, asset metadata, or manual section.

Prefix caching reuses previously computed KV state for an identical prefix. It can reduce prefill latency and compute, especially when prompts contain large stable instructions.

For the Factory AI Engineer, a site policy and tool schema might be reused across many incidents. But cache identity must include every input that changes semantics: model revision, tokenizer, adapter, system prompt, tool definitions, access policy, and relevant configuration.

Reusing a cache across incompatible policy revisions is like loading a machine with yesterday’s recipe because the first few steps looked identical.

Security matters too. A shared cache must not let one tenant infer or receive another tenant’s private prefix state. Cache keys, isolation, eviction, and observability belong in the threat model.

#### What to benchmark

Build a workload distribution, not one heroic benchmark.

Include short prompts with short outputs, long RAG prompts with concise outputs, long-form generation, multi-turn tool loops, concurrent operator questions, and background evaluation.

Run at increasing offered load. For each load point, record accepted requests, rejected requests, queue time, time to first token, inter-token latency, p95 completion latency, tokens per second, cache occupancy, and failures.

The interesting graph is not peak throughput. It is the knee where tail latency begins to climb sharply. That is the point where a small increase in arrival rate produces a large increase in waiting.

Set admission below that knee for interactive work. Reserve headroom for bursts and failures. If another replica takes time to load model weights, autoscaling cannot rescue a ten-second spike immediately.

Warm capacity, routing policy, and load-shedding rules must cover the gap.

#### Connecting this to JetStream

JetStream and an inference scheduler both manage variable work, but their responsibilities differ.

JetStream provides durable messaging, replay, consumer state, and delivery control. It is appropriate for asynchronous evaluation, document ingestion, or a diagnosis job that may complete later.

The inference engine manages accelerator-resident sequences at token timescales. It owns KV memory, decode slots, and continuous batching.

Do not treat the broker queue as the entire serving queue. A message may be delivered to an inference worker and still wait internally for prefill or decode capacity.

End-to-end observability should carry one request identifier through the broker, gateway, scheduler, model server, agent, and tool calls. Otherwise each component reports healthy local metrics while the user experiences a slow system.

This is the data-platform version of tracking a serial number across every factory buffer rather than counting only the parts currently on each machine.

### Current capstone checkpoint — unchanged

Because the repository does not show completion, keep the same checkpoint. Do not add a new task.

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

The scorer should compute diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. It should emit either pass or stop.

A forbidden tool call, invalid citation, or missed required abstention must force a stop. The output should print the exact task ID and gate responsible.

Include four clean cases and one case containing an unsafe write attempt. Prove that good average metrics cannot override the mandatory stop. Then remove the violation and confirm the same run passes.

This remains the only capstone action item.

### Practical takeaway

For one AI endpoint, put these six measurements on the same dashboard:

Queued input tokens.

Active sequences.

KV-cache occupancy.

Time to first token.

Inter-token latency.

And rejection or deferral rate by workload class.

If you watch only GPU utilization and total tokens per second, you cannot tell whether the service is responsive, overloaded, fair, or safe.

### Closing recap

NATS Server two-point-fifteen adds a reconciliation model for safer JetStream placement changes, plus evacuation, quorum rescue, improved backup and restore, and faster recovery of source state.

GitHub Actions execution protections add a start permissive based on actor, event, and workflow file, with API-driven management and policy insights.

And an AI inference service is a variable-length production line.

Prefill prepares the job. Decode advances it one token at a time. The KV cache stores work in process. Continuous batching fills open stations. Admission control limits released work. Backpressure keeps overload explicit. Priority determines which deadline matters.

Busy hardware is not the goal.

The goal is predictable useful service under a workload that never arrives perfectly evenly.

That’s today’s Engineering Commute.

Have a good Friday.

## Compact show notes

- **NATS Server 2.15.0 — September 17, 2026:** JetStream desired-state reconciliation, safer moves and scaling, move cancellation, server and peer evacuation, metadata-quorum rescue, stream backup format v2, persisted source indexing, and a new default limit of 1,000 consumers per stream. [Official NATS release](https://github.com/nats-io/nats-server/releases/tag/v2.15.0), [2.15 upgrade guide](https://docs.nats.io/release-notes/upgrade-to-2.15), and [desired-state ADR](https://github.com/nats-io/nats-architecture-and-design/blob/main/adr/ADR-62.md)

- **GitHub Actions execution protections — September 17, 2026:** Generally available actor and event allowlists now add workflow-file targeting, enforcement insights, and REST API management. [GitHub changelog](https://github.blog/changelog/2026-09-17-workflow-execution-protections-in-github-actions-generally-available/)

- **Playground status:** No repository change after the September 9 curriculum expansion, and `evals/score_run.py` remains absent. [Course roadmap](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/README.md), [Module 4: batching and queueing](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/04_inference_scheduling.md), [continuous-batching simulator](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/labs/06_batching_sim/continuous_batching_sim.py), [capstone](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/projects/capstone_factory_ai_engineer/README.md), and [current commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d)

- **Unchanged checkpoint:** Create `evals/score_run.py` plus `evals/sample_run.jsonl`; score diagnosis success, evidence coverage, citation validity, tool calls, and latency; make forbidden writes, invalid citations, and missed abstentions mandatory stop conditions; prove averages cannot override the unsafe case, then remove it and confirm a pass.

- **Estimated spoken runtime:** Approximately 24 to 27 minutes; about 3,350 spoken words.
