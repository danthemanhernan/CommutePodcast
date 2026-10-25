# The Engineering Commute — September 21, 2026

## Narration-ready episode

Good morning, Dan.

Today’s Engineering Commute is about routing at two different scales.

At the application boundary, a model router chooses which model should handle a request. Inside a Mixture-of-Experts model, a learned router makes a much faster and finer-grained decision: which parameter blocks should process each individual token.

Those systems sound similar, but they solve different problems, operate at different time scales, and fail in different ways.

We’ll start with one concise current development from Ollama and one implementation signal from SGLang. Then the main lesson goes deep on Mixture-of-Experts architecture: sparse activation, top-k routing, capacity factors, expert parallelism, all-to-all communication, load balance, determinism, and the metrics that tell you whether the system is healthy.

I also checked the AI Systems Engineering Playground. The repository has not changed since the September ninth curriculum expansion, and the evaluator checkpoint is still not present. So there is no new capstone task today. The existing checkpoint stays exactly the same.

### Current development: model capabilities are becoming machine-readable

First, the reported facts.

On September nineteenth, Ollama published version zero-point-thirty-four-point-three release candidate one.

This is a release candidate, not a final production release, and its change list is small.

The most relevant change is that the model-inspection API can now advertise a model’s thinking controls and its default thinking setting. The release also adds Nemotron H vision support through MLX on Apple Silicon, along with fixes for the macOS window and some model pulls.

Now the engineering analysis.

The interesting part is not a new user-interface switch. It is that a serving system can expose a capability as structured metadata.

Imagine an application router choosing among several models. One request needs a fast extraction model. Another requires a reasoning mode. A third contains an image. If the router depends on a hardcoded table maintained separately from the serving runtime, that table can drift from reality.

Machine-readable capability metadata gives the routing layer a better discovery mechanism. It can ask what a model says it supports instead of relying entirely on naming conventions or configuration copied by hand.

But discovery is not verification.

A model reporting that it supports vision, tools, or thinking controls is like a field device publishing its identity and supported function blocks. That tells the controller which commands may be meaningful. It does not prove the device is calibrated, the command is safe for this process, or the measured performance meets the application requirement.

An application router should combine capability metadata with policy and measured evidence.

Does the model support the required input type?

Is it approved for this data classification?

Has it passed the relevant golden tasks?

Does it meet the latency and cost envelope under current load?

Is this capability enabled in the deployed version, rather than merely present in a model family?

That distinction connects directly to the evaluator checkpoint in the Playground. Metadata may decide which candidates are eligible. A deterministic gate still decides whether the observed run is acceptable.

### Current implementation signal: MoE routing is numerically sensitive

Yesterday’s SGLang release was already covered for distributed inference, so I will not repeat that story. One different detail from the same release is useful for today’s lesson because it exposes a real Mixture-of-Experts failure mode.

The reported facts are these.

SGLang zero-point-five-point-twenty includes several MoE-specific changes. It keeps routing weights in thirty-two-bit floating point for deterministic inference, corrects a routing underflow and renormalization problem in DeepSeek V4, and includes fixes involving expert-parallel buffers and top-k expert identifiers.

The release also introduces a FlashInfer MegaMoE backend. In one vendor-reported DeepSeek V4 Flash benchmark, SGLang reports as much as eleven-point-nine percent higher prefill throughput than the comparison runner at a particular long-sequence configuration. That is one selected implementation benchmark, not a general performance guarantee.

Now the analysis.

Routing looks like a small classifier, but a small numeric change near a decision boundary can select a different expert.

Suppose two experts receive almost equal router scores. Quantization, reduced precision, a changed reduction order, or an underflow during normalization can reverse their order. With top-two routing, the selected pair changes. That sends the token to different weights, potentially changes the output, changes the load on two devices, and may change later tokens through the autoregressive sequence.

In a conventional dense layer, a small rounding change usually perturbs the same computation. In sparse expert routing, the change can alter which computation happens at all.

That is why routing precision, stable top-k selection, and deterministic communication deserve first-class attention. The router is not merely an optimization hint. It is part of the model’s functional path.

## Playground Lesson: Mixture-of-Experts from routing decision to cluster behavior

The AI Systems Engineering Playground’s Module Five combines speculative decoding and Mixture-of-Experts serving. We covered speculative decoding earlier this month. Today we complete the other half.

Start with the dense transformer.

A transformer block normally contains attention and a feed-forward network. Attention mixes information across token positions. The feed-forward network then applies learned transformations to each token position independently.

