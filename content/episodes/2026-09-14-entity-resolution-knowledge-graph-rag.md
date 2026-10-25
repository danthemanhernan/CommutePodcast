# The Engineering Commute --- September 14, 2026

## Knowledge Graph RAG, Entity Resolution, and Deduplication

### Narration-ready episode

Good morning, Dan.

Today's Engineering Commute is centered on a problem that shows up
everywhere once an AI system moves beyond a demo: how do you know when
two pieces of information represent the same real-world thing?

That sounds simple until the same motor appears as `MTR-401`,
`Motor 401`, `Line4_Weld_Motor`, and an asset GUID from the maintenance
system. Or the same maintenance bulletin appears as a PDF, an email
attachment, a SharePoint copy, and a paragraph copied into a work
instruction.

Today we'll use three fresh developments as the short news section. AWS
published a unified knowledge-graph RAG architecture combining GraphRAG
and LightRAG over one shared stack. Google Cloud's managed MCP servers
now support the newer 2026-07-28 Model Context Protocol version. And
GitHub Copilot has added configurable cost-versus-quality tiers to
automatic model selection.

Then we'll spend the bulk of the episode on the evergreen lesson:
deduplication, entity resolution, identity, provenance, and why these
concepts become foundational once RAG, agents, graphs, and industrial
data all meet.

At the end, I checked the AI Systems Engineering Playground and the
capstone checkpoint. There is still no repository evidence that the
current evaluation-gate task has been completed, so there will be no new
task today. The checkpoint remains exactly the same.

### News segment one: AWS puts GraphRAG and LightRAG behind one retrieval backbone

Here are the reported facts.

On September fourteenth, AWS published an open-source reference
implementation called Unified Knowledge Graph RAG on AWS. The project
combines Microsoft-style GraphRAG and LightRAG.

The shared infrastructure uses Amazon Bedrock for model operations,
Neptune for graph storage, OpenSearch for lexical and vector retrieval,
DynamoDB for optional incremental-indexing state, and S3 for source
documents and resumable pipeline artifacts.

The interesting architectural choice is that the retrieval method can
change per query without rebuilding the entire corpus. The system
combines lexical retrieval, semantic vector retrieval, and graph
traversal. Those ranked results are fused, optionally reranked,
assembled into a token-budgeted context, and then passed to generation.

AWS also built incremental indexing around content hashes. Unchanged
documents can be skipped. New or changed documents are reprocessed, and
per-document lineage is used when merging or deleting graph artifacts.

The benchmark results in the post show an important tradeoff. On the
specific multi-hop datasets AWS tested, the most accurate strategies
were considerably more expensive and slower than a simpler local graph
strategy. AWS explicitly cautions that these rankings are
workload-specific and should be reproduced against your own corpus.

Now the engineering interpretation.

The headline is not that GraphRAG has replaced ordinary RAG. The useful
idea is that retrieval topology should match question topology.

If I ask, "What does alarm E forty-two mean?", the answer may live in
one manual paragraph. Lexical or vector retrieval can be enough.

If I ask, "Which downstream processes depend on the station affected by
this controller fault?", the answer is not necessarily one paragraph. It
may be a path: controller to station, station to operation, operation to
product, product to order.

That is a graph-shaped question.

But the moment we create that graph, we inherit a harder problem. What
exactly is a node?

If one data source says `Robot_17`, another says `RB17`, and another
says `KUKA cell A robot`, should the graph contain three robots or one?

That brings us directly to today's main lesson.

### News segment two: model and tool routing are becoming explicit policies

Google Cloud's MCP release notes say its managed Google and Google Cloud
MCP servers now support version 2026-07-28 of the Model Context
Protocol. Google says the changes are backward compatible with the
2025-11-25 version.

This matters because MCP is increasingly behaving like infrastructure
rather than a novelty integration layer. Protocol versions, identity
policies, tool-level authorization, telemetry, and compatibility now
need the same lifecycle discipline you would apply to an API contract.

