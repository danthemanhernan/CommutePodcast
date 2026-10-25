# The Engineering Commute — October 10, 2026

## Narration-ready episode

Good morning, Dan.

Today’s theme is a simple production rule: when an AI system crosses a boundary, make that boundary machine-checkable.

Google has brought a broad set of data-platform tools into coding agents. Postman has published hard-won lessons from operating an agent across a mature product. And GitHub’s latest CodeQL release shows why executable models of software behavior remain essential even as more code is written with AI assistance.

Then, in the Playground Lesson, we’ll build the mental model for schema-first AI integration: inputs, outputs, invariants, validation, and the difference between a data shape and a safety contract.

### Segment one: Data agents are moving into the live platform

First, the reported facts.

On October ninth, Google Cloud’s data update highlighted the general availability of Data Agent Kit. The kit provides Model Context Protocol tools and Google-authored agent skills that connect coding agents to more than fifteen Google Cloud data services. The supported workflows include inspecting schemas, authoring queries, reading job information, and building data pipelines from an IDE or command line.

Google says the kit now covers services including BigQuery, Bigtable, Managed Service for Apache Spark, and BigQuery Graph. It can connect as the user or through service-account impersonation, which means existing row-level and column-level security still apply. Google also describes governance layers including IAM, VPC Service Controls, Principal Access Boundaries, and traffic screening with Model Armor.

The included skills encourage cost-aware behavior. One example is checking partition keys and performing a dry run before executing a BigQuery query, so an agent does not accidentally scan an entire large table.

Now the analysis.

This is a meaningful shift from an assistant that writes a SQL string to an agent that can inspect the actual environment, decide what to query, execute the query, and interpret the result. That closes the feedback loop, but it also joins two different control planes: the probabilistic planning layer and the deterministic data platform.

The important word is not “agent.” It is “identity.” If the agent acts as you, it inherits both your legitimate reach and the consequences of your mistakes. Existing data permissions are necessary, but they do not express every operational constraint. A user may be allowed to query a table while still being expected not to launch an unbounded scan during peak production hours.

Think of this like giving an optimization routine access to a plant historian. The historian may enforce which tags the service account can read. It will not necessarily know that a ten-year, one-second-resolution query is unacceptable during a shift change. Authorization answers, “May this identity access the resource?” A runtime policy must also answer, “May this operation run now, at this estimated cost, with these filters?”

That makes schema inspection, query dry runs, byte estimates, timeouts, result limits, and audit records part of the agent interface. The model can propose work. A deterministic gateway should evaluate the proposed operation before the warehouse accepts it.

### Segment two: Postman found that more tools can make an agent worse

Here are the reported facts.

On October ninth, Postman and AWS published an architecture account of Postman Agent Mode, which serves workflows across API testing, documentation, discovery, and implementation. The system runs on Amazon Bedrock and is designed for a product used by forty million developers.

Postman reports that early versions exposed many small, atomic tools. Complex work then required long sequences of calls, each returning to the model before the next step. In its testing, tool-selection errors increased when the visible catalog exceeded roughly forty tools. The agent could invent a tool, pass incorrect arguments despite a valid schema, or choose a plausible but contextually wrong operation.

Postman now narrows a catalog of more than one hundred seventy tools to roughly fifteen relevant tools for a task, then gives those to a context-isolated agent. For structured analytics, it also replaces many narrow read tools with schema-aware query access. Actions that modify application state still require user approval.

Postman’s other major finding was that context, not capability, was usually the bottleneck. Objects designed for rendering a user interface were not automatically good representations for model reasoning, so the team built dedicated context handlers that distill each entity into task-relevant information.

Now the analysis.

There are two different contracts here.

The tool contract says what operations exist, which arguments they accept, and what they return. The context contract says which state the model needs in order to choose the correct operation.

A perfect tool schema cannot compensate for the wrong equipment identifier, stale alarm state, or missing production mode. Imagine a maintenance assistant with a flawlessly typed `get_motor_history` function. If the context says only “motor seven,” but the plant has a motor seven on four lines, the call can be syntactically valid and operationally wrong.

Postman’s result also explains why tool count is not a pure capability metric. In control-system terms, adding every possible tool to every prompt is like placing every plant command on one HMI screen. Nothing is technically missing, but selection risk and operator load rise.

