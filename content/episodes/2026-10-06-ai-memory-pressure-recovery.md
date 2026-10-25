# The Engineering Commute — October 6, 2026

## Narration-ready episode

Good morning, Dan.

Today’s Engineering Commute is about what happens when software meets a physical limit.

Kubernetes has published new benchmark results showing that fast local swap can significantly increase the density of bursty agent sandboxes. The headline reaches three times as many isolated Python environments on one node, but the more important lesson is where the result stops working: swap can absorb dormant state, but it cannot cheaply replace an active working set.

AWS has also introduced a first-class CodeDeploy restart mode. It can reapply the last successful revision while retaining batch controls, health checks, alarms, lifecycle hooks, and deployment history.

Those stories meet in today’s Playground Lesson: memory pressure and recovery design for AI systems. We will distinguish allocated memory from the active working set, explain requests, limits, swap, eviction, and out-of-memory behavior, and build a practical hierarchy for deciding what to preserve, spill, recompute, reject, or restart.

The Playground repository remains unchanged, so the existing evaluator checkpoint remains the only assignment.

### Segment one: Kubernetes treats fast swap as a density tool

Here are the reported facts.

On October fifth, the Kubernetes project published benchmark results for node swap backed by fast local NVMe storage.

Running Kubernetes nodes with swap reached general availability in version one-point-thirty-four. The current configuration uses cgroup version two, which accounts for memory and swap separately. That matters because older cgroup behavior made it difficult to see or constrain how much anonymous memory a container had moved to disk.

The tests covered Linux kernel builds, headless-browser sandboxes, and isolated Python runtimes.

For a kernel-build workload, local swap allowed the memory limit to fall from six hundred megabytes to three hundred without a slowdown in the reported run. Reducing the limit further to two hundred megabytes pushed active data into swap and increased execution time by more than forty percent.

For sandboxed browsers, gVisor density doubled from eighty to one hundred sixty concurrent pods. Kata micro-VM density rose from forty to fifty.

The Python test analyzed five million MovieLens rows in isolated gVisor environments. Without swap, the node failed at eighty concurrent sessions. With local SSD swap, it supported two hundred forty, a three-times increase.

The project recommends LimitedSwap with Burstable quality of service: requests below limits, giving the node room to move dormant anonymous memory out of RAM while retaining active state.

Now the engineering analysis.

The useful idea is not “turn on swap.” It is “classify memory by temperature.”

An agent sandbox may load an interpreter, libraries, browser process, and security-runtime state, then wait for minutes between useful operations. Much of that state is necessary for a quick resume but is not being touched right now. Fast swap converts expensive always-resident state into slower retained state.

This resembles a manufacturing cell with fixtures and material staged nearby. Keeping every fixture mounted on the machine gives the fastest possible changeover but wastes the constrained workspace. Moving rarely used fixtures to a nearby rack increases capacity. Moving the active fixture to a warehouse across town does not.

The benchmark’s two-hundred-megabyte kernel build is the warning. Once the active working set no longer fits in RAM, the system repeatedly faults pages in and out. Throughput collapses through thrashing.

For AI systems, measure resident memory, swap use, major page faults, page-in latency, CPU contention, and task latency together. A node can look stable because it avoids out-of-memory kills while silently turning a two-second tool call into a thirty-second call.

Also separate CPU memory from accelerator memory. Kubernetes node swap does not make GPU high-bandwidth memory elastic. Model weights, KV cache, activations, and CUDA graph state still need an explicit GPU-memory plan. A pod can have plenty of host swap and still fail because its accelerator allocation is exhausted.

The decision is workload-specific. Dormant browser sandboxes, build workers, and intermittent Python tools are good candidates. Low-latency inference workers with continuously active memory are much less forgiving.

### Segment two: AWS makes restart a controlled deployment

Here are the reported facts.

Also on October fifth, AWS introduced a CodeDeploy RESTART deployment mode for EC2 and on-premises in-place deployment groups.

The mode resolves the deployment group’s last successful revision and reapplies it. It retains deployment configuration, lifecycle hooks, CloudWatch alarm monitoring, rollback settings, and deployment history. Agents at version two-point-one-point-zero or later can reuse the previous deployment archive locally; if that archive is missing or invalid, the agent downloads the same pinned revision.

AWS reports that feature testing completed some fleet restarts up to six-point-one times faster than a standard deployment.

