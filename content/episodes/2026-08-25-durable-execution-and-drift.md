---
title: The Engineering Commute — August 25, 2026
date: 2026-08-25
status: ready
topics:
  - durable execution
  - infrastructure drift
  - infrastructure operations
  - AI systems engineering
sources: []
---

# The Engineering Commute — August 25, 2026

Good morning, Dan.

Today’s Engineering Commute is about something that shows up everywhere from Kafka consumers to AI agents:

**What state should survive when execution stops?**

We’ll look at AWS’s new durable-function architecture and why it sits somewhere between ordinary serverless functions and a workflow engine.

Then we’ll look at infrastructure drift—why GitOps and infrastructure-as-code only work when the declared state remains authoritative.

After that, we’ll move into high-performance engineering infrastructure and examine what semiconductor tape-out teaches us about observability, capacity planning, and the cost of waiting.

And in the Playground Lesson, we’ll move forward from yesterday’s attention discussion into tokenization and next-token generation.

The important shift today is this:

Yesterday we looked inside the transformer.

Today we start looking at what actually enters and leaves it.

Kafka and NATS JetStream remain quiet on meaningful new releases, so there’s no reason to manufacture a messaging announcement. Instead, several of today’s stories expose distributed-systems principles that apply directly to Kafka, JetStream, backend services, and agent workflows.

Let’s start with durability.

## Segment one: Serverless functions are learning how to remember

AWS published a new technical walkthrough over the weekend for Lambda durable functions.

Here are the reported facts.

The problem AWS describes is familiar: a multistep application performs some work, waits on another operation, encounters a failure, and must decide whether to restart everything or somehow resume from the last successful point.

Traditional Lambda functions are intentionally ephemeral.

If execution ends, local process state disappears. Developers building longer workflows therefore need to externalize progress into a database, queue, object store, or orchestration system.

AWS’s durable-functions model adds durable execution semantics so application code can suspend, preserve progress, and resume rather than manually rebuilding the entire workflow from scratch.

AWS contrasts this with Step Functions, which remains a more explicit workflow-orchestration service.

Now the engineering interpretation.

This is fundamentally a checkpointing problem.

Imagine a five-stage pipeline:

Receive a document.

Extract its contents.

Call a model.

Wait for human approval.

Then write the final result.

If stage four fails after the expensive model call, restarting from stage one wastes compute and potentially repeats side effects.

The correct recovery point is after stage three.

That is exactly the same reason stream processors checkpoint state.

A Kafka consumer may have processed ten thousand events, updated local aggregates, and advanced internal state.

If it crashes, you do not want to reconstruct the entire application lifetime from zero unless replay is deliberately part of the design.

You restore from a known checkpoint and replay the bounded interval after it.

But durable execution introduces a subtle constraint:

Code that can be replayed must distinguish deterministic computation from external side effects.

Suppose your workflow reaches:

Charge credit card.

Then crashes before recording that the charge completed.

If the runtime replays that step naïvely, the customer gets charged twice.

Or consider an industrial workflow:

Create maintenance work order.

Crash.

Replay.

Create another work order.

Durability does not remove idempotency requirements.

It makes the boundary clearer.

A useful design is to classify each step into one of three categories.

Pure computation.

Durable state transition.

External side effect.

Pure computation is generally replay-safe.

Durable state transitions need versioning and consistency.

External side effects need an idempotency key or a reconciliation mechanism.

That same framework works for agents.

Suppose a troubleshooting agent:

Reads an alarm.

Queries the historian.

Retrieves a maintenance manual.

Creates a diagnosis.

Requests human approval.

Then creates a work order.

The reasoning stages can often be recomputed.

The work-order creation cannot casually be repeated.

So persist an action identifier before execution and make the downstream API recognize repeated requests as the same logical operation.

The architectural decision between a durable function and an explicit workflow engine should come down to visibility and complexity.

If the workflow is mostly application code with waits, retries, and a manageable number of steps, durable functions can reduce orchestration boilerplate.

If business users need to inspect the state machine, if many independent services participate, or if branching and compensation logic become complex, an explicit workflow engine can remain easier to reason about.

The controls analogy is a PLC sequence.

You can encode a sequence as procedural logic with retained step state, or represent it explicitly as a state machine.

Both can work.

But once the sequence becomes complicated enough, explicit state usually becomes easier to diagnose.

The key question is not “Can this function run longer?”

It is:

**Can I reconstruct exactly which logical actions have happened after a crash?**

That is the real durability contract.

## Segment two: Infrastructure-as-code is useless if nobody notices drift

AWS also recently published a practical guide around CloudFormation drift detection and the transition from so-called ClickOps toward governed infrastructure-as-code.

The reported problem is straightforward.

Cloud environments often begin with resources created manually through a console, CLI, or SDK.

Later, teams introduce CloudFormation, Terraform, or another infrastructure-as-code system.

But manual modifications continue.

The declared configuration and the actual environment gradually diverge.

That divergence is drift.

Now for the engineering analysis.

This problem should feel extremely familiar if you have worked with PLCs.

Imagine having an offline PLC project that says a timer is five seconds.