Dynamic tool scoping acts like a mode-specific faceplate. During diagnosis, expose read-only telemetry, documentation, and test tools. During an approved change workflow, expose a small set of mutation tools with explicit confirmation. The agent receives less choice, but the system gains more reliable behavior.

### Segment three: Static analysis is an executable model of risk

Here are the reported facts.

GitHub released CodeQL version 2.27.2 on October ninth. GitHub says the default query suite now runs four hundred ninety-eight security queries covering one hundred seventy Common Weakness Enumerations. The extended suite adds another one hundred thirty-one queries.

The release adds and improves models across C and C++, Go, Rust, and JavaScript or TypeScript. Examples include SQL-injection sinks for a C database interface, additional WebSocket modeling in Go, better asynchronous data flow in Rust, and recognition of workflow directives plus improved route-handler tracking in JavaScript and TypeScript.

For GitHub Actions, maintainers can now remove an owner from the trusted set used by the unpinned-tag query. The CLI also rejects some malformed values that were previously truncated or produced less useful failures.

One operational caveat is that traced analysis for compiled languages is not supported with the newest macOS and Xcode combination because Apple no longer ships the multi-architecture binaries that CodeQL requires for that mode.

Now the analysis.

Static analysis is relevant to AI integration because generated code is still code, and tool wrappers are security boundaries. A schema can prove that an argument is a string. It cannot prove that the string will not reach a SQL sink unsafely, that a user-controlled value will not become a shell command, or that an asynchronous path preserves the intended authorization check.

CodeQL works by modeling program structure and data flow. That is complementary to runtime validation. Runtime checks ask whether this particular input satisfies the contract. Static analysis asks whether some possible path can carry untrusted data into a dangerous operation.

For an agent gateway, use both. Validate every proposed tool call against a runtime schema, then scan the gateway implementation and its adapters for unsafe flows. One protects the transaction. The other examines the machinery.

### Playground Lesson: Schema-first AI integration

Let’s build the underlying concept carefully.

A schema is a formal description of data. At minimum, it defines fields and types. A tool might accept an equipment identifier, start timestamp, end timestamp, and requested signals. Its output might contain time-series samples, units, quality codes, and source metadata.

That basic shape matters because language models generate tokens, not typed objects. Even when a model is instructed to return JSON, it can omit a field, choose an invalid enum value, emit a number as text, or construct JSON that parses but violates the application’s assumptions.

The first defensive layer is structural validation. Parse the object. Reject unknown or missing fields according to policy. Check types, formats, enumerations, and bounds. Do this outside the model.

But a schema is not yet a full contract.

Suppose `start_time` and `end_time` are both valid timestamps. The request is still invalid if the end precedes the start. Suppose `sample_interval_ms` is a positive integer. It may still be unsafe if the agent requests one millisecond samples across five years. Suppose the tool name and arguments are valid. The operation may still be forbidden because the current workflow is diagnostic and the tool writes to production.

So a production contract has at least four layers.

Layer one is shape: fields, types, formats, and allowed values.

Layer two is relationship: cross-field rules such as start before end, matching units, or a required reason whenever override mode is selected.

Layer three is authority: whether this identity, task, environment, and approval state may perform the operation.

Layer four is operating envelope: cost, time range, row count, rate, timeout, concurrency, and acceptable effect.

This maps cleanly to controls engineering. A PLC function block has typed inputs, but safe operation also depends on interlocks, permissives, mode, and equipment limits. A Boolean `start` command is structurally valid whether or not lubrication pressure is present. The interlock is what turns a valid signal into an allowed transition.

For AI applications, treat the model as a proposal generator upstream of that logic. The model proposes a typed operation. The validator normalizes and checks it. The policy engine evaluates identity and state. The executor applies hard limits. The audit layer records the proposed call, the validated call, the policy decision, the result, and the versions of the schema and policy.

Versioning is important because schemas evolve. Adding an optional response field is usually backward compatible. Renaming a required argument is not. Changing an enum’s meaning can be more dangerous than changing its syntax. The agent’s prompt, tool description, client validator, server implementation, and evaluation set must agree on the same contract version.

This is where many systems fail quietly. A server adds a new capability, the agent discovers it, and the organization assumes discovery equals authorization. Or a tool changes its description while keeping the same name, causing the model to select it in new situations. Treat tool metadata like an API release: diff it, review it, test it, and promote it through environments.

