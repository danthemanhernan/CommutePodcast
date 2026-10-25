# The Engineering Commute — September 24, 2026

## Narration-ready episode

Good morning, Dan.

Today’s Engineering Commute is about containment and proof.

GitHub has added a local sandbox for Copilot agent sessions, with enforceable boundaries around files, networks, and credentials.

Kubernetes 1.37.1 fixes two device-allocation defects that could either make every device in a cluster unschedulable or crash the scheduler when a claim contained impossible counts.

Then we’ll spend most of the episode on grounded generation: how a RAG system turns retrieved passages into claims, citations, uncertainty, and a safe abstention—and how to verify that the answer did not outrun the evidence.

The AI Systems Engineering Playground has not changed since its September ninth curriculum expansion. The evaluator file is still absent, so the unfinished checkpoint at the end will remain unchanged.

### Current development one: GitHub gives local coding agents an enforceable work envelope

First, the reported facts.

On September twenty-third, GitHub announced local sandboxing in public preview for the GitHub Copilot app.

The sandbox is configured per project for local repository and working-tree sessions. Its filesystem policy can add read-write locations, add read-only locations, and deny folders. Its network policy controls outbound internet and local-network access. Credential settings separately govern authenticated HTTPS Git operations and GitHub CLI authentication.

GitHub says enterprise-managed settings may make the effective policy more restrictive than the policy requested by the project.

The fail-closed detail matters. If the operating system cannot enforce the requested policy, the sandboxed shell fails instead of silently starting without containment.

Sandboxing is off by default. Enabling it as a project default affects new sessions. An existing local session can be sandboxed with a command, while later policy changes require a restart. The settings do not cover cloud sandboxes or remote-host sessions, and Copilot app and Copilot CLI sandbox settings remain separate.

Now the engineering analysis.

An agent’s permission boundary should be treated like a machine cell, not like an instruction painted on the floor.

Telling a robot, “Do not enter this area,” is behavioral guidance. A guarded enclosure, safety-rated scanner, and interlocked gate create an independent physical constraint. The equivalent for a coding agent is that the process cannot open a denied directory, reach an unapproved endpoint, or inherit a credential—even if its plan, generated command, or a malicious repository instruction asks it to.

There are three distinct containment surfaces here.

The filesystem boundary limits what the agent can observe or modify. A useful default is read-write access to the working tree, read-only access to explicitly needed dependency caches or reference material, and denial of home-directory secrets, SSH keys, browser profiles, and unrelated repositories.

The network boundary limits what information can leave and what remote systems the agent can influence. A package install may need the public package registry. A test suite rarely needs the plant network, production database, or metadata service. If the task needs one endpoint, an allowlist is better than general outbound access.

The credential boundary limits authority. Network access without credentials may permit documentation lookup. The same network path plus a cloud token can permit deployment, deletion, or data extraction. Credentials should therefore be attached to the narrowest task that requires them rather than inherited automatically by every session.

Containment is not a claim that the model will misbehave. It is the acknowledgement that the complete input includes source code, comments, test fixtures, package metadata, tool output, and possibly adversarial text. Any of those inputs can redirect a flexible planner.

For the Factory AI Engineer, use the same architecture. A troubleshooting agent can read a simulated historian and maintenance corpus. It does not need write access to PLC tags. A future maintenance-work-order tool can require a separate scoped identity, an explicit approval, and a schema that cannot express arbitrary database mutations.

One subtle operational risk remains: policy drift.

If a project’s sandbox configuration changes, record the effective policy with each run. Otherwise, two sessions executing the same commit may have materially different authority. The trace should identify the repository revision, sandbox-policy revision, credential class, allowed network destinations, and every denied operation.

The important principle is simple: prompts express intent; the runtime enforces authority.

### Current development two: Kubernetes fixes dangerous ambiguity in device selection

Now the reported facts.

On September twenty-third, Kubernetes published patch releases across supported branches, including version 1.37.1.

Two fixes in 1.37.1 are especially relevant to accelerator clusters.

The first concerns Device Resource Allocation, or DRA. Kubernetes supports device taint rules that can make certain devices unavailable to workloads. A rule with no device selector was documented to match no devices. Instead, it incorrectly matched every device in the cluster. With a NoSchedule or NoExecute effect, one malformed rule could therefore make the entire DRA device inventory unschedulable.

The patch restores the documented behavior: an omitted selector matches nothing. An explicit empty selector matches all devices.

