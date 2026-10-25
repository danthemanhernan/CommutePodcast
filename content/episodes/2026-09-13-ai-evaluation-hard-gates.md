# The Engineering Commute — September 13, 2026

## Narration-ready episode

Good morning, Dan.

Today’s Engineering Commute is about evaluation: how to decide whether an AI system is actually ready to do useful work.

GitHub has expanded Copilot code review with shell-based validation and an ensemble of reviewing agents. Google has added a BigQuery function that calculates classification and regression metrics from any table of predictions and actual outcomes, without requiring a stored model.

Both are useful. Neither changes the fundamental rule that a metric only answers the question encoded into its data, labels, aggregation, and acceptance policy.

Then we’ll spend most of the episode building a complete evaluation architecture for the Factory AI Engineer: golden tasks, subsystem metrics, deterministic checks, model graders, safety gates, statistical uncertainty, shadow testing, canaries, and production feedback.

I inspected the AI Systems Engineering Playground before recording. The latest commit is still the September ninth curriculum expansion. There is no `score_run.py` or other evidence that the existing checkpoint is complete, so I am not adding another task. We will use today’s lesson to make that same task easier to understand and implement.

There is no substantive new Apache Kafka or NATS JetStream release to revisit this morning.

### Current development one: Copilot code review adds tools and an agent ensemble

First, the reported facts.

On September eleventh, GitHub announced several changes to Copilot code review.

When a later commit addresses a Copilot review comment, Copilot can now resolve that comment during rereview. When a developer applies an autofix suggestion, Copilot generates a commit-message suggestion based on the change.

The larger systems change is behind the review. Copilot now uses the shell-tool set from the Copilot SDK behind GitHub’s agent firewall. GitHub says the reviewer can use those tools to run builds, execute tests and targeted scripts, and retrieve information from available tools and APIs.

GitHub also changed the Lite review effort to use an ensemble of agents. Several agents contribute perspectives, and the system combines their findings into one review.

In GitHub’s experiments, the ensemble increased the average number of addressed comments by forty-seven percent for high-severity findings, thirty-one percent for medium-severity findings, and eleven percent for low-severity findings, while reducing review cost by about eight percent. These are vendor-reported experimental measurements, not a general benchmark for every repository.

Now, the analysis.

Giving a reviewer tools moves it from pure language critique toward evidence-producing verification. It can inspect whether the code compiles, whether a targeted test fails, and whether a proposed API actually exists.

That is stronger than asking one model to read a diff and sound confident.

But tool access and multiple agents do not automatically create independent evidence.

If every reviewer sees the same misleading requirements, shares the same blind spot, or relies on the same incomplete tests, the ensemble can agree and still be wrong. Five instruments connected to one incorrectly calibrated transmitter do not create five independent measurements.

The reported metric—addressed comments—is also a proxy. It tells us developers acted on more findings. It does not by itself prove that fewer defects reached production. A reviewer that produces more persuasive comments could raise the metric without improving real outcomes.

A serious evaluation would connect review behavior to seeded defects, security findings, escaped bugs, reverts, incidents, and human-review time. It would segment results by language, repository type, change risk, and tool availability.

The lesson is not that GitHub’s result is weak. The lesson is to ask exactly what was measured before deciding what the number authorizes.

### Current development two: BigQuery separates metrics from the stored model

Here are the reported facts.

On September tenth, Google Cloud put BigQuery’s `ML.METRICS` function into preview.

The function accepts a table or query containing a predicted column and an actual column. It calculates evaluation metrics without requiring the predictions to come from a model stored in BigQuery ML.

For regression, the returned values include mean absolute error, mean squared error, mean squared logarithmic error, median absolute error, R-squared, and explained variance.

For classification, it returns precision, recall, accuracy, and F-one.

Boolean labels are evaluated as binary classification with `true` treated as the positive class. String labels are treated as multiclass classification, even if the data contains only two distinct strings, and the function macro-averages each metric across classes.

Rows with null predicted or actual values are omitted. If the input is empty, or all rows are removed by that rule, the function returns one row with null metrics.

Now, the analysis.

This is a useful decoupling. Predictions can come from an external model, a rules engine, an agent, a legacy system, or a baseline query. Once actual outcomes arrive, the warehouse can compare them through one SQL interface.

The subtle details matter.

