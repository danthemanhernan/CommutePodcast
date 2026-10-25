# The Engineering Commute — Federated Agent Data and Residency

**Episode date:** October 16, 2026  
**Estimated runtime:** 15–16 minutes  

## Narration

Good morning, Dan. This is *The Engineering Commute*.

Today’s thread is location—not just where a model runs, but where data stays, where tools execute, where identity is enforced, and where verification happens. We have three developments from the last day: GitHub has taken both AI-assisted vulnerability detection and agentic remediation to general availability; Google Cloud is wiring Gemini into a federated, cross-cloud lakehouse; and AWS is expanding both current-web grounding and governed Kafka tooling into regions where latency and sovereignty are first-class constraints.

The reported facts come first. I’ll label my analysis separately. Then the Playground Lesson will turn those announcements into a practical architecture for agents that need to reason across distributed industrial and enterprise data without casually copying everything into one place.

## GitHub closes more of the security loop

First, GitHub announced general availability for two related application-security capabilities on October fifteenth.

The first is AI Scan for pull requests. GitHub says it complements CodeQL by examining pull-request changes in languages and frameworks that CodeQL does not currently cover, including PHP, Shell and Bash, Terraform HCL, Dockerfiles, JSP, and Blazor. When code scanning and the effective AI Scan setting are enabled, findings appear beside CodeQL results in the pull-request conversation and changed-files views. They are marked as AI findings and can include a risk explanation plus a suggested fix.

There is an important boundary: these findings are advisory. They do not fail the code-scanning check, they cannot be used directly as a ruleset requirement to block a merge, and the scan does not run on pull requests from forks or Dependabot. Public repositories can use it, while private and internal organization repositories require GitHub Code Security or Advanced Security. Usage consumes Code Security AI Credits.

The second capability is agentic autofix for existing code-scanning alerts. When an alert on the default branch is assigned to Copilot, the agent explores relevant files, proposes a repair, reruns CodeQL to see whether the alert closes, iterates if needed, and opens a draft pull request for human review. Teams can also select up to twenty-five alerts and ask Copilot to address them together. The feature requires enterprise policy enablement and consumes both AI credits and GitHub Actions minutes.

That is the reported product behavior. Here is my analysis.

The interesting architecture is the separation between detection, actuation, and acceptance. AI Scan widens the sensor coverage, but GitHub deliberately keeps its findings advisory. Agentic autofix can actuate by writing a patch, but it produces a draft pull request rather than silently merging. CodeQL is rerun as a verifier, and the human reviewer remains the final authority.

That resembles a guarded control loop. A new sensor can improve coverage without immediately becoming an interlock. A manipulator can propose a correction without receiving unrestricted authority over the plant. And a verifier checks whether the original fault signal cleared. But clearing the alert is not the same as proving the system is safe. A patch can suppress the symptom, introduce a behavioral regression, or shift risk into a path that the original rule does not observe. The engineering move is to add independent tests, policy checks, and review criteria around the vendor’s inner loop.

The useful question is not, “Can the agent fix security alerts?” It is, “What evidence must exist before a proposed fix is allowed to move from a draft into a trusted release?”

## Google brings Gemini to federated lakehouse data

Second, Google Cloud announced a preview integration between Gemini and its borderless Lakehouse. The stated goal is to let users and agents query data across BigQuery and external catalogs, including Databricks Unity Catalog and Snowflake Horizon, without first moving all of that data into one warehouse.

Google also reported that several supporting capabilities are generally available. These include cross-cloud interconnect and caching for AWS and Azure, Apache Iceberg version three support in BigQuery, read-write interoperability between BigQuery and managed Spark on Iceberg tables, AlloyDB lakehouse federation, bidirectional catalog caching with AWS Glue, Unity Catalog, and Horizon Catalog, plus zero-copy integrations for enterprise applications. Confluent Tableflow is now included in the partner ecosystem so Iceberg tables it produces can appear in BigQuery through the shared catalog path.

Google’s post makes a scale distinction that matters. An agent’s context window can accept only a bounded payload, while enterprise questions may require joins across petabytes. The proposed design is not to pour petabytes through an MCP tool into a prompt. It is to let the data platform perform filtering, joins, caching, and access control near the data, then return a compact result and the metadata needed to interpret it.

Now my analysis.

This is a shift from retrieval as document shipping to retrieval as delegated computation. A simple RAG system asks a search service for chunks and places those chunks in the model context. A federated analytical agent instead creates a plan: identify governed assets, push predicates and aggregations into the appropriate engines, combine only the necessary intermediate results, and give the model a small evidence package.

