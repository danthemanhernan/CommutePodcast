# The Engineering Commute --- September 1, 2026

## BigQuery Graph, Data Agents, and Durable Orchestration

### Narration-ready episode

Good morning, Dan.

Today's Engineering Commute is about turning flexible intelligence into
dependable work.

BigQuery Graph is now generally available. Google's Data Agent Kit can
generate, deploy, monitor, and troubleshoot declarative Airflow
pipelines. And GitHub is making coding-agent sessions more portable,
reviewable, and persistent.

### Segment one: BigQuery Graph brings relationships and agent traces into the warehouse

BigQuery Graph maps warehouse tables into nodes and edges and supports
Graph Query Language alongside SQL.

Graph systems become useful when the relationship is part of the
question.

For a factory digital twin, nodes might represent plants, lines,
stations, controllers, robots, tools, materials, recipes, and suppliers.
Edges express installed-at, feeds, controlled-by, depends-on, or
produced-by relationships.

Google is also introducing context graphs for agent analytics. An
agent's decisions, applied policies, rejected alternatives, and outcomes
can be represented as a typed, queryable graph.

The graph should prioritize observable evidence: prompts, tool calls,
returned data, policy decisions, retries, approvals, outputs, and
subsequent outcomes.

### Segment two: Google is packaging data-pipeline knowledge as an agent skill

Google published a workflow for using Data Agent Kit to create and
operate data pipelines from an IDE or command-line agent environment.

The useful architectural choice is the declarative intermediate
representation. Natural language is flexible but ambiguous. Airflow
Python is executable but arbitrary. A constrained YAML pipeline sits
between them and can be validated before deployment.

Agentic troubleshooting should distinguish diagnosis from authority. A
proposed infrastructure change should include evidence, expected effect,
cost impact, confidence, and rollback procedure.

### Segment three: Coding-agent sessions are becoming persistent engineering objects

GitHub's Copilot updates include side conversations, prompt timelines,
portable plugins, cross-application sessions, multi-window support,
second-model review, and token reporting.

This reflects a shift from chat as a temporary interface to an agent
session as a managed unit of engineering work.

A persistent agent session should make work easier to resume and
audit---not create a second undocumented source of project state.

### Playground Lesson: agent orchestration is state management under uncertainty

An agent is a runtime loop that repeatedly decides what information or
action it needs, invokes a bounded capability, observes the result,
updates working state, and decides whether to continue.

A planner-and-executor architecture separates planning, execution,
verification, and orchestration.

The orchestrator must enforce hard boundaries: maximum steps, allowed
tools, time and cost budget, required evidence, approval before writes,
and terminal states for success, insufficient evidence, policy
rejection, or failure.

Memory has several meanings: working memory, episodic memory, and
semantic memory. Do not store all three as an undifferentiated
transcript.

Your checkpoint is to build a checkpointed troubleshooting-agent state
machine, force a mid-run crash, and verify recovery without repeating
completed tool calls.

### Show notes

-   BigQuery Graph:
    https://cloud.google.com/blog/products/data-analytics/bigquery-graph-connecting-data-and-ai-at-scale
-   Data Agent Kit:
    https://cloud.google.com/blog/products/data-analytics/build-data-pipelines-in-less-time-with-data-agent-kit
-   GitHub Copilot VS Code:
    https://github.blog/changelog/2026-08-31-github-copilot-in-vs-code-august-2026-releases/
-   Playground:
    https://github.com/danthemanhernan/AiSystemsEngPlayground