Macro-averaging gives each class equal weight, which helps prevent a common class from completely hiding a rare class. But one macro average can still hide which class is failing.

Null omission is convenient, but missingness may itself be a failure. If a classifier refuses to predict the hardest cases and those rows silently disappear from the calculation, the reported score can improve while coverage collapses.

For a weld-fault system, you would store an explicit terminal state such as abstained or insufficient evidence and score it according to the task contract. Do not let missing results become invisible.

The warehouse can calculate the arithmetic. The engineering team still owns the population, labels, time boundaries, slices, failure costs, and deployment decision.

### Evergreen technical lesson: evaluation as an engineering measurement system

Evaluation is often described as testing the model. That is too narrow for an AI application.

The Factory AI Engineer contains a gateway, model router, language model, retrieval pipeline, tool server, orchestration loop, policy checks, structured report, and human interaction. A correct final sentence can hide an unsafe trajectory. A wrong answer can originate from perfect reasoning over the wrong manual.

The object being evaluated is the complete decision process.

Think of evaluation as a metrology system for software behavior. You need a defined measurand, calibrated references, known uncertainty, repeatable procedures, traceability, and acceptance rules.

#### Start with the decision the evaluation will control

Before choosing a metric, write down the decision it will influence.

Are you comparing two prompts? Selecting a model? Allowing a new retrieval index into staging? Granting a tool access to production? Deciding whether an automated recommendation may reach an operator?

Different decisions require different evidence.

A prompt experiment might tolerate a small noisy sample. A production authorization for an effectful tool needs stronger coverage, explicit safety cases, and hard failure gates.

Define the intended outcome in operational terms.

For the capstone, “good answer” is vague. A more useful objective is:

Given a simulated plant incident, collect the required authorized evidence, avoid prohibited actions, identify plausible causes supported by that evidence, recommend bounded next checks, cite every factual claim, and abstain when the available evidence cannot support a diagnosis.

Now the evaluation has something concrete to measure.

This resembles writing a functional specification before commissioning a machine. If “works well” is the acceptance criterion, every stakeholder can interpret success differently.

#### Draw the system boundary and failure tree

Map each stage from input to outcome.

The user supplies an incident description.

The router selects a model.

The planner chooses tools.

The tool layer validates and executes calls.

Retrieval selects documents.

The model assembles a diagnosis.

The verifier applies requirements and safety policy.

The user interprets the recommendation.

For each stage, ask how it can fail.

The incident may be ambiguous. The router may choose a model without enough capability. The planner may omit the historian. The historian call may use the wrong time zone. Retrieval may return an obsolete manual. The model may cite a relevant source that does not support the claim. The verifier may reward the presence of citations without checking entailment. The operator may read a recommendation as an instruction.

This failure tree tells you which observations the evaluator must retain.

If you save only the final answer, you cannot distinguish retrieval failure from reasoning failure. It is like diagnosing a stopped line from the finished-part count while discarding every station status and alarm.

#### Build golden tasks as engineered test fixtures

A golden task is a versioned scenario with a known evaluation contract.

It should include the user request, available plant state, permitted tools, source documents, expected evidence, acceptable conclusions, forbidden behavior, and required terminal state.

The word golden does not mean there is one perfect paragraph. Many troubleshooting problems permit several reasonable explanations or next checks. The gold standard can be a set of constraints rather than an exact string.

For example, one task might say:

The run must read alarms and a ten-minute current window. It must cite manual revision seven. It may rank electrode wear or force instability as plausible. It must not claim certainty. It must not call any write tool. If the historian quality is bad, it must abstain from a root-cause conclusion.

Build task families, not isolated examples.

Include normal operation, common faults, rare faults, ambiguous reports, conflicting sensors, stale manuals, missing units, invalid quality codes, permission denials, backend timeouts, prompt injection, and unsafe user requests.

Use parameterized variants. Change the line number, controller type, time window, units, alarm code, and document revision. This reveals whether the system learned the mechanism or memorized a fixture.

Every task needs provenance: who authored it, what source defines the expected behavior, when it was reviewed, and what system versions it applies to.

#### Split evaluation data by the way reality changes

Random train-and-test splits are often wrong for operational systems.

If nearly identical incidents from one asset appear in both sets, the test overstates generalization. If a later manual revision leaks into an earlier scenario, the system benefits from future knowledge.

