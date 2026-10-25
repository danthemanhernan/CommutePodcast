# The Engineering Commute — September 19, 2026

## Narration-ready episode

Good morning, Dan.

Today’s Engineering Commute is about model routing: how an AI system decides which model should handle a request, when a small model is genuinely good enough, and when the system should spend more time and money—or refuse to proceed.

Two current developments make the topic concrete.

GitHub is rolling out cost, quality, and response-time settings for automatic model selection, while also announcing that several Copilot models will disappear in October.

And GitHub Actions is preparing to move the meaning of `ubuntu-latest` from Ubuntu twenty-four oh four to Ubuntu twenty-six oh four.

One story is explicitly about model choice. The other looks like ordinary CI infrastructure. Both expose the same engineering principle: a symbolic label is not a permanent contract. The thing behind the label can change, so production systems need explicit requirements, compatibility tests, observability, and a safe fallback.

Then we’ll spend most of the episode on the Playground Lesson: designing a model router for the Factory AI Engineer. We’ll cover routing signals, policy layers, quality floors, cascades, confidence, verification, failure handling, cost accounting, and drift.

And because the capstone evaluator checkpoint is still unfinished in the repository, the checkpoint at the end remains exactly the same. No new backlog item today.

### Current development one: model selection is becoming a product policy

Here are the reported facts.

On September eighteenth, GitHub summarized its latest Copilot releases. Copilot’s automatic model selection now offers three modes called efficiency, balance, and intelligence. GitHub says the modes let users choose how the selector weighs cost, quality, and response time. All three choose from the same pool of available models; the difference is the selection policy.

The release also adds usage metrics for the dedicated agents window in Visual Studio Code, including daily active users, session counts, and user-message totals. Separately, GitHub’s Copilot command-line metrics now report activity involving skills, custom agents, MCP servers, slash commands, and plugins.

Also on September eighteenth, GitHub announced that six model entries will be removed from Copilot on October nineteenth. The list includes Gemini three point seven Flash, GPT five point five, GPT five point four, GPT five point four mini, GPT five mini, and Grok four point five. GitHub named newer suggested alternatives and said administrators may need to enable those alternatives depending on their model-policy settings.

That is the factual report. Here is the engineering interpretation.

The important part of efficiency, balance, and intelligence is not the branding. It is the admission that model selection is multi-objective scheduling.

There is rarely one model that is simultaneously cheapest, fastest, most capable, easiest to host, safest for sensitive data, best at tool use, and most reliable for every task. A router chooses an operating point.

But three user-facing modes are not enough to describe a production policy. If “efficiency” sends a safety analysis to a cheap model, or “intelligence” sends every spelling correction to the most expensive model, the label has hidden a bad decision.

The enterprise question is not, “Which mode do we like?” It is, “What guarantees does each task class require, and what evidence proves the selected route meets them?”

The deprecation notice adds lifecycle pressure. A router that refers directly to one vendor model name in dozens of applications will become brittle. When that model is retired, every application inherits the migration event.

A better architecture routes through capabilities and policy. An application requests something like: code review, tool use required, twenty-thousand-token context, structured JSON, maximum five-second latency, medium consequence, and no external data retention. The routing service maps that contract to a currently approved deployment.

The difference is similar to requesting an industrial motor by duty, enclosure, voltage, torque, and hazardous-location rating instead of writing one supplier’s exact catalog number into every machine program. The catalog choice can change. The application’s engineering requirement should remain legible.

That abstraction does not eliminate model migrations. It makes them testable in one place. Before replacing a model, replay representative requests, compare task success, tool-call correctness, latency, token use, and cost, then promote the new mapping under version control.

One caution on the new usage metrics: usage is not value.

An MCP server with many connection attempts may be popular, unreliable, or simply configured to reconnect too often. A skill with many invocations may save hours, or it may be a noisy default. GitHub explicitly notes that MCP interaction counts represent connection or reconnection attempts, successful and failed, rather than every tool call.

That is a useful reminder for any AI platform. Adoption metrics tell you what is happening. They do not tell you whether the work is correct, safe, or economical. Pair activity with outcome measures.

### Current development two: `latest` is a routing alias too

Here are the reported facts.

On September seventeenth, GitHub made the Ubuntu twenty-six oh four runner image generally available for production GitHub Actions workflows on both x sixty-four and Arm sixty-four.