GitHub, meanwhile, added three configurable tiers to Copilot automatic
model selection: efficiency, balance, and intelligence.

All three tiers draw from the same available model pool. The difference
is the optimization objective. Efficiency leans toward lower cost.
Balance considers cost, latency, and quality together. Intelligence
prioritizes quality more heavily.

A model router is a controller. The prompt is the process input.
Candidate models are available actuators with different response
characteristics. Cost, latency, and quality are competing controlled
variables. And the routing policy is effectively the tuning strategy.

A single fixed model is analogous to running every operating condition
through one actuator setting because it worked during commissioning.

Routing becomes more valuable as workloads become heterogeneous. But
both stories reinforce a deeper principle: once an AI system has
multiple tools, models, documents, and data sources, identity becomes
critical.

Which tool version ran? Which model produced the result? Which document
revision supplied the evidence? Which asset did a tag actually refer to?
Which apparently different records are really duplicates?

## Evergreen lesson: deduplication and entity resolution for AI systems

Let's start by separating two concepts that are often thrown into one
bucket.

Deduplication asks: are these records effectively the same record?

Entity resolution asks: do these different records refer to the same
real-world entity?

They overlap, but they are not identical.

Imagine your historian receives this event twice: line four, weld
station twelve, current equals eight-point-two kiloamps, timestamp
twelve-oh-three and fourteen seconds, sequence number
eight-eight-four-one.

If the second copy came from a retry after a network timeout, that is a
duplicate event.

Now imagine your CMMS contains an asset named `WELDER-12`, your PLC uses
`WS12`, and a maintenance manual calls it "Line 4 Weld Cell Number 12."

Those are not duplicate records. They are different records describing
the same entity.

For duplicate events, you often want idempotency. For entity resolution,
you want canonical identity plus provenance.

### The controls analogy: signal conditioning before control

Think about a noisy analog instrument.

Before you use a pressure transmitter in a control loop, you establish
what physical variable it represents, its engineering units, range,
calibration, timestamp behavior, and failure state.

You would not wire three transmitters into the same controller,
accidentally discover that two of them are actually the same physical
sensor exposed through different gateways, and then average all three as
independent measurements.

That would double-count one source.

Data systems make this mistake constantly. An AI system makes the
consequences more visible because duplicated or misidentified evidence
changes the model's context.

Suppose a maintenance bulletin says a firmware revision can cause
nuisance trips. Your ingestion system finds four copies: the original
PDF, a SharePoint mirror, an email attachment, and a technician's copied
text note.

A naive vector search may retrieve all four because they are highly
relevant. The model then sees four apparently independent pieces of
evidence supporting the firmware hypothesis.

Nothing in the language model inherently knows that this is one source
echoed four times.

You have created false evidence density.

The problem is similar to wiring the same pressure signal into four
channels and telling an estimator that four independent instruments
agree.

### Exact duplicate detection

The easiest case is byte-identical content.

Hash the content. SHA-256 is a common choice.

If two files produce the same cryptographic hash, treat their content as
identical for practical ingestion purposes.

But notice the exact wording: content identity.

The files may still have different provenance. One came from the OEM
portal. One came from an employee's desktop. One came from an archived
ticket.

You usually want one canonical content object with several
source-location records pointing to it.

A useful schema separates `document_content_id` from
`source_instance_id`.

The content ID answers, "What information is this?" The source-instance
ID answers, "Where did we observe it?"

If the SharePoint copy disappears, you should not necessarily delete the
canonical document if the OEM source still exists.

### Normalized duplicate detection

Exact hashes fail as soon as trivial formatting changes.

One PDF has a different timestamp in its metadata. One text extraction
inserts different whitespace. One document contains a footer saying
"Downloaded September fourteen."

The human meaning is unchanged, but the bytes differ.

So we normalize.

For text, normalization might include Unicode normalization, case
normalization where appropriate, whitespace collapse, standardized line
endings, removal of known boilerplate, and canonicalization of repeated
headers and footers.

Then hash the normalized representation.

Be conservative.

