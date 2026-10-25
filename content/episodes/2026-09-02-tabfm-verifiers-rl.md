# The Engineering Commute --- September 2, 2026

## TabFM, Automated Approval, and RL Verifiers

### Narration-ready episode

Good morning, Dan.

Today's Engineering Commute is about deciding whether a measurement
deserves authority.

Google has added a pretrained tabular foundation model to BigQuery.
Cloudflare has prototyped compressing cached objects internally. And
GitHub can now allow Copilot's code review to count as an approving
pull-request review.

### Segment one: BigQuery turns labeled rows into in-context examples

Google announced TabFM in BigQuery, a pretrained foundation model for
tabular regression and classification.

Removing the training job does not remove the evaluation problem.

For predictive maintenance, define the observation cutoff, prediction
horizon, label delay, equipment population, and test period before
trusting output. Split evaluation data by time and, where appropriate,
by site or asset.

A prediction is an instrument reading. Before placing it in a control
loop, establish its range, calibration, failure modes, and validity
conditions.

### Segment two: Cloudflare is buying storage with CPU cycles

Cloudflare published results from a Cache Transcoding prototype built
inside Pingora.

The prototype encodes eligible uncompressed responses with Zstandard
before writing them to disk and decodes them at the client-facing hop.

This is resource conversion: spend CPU to consume fewer disk and network
bytes and potentially improve cache density.

The correct decision cannot be based on compression ratio alone.
Evaluate origin offload, hit ratio, backbone traffic, storage cost, CPU
saturation, tail latency, and power use.

### Segment three: Copilot can receive approval authority

GitHub announced that Copilot code review can include an approval
assessment, and administrators can separately authorize Copilot to
submit a formal approving review.

The essential distinction is between advice and authority.

Once an automated reviewer can make a pull request mergeable, its
false-negative rate becomes an operational concern. Required
deterministic tests and policies should remain independent gates.

Automation should earn authority through bounded scope and observed
performance.

### Playground Lesson: reinforcement learning, rollouts, and verifiers

Supervised fine-tuning teaches a model to imitate desirable examples.
Preference optimization uses comparative signals.

DPO trains directly on chosen and rejected response pairs. GRPO-style
methods generate a group of responses for the same prompt and compare
their rewards within that group.

A verifier evaluates whether an output satisfies a contract. For code,
it may run tests. For an industrial troubleshooting agent, it could
confirm that every conclusion cites an observation and that prohibited
actions were never requested.

The hazard is reward hacking: optimizing the inspection rather than the
product.

Your checkpoint is to build a toy verifier loop with deterministic
correctness and a deliberately weak presentation reward, then
demonstrate a confidently formatted but incorrect answer exploiting the
weak metric.

### Show notes

-   TabFM:
    https://cloud.google.com/blog/products/data-analytics/tabfm-adds-predictive-ml-to-bigquery
-   Cache Transcoding: https://blog.cloudflare.com/cache-transcoding/
-   Copilot approvals:
    https://github.blog/changelog/2026-09-01-copilot-code-review-can-now-approve-pull-requests/
-   Playground:
    https://github.com/danthemanhernan/AiSystemsEngPlayground