Workflows can select it explicitly with the Ubuntu twenty-six oh four labels. GitHub warns that the image includes updated tools and, in some cases, removed tools compared with earlier images.

Between October nineteenth and November nineteenth, the `ubuntu-latest` label will gradually move from Ubuntu twenty-four oh four to Ubuntu twenty-six oh four. GitHub recommends testing against the new image before the migration. Teams that are not ready can pin Ubuntu twenty-four oh four.

Now the analysis.

`ubuntu-latest` is a tiny router. The workflow asks for an abstract destination, and the platform resolves that alias to a concrete runtime image.

The alias is convenient because applications automatically receive a supported environment. It is risky when teams mistake “latest” for “unchanging.”

Model aliases create the same tension. An alias such as `fast-model` or `best-available` lets the platform upgrade its target. That can improve quality without application changes. It can also change tokenization, tool behavior, latency, output style, safety refusals, or cost.

The answer is not always to pin everything forever. Permanent pinning avoids surprise but also avoids patches, improvements, and supported upgrades. The answer is controlled movement.

Use a floating alias in a test lane first. Replay contract tests. Compare the candidate with the current target. Hold the old target as a rollback option. Promote the alias only after the new target meets its requirements.

In controls terms, this is a changeover procedure. You do not swap a sensor type because the new catalog revision is called “current.” You confirm range, scaling, wiring, update rate, failure behavior, and the effect on the loop. Then you commission the change with a rollback plan.

The practical CI action is simple: add an Ubuntu twenty-six oh four matrix job now, discover hidden assumptions, and either fix them or pin the old image temporarily. The larger lesson is that every moving alias needs a qualification boundary.

### Playground Lesson: model routing is a quality-control system

I inspected the AI Systems Engineering Playground through GitHub this morning: the README, curriculum modules, labs, recent commits, model-router code, and Factory AI Engineer capstone.

The latest commit remains the September ninth curriculum expansion. The repository still has no evaluator implementation, so the existing capstone checkpoint remains open.

The next useful curriculum topic is Module Seven: Nexus-style model routing. Its lab contains three mock models: a small open model, a coding model, and a frontier reasoner. Each model has a quality score, latency, cost, and set of skills. The router filters by skill and latency, computes a quality threshold from task difficulty, and chooses the cheapest model that clears that threshold.

That is a good teaching scaffold. Now let’s turn it into a production mental model.

#### First principle: route the work, not the wording

A user prompt is not yet a task specification.

Consider these three requests:

“Summarize this alarm log.”

“Summarize this alarm log and identify the most likely failed device.”

“Summarize this alarm log, identify the failed device, and tell the operator whether it is safe to restart the cell.”

They share words and source data, but they do not carry the same consequence.

The first is transformation. The second is diagnosis. The third may influence a physical action.

A router that classifies only by topic might send all three to the same summarization model. A useful router represents the requested effect.

For the Factory AI Engineer, request attributes could include intent, consequence, required tools, context length, response schema, data sensitivity, maximum latency, budget, freshness requirement, and whether the result can cause an external action.

Think of the router as a manufacturing dispatch system. It does not send a part to a machine merely because the operator called it a “bracket.” It considers material, tolerance, dimensions, inspection plan, due date, and whether the process is qualified for that part family.

The language model is a work center. The request is a job traveler. The route is valid only when the work center’s demonstrated capability matches the traveler’s requirements.

#### The hard-policy layer comes before optimization

Model routing is often described as choosing the best model. Production routing should begin by eliminating forbidden choices.

Hard constraints might say:

Plant-confidential data may not leave an approved environment.

A model that cannot produce the required structured schema is ineligible.

A model without tested tool calling may not enter an agent loop.

A safety-relevant conclusion requires either a validated specialist model or human review.

A request containing regulated personal data may use only deployments with the approved retention policy and region.

These are permissives, not preferences.

In a PLC sequence, you do not calculate which motion path is fastest and then check the guard door. You check the safety conditions first. Only legal states enter the optimizer.

This gives the router two conceptual stages.

Stage one is admission: which models are allowed to handle this request?

Stage two is optimization: among the allowed models, which route best meets cost, latency, and quality objectives?