The most useful testing pattern is contract testing around failure cases.

Start with valid examples, but spend more effort on near-valid inputs: an unknown field, a timestamp with the wrong timezone, a tag that exists in another site, a write request in a read-only workflow, a query whose dry-run cost exceeds the budget, or a response that cites a record the tool never returned.

Then add properties that should always hold. A read-only session never invokes a mutation tool. A rejected operation never reaches the executor. Every diagnosis cites retrieved evidence. Every mandatory abstention stops the workflow. A good average score never cancels a hard safety failure.

That last rule is the bridge to the Factory AI Engineer capstone. The evaluator is not just measuring quality. It is encoding the contract between a probabilistic diagnosis and an operationally acceptable result.

### Playground checkpoint — unchanged

The repository still does not contain `evals/score_run.py` or `evals/sample_run.jsonl`, so this remains the only assigned checkpoint. Do not add another task until these files appear in GitHub.

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

Compute diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. Emit either pass or stop.

Make these mandatory stop conditions: a forbidden tool call, an invalid citation, or a missed required abstention. Print the exact task ID and failed gate.

Use four clean cases and one unsafe-write case. Prove that good averages cannot override the mandatory stop. Then remove the violation and confirm that the same run passes.

This should take roughly twenty to thirty minutes.

### Practical takeaway

For one agent tool you already use, write down four things: its data shape, its cross-field invariants, its authorization rule, and its operating envelope. If any of those exists only in the prompt, move it into executable validation or policy.

### Closing recap

Google’s Data Agent Kit brings live data-platform context and actions into coding agents, making identity, cost controls, and query validation part of the application boundary.

Postman’s production experience shows that a smaller, task-specific toolset and purpose-built context can outperform a giant catalog of atomic capabilities.

CodeQL’s latest release expands the static models that find unsafe flows across several backend languages and GitHub Actions.

And the core lesson is that a schema describes data, while a production contract also defines relationships, authority, and operating limits.

Models should propose. Deterministic systems should validate, authorize, bound, and record.

That’s today’s Engineering Commute. Have a good Saturday.

## Compact show notes

- **Google Data Cloud update — October 9, 2026:** Data Agent Kit connects coding agents to more than 15 Google Cloud data services through MCP tools and skills; the weekly update also covers Spanner Omni, AlloyDB hybrid search, Dataflow controls, and Valkey 9.1. [Google Cloud weekly update](https://cloud.google.com/blog/products/data-analytics/whats-new-with-google-data-cloud)
- **Data Agent Kit GA — September 30, 2026:** Service coverage, identity model, cost-aware query practices, IAM, Model Armor, VPC Service Controls, and Principal Access Boundaries. [Google Cloud announcement](https://cloud.google.com/blog/topics/developers-practitioners/data-agent-kit-is-now-ga-bring-google-data-cloud-to-any-coding-agent)
- **Postman Agent Mode — October 9, 2026:** Production lessons on tool sprawl, dynamic tool selection, schema-aware reads, purpose-built context, user approval, and Bedrock deployment. [AWS and Postman architecture article](https://aws.amazon.com/blogs/machine-learning/how-postman-runs-agent-mode-for-40-million-developers-on-amazon-bedrock/)
- **CodeQL 2.27.2 — October 9, 2026:** New and improved analysis for C and C++, Go, Rust, JavaScript and TypeScript, plus GitHub Actions and CLI changes. [GitHub changelog](https://github.blog/changelog/2026-10-09-codeql-2-27-2-improves-c-go-rust-and-javascript-analysis/)
- **Playground:** [Repository overview](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/README.md), [modules](https://github.com/danthemanhernan/AiSystemsEngPlayground/tree/main/modules), [labs](https://github.com/danthemanhernan/AiSystemsEngPlayground/tree/main/labs), [capstone module](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/13_capstone.md), and [current repository commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d).
- **Checkpoint:** Unchanged. Create `evals/score_run.py` and `evals/sample_run.jsonl`; demonstrate that forbidden tools, invalid citations, and missed abstentions force a stop even when aggregate metrics pass.
- **Estimated runtime:** Approximately 15 minutes; about 2,200 spoken words.
