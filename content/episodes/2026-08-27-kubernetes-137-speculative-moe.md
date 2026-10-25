# The Engineering Commute --- August 27, 2026

## Kubernetes 1.37, Fault Injection, and Speculative Decoding

### Narration-ready episode

Good morning, Dan.

Today's Engineering Commute is about testing assumptions before
production tests them for you.

Kubernetes version one-point-thirty-seven has shipped with meaningful
changes for AI workloads, identity, autoscaling, and observability.
Google Cloud has introduced managed fault injection. And Google is
proposing more structured packaging of trusted organizational knowledge
for agents.

### Segment one: Kubernetes is learning to schedule complete AI workloads

Kubernetes 1.37 includes gang scheduling graduating to beta. Kubernetes
can treat a group of tightly coupled pods as one schedulable workload
and admit the group only when sufficient resources exist for all of it.

Workload-aware preemption lets the scheduler reason about the complete
pod group that needs to run. Dynamic Resource Allocation continues to
mature, while HPA scale-to-zero support reaches beta.

Gang scheduling fixes a costly partial-start condition. If distributed
training requires eight GPU workers and only six start, the workload may
make zero progress while consuming six GPUs.

The common theme is progress-aware scheduling: allocate capacity
according to the conditions required to complete useful work.

### Segment two: High availability is only real after a controlled failure

Google announced Fault Injection Testing in public preview. It supports
Cloud SQL failover and degraded Layer Seven application traffic through
injected latency or HTTP errors.

Many systems have high-availability architecture without verified
high-availability behavior. A diagram shows redundancy, but the first
actual failover may reveal stale connections, synchronized retries, or
hidden local state.

Chaos engineering should follow the same discipline as commissioning:
define the expected response before injection, limit scope, establish
abort conditions, capture synchronized telemetry, and convert the result
into a repeatable test.

### Segment three: Agents need governed context

Google describes Open Knowledge Format as an open specification for
packaging contextual knowledge used by agents. Trust signals include
provenance, verification, freshness, and attestation.

Agent knowledge needs the same treatment as production data: version it,
test it, observe it, and retire it deliberately.

### Playground Lesson: speculative decoding and Mixture of Experts

Speculative decoding adds a smaller draft model. The draft quickly
proposes several tokens. The large target model evaluates that sequence
in parallel and accepts the draft tokens that agree.

The target model remains authoritative. Acceptance rate is central.

Mixture of Experts attacks a different cost. An MoE layer contains
multiple expert networks plus a router. For each token, the router
selects a small number of experts rather than activating all of them.

The difficult part is routing balance. If most tokens choose the same
expert, that expert becomes a bottleneck. When experts live on different
GPUs, token routing also becomes network traffic.

Your checkpoint is to build a toy draft-and-verify decoder, measure
acceptance and target-model calls, then simulate top-two routing across
eight experts and quantify imbalance.

### Closing recap

Kubernetes 1.37 improves progress-aware scheduling. Fault injection
turns HA assumptions into evidence. Agent context is becoming governed
data. And speculative decoding plus MoE show two different ways to
reduce inference cost: generate more tokens per target pass, or activate
fewer parameters per token.

### Show notes

-   Kubernetes 1.37:
    https://kubernetes.io/blog/2026/08/26/kubernetes-v1-37-release/
-   Fault Injection Testing:
    https://cloud.google.com/blog/products/networking/introducing-google-cloud-fault-injection-testing-in-preview
-   OKF and Knowledge Catalog:
    https://cloud.google.com/blog/products/data-analytics/scale-okf-bundles-across-an-organization-with-knowledge-catalog
-   Playground:
    https://github.com/danthemanhernan/AiSystemsEngPlayground