An engineer goes online during troubleshooting and changes the live value to eight seconds.

Production improves.

Nobody updates the source project.

Three months later, another engineer downloads the official project.

The timer silently returns to five seconds.

The problem was not that online editing exists.

The problem was that nobody reconciled the running state with the authoritative state.

Cloud infrastructure has the same failure mode.

Your Git repository might say:

Three replicas.

One security group.

A particular IAM policy.

A specific database configuration.

But someone fixes an incident at two in the morning by modifying the live environment.

Now there are two truths.

Git says what should exist.

The cloud says what does exist.

A mature infrastructure workflow must eventually force reconciliation.

That does not mean banning emergency manual changes.

Sometimes emergency intervention is correct.

It means manual changes need a lifecycle.

Detect.

Attribute.

Review.

Then either codify or revert.

This is where drift detection becomes much more useful when connected to CI/CD.

Imagine a scheduled GitHub Actions workflow.

Once per day, it checks infrastructure drift.

If nothing changed, it records success.

If drift appears, it creates an issue or pull request containing:

The affected resource.

Expected value.

Actual value.

Time detected.

Recent deployment information.

And perhaps the relevant CloudTrail actor.

Now drift becomes an observable event instead of tribal knowledge.

There is an interesting agent opportunity here as well.

An agent could inspect the difference and classify it.

Was this likely emergency remediation?

An autoscaling side effect?

A console change?

A deployment bug?

Then it could propose either an IaC patch or a revert.

But the agent should not automatically normalize every difference.

Some resources contain runtime-managed fields.

Others are intentionally mutable.

The deterministic layer needs to define which properties constitute meaningful drift.

Again, intelligence belongs above a clear contract.

For industrial infrastructure, the same pattern could eventually apply to edge gateways, container configurations, OPC UA connectors, data collectors, and even controller configuration snapshots.

Desired configuration goes into version control.

Observed configuration is collected automatically.

A reconciler identifies differences.

And human-approved automation closes the loop.

That is GitOps in its most general form:

Not Kubernetes specifically.

A control system for configuration.

## Segment three: Semiconductor tape-out is an extreme lesson in queueing economics

AWS published another useful piece around semiconductor electronic-design-automation workloads and chip tape-out.

This is not a new cloud service.

It is an operational case study.

AWS describes verification regressions where infrastructure failures can add days to a chip schedule, highly variable compute demand during tape-out crunch periods, expensive design intellectual property, and environments where incident response and capacity planning have direct consequences for product delivery.

AWS’s Unified Operations offering assigns persistent specialists around these workloads and advertises incident response within five minutes for covered critical infrastructure.

Ignore the sales packaging for a moment.

The engineering lesson is excellent.

EDA workloads demonstrate what happens when compute becomes part of the critical path of physical product development.

Imagine ten thousand verification jobs waiting for CPU or accelerator capacity.

If compute capacity is insufficient, engineers wait.

If storage throughput collapses, CPUs wait.

If a regression fails unnoticed on Friday night, the entire project waits.

This means utilization alone becomes a terrible optimization metric.

Suppose cluster A runs at ninety-five percent utilization but verification jobs spend six hours queued.

Cluster B runs at sixty-five percent utilization but begins high-priority regressions immediately.

Which one is more efficient?

If one day of tape-out delay costs vastly more than the unused compute, cluster B may be economically superior.

This is the same reason factories intentionally maintain buffer capacity around bottleneck processes.

Maximum utilization and maximum throughput are not synonymous.

Queueing theory becomes increasingly important in AI infrastructure for the same reason.

GPU fleets are expensive, so everyone wants high utilization.

But driving every accelerator toward one hundred percent occupancy can increase queueing latency and make bursty high-priority workloads wait.

The correct objective might instead be something like:

Maximize useful completed work per dollar,

subject to a maximum queueing delay for priority workloads.

That is a constrained optimization problem.

For data centers, you can extend it again.

A cluster may have GPU capacity but insufficient power headroom.

Or sufficient power but a network bottleneck.

Or enough hardware but a scheduler that creates fragmentation.

So productive compute is constrained by the minimum capacity across several interacting systems.

Power.

Cooling.

Network.

Storage.

Accelerator memory.

Scheduler placement.

And application behavior.

That is why modern AI infrastructure increasingly looks less like ordinary web hosting and more like industrial capacity engineering.

## Playground Lesson: tokens are the actual units your model sees

Now let’s move into today’s Playground Lesson.

I checked the AI Systems Engineering Playground again for this episode.

The repository currently has one initial commit, and the roadmap explicitly progresses from transformer internals into tokenization and next-token generation.

The Module Two learning goals include BPE and SentencePiece tokenization, logits, softmax, temperature, top-k and top-p sampling, greedy decoding, and hallucination mechanics.

There is already a token-inspector lab in the repository.

It deliberately uses a tiny educational tokenizer so it works offline.

And this is the right place to begin.

When you type:

“industrialization”

the model does not necessarily receive one object called industrialization.

It might receive something conceptually closer to:

“industrial”

plus

“ization.”

Another tokenizer may divide it differently.

