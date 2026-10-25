# The Engineering Commute — September 22, 2026

## Narration-ready episode

Good morning, Dan.

Today’s Engineering Commute is about the machinery underneath retrieval-augmented generation.

We often describe RAG as: embed the question, retrieve relevant chunks, and give them to the language model. That summary is correct in the way that saying a warehouse “stores and retrieves parts” is correct. It skips the engineering decisions that determine whether the right part arrives, how quickly it arrives, and whether the inventory record matches physical reality.

The current development is Milvus version three-point-zero-point-two, released September twentieth. Its changes make a useful case study because they touch filtered-search performance, admission control, index construction, streaming recovery, rolling upgrades, and several correctness failures.

Then the main Playground Lesson goes deeper: what an embedding represents, how cosine similarity differs from dot product and Euclidean distance, why approximate nearest-neighbor search exists, how HNSW and inverted-file indexes work, why filters complicate retrieval, and how to evaluate the retriever independently from the language model.

I checked the AI Systems Engineering Playground through GitHub. The README, modules, labs, and commit history are unchanged. The last commit is still the September ninth curriculum expansion, and `evals/score_run.py` still does not exist. The capstone checkpoint therefore remains exactly the same. We are not adding another task.

### Current development: Milvus 3.0.2 treats vector search like a complete data system

First, the reported facts.

Milvus released version three-point-zero-point-two on September twentieth.

The release focuses on search and query performance, external collections, Storage V2, streaming, compaction, index management, and stability.

For filtered search, Milvus says it removed an atomic reference-count hotspot that represented about forty-eight percent of leaf CPU time in one search path. It also pins a sealed-segment snapshot once per request to reduce repeated atomic and reference-count overhead.

The query planner can now merge chained array-membership predicates into a single contains-any or contains-all expression. Bloom-filter and Roaring-bitmap membership checks are exposed through one expression, including Go-client support.

Index building receives several changes. Milvus reports lower write amplification for Tantivy-based text, N-gram, and JSON-statistics indexes. It also fixes index jobs that could retry forever on malformed JSON instead of failing clearly and releasing resources.

At the service boundary, the REST query endpoints now apply admission control before decoding a request when the query queue is full. The service returns HTTP four-twenty-nine and a retry-after instruction.

For upgrades, a cluster-version gate delays a new write-before-materialization behavior until every node has completed the rolling upgrade. Milvus also added a compliance API that reports whether load configuration has converged globally and within each resource group.

Several fixes concern correctness rather than speed. The release addresses incorrect query results after a structured array field was dropped and re-added, incomplete binlog chunks that could be treated as fully read, duplicated sparse-vector rows in REST requests, and compaction behavior that could misalign packed-column indexes.

It also fixes a placement problem that could assign all replica channels to one query node, repeatedly exhaust that node’s memory, and leave the replica unavailable. Another fix addresses repeated write-ahead-log fencing that could stall writes for forty-five to sixty seconds every few minutes under sustained ingestion.

Finally, the release upgrades its Kafka client library to correct authentication failures against Kafka four-dot-x brokers.

Now the engineering analysis.

The release is a reminder that a vector database is not merely a fast cosine-similarity function.

It is a distributed data platform with query planning, scalar indexes, write-ahead logs, snapshots, compaction, placement, backpressure, rolling upgrades, and recovery semantics.

The forty-eight-percent CPU hotspot is especially revealing. The expensive step was not necessarily vector arithmetic. Bookkeeping around filtered search consumed a large share of leaf CPU time. This happens in many systems: the math attracts attention, but object ownership, synchronization, allocation, metadata filtering, and network movement determine production performance.

The admission-control change is equally important. If the queue is already full, decoding and allocating an entire request wastes resources while the system is overloaded. Rejecting early with a retry signal is analogous to stopping material at the plant entrance when downstream accumulation is full. Accepting more work does not increase throughput; it increases work-in-process, memory pressure, and recovery time.

The correctness fixes show why retrieval needs its own validation boundary. If a storage reader silently treats an incomplete chunk as complete, the search engine may omit the relevant record without returning an obvious error. The language model then receives plausible but incomplete evidence and answers confidently.

From the application’s perspective, that looks like a model hallucination. The actual cause is a data-path integrity failure.

That distinction leads directly into today’s lesson.

## Playground Lesson: embeddings, vector indexes, and filtered retrieval

Module Eight in the Playground covers RAG and context engineering. We previously discussed the overall industrial RAG pipeline, chunking, citations, entity resolution, and knowledge graphs. Today we isolate the retrieval stage and study it as an instrument.

The key principle is this:

