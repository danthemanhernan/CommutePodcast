# The Engineering Commute: Streaming Data Is the Nervous System, Not the Brain

Welcome back to The Engineering Commute, where we connect current engineering developments to systems you can build.

Today we are looking at one of the most useful architecture questions in applied AI: if an agent needs fresh operational data, should the agent go looking for that data, or should the data come to the agent?

The short answer is both, but not for the same information and not at the same time.

This week, AWS published an architecture discussion built around three patterns for combining streaming data with agentic systems. The patterns are streaming feature engineering followed by inference and action, event-driven agent invocation, and real-time context synchronization. The vendor-specific diagrams use services such as managed Kafka, Kinesis, Flink, Bedrock, and Iceberg tables. But the more important ideas are platform-independent.

They map cleanly onto industrial systems, observability platforms, and the kind of data-center digital twin you have been building.

Let’s start with the central distinction. A stream-processing system is good at continuously evaluating large numbers of small facts. An agent is good at reasoning across ambiguous context, selecting tools, and generating an adaptive response. Problems begin when we ask either component to impersonate the other.

You probably do not want a large language model evaluating every ten-millisecond vibration sample from every motor. That is expensive, slow, difficult to test, and unnecessary. A deterministic stream processor can calculate windows, rates of change, rolling distributions, correlations, and anomaly scores far more reliably.

At the other extreme, a hard-coded stream processor is not the best tool for interpreting a maintenance history, comparing several remediation options, checking operational constraints, and drafting a work order for a human.

Think of the streaming layer as the nervous system. It senses continuously and transmits structured signals. The agent is a higher-level decision layer. It wakes up when the signal deserves reasoning.

The first architecture pattern is a continuous path from feature engineering to inference to action.

Raw events arrive from equipment, applications, or users. A stateful processor groups those events into useful features. For a motor, those features might include a ten-minute rolling vibration average, temperature slope, current imbalance, start count, and deviation from the asset’s normal operating envelope. Those features feed a conventional machine-learning model or a generative model. The result then drives an action such as ranking an alert, changing a recommendation, or creating an explanation.

At the same time, the feature stream should usually flow into durable analytical storage. That second path matters because serving and learning have different time horizons. The online path needs low latency. The historical path needs reproducibility, backfills, model evaluation, and comparison across weeks or months.

This is a powerful design principle: compute a feature definition once, but make it useful to both the immediate decision path and the historical learning path.

The hard part is consistency. If the feature used during training is subtly different from the feature computed in production, the model learns one world and operates in another. Engineers call this training-serving skew. A shared feature definition, versioned schemas, event-time processing, and repeatable backfills help reduce it.

Event time deserves emphasis. The moment an event arrives at your stream processor is not necessarily the moment the measurement occurred. Network loss, buffering, gateway reconnects, and clock problems can deliver old telemetry late. If your rolling window uses arrival time without thinking, a delayed batch can appear to describe the present.

For industrial data, carry the source timestamp, ingestion timestamp, asset identity, quality code, and schema version as first-class fields. Decide how much lateness the system will tolerate. Then make the late-data behavior visible instead of silently discarding inconvenient facts.

The second pattern is event-driven agent invocation.

Here the stream processor does not invoke an agent for every event. It continuously detects a condition, assembles a context package, and publishes a higher-value event that causes the agent to run.

Suppose a cooling pump in a data center shows rising vibration while discharge pressure falls and motor current increases. Any one signal might be noise. A stream-processing job can correlate the three signals across a window, compare them with baseline behavior, and emit a pump-degradation event only when the combined condition crosses a threshold.

The event should not say only, pump anomaly equals true. It should include the evidence the agent needs: the asset identifier, detection time, contributing signals, current values, baseline values, recent maintenance, confidence, and links or identifiers for deeper retrieval.

The stream processor is the detector. The context package is the handoff contract. The agent is the responder.

This separation gives you several advantages. You can tune anomaly logic without rewriting the agent. You can improve the agent’s response tools without changing every detector. You can replay historical detection events through a newer agent version. And you can test each boundary independently.

The handoff contract needs a lifecycle, not just a JSON shape. An anomaly can be detected, enriched, acknowledged, investigated, resolved, or dismissed as a false positive. Model those as explicit events or state transitions. Do not repeatedly mutate one ambiguous record until nobody can reconstruct what happened.

Schema evolution matters here. Version one of an event may contain a temperature and threshold. Version two may add baseline statistics and confidence. A consumer written for version one should either continue working with the fields it understands or reject the event clearly. Additive, optional fields are usually easier to evolve than changing the meaning or type of an existing field. If a meaning must change, publish a new version and define the migration deliberately.

The schema registry is only part of the contract. Semantics live in documentation and tests. State whether temperature uses Celsius, where event time comes from, what confidence means, and whether a missing value means unavailable, not applicable, or zero. Controls engineers already understand this through tag naming, engineering units, quality bits, and alarm philosophy. Event contracts need the same discipline.

But the moment an agent can act, reliability becomes more important than cleverness.

Assume the invocation event will be delivered more than once. A consumer may crash after creating a work order but before acknowledging the message. The broker redelivers it, and the agent tries to create a second work order. This is not an edge case. It is the normal consequence of at-least-once delivery.

Every action needs an idempotency strategy. Use a stable incident identifier derived from the detection event. Before creating an external resource, check whether that identifier has already been processed. Store the action result durably. If the agent retries, return the existing result instead of repeating the side effect.

