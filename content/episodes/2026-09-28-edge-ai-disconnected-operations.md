# The Engineering Commute — September 28, 2026

## Narration-ready episode

Good morning, Dan.

Today’s Engineering Commute is about designing an AI system that keeps doing useful work when the cloud is slow, unreachable, or simply not allowed into the control loop.

AWS has published a decision framework for running one Kubernetes standard across connected factories, intermittently connected sites, air-gapped plants, and greenfield edge locations.

GitHub has separated pull-request review time into three measurable stages, giving us a clean example of why end-to-end averages rarely identify the constraint.

Then, in the Playground Lesson, we’ll build an edge-AI operating model: local authority, desired and observed state, store-and-forward data, reconciliation after an outage, model versioning, and safe fleet rollouts.

I checked the AI Systems Engineering Playground through GitHub. The repository is still at its September ninth commit. The two evaluator files remain absent, so the existing checkpoint stays exactly the same. No new task will be added.

### Segment one: one Kubernetes API does not mean one operating model

First, the reported facts.

On September twenty-fifth, AWS published a framework for selecting an Amazon EKS deployment model at the edge.

Its proposal separates the platform standard from the physical deployment model. The common standard is Kubernetes: the API, manifests, container images, engineering skills, and delivery pipeline. The deployment model changes according to the site.

AWS describes four points on the spectrum.

EKS Anywhere runs a customer-managed control plane and is intended for air-gapped sites or environments with disconnected, disrupted, intermittent, or limited connectivity.

EKS Hybrid Nodes attach customer-owned bare-metal machines or virtual machines to an AWS-managed control plane. This requires reliable connectivity to the AWS Region. Existing workloads continue running during a brief disconnection, but scheduling and control-plane operations wait for the connection to return.

EKS on AWS Outposts places AWS-delivered hardware at the site and can support locations without suitable existing infrastructure. At the fully connected end, ordinary EKS can run in an AWS Region or Local Zone.

All four approaches use the same EKS distribution and Kubernetes APIs, although supporting storage, networking, load balancing, and management responsibility differ. AWS recommends gating first on connectivity. For connected sites, the next decision is whether suitable infrastructure already exists. It also notes that EKS Anywhere and Hybrid Nodes are Linux-only for on-premises workers, while some Outposts configurations support Windows workers.

Now, the engineering analysis.

The useful idea is not that every plant should buy the same AWS product. It is that connectivity is a hard architectural input, not an implementation detail.

If a conveyor diagnostic service must operate during a wide-area outage, a cloud-hosted control plane cannot be part of its immediate availability chain. The already-running pod may survive, but a failed node cannot ask the remote scheduler for a replacement. A new model cannot be pulled from a registry it cannot reach. A token cannot be refreshed from an unavailable identity service.

This resembles a PLC continuing its downloaded program after the engineering workstation disconnects. Runtime execution and engineering control are separate paths. Losing the engineering station should not stop the scan cycle, but it does change what can be reconfigured, diagnosed, or restored.

Standardized manifests help portability, yet a manifest alone does not make two sites operationally equivalent. A connected distribution center and an air-gapped factory need different answers for artifact distribution, certificate rotation, telemetry buffering, secrets, time synchronization, backup, and break-glass access.

So standardize the workload contract, then document the failure contract for each site class.

### Segment two: GitHub measures where review time actually accumulates

The second development comes from GitHub on September twenty-fifth.

Here are the reported facts.

Enterprise and organization repository-level Copilot usage reports now include a pull-request review-times array. For qualifying pull requests, it reports the median and ninetieth percentile for three intervals: ready-for-review to first review, first review to final review, and final review to merge.

The first release measures pull requests opened by a person and reviewed by at least one other person. Copilot, bot, and author reviews are excluded from the timing population. The data is attributed to the day the pull request merged, and GitHub is not backfilling older history. A day with no qualifying merge produces an empty array, not a zero. A pull request with one review records zero minutes between first and final review.

Now, the analysis.

This is basic flow instrumentation done correctly.

An end-to-end merge time is like reporting only total cycle time for a manufacturing cell. It tells you that output is late, but not whether parts waited before inspection, circulated through rework, or sat finished because downstream material handling was unavailable.

The three GitHub stages correspond to three different queues.

