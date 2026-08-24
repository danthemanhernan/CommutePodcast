# The Engineering Commute: Your CI Pipeline Is a Production System

Welcome to The Engineering Commute, the show that turns the week’s engineering changes into ideas you can actually use.

Today’s episode starts with a small GitHub changelog entry that points to a much larger lesson: your continuous integration pipeline is not just a test runner. It is a production system with credentials, compute, network access, writable caches, and the ability to publish software. That makes it part of your attack surface.

This matters even if you are working on a personal portfolio project. A workflow may be only fifty lines of YAML, but those fifty lines can clone untrusted code, execute shell commands, access repository tokens, upload artifacts, write to caches, publish containers, and deploy infrastructure. In security terms, the YAML is not configuration sitting beside your software. The YAML is software.

GitHub’s latest CodeQL update, version 2.26.3, improves how code scanning reasons about GitHub Actions workflows. One specific change is that CodeQL now recognizes data from the merge-group event as untrusted. Merge groups are used by merge queues to test a temporary combination of pull requests before those changes reach the protected branch. The event is useful, but its fields still describe code and metadata that may have originated outside your trusted boundary.

That gives us the first principle for today: event data is input data.

Imagine an industrial controller receiving a recipe name from an upstream system. You would not concatenate that value directly into a command string and execute it with administrator privileges. You would validate it, constrain it to an expected schema, and keep the execution context as limited as possible. A CI workflow should receive the same treatment.

Fields such as a branch name, pull-request title, commit message, issue body, or event payload can eventually reach a shell command. If an expression is expanded directly inside a run block, special characters can change the meaning of that command. The dangerous mental shortcut is assuming that data is trusted because GitHub supplied it. GitHub may be transporting the value, but the value can still have been chosen by an untrusted contributor.

A safer pattern is to separate data from code. Put the expression into an environment variable and let the process read it as data. Quote variables at the shell boundary. Prefer structured inputs over string construction. If you need a short label, validate it against an allowlist. And most importantly, do not give the job more permission than it requires.

GitHub Actions supports explicit permissions for the built-in repository token. A test job that only checks out code usually does not need permission to write packages, modify pull requests, or create deployments. Start with read-only permissions and add individual write capabilities only where a job truly needs them. Better yet, separate an untrusted validation workflow from the trusted release workflow. Testing a pull request and publishing a container do not need to happen inside the same authority boundary.

This resembles the separation between safety logic and normal control logic in industrial systems. You do not want a convenience function to inherit the ability to bypass every interlock. In the same way, a lint step should not inherit a deployment token simply because both steps happen to live in one workflow file.

The CodeQL update also removed a module that attempted to classify runners by their labels. GitHub’s explanation is important: runner labels do not reliably distinguish a self-hosted runner from a managed runner.

That sounds like an implementation detail, but it exposes a general security mistake: using a descriptive label as proof of identity or trust.

A label such as Linux, build, internal, or self-hosted tells you how someone intended to categorize a runner. It does not prove where the machine is, what network it can reach, which secrets it has, or who can cause work to execute on it. Trust should come from enforceable boundaries: runner groups, repository policies, network segmentation, short-lived credentials, protected environments, and approval gates.

Self-hosted runners deserve special attention because they may sit inside your network. If an untrusted pull request can execute arbitrary code on one, that code may scan internal services, read persistent files, tamper with later jobs, or steal credentials that were never intended for the pull request. An ephemeral runner reduces persistence risk because the environment is destroyed after the job, but it does not eliminate the need for least privilege and network controls.

Here is a useful model. Treat every workflow run as a temporary contractor arriving at a factory. Ask four questions. Who requested the work? What instructions can they influence? Which rooms can the contractor enter? And what remains behind after the contractor leaves?

The first question maps to the trigger. A scheduled workflow, a push to a protected branch, and a pull request from a fork carry different levels of trust.

The second maps to code and event data. Can the requester change the workflow itself, the scripts it calls, dependency lock files, test fixtures, or command-line arguments?

The third maps to permissions, secrets, network access, environments, and runner placement.

The fourth maps to caches, artifacts, persistent workspaces, packages, images, and anything written to an external system.

That last category is easy to miss. A malicious job does not always need to steal a secret immediately. It can poison something that a more trusted job consumes later.

Credentials are another place where convenience can hide the real boundary. A long-lived cloud access key stored as a repository secret behaves like a physical master key copied into a lockbox. Every workflow that can open the lockbox inherits the life and reach of that credential. If it leaks, the credential remains useful until someone discovers the problem and revokes it.

A stronger pattern is workload identity with short-lived credentials. The workflow proves its identity to the cloud provider, usually through an OpenID Connect token, and receives a temporary credential limited to a particular role. The cloud trust policy can examine claims such as the repository, branch, environment, or workflow before granting access. You have replaced a stored secret with a time-limited exchange governed by policy.

Short-lived does not mean harmless. If an untrusted workflow is permitted to request the role, the attacker can still use the credential during its valid window. The real security improvement comes from combining short lifetime with narrow permissions and strict identity conditions.

Protected deployment environments add another useful boundary. A build job can produce a candidate artifact without receiving production credentials. A separate deployment job targets a protected environment, waits for required approval or branch policy, and only then receives the environment’s secrets. The artifact crosses the boundary, but the authority does not flow backward into the build.