The second fix handles a ResourceClaim whose requested device counts add up beyond the integer range. That input could crash the scheduler or prevent the allocator from trying a smaller `firstAvailable` alternative. Kubernetes now rejects a request over the per-claim device limit with a named error, while an oversized alternative can fall through to a smaller valid choice.

The release also fixes a Windows kube-proxy panic and a kubeadm configuration issue, and moves the build to Go 1.26.8.

Now the analysis.

This is more than a pair of edge cases. It shows why absence, emptiness, and wildcard must be separate states in infrastructure APIs.

Imagine a selector on a factory work order.

An omitted asset list might mean, “This draft has not selected any machine.” An explicitly empty filter might mean, “Apply to every machine.” If software collapses those representations, a missing field can become a plant-wide command.

The same danger appears in agent tools. A missing `asset_ids` field must not quietly mean all assets. A missing time range must not mean all historical data. A missing approval identity must not mean anonymous authorization.

Model the states explicitly, validate them at the boundary, and write negative tests for omitted, null, empty, malformed, and oversized inputs.

The integer-overflow fix carries a related lesson. A scheduler is a control-plane service; rejecting one impossible claim is acceptable. Crashing or stalling placement for unrelated workloads is not. Boundary validation protects the shared decision-maker from tenant-shaped input.

For GPU inference clusters, DRA is particularly interesting because accelerators are not interchangeable scalar CPU units. A workload may need a GPU family, memory capacity, interconnect topology, driver compatibility, or a shareable partition. Rich selectors are useful, but rich selectors also create more ways for one ambiguous rule to remove capacity unexpectedly.

Monitor both demand and eligibility. If queued inference pods rise while reported GPU utilization stays low, do not conclude that you need more hardware until you inspect unschedulable reasons, claim failures, taints, topology constraints, and available device classes.

It is the same troubleshooting pattern as a conveyor with parts waiting upstream while a station appears idle. The problem may not be raw station capacity. An interlock, recipe mismatch, or routing rule may be preventing eligible work from entering.

### Playground Lesson: grounded generation, citation verification, and abstention

Now to the main lesson.

Yesterday we followed a query through eligibility filters, hybrid retrieval, reranking, deduplication, diversity control, and a finite evidence budget.

At the end of that pipeline, the model receives perhaps five passages. The next question is deceptively simple:

How do we know the answer is supported by those passages?

A RAG system has at least three truth boundaries.

Retrieval asks whether the needed evidence entered the candidate set.

Context assembly asks whether the needed evidence survived reranking and budgeting into the prompt.

Grounded generation asks whether each consequential claim in the answer follows from that evidence.

These failures must be separated. If the correct maintenance bulletin was never retrieved, changing the answer prompt is unlikely to fix the system. If the bulletin was retrieved at rank twelve but only five chunks were admitted, the failure belongs to ranking or budgeting. If the exact evidence was present but the model invented a cause, the failure belongs to generation or verification.

Think of this like an incident investigation.

The historian and maintenance records are raw evidence. Retrieval is the technician collecting relevant traces and documents. Context assembly is the evidence board placed in front of the review team. Generation is the written conclusion.

A polished report does not prove the investigation was sound. You need traceability from each conclusion back to the observations that justify it.

#### Start with an answer contract

Do not ask only for free-form prose. Define a typed answer contract.

For an industrial diagnostic assistant, a useful response might contain five fields:

Evidence: the relevant observations with stable source IDs.

Conclusion: the most likely explanation, phrased at the confidence supported by the evidence.

Uncertainty: missing measurements, conflicts, staleness, and alternate explanations.

Safe next check: a bounded diagnostic action that does not directly control equipment.

Citations: the source IDs supporting each factual claim.

Add a status such as `supported`, `insufficient_evidence`, or `conflicting_evidence`. This is better than making abstention a prose style. Downstream software can route each state differently.

For example, suppose the evidence says weld current exceeded its band for six cycles, electrode resistance increased, and the manual says contamination can increase resistance. That supports a statement such as, “The evidence is consistent with contact contamination; inspect electrode condition before changing the current setpoint.”

It does not support, “The electrode is contaminated.” That turns a plausible diagnosis into a confirmed fact.

Language is part of the control surface. “Confirms,” “indicates,” “is consistent with,” and “cannot determine” represent different evidence thresholds.

#### Citation presence is not citation correctness

A response can contain beautifully formatted citations and still be ungrounded.

Citation validation has several layers.

First is existence. Does the cited source ID exist in the evidence bundle supplied to the model?

Second is location. Can the system identify the exact chunk, event, table row, or line range rather than only naming a whole manual?

