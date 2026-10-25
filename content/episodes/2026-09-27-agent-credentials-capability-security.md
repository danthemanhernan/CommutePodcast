# The Engineering Commute — September 27, 2026

## Narration-ready episode

Good morning, Dan.

Today’s Engineering Commute is about giving an AI system enough authority to work without giving it enough authority to become an incident.

The Model Context Protocol TypeScript SDK has added request-level authorization challenges, sender-constrained tokens, and stricter transport limits. ClickHouse has introduced short-lived, reduced-privilege tokens for applications and agents. And GitHub now validates centrally managed Copilot policy files before administrators depend on them.

Those developments lead into today’s Playground Lesson: capability security for AI integrations. We’ll separate identity from authority, examine how scopes, expiry, token binding, and resource limits work together, and map the design to controls concepts such as keyed mode selection, temporary work permits, and independent protective limits.

The AI Systems Engineering Playground has not changed since the September ninth commit. Its evaluator files are still missing, so the existing checkpoint remains the only assignment. No new backlog item today.

### Segment one: MCP authorization becomes more specific and more defensive

First, the reported facts.

On September twenty-third, the official Model Context Protocol TypeScript SDK released version two-point-one of its server and client packages, alongside a one-point-thirty-one maintenance release for the older line.

The server can now require additional OAuth scopes at request time for individual tools, resources, resource templates, and prompts. If a caller lacks a required scope, the SDK returns a forbidden response with an insufficient-scope challenge before it starts the handler or establishes a streaming response.

The client also adds support for Demonstrating Proof of Possession, usually called D-PoP. A client creates a signed proof for a particular request, binding use of the access token to a cryptographic key. The implementation includes nonce handling so a server can require a fresh proof.

The release also puts explicit limits around the protocol surface. Streamable HTTP request bodies are capped at four mebibytes by default. JSON-RPC batch arrays are capped at one hundred items. Oversized inputs are rejected before dispatch. Host and origin validation now occur before JSON parsing, and the release fixes handling of request identifier zero, which previously could be mishandled as a false-like value in cancellation and request-association paths.

Now, the engineering analysis.

Request-time scopes change the authorization model from “connect once and receive broad powers” to “prove the required authority at the operation boundary.” That matters because MCP servers often combine harmless lookup tools with consequential actions. Reading a maintenance manual and closing a work order may share one server but should not share one permission decision.

Think of a plant badge. The badge proves who entered the building. It does not automatically authorize that person to place a line in manual mode, bypass an interlock, or modify a safety setpoint. Those actions need separate authority at the point of use.

D-PoP addresses a different failure. An ordinary bearer token behaves like a copied door code: whoever possesses it can use it. A sender-constrained token is closer to a badge that must be presented with a live cryptographic signature from the enrolled device. Stealing the token string alone is no longer sufficient.

That does not make the client trustworthy. Malware with access to the private key may still act, and an authorized client can still make a harmful request. But it narrows the credential-theft failure mode.

The body and batch limits are equally important. Authorization controls what a caller may attempt. Resource limits bound how much work one accepted request can force the server to perform. A four-mebibyte input ceiling and one-hundred-item batch ceiling act like a fuse: they do not determine whether the machine should run, but they stop an allowed circuit from drawing unbounded current.

For an agent platform, use all three layers. Authenticate the caller. Authorize the specific operation. Then constrain the cost and shape of the request even after authorization succeeds.

### Segment two: ClickHouse adds temporary, reduced-privilege credentials

The second development comes from ClickHouse release twenty-six-point-nine, published September twenty-third.

Here are the reported facts.

ClickHouse says the release contains fifty-six features, one hundred thirty-five performance improvements, and four hundred sixty-four bug fixes. Data-platform additions include disk spilling for high-cardinality distinct operations, incremental refreshes for append-only materialized views, conditional limit boundaries, and expanded PromQL support in its preview time-series engine.

The security feature most relevant today is the new create-token command.

An administrator or user can mint a time-limited credential for an application, script, continuous-integration job, or agent. The token can be restricted to a subset of the parent user’s existing privileges. It cannot grant authority the parent does not already possess. It stops working when it expires or when the parent user is removed, and the token value is displayed only once. If no duration is supplied, the documented default lifetime is thirty minutes.

Now, the analysis.

This is a useful alternative to giving an AI worker a permanent database password.

Suppose a diagnostic agent needs to investigate a compressor-temperature anomaly. It may require select access to telemetry and maintenance tables for ten minutes. It does not need the ability to alter tables, create users, inspect unrelated financial data, or retain access next week.