Also separate recommendations from commands. An agent that summarizes evidence and proposes an intervention has a different risk profile from one that changes a setpoint. For physical equipment, begin with a human approval boundary. Even when you later automate low-risk actions, encode allowed actions, operating ranges, time limits, rollback behavior, and interlocks outside the language model.

The model can choose from safe tools. It should not define what safe means at runtime.

Now we reach the third pattern: real-time context synchronization.

An agent can be reactive. It starts with minimal state and calls databases, APIs, or Model Context Protocol servers whenever it needs information. This is flexible and keeps the prompt small, but each call adds latency, failure modes, authentication boundaries, and cost.

Or an agent can be proactive. Important state is continuously synchronized into a context store so the agent begins with a current picture of the system. Change-data capture can publish database changes. Telemetry streams can maintain current asset summaries. Maintenance events can update an asset timeline. When the agent is invoked, much of the expensive gathering work has already happened.

The choice is not all or nothing. Use synchronized context for information that changes frequently, is requested often, and materially affects fast decisions. Use on-demand retrieval for large, rare, sensitive, or authoritative data that should be fetched only when needed.

For example, keep the current operating state, recent alarms, rolling features, and open incident identifiers in a low-latency context store. Fetch the full maintenance manual through an MCP tool only when the diagnosis requires it. Fetch the authoritative work-order status from its source system before taking a new action. Do not copy every document and database row into a giant memory layer just because you can.

This brings us to a subtle point: agent memory is a projection, not the source of truth.

A projected state can be stale, incomplete, or built from an event that later gets corrected. Attach freshness metadata and source identifiers. Define which system is authoritative for each field. Give the agent a way to refresh critical facts before acting. If the context says a breaker is open but the live control system says it is closed, the control system wins.

Corrections are especially important in event-driven systems. You may receive a measurement with the wrong quality code, a maintenance record may be backdated, or an upstream service may reverse a status. Decide whether the correction replaces a prior event, appends a compensating event, or triggers a complete rebuild of the projection. The answer depends on the domain, but silence is not a strategy.

For an operational audit trail, append-only facts plus explicit corrections are often easier to reason about than destructive updates. For a low-latency dashboard, a compacted current-state view may be more practical. Keep both when the use case needs both: the log explains how you arrived here, while the projection answers what is true now.

The event backbone helps because it gives multiple consumers the same sequence of facts. An operations dashboard, anomaly detector, historical lakehouse, digital twin, and agent-context builder can each maintain a view suited to its job.

This does not mean every event bus is interchangeable.

Kafka is a strong fit when you want partitioned, retained logs; independent consumer groups; replay; high-throughput analytics; and a durable history that can rebuild projections. NATS JetStream is attractive when you want a simpler messaging fabric, flexible request-reply and pub-sub, work-queue patterns, low operational overhead, and durable streams without committing every use case to the Kafka ecosystem.

The decision should follow semantics. Ask whether a new consumer must replay months of history. Ask whether ordering is required per asset, per site, or globally. Ask how you will handle redelivery. Ask whether the stream is primarily a historical record, a work queue, or a transport layer. Ask who will operate it at two in the morning.

Recent NATS improvements illustrate how these categories can overlap. NATS Server 2.14 added first-class support for higher-throughput publishing into JetStream and extended server-side message scheduling, while also fixing correctness issues for stream sourcing and mirroring. Kafka has also been expanding beyond its log roots with production-ready share-group behavior in recent releases. Product boundaries move. Your required semantics remain the stable decision point.

There is also a useful operational lesson in a new Amazon Managed Streaming for Kafka feature. MSK can now configure custom advertised domain names through one validated cluster property for both ZooKeeper and KRaft-based provisioned clusters. The practical value is stable indirection. Clients can keep a customer-controlled naming layer while the underlying brokers scale, migrate, or participate in disaster recovery.

But the release also reinforces a recurring infrastructure truth: DNS is not the network. Before brokers advertise the custom address, the load balancer, certificate trust, routing, security groups, and name resolution must already work. Changing the advertised listener first can disconnect clients as soon as they refresh metadata.

That sequence is a good analogy for agent systems. Do not advertise a capability before the trusted execution path exists. Build the boundary, identity, observability, and rollback path first. Then allow the agent to use it.

Here is your practical build challenge for this episode.

In your data-center digital-twin project, define one event called cooling anomaly detected. Give it a stable incident identifier, asset identifier, event time, ingestion time, schema version, contributing measurements, baseline values, confidence score, and a list of evidence references.

Publish that event to Kafka or JetStream. Build one consumer that writes the event to historical storage and another that creates an agent-ready context package. Make the second consumer idempotent. Then have the agent produce only a recommended response, not an automatic control command.

Finally, simulate three failures: deliver the event twice, deliver it late, and remove one referenced data source. If the system remains understandable and avoids duplicate side effects, you have learned more about production agents than you would by building a more impressive prompt.

Today’s takeaway is this: streaming systems should decide when something deserves attention and should assemble the facts. Agents should reason about those facts and select bounded tools. Durable logs should preserve what happened. Context stores should accelerate common decisions without pretending to be the source of truth. And physical actions should remain behind deterministic safety constraints.

Streaming data is the nervous system. The agent is not the entire brain, and it definitely should not be the safety circuit.

That is your Engineering Commute. In the next episode, we can go deeper on event schemas, idempotency keys, and how to evolve a context package without breaking old consumers.