In a dense model, every token passes through the same feed-forward weights in that layer. If the feed-forward network contains billions of parameters, all of those relevant weights participate for every token.

A Mixture-of-Experts layer replaces that one feed-forward network with several alternative feed-forward networks called experts. A small learned router scores the experts for each token. Only the selected expert, or small set of experts, processes that token.

The word expert can be misleading. An expert is usually not a complete model with a clean label such as electrical engineering, Python, or Spanish. It is a parameter block whose specialization emerges during training. Researchers can sometimes observe patterns, but the boundaries may be distributed, overlapping, and unstable across layers.

Think of a manufacturing line with a bank of specialist process cells.

Every part passes the shared inspection and transport system. At one station, a classifier directs the part to one or two specialist cells. The plant owns all of the cells, but one part activates only a few of them.

That is the central bargain of MoE.

The model can contain many more total parameters than it activates for one token. This can expand model capacity without increasing arithmetic per token in direct proportion to the total parameter count.

But sparse compute does not mean free capacity.

All expert weights still need to exist somewhere in memory. Tokens must be dispatched to the devices holding their chosen experts. Outputs must return to the original token order. Some experts may receive too much work while others sit idle. Communication, memory capacity, and load imbalance can become the real constraints.

### The router operates per token

For each token representation, the router produces a score for every expert in that layer. A softmax or related normalization can turn the scores into routing weights. The system chooses the highest-scoring expert or experts.

With top-one routing, each token goes to one expert.

With top-two routing, each token goes to two experts, and their outputs are combined using routing weights.

Top-two routing can provide a richer signal and some resilience, but it roughly doubles expert work and dispatch volume compared with top one. The precise cost depends on implementation, batching, and hardware utilization.

The same prompt may be split across many experts. A token representing an equipment identifier may route differently from a token representing a causal relationship. The next layer makes a new decision using the token’s updated representation.

This is fundamentally different from the request-level router we discussed two days ago.

An application router might send an entire maintenance question to a small model, a large reasoning model, or a vision model. That decision occurs once, or a few times, for a request. It can consider business policy, price, latency, user tier, and data sensitivity.

An MoE router lives inside one model. It executes at multiple layers for every token. It is learned with the model, normally invisible to the application, and must operate at accelerator speed.

The application router is like dispatching a work order to the correct plant.

The MoE router is like directing every component through specialist cells inside that plant.

### Sparse activation changes the resource equation

Suppose a layer has eight experts and uses top two. The model owns eight feed-forward parameter blocks, but each token activates only two.

That does not mean the token costs exactly one quarter of a dense model with all eight blocks combined. The router adds work. Dispatch and collection add work. Small expert batches may use matrix hardware inefficiently. Communication can dominate arithmetic. Padding and reserved capacity can waste space.

The useful distinction is between total parameters and active parameters.

Total parameters influence storage, accelerator memory, checkpoint size, load time, and how many devices are required to hold the model.

Active parameters influence much of the arithmetic performed for a token.

An MoE model may therefore offer a high total parameter count with a smaller active-compute footprint. But the cluster must still host the complete model and move tokens to the correct experts.

This is similar to a factory owning ten specialized machines while each product visits only two. The processing time per product depends on two machines, but the factory still pays for the floor space, maintenance, utilities, and availability of all ten.

### Capacity is a queueing problem

The router does not naturally promise equal traffic.

During one batch, a common pattern or language may send many tokens to the same expert. That expert becomes a hot station. Other experts may receive little work.

Training and serving systems often define an expert capacity: the number of tokens an expert can accept for a batch or routing group.

A simplified capacity formula starts with the average tokens per expert and multiplies it by a capacity factor.

If a routing group contains eight thousand token assignments and eight experts, the average is one thousand assignments per expert. A capacity factor of one-point-two reserves space for about twelve hundred per expert.

That extra twenty percent absorbs ordinary imbalance. It also consumes memory and may require padding.

If an expert receives more tokens than its capacity, the implementation needs an overflow policy.

It may drop excess assignments.

It may reroute them to the next-best expert.

It may send them through a shared fallback path.

It may increase dynamic buffers and accept a latency penalty.

Each choice changes model quality, determinism, memory use, or tail latency.

This looks like queueing at a set of unequal service stations. Average plant utilization can be low while one critical machine has a long queue. Looking only at total accelerator utilization can hide the bottleneck.

You need the distribution.

How many tokens reached each expert?