Keeping those stages separate makes policy review easier. It also prevents an optimizer from trading away a safety boundary because another route scored slightly better on price.

#### Quality floors are better than vague rankings

Suppose model A succeeds on ninety-four percent of routine classification tasks and costs one tenth as much as model B, which succeeds on ninety-seven percent.

Which is better?

There is no answer until we define the task’s acceptable failure rate and the cost of each error type.

For classifying internal support tickets, ninety-four percent may be excellent if uncertain cases enter a manual queue. For identifying whether a maintenance procedure applies to a high-voltage cabinet, a three-point difference may be unacceptable—and average success may hide the rare case we care about.

A quality floor converts “better model” into “adequate for this contract.” Once all eligible models clear the floor, the router can minimize cost or latency.

But the floor must come from evaluations, not a vendor benchmark or one universal score.

For the Factory AI Engineer, create task-specific measures:

For alarm classification, measure per-class precision and recall, especially for rare critical alarms.

For retrieval-grounded diagnosis, measure required-evidence coverage, citation validity, and whether the diagnosis contradicts the cited evidence.

For tool use, measure correct tool selection, argument validity, forbidden-call rate, and recovery from timeouts.

For structured reports, measure schema validity and required fields.

For safety behavior, measure required abstention and escalation.

The router’s quality estimate should point to that evidence. A made-up scalar such as “model quality equals eighty-four” is fine for a toy lab. In production, the number needs provenance: evaluation set, model version, prompt version, tool schema version, sample size, date, and uncertainty.

#### Static routing, learned routing, and cascades

There are three common routing patterns.

The first is static policy.

If the task is document classification and the input is under four thousand tokens, use the small model. If the task is code generation, use the coding model. If the task is safety-relevant diagnosis, use the frontier model and require review.

Static rules are understandable, testable, and easy to audit. Their weakness is that reality contains ambiguous requests and models change.

The second pattern is a learned router.

A classifier or scoring model predicts which candidate is likely to succeed. Its input may include prompt features, embeddings, task history, context length, or expected tool use. It can learn finer boundaries than hand-written rules.

But now the router itself is a model. It can drift, fail on novel inputs, and optimize the wrong label. It needs evaluation and observability like any other prediction system.

The third pattern is a cascade.

Send the request to a cheap model first. If its output clears a confidence or verification gate, return it. Otherwise escalate to a stronger model.

A cascade resembles graduated inspection. A fast gauge checks every part. Borderline or high-consequence parts move to a slower coordinate-measuring machine. You save inspection capacity without lowering the acceptance requirement.

The critical word is verification.

Self-reported confidence is often weak evidence. A model can be confidently wrong. Stronger gates use signals outside the generated prose: schema validation, deterministic tests, retrieval coverage, citation resolution, agreement with another independent method, or a calibrated classifier trained on past outcomes.

For a code task, run the tests. For a database query, check syntax, permissions, estimated scan cost, and perhaps execute it in a read-only sandbox. For a diagnosis, verify that every asserted tag value exists in tool output and every procedure citation resolves to the correct document revision.

If the system cannot verify the important property, it should not pretend that a confidence score proves it.

#### Fallback is not the same as escalation

These terms are easy to blur.

A fallback handles unavailability. The preferred model times out, hits a quota, or becomes unhealthy, so the router selects another compatible deployment.

An escalation handles uncertainty or consequence. The first model completed normally, but the result did not clear the quality gate, or the task’s risk requires a stronger path.

A second opinion is different again. Two routes evaluate the same problem independently, and a reconciler compares them.

Those paths need different telemetry. A timeout fallback is an infrastructure event. A quality escalation is a model-performance event. A disagreement between two models is an uncertainty signal. Combining all three under a field called `used_backup` destroys useful information.

Also decide whether a fallback is truly compatible.

If the primary model supports a fifty-thousand-token context and the backup supports eight thousand, silently truncating the request is not graceful degradation. If the primary model can call tools and the backup cannot, returning a plausible answer without evidence is not recovery.

A safe router may return “temporarily unavailable” instead of producing a lower-integrity answer. Availability is not the only objective.

#### Route by total job cost, not token price alone

Model price tables tempt teams to optimize input and output tokens. That is only one part of the cost.

Total job cost can include classification, retrieval, prompt construction, model inference, tool calls, retries, verification, human review, and the cost of a wrong result.