Use splits that represent deployment risk.

Hold out time periods to test future behavior.

Hold out assets or sites to test transfer.

Hold out fault families to test novelty.

Preserve a private regression set that prompt and pipeline authors do not repeatedly tune against.

For point-in-time evaluation, expose only the documents, tag data, and incident history that would have been available at the decision time. A maintenance note written after the repair cannot be evidence for a diagnosis made before the repair.

The controls analogy is validating a predictive algorithm with the future failure flag accidentally wired into an input. The result can look perfect while proving nothing.

#### Measure every subsystem with the right instrument

Start with retrieval.

Measure recall at K: did the candidate set include the required evidence?

Measure precision at K: how much of the retrieved set was useful?

Measure ranking: how early did the needed source appear?

Also measure stale-source rate, duplicate concentration, unauthorized-source rate, and citation-ready metadata coverage.

Then evaluate tools.

Was the correct tool selected? Were its arguments valid? Was the asset scope correct? Were required tools omitted? Were unnecessary calls added? Did any call violate policy? Did retries duplicate work?

Evaluate orchestration.

Did the run checkpoint after completed calls? Could it recover after a forced crash? Did it stop within step and retry budgets? Did it terminate in the correct state? Did it preserve the relationship between observations and conclusions?

Evaluate the answer.

Check diagnosis acceptability, required sections, claim-level citation validity, evidence support, contradictory-evidence handling, calibrated confidence, useful next actions, and required abstention.

Evaluate system performance.

Record time to first response, total latency, latency by tool and model stage, token consumption, model cost, tool-call count, backend load, and high-percentile behavior.

One overall score cannot replace this measurement vector.

#### Use deterministic checks wherever the contract is deterministic

If a rule can be checked exactly, do not ask another model to guess.

A program can verify that every cited source ID exists. It can detect forbidden tool names, enforce maximum call counts, validate JSON Schema, compare numeric readings with tolerance, confirm required fields, and identify missing abstention states.

Unit tests can execute code. A policy engine can evaluate authorization. A database query can check whether the selected document revision was current at incident time.

These checks are cheap, repeatable, and explainable.

Model graders are useful for semantic questions: whether a conclusion is reasonably supported, whether an explanation contradicts a source, whether the recommended check is useful, or whether the tone could mislead an operator.

But model graders are models. They have position bias, verbosity bias, self-preference, prompt sensitivity, and inconsistent thresholds.

Calibrate them against expert-labeled examples. Measure agreement and disagreement by category. Use several grading prompts or models for high-impact judgments. Require the grader to identify the specific evidence behind its decision.

Do not use a model grader where a deterministic verifier exists.

#### Understand confusion matrices before headline accuracy

Suppose one hundred incidents contain ninety routine cases and ten hazardous faults.

A classifier that labels every case routine achieves ninety percent accuracy while detecting zero hazardous faults.

Precision answers: of the cases predicted hazardous, how many actually were?

Recall answers: of the truly hazardous cases, how many did we detect?

The choice depends on consequence.

High recall may be appropriate when missing a dangerous state is costly, but excessive false alarms can train operators to ignore the system. The operating point should reflect both risk and human workload.

For multiclass faults, inspect per-class metrics and the full confusion matrix. A macro average weights every class equally. A micro average weights individual examples, favoring common classes. A weighted average sits between them.

None tells you the whole story.

For abstention, measure coverage and selective accuracy together. Coverage is the fraction of cases the system attempts. Selective accuracy is performance on those attempted cases.

A system can raise selective accuracy by abstaining constantly. That may be safe but useless. Conversely, maximum coverage can create confident wrong answers. Choose a coverage-risk curve that matches the application.

#### Separate averages from hard gates

Some failures cannot be averaged away.

Imagine one hundred capstone tasks. Ninety-nine are excellent. One run issues a prohibited PLC write.

An average safety score of ninety-nine percent does not make the release acceptable.

Use two layers.

First, hard gates. Any forbidden tool call, invalid citation used as evidence, cross-scope data access, or failure to abstain in a defined critical condition produces stop.

Second, scored objectives. Among runs that pass the gates, compare diagnosis quality, evidence coverage, latency, cost, and operator usefulness.

This is exactly how many engineered systems combine permissives with optimization. The optimizer may choose the most efficient valid operating point. It does not get to trade away an emergency interlock for slightly higher throughput.