A good token broker can translate the approved task into a narrow credential: read these schemas, under this identity, until this expiry. The model never needs to see the long-lived parent secret.

The controls analogy is a temporary work permit. A contractor may be qualified and known to the site, but the permit still names the equipment, allowed work, isolation state, and expiration time. Identity is necessary. It is not the complete authorization contract.

Short lifetimes reduce exposure, but they also create operational questions. What happens when a query runs past expiry? Can a retry silently obtain a fresh token? Does the audit trail preserve the original task identity? Can the agent request broader privileges after a denial?

The safest pattern separates planning from credential issuance. The model proposes an operation. A deterministic policy layer checks the tool, resource, requested scope, task identity, and approval state. Only then does a broker mint or retrieve the minimum credential. The executor uses it without returning the secret to the model transcript.

ClickHouse’s other release features reinforce a related lesson: efficiency features need operating limits. Disk spilling can prevent a high-cardinality distinct query from exhausting memory, but it may exchange a memory failure for heavy disk traffic and long latency. Incremental materialized-view refreshes can reduce repeated work, but only when the append-only assumption is true. Capacity protection and semantic correctness are separate gates.

### Segment three: GitHub validates policy before relying on enforcement

The third development is smaller, but it closes an important governance gap.

Here are the reported facts.

On September twenty-fifth, GitHub announced an in-product validator for enterprise-managed Copilot settings. The validator checks policy files stored in the enterprise’s private configuration repository. It can detect malformed JSON, unsupported configuration, invalid team mappings, and other errors that prevent settings from being enforced. It identifies the affected file and JSON path so an administrator can correct the problem, commit the fix to the default branch, and review the result again from the Agents administration page.

Now, the analysis.

Policy-as-code is only policy when the enforcement system can parse and apply it.

A configuration file may exist, pass code review, and communicate human intent while still failing open or failing to load because of one invalid field. That resembles writing a permissive value into a PLC data block while assuming the safety controller consumed it. The text is not the protection. The active, validated runtime state is the protection.

For agent systems, validation should cover more than syntax. Check that referenced teams exist, tool names resolve, scopes are supported, denied resources stay denied, and precedence rules produce the expected effective policy. Then test the negative path with an identity that should not have access.

Record the version of policy used for every consequential tool call. During an incident, “the repository contained the correct file” is weaker evidence than “this request was evaluated against commit X, rule Y, and was denied for reason Z.”

The connection across all three stories is straightforward. A scope definition, a temporary database token, and a managed settings file are representations of authority. Each representation must be narrow, valid, active, observable, and independently enforced.

### Playground Lesson: capability security for AI integrations

Let’s build the model from first principles.

Authentication answers: who or what is making this request?

Authorization answers: may that identity perform this action on this resource under these conditions?

A capability is concrete authority that the holder can exercise, often represented by a token, signed request, delegated credential, or unforgeable reference.

These concepts overlap, but they are not interchangeable. A service account can be strongly authenticated and still be overprivileged. A correctly scoped token can be stolen and replayed. A perfect policy can be bypassed if one execution path does not consult it.

Start with scope.

Scopes should describe operations a policy engine can enforce. “Database access” is too broad. “Read telemetry for site seven” is closer. For an MCP tool, combine the tool name with resource constraints and operation class. A maintenance agent might call get-asset-history for an allowed site, while update-work-order requires an additional write scope and human approval.

Avoid encoding every condition into one enormous scope string. Use scopes for stable permission classes, then evaluate dynamic attributes separately: site, asset, shift, incident ticket, environment, and approval status.

Next, minimize lifetime.

A permanent credential creates a long interval in which theft or accidental disclosure matters. A task-bound token reduces that interval. Its expiry should cover expected execution plus a small allowance, not the lifetime of the application.

But short-lived credentials need controlled renewal. If the agent can renew forever, expiry is cosmetic. Renewal should re-evaluate the task, current policy, and any approval requirement. A stopped or completed task should lose its path to fresh credentials.

Next, bind the credential.

Audience binding says which service may accept a token. Resource binding narrows what it can touch. Sender constraint, such as D-PoP, requires proof from the client’s key. These controls limit different forms of replay.

Imagine a hydraulic quick-connect. Possessing a hose is not enough. The coupling must match the correct port, and a keyed connector prevents attachment to the wrong circuit. Audience and resource constraints are those mechanical incompatibilities expressed in software.

Then separate decision from execution.