A cheap model that fails twice and escalates may cost more than sending the job to the stronger model first. A slower model may hold scarce GPU memory longer and reduce system throughput. A local model may have no per-token invoice but still consume hardware, power, operations time, and deployment effort.

For a factory system, include the operational consequence. A false alarm can waste technician time. A missed fault can extend downtime. A confident unsafe recommendation can be unacceptable regardless of token savings.

This is similar to maintenance economics. The cheapest replacement bearing is not cheapest if it fails early and stops the line. Procurement price is not lifecycle cost.

Track cost per successful task, not merely cost per request. Break it down by task class and route. Include escalations and failed attempts.

#### Latency is a distribution and a budget

A router also needs to understand latency as more than an average.

The total response includes queue time, prefill, decode, retrieval, tools, verification, and possible escalation. A two-stage cascade may have excellent median cost but poor tail latency because difficult requests pay for both models.

Allocate a latency budget across the path.

For example: one hundred milliseconds for classification, five hundred for retrieval, four seconds for the first model, one second for verification, and eight seconds reserved for escalation.

If the first stage consumes the entire deadline, the fallback exists only on paper.

In control systems, a component can meet its own scan-time target while the complete loop misses its response requirement. End-to-end timing is the contract.

Measure median, ninety-fifth, and ninety-ninth percentile latency by route and task. Record queue time separately from execution. When the system is overloaded, the routing policy may deliberately shed low-priority work or choose a degraded but qualified route.

#### Caching is another route with a freshness contract

A cache can be the cheapest and fastest model: no model call at all.

But semantic caching is dangerous when two prompts look similar while their required answers differ.

“What is the restart procedure for weld controller revision A?” is not equivalent to revision B. “Why did Line Four stop?” may have a different answer five minutes later.

A cache key needs the inputs that determine validity: equipment identity, document revision, data timestamp, policy version, user permissions, model or prompt version when relevant, and a time-to-live appropriate to the task.

Cache only outputs that remain valid under an explicit freshness policy. Never let an old diagnosis masquerade as a current plant observation.

#### Observability should explain every route

When a router makes a decision, log enough to reconstruct it without storing sensitive raw prompts unnecessarily.

Useful fields include request ID, task class, consequence level, required capabilities, eligible candidates, rejected candidates and reasons, chosen model and version, policy version, estimated quality, latency budget, actual latency, cost, cache status, fallback or escalation reason, verifier results, and final outcome.

The decision record should answer:

Why was this model allowed?

Why was another model rejected?

Did the selected model meet its quality floor?

Did the request escalate?

What changed when routing behavior shifted?

This is the AI equivalent of a sequence-of-events record. A final alarm tells you that something went wrong. A timestamped transition history lets you diagnose why.

#### Drift happens even when your code does not change

Model providers update deployments. A model name may be retired. Prices change. Traffic mix changes. Prompt templates evolve. Tool schemas gain fields. Documents get revised. A classifier sees new request types.

Therefore routing quality can drift while the routing code is untouched.

Use a replay set of representative, difficult, and safety-relevant tasks. Run it when a model, prompt, tool, retrieval index, or policy changes. Also sample production outcomes and add newly observed failures to the evaluation set.

Monitor route share over time. If the small model previously handled seventy percent of requests and suddenly handles ninety-five percent, that may be an efficiency win—or a broken difficulty classifier. If escalation rises, the first-stage model may be degrading or the workload may have changed.

Treat route distribution like a process variable. Establish expected bands, investigate shifts, and connect them to versions and deployments.

#### Applying this to the Factory AI Engineer

Now assemble a practical architecture.

The chat gateway receives the operator’s question and attaches identity, site, asset, and request time.

A deterministic policy layer identifies prohibited data paths and whether the request could influence a plant action.

A lightweight classifier labels the task: lookup, summarization, retrieval-grounded diagnosis, code help, or action proposal. It also estimates context length and required tools.

The router selects from deployments that meet the hard constraints.

Routine document lookup can use a small local model with retrieval. A code-generation request can use the coding model. A complex diagnosis can use a frontier reasoner, but it still receives bounded tools and read-only plant access.

The output passes through verifiers. Citations must resolve. Required evidence must be present. Structured fields must validate. Forbidden tools must never appear. A safety-relevant recommendation must abstain or request review when evidence is insufficient.