Time before first review reflects reviewer discovery, assignment, and available capacity. Time from first to final review reflects feedback quality, change size, test duration, and rework. Time from final review to merge reflects branch policy, release windows, ownership, and deployment readiness.

Each constraint needs a different intervention. Adding an AI reviewer will not fix an approved pull request waiting two days for a release train. Relaxing a merge rule will not help work that nobody has opened.

Median and ninetieth percentile also belong together. The median describes the normal path. The ninetieth percentile exposes the long tail where large, risky, cross-team, or abandoned changes accumulate. Optimizing only the median can make the dashboard look healthy while the changes most likely to cause coordination problems remain stuck.

Be careful with the denominator. Because the first release counts only human-authored, human-reviewed work, it cannot by itself measure whether agent-generated pull requests improve total delivery flow. The population definition is part of the metric. An empty array is missing activity, not instantaneous review.

The broader lesson applies directly to AI pipelines: divide latency into queue time and service time at each boundary. Measure retrieval, tool authorization, model inference, human approval, and action execution separately. A single end-to-end number cannot tell you which station is constrained.

### Playground Lesson: operating edge AI through disconnection

Let’s design the operating model for a factory AI assistant.

Start by separating the control plane from the data plane.

The control plane declares what should run: software version, model digest, configuration, permissions, rollout group, and health policy. The data plane performs local work: collect signals, run inference, retrieve approved documents, and produce a bounded recommendation.

In controls terms, the control plane is the engineering and commissioning layer. The data plane is the runtime panel executing the validated program. Cloud connectivity may update the program, but it should not be required for every scan.

Next, classify every site by connectivity instead of using the vague label edge.

A reliably connected site can depend on a remote control plane for scheduling, identity, and fleet management, as long as the consequences of a brief loss are understood.

An intermittently connected site must tolerate hours or days without coordination. It needs local artifact caches, renewable or offline-verifiable identity, bounded local queues, and explicit reconnection behavior.

An air-gapped site needs an entirely local control plane and a controlled transfer process for images, models, signatures, policies, and audit exports.

Now define local authority.

An edge model may classify a weld image, summarize alarms, or propose a maintenance check. Deterministic software should enforce which tags it can read, which tools it can invoke, and whether any output may influence equipment. The safety PLC remains independent.

Write an autonomy budget for disconnected operation. It should state how long the service may continue, which data may become stale, which actions remain allowed, and what condition forces degradation or shutdown.

For example, a diagnostic assistant may continue reading cached manuals and live local tags for twenty-four hours. It may not close a work order without the central system. If its model attestation or authorization expires, it can still display raw measurements but must stop producing recommendations.

The next pattern is desired state versus observed state.

The fleet controller says site seven should run application version twelve, model digest A-B-C, and policy version nineteen. The site reports what is actually running. A reconciler compares the two and attempts safe convergence.

That sounds like Kubernetes because it is the same feedback-loop pattern as a temperature controller: compare setpoint with process value, calculate error, and apply a bounded correction. But software reconciliation must handle versions, dependencies, and irreversible changes.

Do not assume the newest desired state should always win immediately after reconnection. The site may have produced local data under the old schema. The new model may require a preprocessing version the site does not have. A queued command may have expired while offline.

Reconciliation therefore needs preconditions. Confirm artifact signatures, disk space, runtime compatibility, policy version, schema migration state, and rollback availability before changing the local workload.

For telemetry, use store-and-forward rather than pretending the network is continuous.

Write events to a durable local outbox before attempting delivery. Give each event a stable identifier, asset identifier, event timestamp, schema version, and monotonic sequence within its source. Acknowledgment from the upstream consumer advances the local checkpoint. Retries reuse the same identifier so the destination can deduplicate them.

This is the same discipline you would use with Kafka or JetStream: at-least-once delivery means duplicates are normal, not exceptional. Exactly-once business behavior comes from idempotent processing and a clearly defined effect boundary.

Bound the queue. When storage approaches its limit, choose deliberately between dropping oldest low-value telemetry, reducing sample rate, retaining alarms and state changes, or stopping ingestion. Silent disk exhaustion is not a buffering strategy.

Model deployment needs an equally explicit contract.

Address models by immutable digest, not a mutable latest tag. Bundle or reference the tokenizer, preprocessing code, expected input schema, calibration metadata, evaluation result, and compatible runtime. Sign the package and verify it locally before activation.