The language model can decide that a query would help, but it should not decide whether its own credential request is permissible. Put a deterministic broker between the planner and the tool. The broker receives a structured request containing task identity, action, resource, scope, expected cost, and approval reference. It returns a denial or a handle to an execution environment with bounded authority.

Prefer handles over raw secrets. If the model receives the token in its prompt or tool result, the credential can leak into traces, memory, error messages, or later model output. An executor can inject the secret directly into the outbound connection while logging only a token identifier and expiry.

Resource governance belongs in the same design.

A read-only query can still scan terabytes. A harmless MCP tool can still accept a gigantic document or a batch of thousands of calls. Define request-size, batch-size, timeout, concurrency, row-count, and cost limits. Treat them like current limits and travel limits: permission to energize does not remove the need for protection against overload.

Finally, make the system observable.

For every privileged operation, capture the task ID, authenticated principal, tool, resource, requested and granted scopes, policy version, decision, approval reference, credential expiry, latency, and outcome. Never log the raw token or private key. Alert on repeated insufficient-scope responses, unusual token minting, renewal loops, cross-site access attempts, and denials followed by a different tool that reaches the same effect.

Test the architecture with failure injection. Steal a token without its D-PoP key. Replay it against the wrong audience. Expire it between planning and execution. Remove a user. Submit an oversized body. Corrupt the policy JSON. Ask a read-only identity to reach a write effect through an alternate tool.

The goal is not merely to show that authorized work succeeds. It is to prove that each independent barrier fails safely.

### Playground checkpoint — unchanged

The repository still does not contain `evals/score_run.py` or `evals/sample_run.jsonl`, so this remains the only assigned checkpoint. Do not add another task until these files appear in GitHub.

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

Compute diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. Emit either pass or stop.

Make these mandatory stop conditions: a forbidden tool call, an invalid citation, or a missed required abstention. Print the exact task ID and failed gate.

Use four clean cases and one unsafe-write case. Prove that good averages cannot override the mandatory stop. Then remove the violation and confirm that the same run passes.

This should take roughly twenty to thirty minutes.

### Practical takeaway

Pick one agent integration and write down five fields: action, resource, maximum scope, credential lifetime, and hard resource limit.

If any field is “all,” “permanent,” or “unlimited,” replace it with the smallest value that still completes the task. Then verify that the enforcement occurs outside the model.

### Closing recap

The MCP TypeScript SDK now supports request-specific scope challenges, D-PoP, and tighter transport limits.

ClickHouse can issue temporary credentials that carry only a subset of a user’s privileges.

GitHub can validate managed Copilot policy files before administrators depend on their enforcement.

And the deeper architecture is consistent across all three: authenticate identity, grant narrow authority, bind it to the intended sender and resource, limit its lifetime and workload, and record the actual policy decision.

For AI systems, the model may request authority. It should not manufacture, expand, or validate that authority itself.

That’s today’s Engineering Commute.

Have a good Sunday.

## Compact show notes

- **MCP TypeScript SDK 2.1 — September 23:** Request-time OAuth scope challenges, DPoP support, bounded request bodies and batches, earlier Host/Origin checks, and request-ID fixes. [Official releases](https://github.com/modelcontextprotocol/typescript-sdk/releases) and [server 2.1.0 release](https://github.com/modelcontextprotocol/typescript-sdk/releases/tag/%40modelcontextprotocol%2Fserver%402.1.0). DPoP is standardized in [RFC 9449](https://www.rfc-editor.org/rfc/rfc9449).
- **ClickHouse 26.9 — September 23:** Short-lived reduced-privilege tokens plus data-platform improvements including DISTINCT spilling and incremental refreshes for append-only materialized views. [Official release article](https://clickhouse.com/blog/clickhouse-release-26-09).
- **GitHub managed-settings validator — September 25:** Validation for malformed or unenforceable enterprise Copilot settings, including file and JSON-path diagnostics. [GitHub changelog](https://github.blog/changelog/2026-09-25-enterprise-managed-settings-in-product-validator/).
- **Playground status:** No commits after September 9; the evaluator artifacts remain absent. [Roadmap](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/docs/roadmap.md), [MCP module](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/09_mcp_tools.md), [agents module](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/10_agents_workflows.md), [capstone](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/projects/capstone_factory_ai_engineer/README.md), and [current commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d).
- **Checkpoint:** Create the two missing evaluator files, prove that an unsafe-write case forces a stop, then fix that same case and confirm the run passes. No additional task is assigned.
- **Estimated runtime:** Approximately 15 minutes; narration target is about 2,200 spoken words.