This also improves incident reconstruction. When a deployment fails, you can answer which artifact was promoted, who approved it, what commit it came from, and which identity performed the change. Good security controls often improve operability because both depend on explicit state transitions.

Think about the pipeline as a state machine. Source becomes candidate. Candidate becomes verified. Verified becomes approved. Approved becomes deployed. Each transition should have an owner, evidence, and a limited capability. If one job can jump directly from arbitrary source code to production, the state machine exists only in your imagination.

CodeQL 2.26.3 improves several queries related to cache poisoning and untrusted checkout behavior. Cache poisoning is a classic boundary-crossing problem. A low-trust job writes content into a shared cache. Later, a high-trust job restores that content and treats it as legitimate. The attacker has moved code across the trust boundary indirectly.

The right response is not to ban caching. It is to design cache identity and write access deliberately. Do not let untrusted and trusted workflows write to the same cache scope. Avoid caching executable output when you can cheaply rebuild it. Include lock-file hashes and relevant toolchain versions in cache keys. Treat a cache miss as a performance event, but treat a cache hit as unverified input unless the platform and scope give you a strong integrity guarantee.

The same principle applies to artifacts. A build artifact is not safe merely because another workflow produced it. You need provenance: which commit produced it, under which workflow, from which trigger, with what permissions, and whether it was modified afterward.

GitHub also recently introduced a self-repository reference syntax for actions and reusable workflows. A uses value beginning with dollar-slash can point to an action in the same repository at the exact commit already running. Previously, teams often used a workspace-relative path after checkout or hard-coded a separate version reference. The new syntax helps internal actions follow the caller’s pinned commit without requiring that checkout step.

Why is that meaningful? Because a dependency reference is part of your software supply chain, even when the dependency lives in your own repository. If the main workflow is pinned to one commit but its helper workflow floats to another ref, your execution is no longer reproducible. The code you reviewed is not necessarily the code you ran.

Commit pinning narrows that gap. It converts a moving name into a specific object. But pinning is not the whole strategy. You still need a process to review and update pinned dependencies. Otherwise, immutability becomes stagnation and you quietly accumulate known vulnerabilities. A useful automation can propose version updates, but a human or trusted policy should review what changed before the new commit becomes authoritative.

Now let’s talk about speed. GitHub Actions recently added native support for background and parallel steps. This is useful. Independent tests, builds, or telemetry uploads no longer have to run sequentially inside a job, and their logs can remain separate.

But concurrency changes correctness. Two steps that were safe in sequence may race when they share a workspace, port, file, cache, database, or service. One test suite may reset a database while another is still reading it. Two builds may write to the same output directory. A background service may survive longer than expected and affect cleanup.

This is the same reason parallel PLC sequences require more than running two routines at once. You have to identify shared resources, define ownership, establish completion conditions, and make failure behavior explicit.

Before parallelizing CI steps, draw a tiny dependency graph. If step B consumes an artifact from step A, they are not independent. If two steps write to the same directory, give them isolated directories. If they share a test service, decide whether the service supports concurrent clients or whether each step needs its own instance. And make cancellation explicit so a failed foreground step does not leave a background process consuming resources or corrupting later output.

The performance metric should also be end-to-end feedback time, not maximum concurrency. Splitting a thirty-second check across four workers may cost more setup time than it saves. Parallelize the long, independent branches. Keep cheap steps simple.

There is a deeper observability lesson here too. A pipeline should expose more than a red or green badge. Track queue time, execution time, flaky-test rate, cache hit rate, retry count, and the age of the artifact being deployed. A workflow that passes only after three retries is not healthy. A test suite that takes twenty minutes but spends fifteen minutes waiting for a runner has a capacity problem, not a testing problem.

Apply the same thinking you would use on a production line. Cycle time is made of distinct states. A single average hides starvation, blockage, rework, and intermittent faults. CI telemetry should let you see whether feedback is slow because jobs wait, dependencies download, tests execute, or failures repeat.

This becomes particularly valuable when you introduce parallel execution. If total compute minutes double while developer feedback improves by only ten seconds, you have purchased activity rather than throughput. Measure the constraint before and after the change.

So what should you do with your own repositories this week?

Take one GitHub Actions workflow and perform a five-boundary audit.

First, label every trigger as low trust or high trust.

Second, find every place event data enters a shell command, file path, cache key, or deployment input.

Third, write down the effective permissions and secrets available to each job.

Fourth, identify anything one job produces that another job later trusts: caches, artifacts, packages, images, generated code, or deployment metadata.

Fifth, mark any step you could parallelize, then list every resource it shares before you change the workflow.

For a portfolio project, save the result as a short threat-model document beside the workflow. That demonstrates something more valuable than knowing GitHub Actions syntax. It shows that you understand execution boundaries, supply-chain risk, and operational correctness.

Today’s takeaway is simple: continuous integration is production infrastructure. Treat event payloads as input, labels as descriptions rather than proof, caches as cross-run data, dependency references as supply-chain decisions, and concurrency as a correctness problem before it becomes a speed optimization.

That is your Engineering Commute. Next episode, we will move from build pipelines to live systems and look at how streaming data can give AI agents fresh context without giving them uncontrolled authority.