The model operates on token IDs.

Those IDs map into embedding vectors.

Everything we discussed yesterday about attention operates on the resulting token representations.

So tokenization is effectively the input encoding layer for the entire model.

Think of a PLC analog input.

The physical system may contain pressure.

But the controller does not directly manipulate the physical concept of pressure.

It receives a numerical representation through an input channel.

The representation affects everything downstream.

Tokens serve a somewhat similar role.

Human language is transformed into a discrete vocabulary that the neural network can process.

Modern tokenizers usually operate using subword units.

Why not just tokenize words?

Because the vocabulary would explode.

You would need separate entries for:

run.

running.

runner.

rerun.

And every unusual identifier, product name, code symbol, typo, and language variation.

Why not individual characters?

Because sequences become much longer.

Subword tokenization is a compromise.

Common patterns get compact representations.

Rare words can still be decomposed into known pieces.

This has direct systems consequences.

API pricing is usually token-based.

Context limits are token-based.

KV-cache consumption grows with tokens.

Prefill work depends heavily on input token count.

Decode produces tokens sequentially.

So two strings containing the same number of characters can have very different inference costs.

Code is a good example.

A compact-looking stack trace containing UUIDs, hexadecimal strings, paths, and unfamiliar identifiers can tokenize much less efficiently than ordinary English.

Industrial tag names can do the same thing.

Imagine:

LINE4_ST20_WELD_CURRENT_ACTUAL.

Depending on the tokenizer, that may become several tokens.

Now multiply that across ten thousand historian records placed into a prompt.

Suddenly the formatting of your data representation affects inference cost.

This is one reason you should not casually dump raw telemetry into an LLM.

Normalize and summarize first.

Now we move from input to output.

After the transformer processes the context, the final layer produces a number for every token in the vocabulary.

These raw scores are called logits.

If your vocabulary contains fifty thousand tokens, you effectively receive fifty thousand scores representing the model’s current preference for the next token.

Softmax turns those scores into a probability distribution.

Suppose a toy model predicts:

“alarm” at sixty percent.

“motor” at twenty percent.

“current” at fifteen percent.

And everything else shares the remaining five percent.

Greedy decoding always chooses the highest-probability token.

That makes generation deterministic for a fixed model and state.

Sampling instead draws from the distribution.

That introduces variation.

Temperature modifies the shape of that distribution.

Lower temperature sharpens it.

High-probability options dominate more strongly.

Higher temperature flattens it.

Less likely options become easier to select.

Top-k says:

Only consider the k highest-probability tokens.

Top-p says:

Consider the smallest set of tokens whose cumulative probability reaches some threshold, such as ninety-five percent.

This is important because generation is not the model retrieving a completed answer from memory.

It repeatedly performs:

Context.

Compute next-token distribution.

Select token.

Append token.

Repeat.

That loop explains both the power and fragility of language models.

A plausible early token changes the context for every subsequent prediction.

If the model begins an unsupported explanation confidently, later tokens are conditioned on that invented premise.

The generation can become internally coherent while remaining externally wrong.

That is one mechanism behind hallucination.

It is not simply a database lookup returning a bad row.

It is probabilistic continuation without sufficient grounding.

Your checkpoint for today should take fifteen to thirty minutes.

Run the existing token inspector.

Then add these three strings:

A normal English sentence about a motor fault.

A realistic industrial tag name with underscores and numbers.

And a compact JSON event containing an asset ID, timestamp, and alarm code.

Compare token counts.

Then open the sampling lab and run the same toy logits repeatedly under:

Greedy decoding.

Low temperature.

High temperature.

Top-k.

And top-p.

Write down one sentence explaining which settings you would prefer for:

Creative writing.

A troubleshooting assistant.

And deterministic structured extraction.

If you understand why those answers differ, you understand the practical purpose of sampling controls.

## Practical takeaway

Today’s challenge is to identify one workflow in which you are relying on execution rather than durable state.

Ask:

If this process crashes at the worst possible line of code, what work repeats?

Which repeated actions are harmless?

Which create duplicate side effects?

And where is the authoritative checkpoint?

That could be a Kafka consumer.

A GitHub Action.

An agent workflow.

A database migration.

Or a factory-data ingestion service.

Design recovery before optimizing throughput.

## Closing recap

Today’s durable-function story reminds us that reliability is ultimately about reconstructing state after failure, not simply keeping a process alive.

Infrastructure drift shows that declarative automation only works when differences between desired and actual state are continuously reconciled.

Semiconductor tape-out demonstrates why maximum utilization is often the wrong infrastructure objective. Queueing delay and business criticality can justify deliberate headroom.

And in the Playground, we moved one step deeper into the LLM runtime.

Human text becomes tokens.

Tokens become vectors.

The model produces logits.

Softmax creates a distribution.

Sampling selects the next token.

And that selected token becomes part of the next control cycle.

Tomorrow, that sets us up perfectly for the next systems-level question:

Why is processing the prompt fundamentally different from generating the response?

That’s where prefill, decode, and eventually KV cache enter the picture.

That’s today’s Engineering Commute.

Have a good Tuesday.