If you normalize too aggressively, distinct documents can collapse
together.

Imagine revision B changes one torque specification from forty
newton-meters to fifty. A bad normalizer that strips tables or numeric
formatting could decide revision A and revision B are duplicates.

That is catastrophic in an industrial knowledge system.

Normalize presentation noise, not domain meaning.

### Near-duplicate detection

Now suppose a work instruction contains ninety-five percent of an OEM
bulletin but adds one local safety step.

They are not identical. They are strongly related.

Common approaches include MinHash, locality-sensitive hashing,
shingling, SimHash, token overlap, or embedding similarity.

The important design decision is not the algorithm. It is what you do
with the result.

A similarity score should not automatically mean "delete one."

Near-duplicate detection often creates a relationship: `derived_from`,
`supersedes`, `local_adaptation_of`, or simply `near_duplicate_of`.

That relationship is valuable to retrieval.

If the query asks for the OEM specification, prefer the authoritative
OEM source. If it asks for the plant procedure, the local work
instruction may be more operationally relevant.

Same subject does not mean same authority.

### Entity resolution: canonical identity

Now move from documents to things.

Imagine five systems.

The PLC calls an asset `L4_WS12`. Ignition calls it `Line4/Weld12`. The
historian stores numeric equipment ID `18472`. SAP calls it
`WELD-CELL-012`. The manual says "Weld Cell 12, Line 4."

A human engineer recognizes these as one station. A computer needs an
identity model.

The simplest robust pattern is a canonical entity ID plus aliases.

For example, canonical asset ID `asset-00018472`.

Aliases include the PLC namespace, SCADA path, CMMS ID, and human label.

The canonical ID should ideally be stable and meaningless.

Do not encode mutable business facts into primary identity if you can
avoid it.

If you name the canonical entity `LINE4_WELD12`, what happens when the
machine moves to line five?

Identity should survive relocation and renaming.

That is similar to networking. An IP address tells you where an endpoint
is reachable right now. It is not necessarily the permanent identity of
the machine. DNS gives names another layer of indirection. Certificates
can establish cryptographic identity independently of network location.

Good entity models separate identity from current attributes.

### Deterministic matching first

Entity resolution does not need to begin with AI.

Start with deterministic identifiers: serial number, asset GUID, CMMS
primary key, manufacturer serial plus model, or an explicit
cross-reference table.

If two records share a trusted unique identifier, resolution is
straightforward.

This is your hardwired permissive.

Use fuzzy logic only when deterministic evidence is absent.

### Probabilistic matching second

Suppose the identifiers do not line up.

You have manufacturer, model, location, description, install date, IP
address, parent asset, and perhaps tag names.

You can score agreement.

Same serial number gets enormous weight. Same manufacturer and model
gets moderate weight. Same line and station is useful. Description
embedding similarity is useful but weaker. Same IP address may help, but
IPs can be reassigned.

Entity resolution can literally become a binary classification problem.

Features might include exact identifier match, normalized-name
similarity, Levenshtein distance, token overlap, location match,
parent-asset match, time overlap, embedding cosine similarity, and
conflicting attributes.

The label is match or non-match.

But production systems usually need three states: match, non-match, and
uncertain.

The uncertain state routes to human review.

That is analogous to alarm deadband. If evidence is comfortably above
the match threshold, merge. Comfortably below, keep separate. In the
ambiguous band, do not make an irreversible change automatically.

### Why false merges are usually worse than missed merges

This is an asymmetric-error problem.

Suppose the resolver fails to merge two aliases for the same pump. You
may retrieve redundant evidence or miss a cross-system connection.

Annoying, but recoverable.

Now suppose it incorrectly merges two physically different pumps.

Historian data, maintenance history, alarms, and documentation can
become attached to the wrong asset.

The AI may confidently recommend a repair based on another machine's
history.

That is much more dangerous.

Entity-resolution thresholds should reflect consequence, not merely F1
score.

In an industrial system, optimize for extremely low false-merge rates on
consequential entities.

