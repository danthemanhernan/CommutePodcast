# The Engineering Commute --- August 26, 2026

## Agent Sandboxes, Hybrid Search, and Continuous Batching

### Narration-ready episode

Good morning, Dan.

Today's Engineering Commute is about four boundaries that production
systems need to make explicit: where untrusted agent code may execute,
how retrieval balances conceptual similarity with exact identifiers,
which code version a serverless workflow actually runs, and how an
inference scheduler divides scarce accelerator capacity among requests
of very different sizes.

### Segment one: Agent sandboxes are becoming schedulable infrastructure

Google Cloud and Anyscale introduced an experimental Ray library for
running gVisor sandboxes across distributed Ray clusters on GKE.

The motivation is post-training and agent workloads in which models
generate code, execute commands, manipulate files, or perform multi-turn
interactions with external tools. The library represents each sandbox as
a Ray Actor. The Ray scheduler chooses a node and reserves CPU and
memory. The Actor manages the sandbox lifecycle, while gVisor supplies
the isolated execution environment.

The important design choice is making isolation part of the scheduler's
resource model. A sandbox consumes capacity, must be created and
destroyed, may fail, and needs to scale alongside rollout workers,
inference engines, and trainers.

The production architecture should separate at least three layers: the
agent decides what experiment or tool call it wants; a deterministic
policy layer validates the request and assigns limits; the sandbox
runtime executes it with bounded resources and network access.

### Segment two: BigQuery combines semantic and exact-match retrieval

Autonomous Embedding Generation and `AI.SEARCH` are generally available,
while Hybrid Search is entering public preview. It combines semantic
vector retrieval with lexical techniques including BM25 and Reciprocal
Rank Fusion.

Hybrid search addresses a weakness in pure vector retrieval: identifiers
often have very little semantic meaning. An embedding search can
understand that "drive overheating" relates to "motor thermal alarm,"
but it may not reliably prioritize an exact alarm code or PLC tag.

For an industrial RAG system, test natural-language symptom
descriptions, exact alarm codes, mixed queries, and near-collision
identifiers. Measure retrieval recall before final-answer fluency.

### Segment three: Airflow Serverless can run ordinary Python and shell tasks

AWS announced native PythonOperator and BashOperator support for Amazon
MWAA Serverless. Teams can package Python modules, shell scripts, and
dependencies into a code bundle stored in S3.

When a workflow is created or updated, MWAA Serverless snapshots that
bundle. Later executions of that workflow version use the snapshot, not
whatever file currently exists at the original S3 location.

Treat the workflow definition and bundle snapshot as one immutable
release artifact. Record a Git commit, bundle checksum, dependency
lockfile, workflow version, and deployment time together.

### Playground Lesson: continuous batching is a live queue, not a fixed batch

The scheduler admits up to a maximum number of active requests. During
each decode tick, every active request receives one output token.
Completed requests leave immediately, and waiting requests can occupy
the newly available positions.

In static batching, the slowest request controls when the next batch
begins. Continuous batching changes the rule: at every decode step,
completed sequences leave and new sequences enter.

This improves throughput, but a request consumes more than a slot. It
occupies KV-cache memory proportional to sequence length, contributes
token work, and has a latency objective.

Your checkpoint is to compare maximum batch sizes of four, eight, and
sixteen, then add an urgent priority class and measure p95 latency
separately for urgent and ordinary traffic.

### Practical takeaway

For one shared service today, identify what its scheduler actually
budgets. If the answer is only workers, pods, or request count, add the
resource that better predicts pressure.

### Closing recap

Agent isolation is becoming a schedulable resource. Hybrid search
combines semantic and exact retrieval. Serverless workflow code is
becoming explicitly versioned. And continuous batching turns inference
serving into a live token-and-memory scheduling problem.

### Show notes

-   Ray gVisor sandboxes:
    https://cloud.google.com/blog/products/containers-kubernetes/gvisor-sandboxes-for-ray-clusters-on-gke
-   BigQuery search innovations:
    https://cloud.google.com/blog/products/data-analytics/bigquery-search-innovations-unify-structured-unstructured-data
-   MWAA Serverless operators:
    https://aws.amazon.com/blogs/big-data/pythonoperator-and-bashoperator-now-available-on-amazon-managed-workflows-for-apache-airflow-amazon-mwaa-serverless/
-   Playground roadmap:
    https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/README.md