For an industrial example, imagine an agent investigating a yield drop. Work orders might live in a SaaS system, batch genealogy in a lakehouse, alarm history in a time-series store, and current machine states behind an on-premises gateway. The wrong architecture copies everything into one convenience database. The better architecture dispatches constrained queries to each authority, preserves each system’s access policy, and returns the few rows, trends, and provenance records needed to test a hypothesis.

Federation does not eliminate movement. Query text, metadata, result sets, cache entries, and logs still cross boundaries. “Zero copy” should therefore be read as an implementation property, not a blanket privacy guarantee. The design review still needs to ask which bytes move, which identities are delegated, where caches live, and whether query plans reveal sensitive names or relationships.

## AWS expands locality for agents and streaming

Third, AWS made two location-sensitive announcements on October fifteenth.

Web Search in Amazon Bedrock AgentCore is now available in four additional regions: Ohio, Oregon, Sydney, and AWS GovCloud West. AWS describes it as a managed tool for grounding agents with current web information. The regional expansion is intended to reduce latency by placing retrieval closer to applications and end users, while the GovCloud availability supports government compliance and data-residency requirements.

Separately, Amazon MSK Connect and AWS Glue Schema Registry are now available in the AWS European Sovereign Cloud in Germany. MSK Connect runs managed Kafka Connect clusters for moving data between Kafka and systems such as databases, filesystems, and search indexes. Glue Schema Registry provides centralized Avro, JSON, and Protobuf schema management so producers and consumers can validate and evolve contracts. Combined with MSK brokers already in that region, the launch fills in more of the streaming toolchain inside the sovereign boundary.

My analysis is that “available in-region” is not a footnote for agent systems. It changes the feasible control architecture.

If an agent must cross a distant or disallowed boundary for every lookup, designers compensate with broad caches, large replicated indexes, or longer-lived credentials. Those compensations increase staleness and exposure. When search, connectors, schemas, and compute can remain inside the required boundary, the system can use shorter cache lifetimes, narrower network paths, and more explicit jurisdictional controls.

Still, regional placement alone does not provide sovereignty. You must trace the complete path: prompts, tool arguments, connector offsets, schema metadata, traces, evaluation samples, support logs, model telemetry, and backup copies. An agent data-flow diagram should treat all of those as process variables, not administrative trivia.

## Playground Lesson: designing a federated agent data plane

Today’s Playground Lesson is the federated agent data plane: how an agent can reason across several systems without turning its context window into a shadow data lake.

Start with a four-layer model.

Layer one is the catalog and semantic layer. It answers: what assets exist, who owns them, what do fields mean, what policy applies, and how fresh is the data? For a factory, this is the difference between a tag called `PV_104` and a governed definition stating that it is reactor outlet temperature, in degrees Celsius, sampled every second, calibrated last week, and restricted to the operations group.

Layer two is the identity and policy layer. The agent should not possess a magical service account that can read every source. It should act with a delegated identity tied to the user, task, and time window. Policy decisions need to survive federation. If a person cannot query employee medical data directly, asking the agent to join it to maintenance records must not create a side door.

Layer three is the execution layer. This is where filters, joins, window functions, vector searches, or graph traversals run. The core rule is: move the smallest safe computation to the data, then return the smallest sufficient evidence to the model. In controls terms, do not route every high-frequency sensor sample through the supervisory display. Compute rate, deviation, and alarm state at the appropriate tier, then publish the bounded signal the supervisor actually needs.

Layer four is the evidence and audit layer. Every answer should carry source identity, query or tool version, execution time, policy context, row counts, truncation information, and any cache age. The model’s prose is the operator display; the evidence record is the historian. If you cannot reconstruct what the system observed, you cannot investigate a bad decision.

Now consider the planning loop.

First, the agent translates the user’s request into a typed information need. It should separate facts needed from transformations needed. “Why did line three scrap increase?” becomes a request for a time interval, scrap classifications, batch and material genealogy, machine-state changes, maintenance events, and the comparison baseline.

Second, a planner maps those needs to governed assets. This step should be deterministic where possible. Let the model propose asset names, but make a catalog service resolve them to approved identifiers. That prevents a plausible table name from becoming an accidental query against the wrong dataset.

Third, the policy engine evaluates each proposed access before execution. It should return allow, deny, or allow with constraints—such as a row filter, masked column, maximum time range, or aggregate-only response. A denial is not a model failure. It is a valid control outcome.

Fourth, the execution service pushes work down. Filter by plant and time before transferring rows. Aggregate one-second telemetry into meaningful features before joining it to work orders. Keep large vector or graph operations inside the system built for them. The model receives results, not raw exhaust.

Fifth, a result assembler checks budgets and provenance. It should reject oversized results, identify partial failures, preserve conflicting observations, and attach citations that point to the executed operations—not merely to a catalog description. If one source timed out, the agent must say that its conclusion is incomplete rather than quietly treating missing data as zero.

Three failure modes deserve special attention.

