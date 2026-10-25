# The Engineering Commute — September 26, 2026

## Narration-ready episode

Good morning, Dan.

Today’s Engineering Commute is about a deceptively simple idea: when an AI system remembers something, what exactly has earned the right to become memory?

GitHub’s agentic security autofix can now read repository-specific Copilot memories and write successful fix patterns back for later use.

GitHub also changed several engineering signals around agent work and CI: Copilot can carry more conversation context from Slack and Teams into GitHub, pull-request metrics now expose review-stage latency, and broad GitHub Actions queries now report a bounded count instead of a misleading partial total.

Then, in the Playground Lesson, we’ll build a practical model of agent memory: working, episodic, semantic, and procedural memory; how memories are consolidated and retrieved; and how provenance, expiration, conflict handling, and deletion prevent yesterday’s useful shortcut from becoming tomorrow’s hidden defect.

I checked the AI Systems Engineering Playground through GitHub again this morning. The README, roadmap, modules, labs, Industrial RAG project, capstone, and commit history are unchanged. The latest commit remains the September ninth curriculum expansion. The two evaluator files are still absent, so the unfinished checkpoint at the end remains exactly the same.

### Current development one: security autofix can learn repository-specific patterns

First, the reported facts.

On September twenty-fifth, GitHub announced that agentic autofix can use Copilot Memory for customers who enable both public-preview features.

When agentic autofix investigates a security alert, it can review existing memories for repository-specific context. After producing a fix, it can store the fix pattern as a new memory. GitHub says those memories may help resolve later security alerts and may also inform other Copilot features, including code review and the cloud coding agent.

GitHub did not claim that a stored pattern is universally correct, nor that memory replaces code scanning, tests, or review. The announcement describes shared contextual knowledge inside the repository’s Copilot experience.

Now the engineering analysis.

This converts one successful repair into a reusable prior.

Suppose a service repeatedly mishandles tenant IDs because the correct repository convention is to derive identity from authenticated middleware, never from a request-body field. The first autofix may discover that pattern by reading the code. A durable memory could help future repairs apply the same convention faster.

That is valuable, but the memory has crossed a trust boundary.

Before storage, the fix was a proposed output for one alert. After storage, it becomes an input that may influence several future decisions. The system is no longer merely remembering history. It is changing future behavior.

Think of a technician writing a workaround into a plant logbook. If the note says, “On line four, firmware revision seven requires this register reset,” it may save hours. If someone later treats that note as a universal procedure for every line and revision, the same shortcut becomes a fault source.

So a production memory should carry scope: repository, component, language, dependency version, security rule, author or generating system, supporting evidence, creation time, and review state. It also needs a condition for invalidation.

A fix pattern learned under one framework version may be wrong after a migration. A memory derived from a reverted commit should not remain authoritative. A pattern that passed unit tests but later caused an incident should be demoted or quarantined.

The important design rule is that successful use is evidence, not proof. Memory should improve search and planning, while deterministic scanners, tests, policy checks, and human approval retain authority over the final change.

### Current development two: context and metrics are becoming more explicit

Here are the reported facts.

Also on September twenty-fifth, GitHub expanded Copilot integrations for Slack and Microsoft Teams.

Copilot can now use supported Slack files, attachments, and message links as context. In Teams it can use inline images, forwarded messages, and channel or thread history. When it creates GitHub work, it checks for similar issues, links to the resulting item, and preserves a link back to the originating conversation.

The integrations also improve recovery from stale, interrupted, or long-running tasks. GitHub specifically says repository switching is safer because superseded Slack sessions cannot keep acting in the old repository.

Separately, GitHub’s Copilot usage-metrics reports now divide pull-request review time into three stages: ready-to-first-review, first-to-final-review, and final-review-to-merge. Reports provide median and ninetieth-percentile duration for each stage. The initial release counts human-authored pull requests with human reviewers, excludes bot and Copilot reviews from the timed review set, has no historical backfill, and represents a quiet day as an empty array rather than zero.

Finally, broad workflow-run searches in the GitHub Actions API and interface now return “two-thousand-five-hundred plus” when more than that many records match. GitHub says attempts to calculate larger exact counts frequently timed out and could return a partial count that looked authoritative. Pagination still returns up to one thousand results, and integrations needing more precision should narrow filters, such as by date range.

Now the analysis.

These changes share one theme: context is only trustworthy when its boundary and meaning are explicit.

A source link from a Teams discussion to a created issue is provenance. It lets an engineer reconstruct why the work exists and which evidence shaped it.