A retriever does not find truth. It ranks stored candidates according to a mathematical and operational contract.

If that contract is poorly chosen, the answer generator never sees the evidence it needs.

### What an embedding actually is

An embedding model converts an input into a vector: an ordered list of numbers.

A text model might convert a maintenance instruction into several hundred or several thousand floating-point values. Those values locate the instruction in a learned high-dimensional space.

Nearby vectors are intended to represent inputs that the model considers related according to its training objective.

That final phrase matters.

An embedding is not an objective coordinate system for meaning. It is a measurement produced by a particular model, version, preprocessing method, and input format.

The dimensions usually do not have stable human labels. Dimension one is not “temperature,” dimension two is not “motor,” and dimension three is not “severity.” Meaning is distributed across the vector.

Think of a vibration signature from a machine. A spectrum is a numeric representation of the signal. Distance between spectra can reveal similar operating conditions, but the representation depends on sensor placement, sample rate, windowing, and preprocessing. Change the measurement chain and distances change.

Embeddings work similarly. Changing the embedding model is closer to replacing the measurement system than updating an ordinary library.

You should version the model name, revision, dimensions, normalization behavior, preprocessing, chunk text, and timestamp. A query vector and document vector must be compatible. Mixing vectors from unrelated embedding spaces is like comparing a temperature measured in Fahrenheit with a control limit defined in Celsius, except the conversion may be unknown.

### Similarity is a design choice

Once you have vectors, you need a distance or similarity function.

Three common choices are cosine similarity, dot product, and Euclidean distance.

Cosine similarity measures the angle between vectors. It largely ignores magnitude and asks whether they point in similar directions.

Dot product combines direction and magnitude. Two aligned vectors receive a larger score when their magnitudes are larger.

Euclidean distance measures straight-line distance between points.

If every vector is normalized to unit length, cosine similarity and dot product produce equivalent rankings, and squared Euclidean distance is directly related to them. Without normalization, they can rank candidates differently.

Do not select a metric because cosine is fashionable. Use the metric expected by the embedding model, then validate it on the application.

Imagine two maintenance passages.

One says, “High weld current may result from low circuit resistance.”

Another repeats the word “current” many times in a long electrical specification.

Depending on the model and normalization, vector magnitude can influence ranking in ways that are useful, irrelevant, or harmful. The model documentation gives the starting contract. A labeled retrieval set tells you whether it works.

The numeric score itself is not a universal confidence value. A cosine score of zero-point-eight does not inherently mean eighty-percent relevance. Score distributions vary by model, domain, chunk length, language, and corpus density.

Calibrate thresholds using real queries and labeled evidence. Also inspect the gap between the first and later candidates. A high top score in a uniformly dense neighborhood may be less informative than a moderate score that is clearly separated from the rest.

### Exact search versus approximate search

The simplest vector search compares the query with every stored vector and sorts the results.

That is exact nearest-neighbor search.

For ten thousand chunks, exact search may be entirely reasonable. It is easy to understand and gives a useful ground-truth baseline.

For hundreds of millions of vectors, scanning every vector for every query becomes expensive. Approximate nearest-neighbor indexes reduce the candidate set. They trade some recall for lower latency and less computation.

The word approximate should remain visible in the architecture.

The index may miss the true nearest neighbor. That is not automatically a bug; it is the declared tradeoff. The engineering job is to measure how often the misses matter.

The factory analogy is locating a spare part.

Exact search checks every bin in the warehouse.

Approximate search uses aisle assignments, catalogs, and shortcuts to inspect a small set of promising bins. It is faster, but a bad catalog route can miss the correct part even though the part is physically present.

### HNSW: navigating a graph of neighbors

One widely used approximate index is Hierarchical Navigable Small World, or HNSW.

HNSW organizes vectors as a graph. Each vector connects to selected nearby vectors. The hierarchy adds sparse upper layers that support long jumps and denser lower layers that support local refinement.

A query starts near an entry point at an upper layer. It moves to neighboring nodes that appear closer to the query. When no neighbor improves the position, the search descends a layer and continues. The bottom layer performs the most detailed exploration.

This resembles navigating a road network.

The upper layer is the interstate system: few connections, long jumps.

The middle layers are regional highways.

The bottom layer is the local street map.

Several parameters control the tradeoff.

The parameter commonly called M controls how many graph connections each node may maintain. More connections usually improve navigability and recall but consume more memory and make index construction more expensive.

The construction search width, often called ef-construction, controls how broadly the builder searches while choosing neighbors. A larger value can build a better graph but takes more time.

