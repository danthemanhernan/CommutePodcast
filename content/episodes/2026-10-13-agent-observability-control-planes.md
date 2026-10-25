# The Engineering Commute — October 13, 2026

## Narration-ready episode

Good morning, Dan.

Today’s episode is about knowing who controlled an AI workflow, where its data actually moved, and what you can prove afterward.

GitHub has introduced privacy-scoped OpenTelemetry controls for Copilot activity and durable attribution for the authenticated user who pushed a commit. AWS has published guidance for running OpenAI GPT models through global cross-region inference while keeping permissions, quotas, and monitoring anchored in the source region.

Then, in the Playground Lesson, we’ll build a clean mental model for control planes, data planes, and observability planes—and apply it to the Factory AI Engineer.

### Segment one: GitHub makes agent telemetry independently configurable

First, the reported facts.

On October twelfth, GitHub added enterprise-managed telemetry controls for Copilot CLI, the Copilot app, and Visual Studio Code sessions using Agent Host.

Administrators can enable identity attribution without collecting prompts, responses, or tool content. The identity setting adds the authenticated GitHub login, the local operating-system account, and the host name to OpenTelemetry data. Identity capture is off by default and remains separate from GitHub’s existing pseudonymous user identifier.

GitHub also exposes five independently controlled content classes: prompts, responses, tool arguments, tool output, and policy details. Every class is off by default. Managed enterprise values override local settings, software-development-kit configuration, and environment variables.

GitHub warns that these classes can contain source code, file contents, commands, tool results, tool schemas, MCP server identifiers, sandbox paths, and user-profile paths. Its guidance is to enable only what the audit use case requires and send the data to an approved collection endpoint.

Now the analysis.

This is a useful correction to the idea that observability means “capture everything.”

Agent traces can be extraordinarily sensitive. A tool argument may contain a database query or customer identifier. Tool output may include production records. A prompt can contain source code, credentials pasted by mistake, or internal policy. Even a sandbox path can reveal a username or project name.

At the same time, an organization may need to answer a narrower question: which authenticated user initiated this agent session, on which managed machine, and which policy version governed it?

Separating identity, prompts, outputs, tools, and policy detail lets the telemetry design follow purpose limitation. Collect the minimum fields required for security, reliability, or cost analysis instead of turning the observability backend into a shadow copy of every workspace.

The controls analogy is historian design. You do not collect every PLC memory address at the fastest possible scan merely because storage is available. You select signals that answer operational questions, define retention and access, and avoid capturing values that create risk without diagnostic value.

For agent systems, make every telemetry field earn its place. Define who uses it, which incident or metric it supports, how long it remains, and whether a less sensitive derived value would work.

### Segment two: GitHub separates commit authorship from authenticated push identity

Here are the reported facts.

Also on October twelfth, GitHub announced a limited public preview for durable push attribution. GitHub now records the authenticated user who pushed each commit and exposes that pusher identity beside the author and committer fields.

Git author and committer names and email addresses are strings supplied by the client. A user with repository write access can set them to another identity. GitHub already authenticates the push connection; the new feature durably associates that authenticated pusher with each commit.

GitHub also introduced a repository rule condition called “Committer must match pusher.” It can block a push when the committer metadata does not match a verified email address belonging to the authenticated pusher.

The preview is available to GitHub Enterprise customers through their account team.

Now the analysis.

This illustrates the difference between claimed identity and observed identity.

The commit says who authored the content and who committed it. The server knows which credential actually delivered it. Those facts can legitimately differ: an integrator may commit someone else’s patch, a bot may push generated changes, or a release service may promote a signed commit. The mistake is collapsing them into one ambiguous “user” field.

Agent workflows need the same separation.

Who requested the task? Which model generated the proposal? Which service identity called the tool? Which human approved the action? Which runtime executed it? Which system accepted the final write?

If an AI coding agent creates a commit, a CI service signs it, and a developer pushes it, attribution should preserve all three roles. Otherwise an investigation sees only the friendly display name embedded in metadata.

In a factory setting, this is the difference between the operator logged into the HMI, the control program that generated a command, the PLC that transmitted it, and the remote I/O module that energized an output. Good audit design records the chain rather than pretending one identity performed every step.

### Segment three: Cross-region inference separates the request endpoint from execution location