A stale session blocked from acting in an old repository is scope enforcement. It prevents valid authority from leaking into the wrong state after context changes.

A pull-request metric split into stages is observability. One end-to-end number can hide whether work waits for initial attention, cycles through review, or sits approved but unmerged.

And “two-thousand-five-hundred plus” is an honest measurement contract. It is less numerically precise but more truthful than a timeout-truncated count presented as exact.

That last point matters in AI systems too. “Unknown beyond this bound” is often better engineering than a confident-looking estimate whose collection process failed.

### Playground Lesson: designing agent memory that can be trusted

Module Ten of the Playground distinguishes working memory from durable memory. That distinction is the starting point, but production systems need a slightly richer model.

Working memory is the current control-room whiteboard.

It contains the user’s request, recent tool results, the current hypothesis, intermediate calculations, and the remaining execution budget. It exists to complete one run. When the run ends, most of it should disappear.

Episodic memory is the event log.

It records that a particular incident occurred, which observations were available, which actions were attempted, and what outcome followed. A prior weld fault, a security repair, or a failed deployment can be an episode.

Semantic memory is the maintained knowledge base.

It contains facts or generalized relationships: a component owner, an approved coding convention, an asset-to-manual mapping, or the fact that a particular alarm commonly accompanies loss of cooling flow. Semantic memory often comes from documents, databases, or consolidation across several episodes.

Procedural memory is the playbook.

It encodes how to perform a task: which diagnostic checks to run, in what order, under which permissions, with which stop conditions. In controls terms, semantic memory resembles configured engineering data; procedural memory resembles a validated sequence.

These categories should not be one undifferentiated vector collection.

Imagine an agent diagnosing a weld-current spike. The current tag values belong in working memory. Yesterday’s incident is episodic. The equipment manual is semantic. The approved read-only troubleshooting sequence is procedural.

If all four are retrieved solely by similarity, a vivid old incident can outrank the current manual, or an obsolete workaround can masquerade as an approved procedure.

The memory pipeline therefore needs four separate decisions.

First is admission: should this observation be stored at all?

Do not write every prompt and model conclusion into durable memory. That creates an echo chamber in which generated claims are later retrieved as though they were external evidence. Store raw events when retention is justified, but promote a conclusion only after validation.

A useful admission record includes the source, evidence references, confidence, scope, sensitivity, and the rule that authorized storage. Personally identifiable information, credentials, and confidential plant data may require redaction or may be prohibited entirely.

Second is consolidation: when does an episode become a rule?

One successful fix is an anecdote. Several independent fixes with the same verified pattern may justify a candidate semantic or procedural memory. Consolidation should preserve links to the supporting episodes and record the transformation that produced the summary.

This is similar to turning historian events into a maintenance standard. You would not change a preventive-maintenance interval because one bearing failed. You would examine repeated failures, operating conditions, inspection results, and engineering review.

Third is retrieval: which memories may influence this decision?

Similarity is only one signal. Filter by repository or asset, component, software or equipment revision, time range, memory type, authorization domain, and review status. Then rank candidates using relevance, freshness, reliability, and outcome quality.

For a safety-relevant diagnosis, evidence from the current tag read and the applicable manual should normally outrank an old narrative. A previous incident can suggest a hypothesis, but it should not overwrite live observations.

Fourth is lifecycle control: how does memory stop being true?

Every durable memory needs an owner, version, creation time, last-validated time, and invalidation path. Some memories expire automatically. Others become stale when a dependency version, equipment revision, policy, or source document changes.

Deletion must propagate. If a source conversation is removed for privacy or a fix is reverted, derived summaries and embeddings may also need deletion or suppression. A tombstone should prevent replay or a later backfill from silently resurrecting invalid memory.

Conflicts deserve an explicit state, not silent averaging.

If one memory says a timeout should be five seconds and a newer approved policy says thirty, the system should surface the conflict, apply the more authoritative scope, or abstain. Blending them into seventeen-point-five seconds is mathematically tidy and operationally absurd.

Memory writes also need transactional behavior.

Suppose an agent repairs code, writes a memory describing the repair, and then the pull request fails integration tests. If the memory commit succeeds before the software change is validated, the system has preserved a lesson from a failed outcome. Use a candidate state first. Promote the memory only after the associated change reaches the required verification milestone, and link both records with an immutable run or commit identifier.

This resembles commissioning a machine recipe. A technician may tune parameters during trials, but the experimental recipe does not become the production standard merely because one cycle completed. Promotion happens after acceptance criteria are met, and rollback must restore both the deployed configuration and the knowledge that future operators see.