Document the gate hierarchy. Print the exact task ID, observed violation, policy version, and supporting trace. A generic red status is difficult to debug and easy to waive without understanding.

#### Engineer the labels and reviewer process

Evaluation quality cannot exceed reference quality.

For simple arithmetic, the label may be objective. For industrial troubleshooting, experts can legitimately disagree about the best diagnosis, how much evidence is sufficient, or when the system should abstain.

Start with a labeling guide. Define the task, permitted evidence, severity scale, acceptable alternatives, citation-support rule, abstention rule, and examples at each boundary. If reviewers use different mental definitions of “supported,” their labels will look precise while measuring different things.

Use at least two independent reviewers for ambiguous or high-impact cases. Do not show the first reviewer’s answer to the second before the second decides; anchoring creates artificial agreement.

When reviewers disagree, record the disagreement before adjudication. Was the task ambiguous? Was required evidence missing? Did the experts use different plant assumptions? Did the scoring rubric omit an acceptable conclusion?

Disagreement is diagnostic data. A high disagreement rate may reveal that the task contract is underspecified rather than that one reviewer is wrong.

Measure inter-rater agreement, but interpret it carefully. Raw percent agreement can appear high when one label dominates. Statistics such as Cohen’s kappa adjust for expected agreement, but no statistic replaces reading representative disagreements.

For the capstone, separate observable labels from judgment labels.

Whether the agent called `read_tag` is observable.

Whether the cited source ID exists is observable.

Whether the current quality code was bad is observable.

Whether the final hypothesis was the most useful one may require expert judgment.

Preserve both. Do not let a subjective overall rating overwrite deterministic facts.

Also separate outcome labels from process labels. A recommendation may later prove correct even though it was unsupported by the evidence available at decision time. That is a lucky outcome, not a good process. Conversely, a well-grounded recommendation can be wrong because the fault is rare or the sensors are misleading.

Score both dimensions so the system does not learn that guessing is acceptable whenever it occasionally wins.

Version labels. If an expert changes a judgment after seeing new evidence, retain the original point-in-time label and add the revised outcome label. That preserves the distinction between what was knowable then and what became known later.

This is similar to calibration work. A reference instrument needs its own certificate, procedure, uncertainty, and history. Calling a spreadsheet “ground truth” does not make it ground truth.

#### Slice failures until the average becomes actionable

An overall score tells you whether something changed. A slice tells you where.

Create evaluation slices that correspond to plausible failure mechanisms.

Slice by plant, line, equipment family, controller type, fault family, document revision, user role, language, query length, evidence quality, incident severity, model route, and time of day.

For retrieval, slice by exact alarm-code queries versus descriptive symptoms. For tools, separate single-call tasks from multi-step investigations. For answers, separate well-supported incidents from cases requiring abstention.

Suppose citation validity is ninety-eight percent overall. That sounds strong. But if every invalid citation occurs on one legacy controller family, the average hides a systematic deployment hazard.

Suppose latency improves by twenty percent. Slice by task length and you may discover that short tasks are faster while long investigations time out completely. The mean improved because the failed cases returned early.

Use a failure taxonomy alongside slices.

An input failure means the task was malformed or outside scope.

A retrieval miss means required evidence never entered the candidate set.

A ranking miss means evidence was retrieved but excluded from context.

A tool-selection failure means the wrong capability was chosen.

An argument failure means the right tool received the wrong asset, range, or units.

A reasoning failure means correct evidence was present but the conclusion was unsupported.

A policy failure means the system attempted or allowed prohibited behavior.

An interaction failure means the answer was technically correct but likely to mislead the operator.

Assign one primary cause and optional contributing causes. Otherwise teams can relabel every failure as “model issue” and learn nothing.

Prioritize slices by consequence, frequency, and detectability. A rare unsafe action may outrank a common wording defect. A problem caught deterministically before execution is less risky than one visible only after an operator acts.

Use the slices to choose the intervention. Retrieval misses suggest corpus or search changes. Argument failures suggest schemas and validators. Reasoning failures may justify prompt, model, or context changes. Policy failures require execution-layer controls, not another sentence in the prompt.

This is the same logic as Pareto analysis on a production line. The purpose of categorization is not to make a colorful dashboard. It is to connect observed defects to the process step capable of removing them.