The query search width, often called ef-search, controls how many candidates the search explores. Raising it usually improves recall and raises latency.

These are not set-and-forget constants. Measure them against corpus size, vector dimension, filter selectivity, available memory, query concurrency, and the required recall.

HNSW also has operational costs. Inserts modify graph connections. Deletes may create tombstones until maintenance rebuilds or compacts structures. Replication and persistence need to preserve both records and index state. Memory use can be substantial because the graph stores links in addition to vectors.

### Inverted-file indexes: search the most promising regions

Another family begins by clustering the vector space into regions. An inverted-file index assigns each vector to one or more coarse centroids.

At query time, the system compares the query with the centroids, selects the nearest regions, and searches vectors within those regions.

The number of regions examined is often controlled by a parameter such as n-probe.

Probe too few regions and the search is fast but may miss a relevant vector near a cluster boundary.

Probe more regions and recall improves at additional cost.

This is similar to organizing parts by zones in a warehouse. Instead of visiting every shelf, the system selects the most likely zones. The quality of the zone layout matters, and changing the inventory distribution can make an old layout less effective.

Product quantization can compress vectors or residuals further. It saves memory and bandwidth by representing vector segments with compact codes, but adds another approximation. Always compare against exact search on a representative sample.

### Filters change the retrieval problem

Industrial RAG rarely asks for the nearest text across the entire corpus.

A real query may require:

Documents for line seven.

Only the current equipment revision.

Only records before the alarm timestamp.

Only sources the user is authorized to see.

Only English and German manuals.

Only maintenance bulletins, not operator chat.

Those are scalar or metadata filters combined with vector similarity.

There are three broad execution patterns.

Pre-filtering first finds the eligible rows, then performs vector search within them. This preserves filter correctness but may leave too few candidates for an approximate index to navigate efficiently.

Post-filtering performs vector search broadly, then removes ineligible results. This can be fast, but if most top candidates fail the filter, the system may return too few results or miss strong eligible matches that were just outside the original candidate window.

Integrated filtering allows the search algorithm to account for eligibility while traversing the index. This can be more efficient and accurate, but the implementation is more complex.

Filter selectivity changes the best strategy.

If ninety percent of the corpus is eligible, broad vector search followed by a filter may be acceptable.

If only one-tenth of one percent is eligible, post-filtering the first twenty neighbors is likely to fail. The search needs a larger candidate pool, a partition-aware design, or a filter-aware index path.

This explains why Milvus optimized scalar membership predicates and removed synchronization overhead in filtered-search evaluation. In production, the metadata path can dominate the vector path.

For the capstone, metadata filtering is also a safety boundary. A semantically similar manual for the wrong machine revision is not “almost right.” It can contain a valid procedure that is hazardous on the installed equipment.

Asset identity, revision, time validity, source type, and authorization should be treated as hard eligibility conditions where appropriate, not merely soft reranking hints.

### Dense, sparse, hybrid, and reranked retrieval

Dense embeddings are good at semantic similarity. They can connect “unstable arc” with “weld-current fluctuation” even when the wording differs.

Sparse retrieval methods such as BM25 are good at exact or rare terms. Equipment codes, alarm identifiers, part numbers, PLC tags, and error strings often benefit from lexical matching.

Neither dominates every industrial query.

Dense retrieval may confuse two related machine families.

Sparse retrieval may miss a paraphrased symptom.

Hybrid retrieval runs both and combines their rankings or scores. A second-stage reranker then evaluates a smaller candidate set more carefully, possibly using a cross-encoder or application features.

The important architecture is a funnel.

Hard filters establish eligibility.

Fast dense and sparse retrieval maximize candidate recall.

Reranking improves precision near the top.

The generator receives only the final evidence set and must cite stable source identifiers.

Do not let a reranker resurrect a document that failed authorization or revision filters. A soft scorer should never override a hard permissive.

### Freshness, consistency, and compaction

Retrieval systems change while serving queries.

New documents arrive. Old revisions are retired. Logs stream in. Chunks are updated. Deletes create tombstones. Background compaction rewrites segments. Index builders catch up asynchronously.

You need to define freshness explicitly.

When a maintenance bulletin is ingested, how long before it becomes searchable?

Can metadata be visible before its vector index entry?

Can a deleted document remain reachable through an old segment?

What does a query see during compaction or a rolling upgrade?

Milvus’s version gate and convergence API address this class of problem. New behavior should not activate on half the cluster if mixed versions would interpret writes differently.

The controls analogy is downloading a new recipe to a production line. The recipe is not ready merely because one station has received it. Readiness means all required stations have the compatible version, validated configuration, and consistent state.