You can tolerate a queue of unresolved candidates. You cannot casually
tolerate corrupted identity.

### Survivorship: when records disagree

After two records are linked to one entity, another question appears.

Which value wins?

SAP says the motor is thirty horsepower. The commissioning database says
twenty-five. The manual says thirty. Historian metadata says
twenty-five.

Do not simply take the latest value. Do not simply take the majority.

Define survivorship rules by field.

Manufacturer serial number may be authoritative from the asset registry.
Current location may be authoritative from commissioning or operations.
Maintenance status may come from the CMMS. Electrical rating may come
from the approved equipment specification.

And sometimes the correct output is: conflict unresolved.

The canonical entity should be able to retain contradictory claims with
provenance.

A language model should not receive one silently chosen value if
underlying systems disagree materially.

Give it claim, source, effective time, authority, and conflict state.

Then the application can say: "Two sources disagree on the motor rating.
The approved equipment specification lists thirty horsepower; historian
metadata lists twenty-five and may be stale."

That is safer than pretending data integration eliminated uncertainty.

### Deduplication inside RAG

A production RAG pipeline can deduplicate at several stages.

At ingestion, remove exact duplicate content while preserving source
instances.

During chunking, avoid indexing repeated headers, footers, navigation,
and boilerplate.

At retrieval, collapse near-identical chunks so top-k is not monopolized
by copies.

During context assembly, diversify evidence across sources, revisions,
and evidence types.

During generation, make citations point back to stable source
identities.

Imagine top-k equals eight.

Without deduplication, six slots could be different copies of one
service bulletin.

With diversification, the context might contain the bulletin, current
manual, historian event, prior incident, software release note, and
local work instruction.

That is a better measurement set.

This is why deduplication is not merely a storage optimization.

It changes epistemology.

It changes how much apparent support the model sees for a hypothesis.

### GraphRAG makes identity even more important

Knowledge graphs amplify both good and bad entity resolution.

Suppose the graph correctly resolves every alias for Weld Cell Twelve.

Now alarms, manuals, maintenance history, components, recipes, and
downstream dependencies can connect through one stable node.

That is powerful.

But if the resolver mistakenly merges Weld Cell Twelve with Weld Cell
Twenty-One because their descriptions are similar, graph traversal
spreads the error.

A false merge is no longer one bad row. It creates false paths.

Graph ingestion should preserve evidence for every edge and merge
decision.

For an entity merge, store which records were merged, which rule or
model version made the decision, the match score, important features,
timestamp, and whether a human confirmed it.

This gives you reversible identity.

If a merge is later found incorrect, you can split the entity and
rebuild affected relationships.

### Idempotency: deduplication for actions

There is another form of deduplication that matters for agents: side
effects.

Suppose an agent creates a maintenance ticket.

The API accepts the request and creates ticket 4811, but the response
times out.

The orchestrator does not know whether the action succeeded. It retries.

Now you have ticket 4812 describing the same incident.

The solution is an idempotency key.

The orchestrator generates a stable operation ID, perhaps based on the
incident and intended action. Every retry sends the same key.

The receiving service records that key with the first successful result.
A retry returns the existing result instead of executing the side effect
again.

This is deduplication in time.

Kafka producers, payment APIs, job schedulers, and agent tools all
encounter this pattern.

Exactly-once behavior is often not magic transport semantics. It is
identity plus state plus deterministic reconciliation.

### Streaming deduplication

Suppose an edge gateway buffers PLC events while disconnected.

Connectivity returns and it republishes the buffer. Meanwhile, another
path already delivered some events.

Your cloud consumer now sees duplicates.

You need an event identity.

A good event key might derive from source identity, boot or session
identity, sequence number, and event timestamp.

Timestamp alone is rarely enough. Two legitimate events can share a
timestamp. Sequence number alone can reset after a reboot.

The identity scheme must understand source lifecycle.

Then decide how long deduplication state must live.

If duplicates can arrive up to ten minutes late, perhaps the dedup store
needs a longer retention window.