#### Quantify uncertainty in the evaluation itself

A measured pass rate is an estimate from a sample.

If a new prompt passes nine of ten tasks, the observed rate is ninety percent, but the true performance could be much lower or higher. Ten examples do not justify a precise claim.

Report sample size and confidence intervals. Use paired comparisons when evaluating two system versions on the same tasks. That separates version effects from task difficulty.

For nondeterministic models, repeat important tasks across several seeds or generations. Measure variance and worst-case behavior, not only the best sample.

Bootstrap confidence intervals are useful when the metric is complex. For rare safety events, however, ordinary sampling may never observe the failure. Use targeted adversarial suites and fault injection in addition to representative traffic.

Define a minimum meaningful change. A one-point improvement may not justify rollout if it falls inside ordinary run-to-run variance or adds substantial latency.

Evaluation is itself a sensor. It has resolution, noise, bias, range, and blind spots.

#### Prevent evaluation leakage and metric gaming

Once a metric controls promotion, people and models optimize it.

If the evaluator rewards citations, the system may add more citations without improving support. If it rewards fast incident closure, the agent may declare success early. If developers repeatedly inspect the private test set, it stops being private.

Maintain layered datasets.

A development set supports iteration.

A regression set protects known behavior.

A private acceptance set supports release decisions.

A rotating adversarial set explores new failures.

Production feedback tests whether offline success transfers to reality.

Version tasks and graders, but keep stable anchor tasks so you can compare over time. When a task changes because the real requirement changed, record that explicitly rather than rewriting history.

Look for suspicious improvements. If answer quality jumps while tool use, retrieval recall, or coverage falls, inspect the traces. The system may have learned to produce polished generic answers or abstain selectively.

#### Move from offline evaluation to controlled production evidence

Offline evaluation is necessary because it is repeatable and safe. It is not sufficient because production contains different language, load, permissions, data quality, and human behavior.

Begin with replay. Run recorded incidents against a new version without affecting users.

Then shadow. Let the new system observe live inputs and produce hidden outputs while the existing process remains authoritative.

Then canary. Expose a small, low-risk population with tight monitoring and rollback.

Only then expand.

Define rollback triggers before rollout: hard-gate violation, citation-validity drop, latency breach, cost spike, abnormal abstention, unauthorized access attempt, or operator-reported harm.

Production metrics should join technical traces with eventual outcomes. Did the recommended check find the fault? Did maintenance confirm the hypothesis? Was the incident reopened? Did the operator override the system? How long until recovery?

Beware delayed labels. Root cause may be known hours later. A repair may appear successful and then fail on the next shift. Preserve the original prediction and join the outcome when it becomes available.

#### Treat evaluator changes like production code

An evaluator has schemas, dependencies, thresholds, and failure modes.

Test it with deliberately good and bad records. Include edge cases: missing fields, null values, duplicate citations, nonexistent sources, forbidden actions hidden after valid calls, and required abstention represented incorrectly.

Version every component: task set, label revision, scoring code, grader prompt, grader model, policy, and aggregation rule.

Pin the evaluator used for a release. If the grader changes next week, you should still be able to reconstruct why today’s version passed.

Monitor evaluator health. A grader API can fail, time out, or drift. A parsing bug can silently mark missing results as passes. A warehouse query can omit null rows. Fail closed for required gates and label incomplete evaluation as incomplete, not successful.

The measurement system needs commissioning too.

#### Apply the architecture to `score_run.py`

Now the existing Playground checkpoint should make more sense.

Each JSON-lines record is one golden-task run. Give it a stable task ID and task version.

Store the expected evidence IDs, observed evidence IDs, cited source IDs, valid source catalog, tool-call sequence, terminal state, whether abstention was required, latency, and diagnosis result.

The scorer calculates diagnosis pass rate across the set.

Required-evidence coverage is the fraction of required items actually collected, reported per task before aggregation.

Citation validity checks that every cited ID exists in the run’s allowed evidence set. Citation support is a later semantic measure; validity itself can be deterministic.

Total tool calls reveal cost and looping. Latency measures usability, but neither should override correctness or safety.

Then apply hard gates before summary scoring.

If any record contains a forbidden tool call, stop.

If any citation ID is invalid, stop.

If a task requires abstention and the run returns an actionable diagnosis, stop.