What was the maximum-to-mean load ratio?

How many tokens overflowed, were dropped, or used a secondary route?

How long did the slowest expert take?

How much capacity was reserved but unused?

The tail expert determines when the synchronization point can complete.

### Training tries to prevent route collapse

If the router discovers that one expert is slightly better early in training, it may send more tokens there. That expert then receives more learning signal and improves faster. The feedback loop can cause route collapse: a few experts dominate while others remain poorly trained.

MoE training commonly adds an auxiliary load-balancing objective. The goal is to discourage extreme concentration and encourage useful utilization across experts.

There is a tension here.

Perfectly uniform routing is not necessarily desirable. If every expert receives exactly the same mixture of tokens, specialization may weaken. But unrestricted specialization can overload a small subset of experts and waste the rest of the model.

The objective is not equality for its own sake. It is productive specialization within a serviceable load envelope.

Controls engineers will recognize the pattern. You are not forcing several parallel pumps to run at precisely the same instantaneous flow regardless of efficiency. You are preventing one pump from operating beyond its safe region while the others contribute nothing.

Router regularization, expert capacity, and routing policy form a control strategy around a learned dispatch mechanism.

### Expert parallelism turns routing into network traffic

A large MoE model rarely fits every expert on every accelerator. Expert parallelism places different experts on different devices.

Consider eight accelerators, each holding one expert for a layer. The incoming token representations begin distributed across the workers according to the preceding computation. The router decides that tokens currently on device one need experts on devices three, five, and seven.

The system performs an all-to-all exchange.

Each worker groups token representations by destination and sends them to the workers holding the selected experts. Each expert processes its received microbatch. A second communication phase returns the outputs so the model can restore token order and continue.

This is not ordinary request traffic. It is a high-volume shuffle inside the forward pass.

The networking analogy is a switch fabric with traffic patterns created by learned classification. A hot expert resembles an oversubscribed destination. Link bandwidth, topology, collective implementation, and message size affect end-to-end token latency.

Expert placement matters.

If commonly co-activated experts sit behind the same constrained link, traffic concentrates there. If expert replicas are available, the system may route to a local or less-loaded copy, but that changes memory use and possibly numerical behavior.

On a single server, high-bandwidth accelerator interconnect may make dispatch manageable. Across servers, the same pattern encounters slower links, more variable latency, and larger failure domains.

The useful metric is not merely model FLOPS. Measure bytes dispatched per generated token, time spent in all-to-all collectives, expert computation time, and the fraction of the step waiting for the slowest rank.

### Batching helps arithmetic and can hurt balance

Serving engines batch tokens so accelerators can process larger matrices efficiently. In dense models, increasing the batch often improves hardware utilization until memory or latency limits intervene.

In an MoE model, batching also creates expert microbatches. If the batch contains diverse tokens, work may spread reasonably across experts. If many requests share a domain or repeated prefix, routing may concentrate.

Two batches with the same token count can therefore have different latency.

One distributes cleanly and produces large, efficient expert matrices.

The other sends forty percent of assignments to one expert, forcing overflow, additional buffers, or a synchronization wait.

That means an MoE scheduler may eventually need routing-aware decisions, not just token-count limits. At minimum, capacity planning should test different prompt populations: code, multilingual text, tool traces, structured extraction, long repeated prefixes, and the industrial documents the application actually uses.

Average benchmark prompts may conceal the traffic pattern that matters in production.

### Routing precision can change behavior discontinuously

Now return to the SGLang implementation signal.

Suppose the router scores expert three at zero-point-three-zero-zero-one and expert seven at zero-point-two-nine-nine-nine. Reduced precision rounds both values. A different tie-breaking order selects expert seven.

That is a discontinuity.

A tiny numeric perturbation does not merely adjust a weighted sum. It changes the selected parameter block.

Quantizing expert weights and quantizing router calculations are therefore different decisions. Expert matrix multiplication may tolerate low precision after calibration. Router logits near the top-k boundary may need more precision or stable ordering to preserve routes.

Renormalization matters too. With top-two routing, the selected expert weights may be normalized again after selection. Underflow or an incorrect normalization changes their relative contribution. In an autoregressive model, a small difference can alter a later sampled token, after which the sequences diverge naturally.

Determinism requires attention to router precision, top-k kernels, tie behavior, collective reductions, token ordering, and capacity overflow. Setting one random seed is not sufficient.

### What to observe in production

An MoE service needs the familiar request metrics: time to first token, inter-token latency, throughput, queue time, errors, memory use, and cost.