The lifecycle still runs application stop, bundle handling, pre-install, install, post-install, application start, and service validation. Operators can restart one host at a time, half at a time, all at once, or with a custom minimum-healthy-host setting.

There is an operational constraint: the restart mode does not execute the load balancer’s block-traffic and allow-traffic steps. Request-serving applications must stop accepting new work and drain in-flight requests themselves.

AWS also describes automated remediation: a CloudWatch alarm can invoke an EventBridge rule and Lambda function that creates a restart deployment. The example includes long-running JVM services and self-managed Kafka brokers experiencing memory growth.

Now the analysis.

A restart is not harmless because the binary version remains unchanged.

Runtime configuration may have changed. In-memory queues may contain work. Leader elections may occur. A broker may trigger partition movement. A worker may abandon a task after producing a side effect but before committing its acknowledgement.

Treat restart as a state transition with entry conditions, sequencing, verification, and abort criteria.

The controls analogy is restarting a production station after a fault. You do not simply cycle power on every station simultaneously. You stop material admission, finish or quarantine work in progress, place actuators in a known state, restart one zone, verify permissives, and only then continue.

For a Kafka broker, that means preserving enough healthy replicas, checking under-replicated partitions, controlling leadership churn, and observing catch-up before moving to the next batch. For an agent worker, it means stopping new task leases, completing or releasing existing leases, persisting checkpoints, and making external actions idempotent.

Automated restart can be useful as a recovery layer, but it must not become a substitute for diagnosis. If memory rises because a queue has no bound, restarting periodically hides the leak while discarding evidence. Preserve a heap profile, task-state snapshot, or diagnostic bundle before recycling when the incident budget allows.

The important advance is that the restart is now governed by the same deployment machinery as a release. That makes health gates, concurrency, and audit history part of the action instead of assumptions in a shell script.

### Playground Lesson: memory pressure as a controlled hierarchy

I inspected the AI Systems Engineering Playground again today. Its README, modules, labs, and commit history have not changed. The latest commit is still the September ninth curriculum expansion, and the expected evals directory is still absent.

This lesson supports the inference, agent workflow, reliability, and capstone portions of the roadmap.

Start with four different memory numbers.

Allocated memory is what a process has requested from an allocator. Resident memory is the subset currently backed by physical RAM. The working set is the subset touched frequently enough that performance depends on keeping it fast. Peak memory is the largest observed footprint during a selected interval.

Those are not interchangeable.

A Python process may allocate several gigabytes over time while actively touching far less. An inference server may have a large, stable weight allocation plus a KV cache that rises with concurrent sequence length. An agent sandbox may initialize a browser and libraries, then leave most pages cold while waiting.

For planning, decompose memory into fixed, per-worker, per-request, and burst components.

Fixed memory includes the runtime, model weights, shared libraries, and base caches.

Per-worker memory includes interpreter or sandbox overhead.

Per-request memory includes tokens, KV blocks, tool payloads, intermediate results, and response buffers.

Burst memory includes compilation, large parsing operations, image decoding, retrieval fan-out, or temporary copies during serialization.

A rough capacity model is:

fixed memory, plus workers times worker memory, plus active requests times request memory, plus burst reserve.

The formula is simple. The hard part is measuring each term under production-shaped work.

Now map that into Kubernetes.

A memory request is primarily a scheduling promise. The scheduler uses it to decide whether a pod fits on a node.

A memory limit is an enforcement boundary. Crossing it can cause the container to be killed.

If request and limit are equal, the pod receives Guaranteed quality of service when the other resource requirements align. If the request is lower than the limit, it is usually Burstable. That difference creates room for opportunistic density, but it also defines who is more exposed when a node is under pressure.

Do not set requests from average memory alone. Averages erase bursts. Use a high percentile over representative workloads, then decide which burst should remain in RAM, which may spill, and which should trigger admission control.

Next, build a five-level response hierarchy.

Level one is reclaim.

Evict expendable application caches, completed conversation state, old retrieval results, decoded media, temporary tensors, and unused worker pools. This should be the cheapest response because the system can recompute the data.

Level two is spill.

Move cold, recoverable state to a slower tier: NVMe swap, object storage, a durable queue, or a checkpoint store. The state remains available, but resume latency increases.

Level three is degrade.

Reduce batch size, shorten context, use a smaller model, stop speculative decoding, lower retrieval fan-out, or disable nonessential tools. This preserves service while reducing quality or throughput in a controlled way.

Level four is reject or defer.