Print the task ID and exact gate. Do not hide the failure beneath averages.

After every record clears the gates, compare the scored thresholds. Perhaps diagnosis pass rate must exceed eighty percent, mean evidence coverage must exceed ninety percent, and high-percentile latency must remain within the user target.

The first unsafe mock record proves the gate works. Removing that violation and passing the same dataset proves the release path works.

That small script is not busywork. It is the first executable acceptance policy for the capstone.

### Playground checkpoint: unchanged until completed

GitHub still shows no completion evidence, so today adds no new task.

Create `evals/score_run.py` and a mock `evals/sample_run.jsonl`.

Calculate diagnosis pass rate, required-evidence coverage, citation validity, total tool calls, and latency. Emit either pass or stop.

Stop must be mandatory if any record contains a forbidden tool call, an invalid citation, or failure to abstain when abstention is required. Print the exact task ID and violated gate.

Use four clean mock cases and one unsafe-action case containing a prohibited write attempt. Confirm that excellent averages cannot override the stop decision. Then remove the violation and confirm that the same scorer passes.

This remains one focused twenty-to-thirty-minute task and will remain the checkpoint until GitHub shows it is complete or you deliberately change direction.

### Practical takeaway

For one AI feature, write the deployment decision first. Then define one hard gate, one quality metric, one operational metric, and one real-world outcome that supports that decision.

If the evaluation produces a number but cannot tell you what action the number authorizes, the measurement contract is incomplete.

### Closing recap

GitHub’s Copilot reviewer can now use more shell tools and combine several reviewing agents, adding ways to collect evidence while leaving the meaning of its reported improvements dependent on the evaluation design.

BigQuery’s `ML.METRICS` can evaluate external classification and regression predictions directly in SQL, but engineers still own missing-data behavior, label quality, class weighting, slicing, and acceptance.

And a production AI evaluation system measures the complete trajectory: inputs, retrieval, tools, orchestration, answers, policy, latency, and outcomes.

Averages help optimize systems that are already safe.

Hard gates decide whether the system is allowed to proceed.

The checkpoint remains unchanged: build the scorer and prove that one safety violation stops the run.

That’s today’s Engineering Commute.

Have a good Sunday.

## Compact show notes

- **Copilot code review — September 11:** GitHub added automatic comment resolution, smart autofix commit messages, broader shell-tool validation, and an ensemble of agents for Lite reviews. GitHub reports more addressed findings in its experiments, with the usual limitation that these are vendor measurements on its evaluation setup. [GitHub changelog](https://github.blog/changelog/2026-09-11-auto-resolution-and-analysis-updates-in-copilot-code-review/).

- **BigQuery `ML.METRICS` — September 10:** Preview SQL evaluation for classification or regression predictions from any table or query, without requiring a stored BigQuery model. [Google Cloud release notes](https://docs.cloud.google.com/release-notes) and [`ML.METRICS` reference](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-metrics).

- **Evergreen lesson references:** [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework), [NIST AI RMF Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence), [Google Rules of Machine Learning](https://developers.google.com/machine-learning/guides/rules-of-ml), and [scikit-learn model-evaluation guide](https://scikit-learn.org/stable/modules/model_evaluation.html).

- **Streaming status:** No substantive Apache Kafka or NATS JetStream release newer than the JetStream 2.15 release candidate covered earlier this week. [Apache Kafka releases](https://kafka.apache.org/blog/releases/) and [NATS Server releases](https://github.com/nats-io/nats-server/releases).

- **Playground status:** No new commit after the September 9 curriculum expansion. [Current commit](https://github.com/danthemanhernan/AiSystemsEngPlayground/commit/e3e18c0a39561919a0da3619c440cd09b728356d), [curriculum roadmap](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/docs/roadmap.md), [Module 13: capstone](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/modules/13_capstone.md), and [Factory AI Engineer project](https://github.com/danthemanhernan/AiSystemsEngPlayground/blob/main/projects/capstone_factory_ai_engineer/README.md).

- **Checkpoint, repeated:** Create `evals/score_run.py` and five mock run records; calculate correctness and process metrics; enforce a non-averaged stop gate for forbidden tool calls, invalid citations, or required-abstention failures.

- **Estimated spoken runtime:** Approximately 29–31 minutes, with about 23–25 minutes devoted to the evergreen evaluation lesson and capstone application.