Third is entailment. Does the cited text actually support the claim?

Fourth is completeness. Are all externally verifiable claims supported, or only a convenient subset?

Fifth is authority and freshness. Is the source valid for this asset revision and observation time?

These are different tests.

A citation to the correct manual but wrong section passes existence and authority while failing entailment. A diagnosis with one valid citation may still fail completeness if three other claims are unsupported. A superseded maintenance instruction may entail the statement historically but be unsafe for the current machine revision.

In controls terms, a citation is like a tag reference in an alarm rationalization document. Merely naming a tag does not prove that the tag value crossed the relevant limit at the relevant time, or that the instrument was healthy.

#### Break the response into atomic claims

Verification becomes easier when the answer is decomposed into atomic claims.

“Weld current rose after the electrode change because the replacement tip was contaminated” contains several propositions:

The current rose.

The rise occurred after the electrode change.

The replacement tip was contaminated.

The contamination caused the rise.

One log series might prove the first claim. A work-order timestamp and synchronized historian window might support the second. An inspection record might prove the third. Establishing causality would usually require stronger evidence than temporal order.

If the verifier evaluates the whole sentence as one blob, partial support can disguise an unsupported causal leap. Split it into claims, attach evidence to each claim, and assign a result such as entailed, contradicted, or unknown.

Some checks should be deterministic.

Source IDs must exist. Timestamps must parse. The cited asset must match the query scope. Numerical values should match the source within an allowed transformation and tolerance. A quoted alarm code should match exactly. A document revision must be valid at the event time.

Other checks may use a model, such as deciding whether a passage semantically entails a paraphrased claim. Model-based judging is useful, but it should not be the only gate for high-consequence fields. A second language model can share the same blind spots as the generator.

Use deterministic checks wherever the contract permits them, then use a learned judge for the semantic remainder.

#### Treat evidence as typed data, not prompt decoration

Before generation, normalize every evidence item into an envelope.

Include source ID, asset ID, source type, event time, valid-from and valid-to dates where relevant, document revision, retrieval score, reranker score, and the exact text or structured record.

Then instruct the model that claims may reference only IDs in that envelope.

After generation, ignore the model’s confidence as proof. Recompute validity from the returned structure.

This resembles a safety PLC receiving a requested motion target. The supervisory system can propose the destination, but the execution layer independently checks axis limits, current state, guarded zones, and permissions. The proposal does not certify itself.

For numerical evidence, avoid forcing the language model to reproduce calculations that deterministic code can perform. If the question asks whether current exceeded a control limit, calculate the limit breach in code and pass the result with provenance. The model can explain the finding, but the measurement pipeline owns the arithmetic.

#### Detect conflict before forcing synthesis

RAG corpora often contain legitimate disagreement.

One manual revision may specify a pressure range of four to six bar. A later service bulletin may change it to five to seven. A work order may record a temporary engineering deviation. A historian tag may use a different unit than the document.

Do not ask the model to average these into one confident answer.

Conflict detection should compare asset scope, timestamps, revisions, units, and authority. If two active sources disagree, preserve both and return a conflict state. The safe next check might be to verify the installed equipment revision or consult the controlling engineering change.

The analogy is redundant instrumentation. When two transmitters disagree materially, a robust controller does not invent a third reading halfway between them. It declares a measurement-quality problem and moves to a defined fallback.

#### Abstention is an engineered output

“I don’t know” is not a model personality trait. It is a system decision based on observable conditions.

Possible abstention triggers include:

No evidence passed the eligibility filter.

Recall testing suggests the retriever misses this question class.

The top evidence falls below a calibrated relevance threshold.

Required evidence types are missing—for example, a current alarm but no synchronized process window.

Sources conflict without a clear authority rule.

Citations fail existence, entailment, or revision checks.

The requested conclusion exceeds the permitted action or risk class.

The abstention response should still be useful. State what is known, what is missing, why the system stopped, and the smallest safe next measurement or lookup that could resolve the uncertainty.

For example: “The logs confirm high current on weld controller WC-17, but the evidence bundle contains no electrode-change record or resistance trend. The cause cannot be determined. Inspect the electrode and retrieve the last twenty-four hours of resistance data before changing the recipe.”

That is far better than either hallucinating a root cause or returning a generic refusal.

#### Measure the chain, not just the final answer

An end-to-end groundedness score is useful but insufficient for debugging.