Here are the reported facts.

On October twelfth, AWS published guidance for accessing OpenAI GPT-6 Sol, Luna, and Astra through Amazon Bedrock cross-region inference from Thailand, Malaysia, Singapore, Indonesia, and Taiwan.

Applications call the Bedrock runtime endpoint in their source region through Converse or OpenAI-compatible APIs. An inference profile can route execution to supported capacity in other regions. AWS describes both geographic profiles, which constrain processing to a defined geography, and global profiles, which can use supported commercial regions worldwide.

Permissions must allow use of the inference profile and its potential destination regions. AWS notes that service-control policies can unintentionally block routing. Global profiles may require policies that account for an unspecified requested region.

CloudWatch and CloudTrail records remain in the source region. CloudTrail includes an inference-region field identifying where the request was processed. AWS says cross-region traffic remains on its network and is encrypted in transit.

AWS documentation positions global profiles for broader capacity and lower pricing, while geographic profiles are the appropriate choice when processing must remain inside a compliance boundary. Inference profiles do not currently support provisioned throughput.

Now the analysis.

An endpoint location is not necessarily an execution location.

That distinction matters for capacity, latency, legal processing boundaries, incident investigation, and cost. A dashboard grouped only by source endpoint can look healthy while one destination region throttles or adds tail latency. A compliance review can fail if it assumes that sending a request to Singapore guarantees processing in Singapore.

The source region acts as the stable control and observation point, while the data plane may use capacity elsewhere. Your trace should preserve both locations, the profile selected, model identifier, request quota, latency, error class, and policy decision that allowed the route.

### Playground Lesson: Control plane, data plane, and observability plane

These three planes are a powerful way to reason about complex systems.

The data plane performs the useful work. In networking, it forwards packets. In a streaming system, it moves events. In AI inference, it transports prompts, runs model computation, and returns tokens. In the Factory AI Engineer, it reads manuals and historian samples, invokes the model, and passes a proposed diagnosis through the workflow.

The control plane decides how that work should happen. It manages identities, policies, routes, schemas, tool availability, quotas, model selection, deployment versions, and approvals. It does not need to touch every data byte, but it determines which paths are legal.

The observability plane records enough evidence to understand performance, decisions, and failures. It carries metrics, logs, traces, audit events, and evaluation results to systems that operators can query without interfering with the primary transaction.

Think about a plant network. The data plane contains real-time I/O, controller traffic, and historian values. The control plane contains configuration, access rules, device identities, routing, and change authority. The observability plane contains alarms, diagnostics, event logs, asset health, and performance trends.

Separating the planes prevents accidental coupling.

If telemetry blocks the production request whenever the collector is down, the observability plane has become an availability dependency. If a model can edit the policy that authorizes its own tools, the data plane has captured the control plane. If administrators must inspect raw prompts to measure latency, the observability plane is collecting far more sensitive data than the metric requires.

For the capstone, draw four boxes inside the control plane.

First is identity: the requesting user, agent runtime, tool service, and approver.

Second is policy: allowed data sources, read-only boundaries, forbidden tools, approval requirements, and hard stop conditions.

Third is routing: which model, retrieval index, historian adapter, or regional endpoint receives the request.

Fourth is version state: prompt, tool schema, model, policy, and evaluator versions.

Then define the data-plane transaction. Give it a trace ID and a task ID. Each model call, retrieval, tool call, validation, and proposed action becomes a span or structured event connected to that transaction.

Trace propagation must cross asynchronous boundaries. If a tool request enters a queue, the worker should continue the logical trace while creating its own execution span. If one event fans out to three tools, preserve a link from every branch to the originating task. Wall-clock nesting alone is not enough because queued work may begin after the parent request has returned. Record causality explicitly.

Be careful with metric cardinality. Task IDs, usernames, document identifiers, and raw tool names can create millions of time-series combinations if used as metric labels. Keep metrics low-cardinality: service, environment, model family, status, and gate type. Put per-request identities in traces or structured logs, where they can be indexed selectively. This is similar to keeping fast dashboard tags bounded while storing detailed batch and serial-number records in the historian or event database.

Do not overload identity fields. Record at least the requester, effective service principal, model, executor, and approver separately. A single `user` field cannot explain delegated authority.

Now design telemetry from questions instead of available data.