Apply backpressure before accepting work that cannot complete safely. Return a retryable response, queue the request with a deadline, or route it to another pool. Rejecting one request is better than allowing the node to thrash and fail every request.

Level five is restart or replace.

Use this when state is corrupted, fragmentation cannot be reclaimed, a leak is confirmed, or the process has crossed a health boundary. Drain first when possible, preserve diagnostics, and restart in bounded batches.

This hierarchy is similar to an electrical load-shedding plan.

You do not wait for the main breaker to trip. You shed nonessential loads, move supported loads to alternate supplies, reduce throughput, stop new starts, and isolate the unhealthy section. An out-of-memory kill is the breaker trip: necessary as a final protection, but evidence that upstream controls did not act in time.

Now define observability.

At the node level, watch available memory, swap used, major page faults, pressure-stall information, disk latency, and out-of-memory events.

At the pod level, watch resident working set, request and limit utilization, restart count, throttled admissions, queue age, and latency.

At the AI runtime level, watch model-weight memory, KV-cache occupancy, cache eviction, active sequences, tokens per request, batch size, and failed allocations.

Correlate these signals on one timeline. A rise in latency with flat CPU may be page faults. A rise in GPU allocation with longer prompts may be KV pressure. A restart followed by immediate regrowth may indicate a leak or an unbounded queue rather than fragmentation.

Finally, define recovery success.

Success is not “the process started.” It is that the service rejoined with the expected model and configuration, accepted work, completed a representative request, restored queue ownership, and stayed below pressure thresholds for a settling interval.

That is the difference between a restart command and a recovery procedure.

### Playground checkpoint — unchanged

The repository still does not contain evals/score_run.py or evals/sample_run.jsonl, so this remains the only assigned checkpoint. Do not add another task until these files appear in GitHub.

Create evals/score_run.py and a mock evals/sample_run.jsonl.

Compute diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. Emit either pass or stop.

Make these mandatory stop conditions: a forbidden tool call, an invalid citation, or a missed required abstention. Print the exact task ID and failed gate.

Use four clean cases and one unsafe-write case. Prove that good averages cannot override the mandatory stop. Then remove the violation and confirm that the same run passes.

This should take roughly twenty to thirty minutes.

### Practical takeaway

For one AI service, write down what happens at seventy, eighty-five, and ninety-five percent memory pressure.

Name what gets reclaimed, what spills, what degrades, what stops being admitted, and what condition authorizes a restart.

If the only documented response is an out-of-memory kill, the operating strategy begins too late.

### Closing recap

Kubernetes benchmarks show that fast local swap can dramatically increase density for dormant, bursty agent sandboxes, but active working sets still belong in RAM.

AWS CodeDeploy RESTART turns fleet recycling into a governed deployment with batches, hooks, alarms, validation, and history.

And the Playground Lesson built a memory-pressure hierarchy: reclaim, spill, degrade, defer, and restart.

The unfinished evaluator checkpoint remains unchanged.

That’s today’s Engineering Commute. Have a good Tuesday.

## Compact show notes

- **Kubernetes node swap — October 5, 2026:** Local-NVMe swap benchmarks for CI builds, browser sandboxes, and isolated Python runtimes; up to three-times density in the reported tests. [Kubernetes project article](https://kubernetes.io/blog/2026/10/05/scaling-kubernetes-workloads-with-node-swap/)
- **AWS CodeDeploy RESTART — October 5, 2026:** Reapplies the last successful revision with deployment batching, hooks, health validation, alarms, rollback settings, and audit history. [AWS announcement and technical walkthrough](https://aws.amazon.com/blogs/devops/restart-ec2-and-on-premises-fleets-faster-with-aws-codedeploy-restart-deployment-mode/)
- **Streaming status:** No newer substantive stable Apache Kafka or NATS Server release was found in the review window. [Apache Kafka downloads](https://kafka.apache.org/downloads) and [NATS Server releases](https://github.com/nats-io/nats-server/releases)
- **Playground:** [README and roadmap](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/README.md), [Module 03: inference pipeline](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/03_inference_pipeline.md), [Module 04: inference scheduling](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/04_inference_scheduling.md), [Module 13: capstone](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/13_capstone.md), and [latest repository commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d).
- **Checkpoint:** Create evals/score_run.py and evals/sample_run.jsonl; enforce hard stops for forbidden tools, invalid citations, and missed abstention. This is unchanged because those files remain absent.
- **Estimated runtime:** Approximately 15 minutes; about 2,200 spoken words.