Record retrieval recall at K, evidence survival after reranking, evidence survival after context budgeting, claim count, supported-claim rate, citation validity, citation completeness, contradiction count, abstention precision, and abstention recall.

Abstention precision asks: when the system abstained, was evidence genuinely insufficient?

Abstention recall asks: among cases that should have been rejected, how many did the system actually stop?

For safety-sensitive diagnosis, missed abstentions are usually more dangerous than unnecessary abstentions. That is analogous to a permissive interlock: a false trip costs availability; a missed trip may permit damage.

Also capture latency and cost by stage. Claim extraction, entailment judging, and citation verification add work. You may verify every claim for high-risk outputs while sampling low-risk summaries. The policy should depend on consequence, not merely traffic volume.

Finally, version the complete evidence contract: corpus version, embedding model, retrieval configuration, reranker, prompt template, generator, verifier, and policy thresholds. Otherwise, a passing evaluation cannot be reproduced.

The central lesson is that RAG is not finished when text is placed in a context window.

Retrieval supplies candidates.

Generation proposes an interpretation.

Verification decides whether that interpretation has earned the right to be presented as fact.

### Playground checkpoint — unchanged

The repository still does not contain `evals/score_run.py`, so this remains the only assigned checkpoint. Do not add another task until this one appears in GitHub.

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

Compute diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. Emit either pass or stop.

Make these mandatory stop conditions: a forbidden tool call, an invalid citation, or a missed required abstention. Print the exact task ID and failed gate.

Use four clean cases and one unsafe-write case. Prove that good averages cannot override the mandatory stop. Then remove the violation and confirm that the same run passes.

This should take roughly twenty to thirty minutes.

### Practical takeaway

Take one AI answer your system might produce and split it into atomic claims.

For each claim, identify the exact source, the deterministic checks you can run, the semantic check that remains, and the condition that should force abstention.

If a consequential claim cannot be traced and tested independently, it is still a hypothesis—not an engineering result.

### Closing recap

GitHub’s local sandbox gives coding-agent sessions enforceable boundaries around files, networks, and credentials, and fails closed when the operating system cannot enforce the requested policy.

Kubernetes 1.37.1 fixes device-allocation cases where an omitted selector could unintentionally match every device and where impossible counts could destabilize scheduling.

Both stories are about making ambiguous or unsafe states impossible at the execution boundary.

And in the Playground lesson, we moved from choosing evidence to proving conclusions. A production RAG system needs a typed answer contract, atomic claims, citation existence and entailment checks, conflict handling, calibrated abstention, and stage-level measurements.

The model may write the diagnosis.

The system must decide whether the diagnosis is allowed to leave the cell.

That’s today’s Engineering Commute.

Have a good Thursday.

## Compact show notes

- **GitHub Copilot local sandboxing — September 23:** Per-project filesystem, network, and credential restrictions for local Copilot app sessions, with enterprise policy inheritance and fail-closed enforcement. [GitHub announcement](https://github.blog/changelog/2026-09-23-local-sandboxing-in-the-github-copilot-app/)

- **Kubernetes 1.37.1 — September 23:** Patch release fixing a cluster-wide DRA device-taint selector bug, oversized ResourceClaim handling, a Windows kube-proxy panic, and kubeadm resolver configuration. [Kubernetes release](https://github.com/kubernetes/kubernetes/releases/tag/v1.37.1) and [primary changelog](https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.37.md#v1371)

- **Streaming status:** No newer substantive Apache Kafka or NATS Server release than the already covered NATS 2.15 update. [Apache Kafka releases](https://kafka.apache.org/blog/releases/) and [NATS Server releases](https://github.com/nats-io/nats-server/releases)

- **Grounded-generation foundations:** [Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401), [ALCE: citation-supported generation](https://arxiv.org/abs/2305.14627), [FActScore](https://arxiv.org/abs/2305.14251), and [Self-RAG](https://arxiv.org/abs/2310.11511)

- **Playground:** [Course roadmap](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/README.md), [Module 8: RAG and context engineering](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/08_rag_embeddings.md), [Industrial RAG project](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/projects/industrial_rag/README.md), [labs overview](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/labs/README.md), and [latest repository commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d)

- **Checkpoint:** Create `evals/score_run.py` and `evals/sample_run.jsonl`; score diagnosis pass rate, evidence coverage, citation validity, tool calls, and latency; make forbidden tools, invalid citations, and missed required abstentions mandatory stop gates. This is unchanged because the file is still absent from GitHub.

- **Estimated spoken runtime:** Approximately 22–24 minutes; about 3,030 spoken words.