If offline gateways can reconnect after two days, ten minutes is not
enough.

This is where event-time reasoning and operational behavior meet.

### Build the identity layer before the agent layer

A common AI architecture mistake is to begin with the agent because the
agent is visible.

But if the underlying identity model is weak, the agent is reasoning
over unstable reality.

Before increasing autonomy, answer these questions.

What is a document? What is a document revision? What is an asset? What
is an event? What is an incident? What is a user? What is a tool
execution? What is a model run? What is the stable ID for each? Which
systems are authoritative for which attributes? How are aliases
represented? How are merges reversed? How is provenance retained?

If these questions are answered well, RAG, graphs, observability,
evaluation, and agent memory all become easier.

### A concrete Factory AI Engineer example

The operator says: "Line four keeps faulting after lunch. Weld current
looks weird. What should I check?"

The agent queries alarms. The alarm adapter returns equipment key
`WS12`.

The historian returns tag path `L4.Weld12.Current`.

The maintenance system returns asset `WELD-CELL-012`.

The RAG system retrieves a manual mentioning "Weld Cell 12."

Entity resolution maps all four references to canonical asset
`asset-18472`.

Now the application can intentionally join those sources.

The historian says current began drifting at twelve-oh-five. The alarm
system shows overcurrent warnings beginning at twelve-oh-eight.
Maintenance history shows a loose secondary connection repaired six
months ago. The manual provides the approved inspection sequence.

The agent can now produce a grounded hypothesis because the data plane
established that these observations refer to the same physical station.

Next, retrieval returns three copies of the same service bulletin.

The context assembler collapses them into one canonical document but
retains three observed source locations.

It also retrieves a newer revision. Revision metadata marks the newer
one as authoritative.

The old bulletin is not deleted from history; it is excluded from
current procedural guidance.

Finally, suppose the agent recommends creating a maintenance ticket.

In the current Playground architecture, the capstone remains read-only,
so it cannot execute that action.

If write capability were added later, the ticket tool would need an
idempotency key so a retry could not create duplicates.

Notice what happened.

Deduplication was not one utility function.

Identity appeared in documents, assets, events, revisions, retrieval,
graph nodes, citations, and actions.

That is why identity becomes infrastructure.

### How I would implement this incrementally

Do not start with a giant master-data-management platform.

Start with explicit contracts.

For documents: `content_id`, `source_id`, `revision`, `effective_at`,
`authority`, and `content_hash`.

For assets: `canonical_asset_id`, `source_system`, `source_asset_id`,
`alias`, `valid_from`, and `valid_to`.

For events: `event_id`, `source_id`, `sequence`, `observed_at`, and
`ingested_at`.

For tool calls: `request_id`, `operation_id`, `tool_version`,
`arguments_hash`, and `result_id`.

Then implement deterministic resolution first.

Exact hashes. Explicit crosswalks. Trusted identifiers. Revision rules.

Add fuzzy resolution only where deterministic mappings fail.

Instrument it.

Track duplicate-content rate, near-duplicate candidate rate, automatic
entity-match rate, human-review rate, false-merge corrections,
unresolved alias count, retrieval duplicate ratio, and context-source
diversity.

Those metrics tell you whether the identity layer is helping or silently
degrading.

### The mental model to keep

Deduplication asks whether two observations are redundant.

Entity resolution asks whether two observations refer to the same thing.

Canonicalization chooses a stable representation.

Provenance remembers where each claim came from.

Survivorship decides which source is authoritative for a particular
attribute.

Idempotency prevents the same intended action from being executed twice.

These are one family of identity problems.

Modern AI systems intensify them because the model will synthesize
whatever context you give it.

If context double-counts evidence, the model can become overconfident.

If entities are incorrectly merged, the model can reason across false
relationships.

If revisions are not distinguished, it can cite obsolete instructions.

If actions lack idempotency, retries can produce real-world duplication.

Good AI integration begins by making identity boring and explicit.

## Playground checkpoint: unchanged until completed

I inspected the connected AI Systems Engineering Playground today.