If the first route fails a soft quality check, the system escalates. If it violates a hard safety check, the run stops. It does not shop around for a model willing to say yes.

That last distinction matters. A fallback chain must not become policy laundering. If one model refuses a hazardous instruction, routing the same request through five models until one complies is the opposite of safety.

The policy boundary belongs outside the models and applies to every route.

### Capstone checkpoint — unchanged

The repository still does not show completion of the existing evaluator checkpoint, so this is the same task as before.

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

Compute diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. Emit either pass or stop.

Make these mandatory stop conditions: a forbidden tool call, an invalid citation, or a missed required abstention. Print the exact task ID and failed gate.

Use four clean cases and one unsafe-write case. Prove that good averages cannot override the mandatory stop. Then remove the violation and confirm that the same run passes.

This remains the checkpoint because it supplies the quality gate that a future model router needs. Until the evaluator can distinguish acceptable work from unsafe work, optimizing route selection would be premature.

### Practical takeaway

For one AI workflow, replace the question “Which model should we use?” with a routing contract.

Write down the task class, hard eligibility rules, quality floor, latency budget, cost measure, verification gate, escalation rule, and stop condition.

If the route cannot explain why a model was eligible and what evidence proved the result acceptable, it is selection—not engineering.

### Closing recap

GitHub’s new Copilot selection modes make cost, quality, and response time explicit routing objectives. Its model deprecations show why applications should depend on capability contracts and tested aliases rather than scattered model names.

The coming GitHub Actions migration from Ubuntu twenty-four oh four to twenty-six oh four shows the same pattern in CI: a convenient alias can move, so qualify the new target before it becomes production reality.

And in the Playground, model routing is a quality-control system.

Hard policy determines what is allowed.

Task-specific evaluation establishes the quality floor.

The router optimizes among qualified choices.

Verifiers decide whether the result may pass, escalate, or stop.

Observability explains the decision.

And the unfinished evaluator checkpoint remains the right next step, because a router cannot optimize toward a standard the system has not yet encoded.

That’s today’s Engineering Commute.

Have a good Saturday.

## Compact show notes

- **Copilot model selection and agent updates — September 18:** Automatic model selection adds efficiency, balance, and intelligence policies that weigh cost, quality, and response time; the same weekly release covers agent metrics, multi-agent Lite reviews, shell-assisted review validation, Sentry integration, and local Dev Containers. [GitHub weekly release](https://github.blog/changelog/2026-09-18-github-copilot-weekly-releases-september-14/)

- **Copilot model lifecycle — September 18:** Six model entries are scheduled for retirement on October 19, with suggested replacements and administrator-policy considerations. [GitHub deprecation notice](https://github.blog/changelog/2026-09-18-upcoming-deprecation-of-selected-github-copilot-models-in-mid-october/)

- **Ubuntu 26.04 Actions runners — September 17:** The x64 and Arm64 images are generally available; `ubuntu-latest` will migrate from 24.04 to 26.04 between October 19 and November 19. [GitHub Actions announcement](https://github.blog/changelog/2026-09-17-ubuntu-26-generally-available-and-latest-migration/)

- **Agentic CLI metrics — September 17:** Usage reports now include top skills, custom agents, MCP servers, slash commands, and plugins, with important interpretation limits for connection attempts and custom names. [GitHub metrics announcement](https://github.blog/changelog/2026-09-17-agentic-cli-customizations-now-in-the-usage-metrics-api/)

- **Playground:** [Course roadmap](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/README.md), [Module 7: Nexus-style model routing](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/07_model_routing_nexus.md), [model-router lab](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/labs/07_model_router/router.py), [Factory AI Engineer capstone](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/projects/capstone_factory_ai_engineer/README.md), and [latest repository commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d).

- **Unchanged checkpoint:** Create `evals/score_run.py` and `evals/sample_run.jsonl`; score diagnosis pass rate, evidence coverage, citation validity, tool calls, and latency; enforce mandatory stops for forbidden tools, invalid citations, and missed abstention; prove averages cannot mask the unsafe-write case; then remove the violation and confirm a pass.

- **Estimated spoken runtime:** Approximately 25–26 minutes; roughly 3,750 spoken words.