It also needs router and expert metrics.

Track assignments per expert by layer.

Track the maximum, minimum, mean, and coefficient of variation.

Track routing entropy. Very low entropy may indicate collapse or a narrow workload. Very high entropy may indicate weak specialization, depending on the model and layer.

Track capacity utilization, overflow, dropped tokens, fallback routes, and padding waste.

Track expert compute time and all-to-all communication time separately.

Track bytes moved across device and server boundaries.

Track route stability for a fixed evaluation set across runtime, kernel, quantization, and model-version changes.

Finally, correlate routing health with output quality.

A perfectly balanced router can still produce poor answers. A highly skewed router may be correct for a specialized workload. Operational metrics identify stress; evaluation determines whether the system still meets the application objective.

For the Factory AI Engineer capstone, you probably do not need to implement an MoE layer. The practical value is knowing what may be happening inside a hosted or open model and why two serving stacks can behave differently with the same nominal weights.

If a model upgrade changes diagnosis quality or latency, investigate more than the model name. Ask whether quantization changed, whether router precision changed, whether expert parallel placement changed, and whether the workload is creating hot experts.

The capstone’s external contract remains the same: evidence-grounded diagnosis, valid citations, bounded tools, required abstention, and measurable latency. Internal model sophistication does not relax that contract.

### Playground checkpoint — unchanged

The repository still does not contain `evals/score_run.py`, so repeat the existing checkpoint exactly. Do not add another task to the backlog.

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

Compute diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. Emit either pass or stop.

Make these mandatory stop conditions: a forbidden tool call, an invalid citation, or a missed required abstention. Print the exact task ID and failed gate.

Use four clean cases and one unsafe-write case. Prove that good averages cannot override the mandatory stop. Then remove the violation and confirm that the same run passes.

This remains the right next step because it establishes the capstone’s protective relay. Model routing, MoE routing, and serving optimizations can change performance, but none may bypass a hard safety trip.

### Practical takeaway

For any routing system, record four things separately:

The candidates that were eligible.

The scores that drove selection.

The capacity or policy constraints that modified the selection.

And the observed quality after execution.

That pattern works for an application model router, an MoE layer, a work-cell dispatcher, or a redundant control strategy. Without those four views, a routing failure looks like random downstream behavior.

### Closing recap

Ollama’s release candidate exposes thinking controls as model metadata. That can improve model discovery, but advertised capability still needs policy and measured verification.

SGLang’s recent MoE fixes illustrate why routing precision, normalization, top-k stability, and expert-parallel buffers are part of model correctness as well as performance.

And in the Playground Lesson, Mixture-of-Experts models trade dense activation for learned token-level routing. They can offer large total capacity with fewer active parameters per token, but the savings introduce expert memory, dispatch traffic, queue imbalance, overflow policy, and new observability requirements.

The engineering principle is simple:

Sparse computation does not eliminate work. It changes where the work appears.

And the capstone checkpoint remains unchanged until the evaluator exists and proves that mandatory safety gates override attractive averages.

That’s today’s Engineering Commute.

Have a good Monday.

## Compact show notes

- **Ollama v0.34.3-rc1 — September 19:** Release candidate adds structured reporting of model thinking controls and defaults, Nemotron H vision support through MLX on Apple Silicon, and several fixes. [Primary release notes](https://github.com/ollama/ollama/releases/tag/v0.34.3-rc1)

- **SGLang v0.5.20 — September 18:** MoE-related work includes FP32 routing weights for deterministic inference, routing normalization fixes, expert-parallel corrections, and the FlashInfer MegaMoE backend. This is included only as an implementation example for the lesson; the broader release was covered previously. [Primary release notes](https://github.com/sgl-project/sglang/releases/tag/v0.5.20)

- **Playground curriculum:** [Course roadmap](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/README.md), [Module 5: speculative decoding and MoE](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/05_speculative_moe.md), [labs overview](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/labs/README.md), [capstone specification](https://github.com/danthemanhernan/AiSystemsEngPlayground/tree/main/capstone), and [latest repository commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d).

- **Checkpoint — unchanged:** Create `evals/score_run.py` and `evals/sample_run.jsonl`; calculate quality, evidence, citation, tool-call, and latency metrics; hard-stop on forbidden tools, invalid citations, or missed abstention; demonstrate that one unsafe case stops the run before correcting it.

- **Estimated spoken runtime:** Approximately 25 minutes.