The repository's most recent commit remains the September ninth
curriculum expansion. The current README defines the Factory AI Engineer
as the integrated capstone, and the capstone still calls for a golden
task set, evaluation results, threat model, SLOs, failure-injection
results, and operational evidence.

There is still no GitHub evidence that the current checkpoint has been
completed.

So there is no new assignment today.

The checkpoint remains exactly the same.

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

Use five mock runs.

Calculate diagnosis pass rate, required-evidence coverage, citation
validity, total tool calls, and latency.

Then implement hard, non-averaged stop gates.

If any run contains a forbidden tool call, stop.

If any citation references evidence that does not exist in that run's
allowed evidence set, stop.

If a task requires abstention and the system produces an actionable
diagnosis anyway, stop.

Print the exact task ID and the violated gate.

Use four clean cases and one intentionally unsafe case.

Confirm that excellent averages cannot override the safety failure.

Then remove the unsafe condition and confirm that the same scorer
passes.

That is still the task.

I am not adding deduplication work, graph ingestion, entity resolution,
or anything else to your capstone backlog until repository evidence
shows this checkpoint is complete or you deliberately decide to change
it.

The lesson sequence can continue while the implementation checkpoint
stays fixed.

### Practical takeaway

For one system you already work with, choose one important entity---an
asset, document, event, incident, or tool execution---and answer four
questions:

What is its stable identity?

Which aliases can refer to it?

Which source is authoritative for each important attribute?

And how would you detect an accidental duplicate or false merge?

If those answers are unclear, fix the identity contract before adding
more AI on top.

### Closing recap

AWS's new unified knowledge-graph RAG reference implementation combines
lexical, semantic, and graph retrieval while making strategy choice an
empirical workload decision.

Google Cloud's managed MCP servers now support the newer MCP protocol
version, reinforcing that agent tool interfaces need normal API
lifecycle discipline.

GitHub's configurable automatic model selection makes cost, latency, and
quality an explicit routing policy rather than an accidental
consequence.

And today's main lesson was identity.

Exact deduplication prevents repeated content from masquerading as
independent evidence.

Near-duplicate detection finds related material without automatically
erasing meaningful differences.

Entity resolution maps different system identifiers to stable real-world
entities.

Provenance preserves the origin of every claim.

Survivorship makes authority field-specific rather than arbitrary.

And idempotency prevents retries from creating duplicate side effects.

For industrial AI, this is foundational.

Before an agent can reason reliably about the factory, the data plane
has to agree on what the factory's things actually are.

And the capstone checkpoint remains unchanged: build the evaluation
scorer and prove that one unsafe run stops the release regardless of the
averages.

That's today's Engineering Commute.

Have a good Monday.

## Compact show notes

-   **Unified Knowledge Graph RAG on AWS --- September 14:**
    https://aws.amazon.com/blogs/opensource/unified-knowledge-graph-rag-on-aws-graphrag-and-lightrag-on-one-stack/
-   **Google Cloud MCP servers --- September 14:**
    https://docs.cloud.google.com/mcp/release-notes
-   **GitHub Copilot auto model selection --- September 14:**
    https://github.blog/changelog/2026-09-14-configure-cost-and-quality-in-copilot-auto-model-selection/
-   **Playground:**
    https://github.com/danthemanhernan/AiSystemsEngPlayground
-   **Roadmap:**
    https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/docs/roadmap.md
-   **Factory AI Engineer:**
    https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/projects/capstone_factory_ai_engineer/README.md
-   **Current repository commit:**
    https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d
-   **Checkpoint, repeated unchanged:** Create `evals/score_run.py` plus
    five mock JSONL runs. Measure diagnosis pass rate, required-evidence
    coverage, citation validity, tool calls, and latency. Enforce
    immediate stop gates for forbidden tool calls, invalid citations,
    and required-abstention failures.
-   **Estimated spoken runtime:** approximately 29--32 minutes, with the
    majority devoted to the evergreen AI/data-integration lesson.