For reliability: what failed, where, and after how much latency? Capture timestamps, component names, status, retry count, and error class.

For safety: did the workflow request a forbidden tool, miss an abstention, or accept an invalid citation? Capture the gate result and evidence identifiers, not necessarily the entire source document.

For cost: which tenant, task type, model, and route consumed tokens or tool capacity? Capture counts and dimensions without retaining the prompt.

For investigation: who requested, approved, executed, and persisted the effect? Capture durable identities and operation IDs.

Content capture should be an escalation mode, not the default. When a defect requires inspecting prompts or tool outputs, enable narrowly scoped capture for a controlled cohort, shorten retention, restrict access, and disable it after the question is answered.

The observability pipeline itself needs backpressure and failure policy. Metrics may be sampled. Security audit events may require durable delivery. Debug logs may be dropped under overload. Do not treat every signal as equally critical.

Document those priorities before the collector or network becomes saturated.

Finally, connect evaluation to production traces. The same task ID and gate names used by the offline evaluator should appear in runtime telemetry. That creates a bridge between “this scenario passed in test” and “this production request encountered the same condition.” Without shared identifiers, evaluation and operations become separate stories.

### Playground checkpoint — unchanged

The repository still does not contain `evals/score_run.py` or `evals/sample_run.jsonl`, so this remains the only assigned checkpoint. Do not add another task until these files appear in GitHub.

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

Compute diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. Emit either pass or stop.

Make these mandatory stop conditions: a forbidden tool call, an invalid citation, or a missed required abstention. Print the exact task ID and failed gate.

Use four clean cases and one unsafe-write case. Prove that good averages cannot override the mandatory stop. Then remove the violation and confirm that the same run passes.

This should take roughly twenty to thirty minutes.

### Practical takeaway

Pick one agent workflow and write three short inventories: what performs the work, what controls the work, and what observes the work. Any component appearing in all three lists deserves scrutiny because it may have too much authority or create an avoidable failure dependency.

### Closing recap

GitHub now lets enterprises attribute Copilot telemetry to authenticated users without automatically collecting prompts, responses, or tool content.

GitHub’s push attribution separates client-supplied author and committer metadata from the authenticated account that delivered the commit.

AWS cross-region inference separates the stable source endpoint and monitoring location from the region that performs model computation.

And the architecture lesson is to keep control, data, and observability responsibilities distinct while connecting them through durable identities, task IDs, policies, and versioned evidence.

That’s today’s Engineering Commute. Have a good Tuesday.

## Compact show notes

- **Copilot telemetry controls — October 12, 2026:** Independent capture settings for identity, prompts, responses, tool arguments, tool output, and policy details through OpenTelemetry. [GitHub changelog](https://github.blog/changelog/2026-10-12-client-telemetry-user-attribution-and-configurable-capture/)
- **Durable push attribution — October 12, 2026:** Authenticated pusher identity is recorded separately from client-supplied author and committer metadata, with an optional repository rule requiring a verified match. [GitHub changelog](https://github.blog/changelog/2026-10-12-push-attribution-public-preview/)
- **Bedrock cross-region inference — October 12, 2026:** OpenAI GPT model access from five Asia-Pacific source regions, inference profiles, IAM and SCP configuration, quotas, and source-region monitoring. [AWS technical guide](https://aws.amazon.com/blogs/machine-learning/accessing-openai-gpt-models-on-amazon-bedrock-with-global-cross-region-inference-in-thailand-malaysia-singapore-indonesia-and-taiwan/)
- **Cross-region routing reference:** Geographic versus global profiles, destination-region visibility, pricing, compliance considerations, and CloudTrail’s inference-region field. [Amazon Bedrock documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html)
- **Playground:** [Repository overview](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/README.md), [modules](https://github.com/danthemanhernan/AiSystemsEngPlayground/tree/main/modules), [labs](https://github.com/danthemanhernan/AiSystemsEngPlayground/tree/main/labs), [capstone module](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/13_capstone.md), and [current repository commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d).
- **Checkpoint:** Unchanged. Create `evals/score_run.py` and `evals/sample_run.jsonl`; demonstrate that forbidden tools, invalid citations, and missed abstentions force a stop even when aggregate metrics pass.
- **Estimated runtime:** Approximately 15 minutes; about 2,200 spoken words.