The first is authorization drift. A catalog may synchronize asset metadata faster than its policy bindings, or a cache may outlive a revoked permission. The mitigation is short-lived authorization decisions, policy-version stamps, and cache keys that include identity and policy context.

The second is semantic drift. Two clouds may expose fields with the same name but different units, time zones, or business definitions. Schema compatibility is necessary, but not sufficient. You also need unit normalization, semantic definitions, and tests for cross-source joins.

The third is cost and latency runaway. An innocent natural-language question can create a cross-cloud Cartesian join. Put hard limits on scanned bytes, transferred bytes, execution time, and fan-out. Require a dry-run estimate for expensive plans, just as a controls change might require a simulation before download.

Here is the architectural checkpoint I would use: an agent may receive authority to plan broadly, but execution authority must remain narrow, typed, policy-checked, budgeted, and observable.

The repository status has not changed. The latest commit remains the September ninth curriculum expansion, and the required evaluator files are still absent. So the existing checkpoint remains unchanged; no new backlog item is being added.

### Playground checkpoint — unchanged

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

Compute diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. Emit either pass or stop.

Make these mandatory stop conditions: a forbidden tool call, an invalid citation, or a missed required abstention. Print the exact task ID and failed gate.

Use four clean cases and one unsafe-write case. Prove that good averages cannot override the mandatory stop. Then remove the violation and confirm that the same run passes.

This should take roughly twenty to thirty minutes.

## Practical takeaway

For one agent workflow you operate, draw two columns today: “data that crosses the boundary” and “computation that can stay near the source.” Include metadata, traces, caches, and evaluation samples—not just business rows. That small inventory usually reveals one unnecessary replication path and one missing policy check.

## Closing recap

GitHub’s new security capabilities show a guarded automation loop: broaden detection, propose changes, rerun a verifier, and keep acceptance under review. Google’s federated lakehouse work shows that enterprise agents should delegate computation to governed data systems instead of stuffing raw datasets into prompts. AWS’s regional expansions show that locality affects latency, credentials, caching, and compliance—not merely deployment convenience.

The common principle is simple: bring constrained computation to governed data, return compact evidence, and keep authority narrower than the agent’s ability to plan.

That’s today’s *Engineering Commute*. Drive safe, and I’ll see you next time.

---

## Show notes

### Primary sources

- GitHub, October 15, 2026: [AI Scan for pull requests generally available](https://github.blog/changelog/2026-10-15-ai-scan-for-pull-requests-generally-available/)
- GitHub, October 15, 2026: [Agentic autofix for code scanning alerts general availability](https://github.blog/changelog/2026-10-15-agentic-autofix-for-code-scanning-alerts-general-availability/)
- Google Cloud, October 15, 2026: [Bringing the borderless Lakehouse into the agentic era with innovations for Gemini](https://cloud.google.com/blog/products/data-analytics/borderless-lakehouse-integrates-with-gemini)
- AWS, October 15, 2026: [Web Search on Amazon Bedrock AgentCore expands to AWS GovCloud and three regions](https://aws.amazon.com/about-aws/whats-new/2026/10/amazon-bedrock-agentcore/)
- AWS, October 15, 2026: [Amazon MSK Connect and AWS Glue Schema Registry in the AWS European Sovereign Cloud](https://aws.amazon.com/about-aws/whats-new/2026/10/amazon-msk-connect-aws-gsr-additional-aws-regions/)

### AiSystemsEngPlayground

- [Repository README](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/README.md)
- [Module 08 — RAG and knowledge systems](https://github.com/danthemanhernan/AiSystemsEngPlayground/tree/main/modules/08_rag_and_knowledge_systems)
- [Module 09 — MCP and tool use](https://github.com/danthemanhernan/AiSystemsEngPlayground/tree/main/modules/09_mcp_and_tool_use)
- [Module 10 — Agents and workflows](https://github.com/danthemanhernan/AiSystemsEngPlayground/tree/main/modules/10_agents_and_workflows)
- [Module 13 — Capstone](https://github.com/danthemanhernan/AiSystemsEngPlayground/tree/main/modules/13_capstone)
- Current repository state inspected October 16, 2026: latest commit remains `e3e18c0a39561919a0da3619c440cd09b728356d`; `evals/score_run.py` and `evals/sample_run.jsonl` are still absent.

### Lab/checkpoint

- **Status:** unchanged; do not add another task until the evaluator files appear in GitHub.
- **Task:** implement the evaluator and sample run described in the Playground checkpoint above.
- **Time box:** 20–30 minutes.
- **Success condition:** the unsafe-write case stops the run despite good aggregate metrics; the corrected run passes.

### Runtime

- Spoken narration: approximately 15–16 minutes.
- Target delivery pace: about 140–150 words per minute.