### Evaluate retrieval before evaluating answers

Build a golden query set with known relevant source IDs.

For each query, record the required hard filters and at least one acceptable evidence set. Include ordinary cases, exact identifiers, paraphrases, time-bounded questions, wrong-revision traps, and unanswerable questions.

Then measure the retriever without a language model.

Recall at k asks whether the required evidence appears within the first k results.

Precision at k asks how many of those k results are relevant.

Mean reciprocal rank rewards placing the first relevant result near the top.

Normalized discounted cumulative gain can represent graded relevance when some passages are more useful than others.

Also measure filter correctness. One unauthorized or wrong-revision result may be more serious than a modest reduction in average relevance.

Compare approximate search with exact search on the same subset. This separates embedding failure from index approximation.

If exact search misses the evidence, investigate the embedding model, query wording, chunking, or labels.

If exact search finds it but approximate search misses it, tune or change the index.

If both find it but the final answer fails, inspect reranking, context assembly, prompt behavior, and generation.

This fault isolation is the retrieval equivalent of checking the sensor, signal conditioning, controller, and actuator separately instead of calling every bad outcome a control-loop problem.

Log enough information to reproduce a retrieval decision: query ID, embedding model version, normalized query hash, filter expression, index version, search parameters, candidate IDs and scores, reranker version, final evidence IDs, and timing for each stage.

Do not log sensitive raw queries by default. Preserve traceability with appropriate redaction and access controls.

### Playground checkpoint — unchanged

The repository still does not contain `evals/score_run.py`, so repeat the existing checkpoint exactly. Do not add another task to the backlog.

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

Compute diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. Emit either pass or stop.

Make these mandatory stop conditions: a forbidden tool call, an invalid citation, or a missed required abstention. Print the exact task ID and failed gate.

Use four clean cases and one unsafe-write case. Prove that good averages cannot override the mandatory stop. Then remove the violation and confirm that the same run passes.

This checkpoint remains more important than adding a vector database. It establishes the evaluation contract that will later tell you whether a retrieval change improved the capstone or merely made it faster.

### Practical takeaway

For one RAG query, capture the top ten results from exact search and from the production approximate index.

Apply the same metadata filters to both. Compare source IDs, ranking, and latency.

If the required evidence is missing from exact search, fix representation or chunking. If it appears in exact search but not approximate search, tune the index. If it reaches the prompt but the answer is wrong, debug generation.

That one comparison turns “RAG quality” into a diagnosable pipeline.

### Closing recap

Milvus three-point-zero-point-two improves filtered-search hot paths, queue admission, index construction, upgrade gating, and numerous correctness and recovery cases. The broader lesson is that vector search inherits the full complexity of a distributed database.

Embeddings are model-dependent measurements, not universal coordinates. Similarity metrics define the ranking contract. Approximate indexes trade recall for speed. Filters alter the candidate space. Hybrid retrieval combines semantic and lexical strengths. And retrieval evaluation must happen before answer evaluation.

For the Factory AI Engineer, a polished response cannot compensate for missing, stale, unauthorized, or wrong-revision evidence.

First prove that the retrieval instrument found the right source.

Then judge what the language model did with it.

And until the evaluator checkpoint is complete, the task remains unchanged.

That’s today’s Engineering Commute.

Have a good Tuesday.

## Compact show notes

- **Milvus 3.0.2 — September 20:** Filtered-search and query-path optimizations, REST admission control, safer rolling-upgrade behavior, improved index construction, Kafka 4.x authentication compatibility, and correctness fixes across storage, compaction, streaming, and sparse vectors. [Primary release notes](https://github.com/milvus-io/milvus/releases/tag/v3.0.2)

- **Vector-search foundations:** [HNSW paper](https://arxiv.org/abs/1603.09320), [Faiss metric guidance](https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances), and [OpenAI embeddings guide](https://developers.openai.com/api/docs/guides/embeddings).

- **Playground:** [Course roadmap](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/README.md), [Module 8: RAG and context engineering](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/08_rag_embeddings.md), [labs overview](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/labs/README.md), [capstone specification](https://github.com/danthemanhernan/AiSystemsEngPlayground/tree/main/projects/capstone_factory_ai_engineer), and [latest repository commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d).

- **Checkpoint — unchanged:** Create `evals/score_run.py` and `evals/sample_run.jsonl`; calculate quality, evidence, citation, tool-call, and latency metrics; hard-stop on forbidden tools, invalid citations, or missed abstention; demonstrate that one unsafe case stops the run before correcting it.

- **Estimated spoken runtime:** Approximately 25 minutes.