For concurrent agents, add optimistic version checks or a single consolidation queue so two runs cannot silently overwrite one another’s conclusions.

The safest architecture treats memory as a sensor input, not a command.

A memory service returns candidates with provenance and status. The agent may use them to form a hypothesis. Deterministic policy decides which tools are available. Live reads confirm present state. Tests and verifiers judge proposed outputs. High-impact effects remain behind approval boundaries.

For observability, log the memory IDs retrieved, which ones entered the final context, their ages and scopes, and whether the final answer relied on them. Track retrieval hit rate, stale-memory rate, conflict rate, deletion lag, and outcomes after memory-assisted decisions.

If performance improves, determine whether memory actually contributed or merely correlated with easier cases. If incidents rise, you need enough lineage to identify which stored pattern influenced the bad decision.

The core principle is simple:

Memory is not truth. Memory is versioned, scoped evidence carried forward from an earlier state.

### Playground checkpoint — unchanged

The repository still does not contain `evals/score_run.py` or `evals/sample_run.jsonl`, so this remains the only assigned checkpoint. Do not add another task until these files appear in GitHub.

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

Compute diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. Emit either pass or stop.

Make these mandatory stop conditions: a forbidden tool call, an invalid citation, or a missed required abstention. Print the exact task ID and failed gate.

Use four clean cases and one unsafe-write case. Prove that good averages cannot override the mandatory stop. Then remove the violation and confirm that the same run passes.

This should take roughly twenty to thirty minutes.

### Practical takeaway

For one durable memory in an AI system, write down five fields: source evidence, scope, review state, expiration or invalidation trigger, and deletion path.

If any field is missing, treat that memory as a retrieval hint—not an operating fact.

### Closing recap

GitHub’s agentic autofix can now reuse and create repository-specific Copilot memories, turning successful repairs into future context while increasing the importance of scope and invalidation.

Copilot’s collaboration integrations now preserve richer source context and safer session boundaries. GitHub’s new review-stage metrics and bounded Actions counts show why measurement semantics matter as much as the displayed number.

And in the Playground Lesson, we separated working, episodic, semantic, and procedural memory; then built a trust pipeline around admission, consolidation, retrieval, provenance, expiration, conflicts, and deletion.

The final design rule is this:

Let memory propose what may matter. Let current evidence, deterministic controls, and explicit authority decide what happens next.

That’s today’s Engineering Commute.

Have a good Saturday.

## Compact show notes

- **Agentic autofix and Copilot Memory — September 25:** Autofix can consult repository memories and store successful fix patterns for later security work. [GitHub announcement](https://github.blog/changelog/2026-09-25-agentic-autofix-now-uses-copilot-memory)

- **Copilot in Slack and Teams — September 25:** Richer attachment and thread context, duplicate-issue checks, source backlinks, model selection, and safer stale-session handling. [GitHub announcement](https://github.blog/changelog/2026-09-25-updates-to-github-copilot-for-slack-and-microsoft-teams/)

- **Pull-request review-stage metrics — September 25:** Median and p90 timing for ready-to-first-review, review iteration, and final-review-to-merge. [GitHub announcement](https://github.blog/changelog/2026-09-25-usage-metrics-api-adds-pull-request-review-stages)

- **GitHub Actions query-count semantics — September 25:** Searches exceeding 2,500 matches now report `2,500+` instead of a potentially misleading timeout-truncated exact count. [GitHub announcement](https://github.blog/changelog/2026-09-25-changes-to-query-results-in-the-github-actions-api-and-ui/)

- **Memory-system foundations:** [Generative Agents research paper](https://arxiv.org/abs/2304.03442) and [GitHub Copilot Memory documentation](https://docs.github.com/en/copilot/concepts/agents/copilot-memory)

- **Playground:** [Course roadmap](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/docs/roadmap.md), [Module 10: agents and orchestration](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/10_agents_workflows.md), [Industrial RAG project](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/projects/industrial_rag/README.md), [capstone](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/projects/capstone_factory_ai_engineer/README.md), and [latest repository commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d)

- **Checkpoint:** Create `evals/score_run.py` and `evals/sample_run.jsonl`; score diagnosis pass rate, evidence coverage, citation validity, tool calls, and latency; make forbidden tools, invalid citations, and missed required abstentions mandatory stop gates. This is unchanged because both files remain absent from GitHub.

- **Estimated spoken runtime:** Approximately 15 minutes; about 2,175 spoken words.