Roll out by rings: laboratory, one noncritical site, a small representative group, then the wider fleet. Health gates should include service availability, resource consumption, inference latency, abstention rate, input drift, and task-specific quality. Keep the previous known-good package locally so rollback does not depend on the same network path that delivered the failure.

Finally, design observability for absence.

Local logs, metrics, traces, model decisions, and audit records need bounded persistence. On reconnection, upload summaries and high-value evidence first, then bulk telemetry. Preserve event time separately from arrival time so an outage does not make yesterday’s alarm appear to have happened now.

Commands flowing in the opposite direction need expiry and replay protection. A cloud instruction generated while the site was unreachable may be unsafe by the time connectivity returns. Include a command identifier, creation time, deadline, target state, and preconditions. The local executor should reject an expired command or one whose preconditions no longer match, then report the rejection instead of trying to make history line up with an old plan.

Also distinguish convergence from consistency. A fleet can eventually converge on one software version without every site seeing updates simultaneously. That is often acceptable for diagnostics. It is not acceptable when two services exchange data under incompatible schemas. Define which interfaces require coordinated change, use backward-compatible formats where possible, and stage producers before retiring old consumers. The network outage then delays convergence without corrupting the contract.

During commissioning, disconnect the site deliberately. Restart a workload, fill the local queue, rotate the desired model, restore the link, and observe the reconciliation sequence. A design that has never been tested offline has only an assumption of resilience.

The key principle is simple: disconnection is a mode the system enters, not an exception it hopes never happens.

### Playground checkpoint — unchanged

The repository still does not contain `evals/score_run.py` or `evals/sample_run.jsonl`, so this remains the only assigned checkpoint. Do not add another task until these files appear in GitHub.

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

Compute diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. Emit either pass or stop.

Make these mandatory stop conditions: a forbidden tool call, an invalid citation, or a missed required abstention. Print the exact task ID and failed gate.

Use four clean cases and one unsafe-write case. Prove that good averages cannot override the mandatory stop. Then remove the violation and confirm that the same run passes.

This should take roughly twenty to thirty minutes.

### Practical takeaway

Choose one edge service and write its disconnected-mode contract in four lines: how long it may operate, what authority remains, what data it buffers, and what condition forces it to degrade.

If those answers exist only implicitly in code, the system is not ready for a real network outage.

### Closing recap

AWS’s new edge framework separates a common Kubernetes standard from site-specific deployment models, with connectivity as the first hard gate.

GitHub’s review metrics divide delivery delay into three queues and report both normal and tail behavior.

And the Playground Lesson applied both ideas to edge AI: separate control from runtime, declare an autonomy budget, reconcile desired and observed state, use a durable idempotent outbox, deploy immutable model packages through rings, and preserve local evidence during disconnection.

At the edge, resilience does not mean pretending the cloud is always present.

It means knowing exactly what the site can safely do when it is not.

That’s today’s Engineering Commute.

Have a good Monday.

## Compact show notes

- **Amazon EKS edge strategy — September 25:** AWS separates the Kubernetes standard from four deployment models and recommends gating first on connectivity, then matching connected sites to existing infrastructure. [AWS Containers article](https://aws.amazon.com/blogs/containers/one-amazon-eks-many-edges-how-to-choose-your-edge-container-strategy-on-aws/) and [EKS Hybrid Nodes documentation](https://docs.aws.amazon.com/eks/latest/userguide/hybrid-nodes-overview.html).
- **GitHub pull-request review metrics — September 25:** Repository reports now expose median and p90 time for ready-to-first-review, first-to-final-review, and final-review-to-merge, with explicit population and empty-day semantics. [GitHub changelog](https://github.blog/changelog/2026-09-25-usage-metrics-api-adds-pull-request-review-stages/).
- **Playground status:** No commits after September 9; the evaluator artifacts remain absent. [README](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/README.md), [roadmap](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/docs/roadmap.md), [agents module](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/10_agents_workflows.md), [capstone module](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/13_capstone.md), [labs overview](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/labs/README.md), and [current commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d).
- **Checkpoint:** Create the two missing evaluator files, prove that an unsafe-write case forces a stop, then fix that same case and confirm the run passes. No additional task is assigned.
- **Estimated runtime:** Approximately 15 minutes; narration target is about 2,200 spoken words.
