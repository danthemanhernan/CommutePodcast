# Commute Podcast

Turn technical podcast scripts into commute-ready MP3 episodes. Stage 1 is a local-first Python
CLI used directly or through a ChatGPT Work skill. The core is intentionally provider-neutral so
the same workflow can later run behind a remote MCP server and an AWS job queue.

## Learn while building

This repository is organized as an engineering capstone, with complete vertical slices and explicit
learning evidence:

- [Learning roadmap](ROADMAP.md): versions, objectives, task checklists, and exit criteria
- [Stage 1 code walkthrough](docs/stage-01-local-pipeline.md): what every current module does
- [Stage 2 provider evaluation](docs/stage-02-provider-evaluation.md): transcript library and comparison workflow
- [Version 0.4 scorecard](docs/v04-evaluation-scorecard.md): objective and listening evaluation template
- [Learning log](docs/learning-log.md): reflection and evidence after each slice
- [Architecture decisions](docs/decisions/README.md): durable choices and their tradeoffs
- [Codex workflow](docs/codex-workflow.md): continue locally, in worktrees, and eventually in cloud
- [Architecture evolution](docs/architecture.md): local-to-MCP system shape

## Stage 1 capabilities

- Configurable OpenAI text-to-speech voice and delivery style
- Paragraph- and sentence-aware script chunking
- Resumable generation with a per-episode working directory
- Deterministic `plan` command that estimates chunks, duration, and API input size without cost
- MP3 concatenation and optional EBU R128 loudness normalization through `ffmpeg`
- Episode manifest containing settings and generated artifacts
- Repository-backed transcript library for repeatable episode generation
- `--dry-run` mode for verifying the entire local workflow without an API call

## Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)
- `ffmpeg`
- An OpenAI API key for real generation

## Setup

```bash
uv sync --extra dev
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. The CLI loads that file automatically and never
prints the key.

You can also set the key in your shell:

```bash
export OPENAI_API_KEY="your-key"
```

## Try it safely

Inspect how a script will be processed:

```bash
uv run commute-podcast plan examples/pilot.md
```

Exercise the complete pipeline without calling a paid API:

```bash
uv run commute-podcast generate examples/pilot.md --dry-run
```

Generate the real episode:

```bash
uv run commute-podcast generate examples/pilot.md --title "Pilot Episode"
```

Output is written under `episodes/<episode-slug>/`, with the finished MP3 copied to
`episodes/<episode-slug>.mp3`.

## Generate new content-library episodes

Put dated transcripts matching `YYYY-MM-DD-topic-slug.md` directly in `content/episodes/`, then
run:

```bash
./scripts/generate-pending-episodes.sh
```

This invokes `commute-podcast generate-all --publish`, creates MP3s in `episodes/finished/`, and skips any
transcript whose source filename or title slug already has a finished MP3. The first Markdown H1
is used as the episode title; when there is no H1, the filename becomes the title. Failed transcripts are
reported while other pending transcripts continue, and the command exits non-zero if anything
failed. Exhausted API credits stop the batch and defer later scripts. After a successful batch,
the script rebuilds the podcast feed, uploads missing audio to S3, and uploads `feed.xml` last.
It publishes even if every episode was already generated. If generation fails, publication is skipped.
Use `--dry-run` to rehearse generation without paid API calls or AWS requests. Hosting configuration
is required for a real run; see below. For local generation only, use `uv run commute-podcast generate-all`.

Run every local quality check:

```bash
make check
```

## Roadmap summary

The project progresses from a local CLI through provider evaluation, containerized jobs, an AWS
pipeline, a remote MCP plugin, scheduled research, and a private RSS feed. See [ROADMAP.md](ROADMAP.md)
for versioned feature lists, learning objectives, implementation checklists, and acceptance tests.

AI-generated voices should be disclosed to listeners. Only clone or use voices for which you have
the necessary consent and rights.

## S3 hosting and Apple Podcasts

The shell script now generates pending episodes **and publishes the feed through Boto3**.
Set up hosting once, then run the same script whenever you add transcripts.

### 1. Set up HTTPS hosting

Use a private S3 bucket with Block Public Access enabled and a CloudFront HTTPS distribution
using Origin Access Control and the S3 REST origin. Grant CloudFront read access to the bucket;
allow GET/HEAD and byte-range playback. Keep the CloudFront origin path empty when using the
matching prefixes below. Set the CloudFront cache policy minimum TTL to 0 so the feed can refresh
after its 60-second cache lifetime. No infrastructure is provisioned by this repository.

Generate a private path once with `openssl rand -hex 24`. Keep and reuse it; changing it changes
your subscription URL. Add the following to the ignored `.env` file:

```dotenv
PODCAST_S3_URI=s3://YOUR-BUCKET/YOUR-RANDOM-PREFIX
PODCAST_BASE_URL=https://YOUR-DISTRIBUTION.cloudfront.net/YOUR-RANDOM-PREFIX
# Optional named profile and region; omit these to use your AWS defaults.
# AWS_PROFILE=your-profile
# AWS_DEFAULT_REGION=us-west-2
```

Use the same prefix in both values. `PODCAST_BASE_URL` is the HTTPS directory, without `feed.xml`.
The CLI loads `.env` automatically, so no manual `export` or `source` is needed. Existing exported
variables take precedence. Keep API keys, AWS credentials, and private feed URLs out of Git.

### 2. Install dependencies and sign in

```bash
uv sync --extra dev
aws configure set region us-west-2  # use your bucket's actual region
aws login
aws sts get-caller-identity
```

Install AWS CLI v2 first if `aws` is unavailable (`brew install awscli` on macOS). For a named
profile, sign in with `aws login --profile your-profile` and set `AWS_PROFILE` in `.env`.
Boto3 uses your AWS credential profile; its CRT dependency supports `aws login` sessions.
When credentials expire, refresh the same profile selected by `AWS_PROFILE` in `.env`:

```bash
aws login --profile commute-podcast
aws sts get-caller-identity --profile commute-podcast
```

Replace `commute-podcast` if you chose a different profile name. For the default profile, run
`aws login` without `--profile`. The AWS CLI does not load this repo's `.env`, so specify the named
profile explicitly when refreshing credentials. After signing in, retry `uv run commute-podcast publish`.
An IAM Identity Center profile instead uses `aws sso login --profile your-profile` to refresh,
after its initial `aws configure sso` setup.

Your uploading identity needs S3 ListBucket, GetObject (for HEAD checks), and PutObject access
for the destination. Restrict object access to your chosen prefix. Multipart transfers can also
need AbortMultipartUpload; customer-managed KMS encryption needs appropriate key permissions.
The script never changes bucket policies, ACLs, or public access settings.

### 3. Generate and publish

```bash
./scripts/generate-pending-episodes.sh
```

The pipeline:

1. Skips finished episodes and reuses validated completed speech chunks.
2. Builds RSS and hashed MP3 copies under `episodes/podcast-feed/`.
3. Checks each referenced MP3 in S3 and skips existing objects with matching size and audio type.
4. Uploads missing MP3s with `audio/mpeg` and immutable cache headers.
5. Uploads `feed.xml` last with `application/rss+xml` and a 60-second cache lifetime.

It uploads only referenced audio, transcript pages, and RSS, keeps `catalog.json` locally, and never deletes hosted
objects. The catalog preserves stable episode IDs and dates: back it up privately and keep source
filenames stable. Run one generator/publisher at a time.

If S3 upload fails, local audio remains intact. Retry publishing without speech API calls:

```bash
uv run commute-podcast publish
```

Validate and package existing audio without AWS requests:

```bash
uv run commute-podcast publish --dry-run
```

This dry run builds local files and validates their hashes, URLs, and lengths. It does not check AWS
credentials, bucket permissions, or which remote objects already exist. To rehearse the generation
script without publishing, use `./scripts/generate-pending-episodes.sh --dry-run`.

Use `--finished-directory` and `--feed-directory` with the generation script for custom paths.
For publish-only runs, use `--source-directory` and `--feed-directory`. `build-feed` remains available
for local packaging without S3. If there are no finished MP3s, publication fails clearly.

### 4. Follow in Apple Podcasts

On iPhone, open **Podcasts → Library → ⋯ → Follow a Show by URL** and enter your
`PODCAST_BASE_URL` followed by `/feed.xml`. On Mac use **File → Follow a Show by URL**.
No Apple Podcasts Connect submission is needed for direct private feed following. Updates appear
when the app refreshes the feed; CloudFront caching can add a short delay.

Verify HTTPS streaming and seeking, including HEAD responses and `206 Partial Content` for range
requests. Your S3 URI is only the upload destination; Apple Podcasts needs the HTTPS URL.
Anyone with the private URL can listen. The feed's directory-blocking tag discourages indexing
but does not provide account authentication.

See [the detailed walkthrough](docs/apple-podcasts.md),
[Apple's private feed guide](https://podcasters.apple.com/support/5108-how-apple-podcasts-distributes-your-shows-to-listeners),
and [Boto3 credential configuration](https://docs.aws.amazon.com/boto3/latest/guide/credentials.html).

### Transcripts and episode order

Episode notes include a **Read the transcript** link when saved narration text is available. The
feed also includes a standard Podcasting 2.0 transcript tag. Apple does not provide its native
transcript view for private-feed episodes; use the link in the notes instead.
[Apple's transcript limitation](https://podcasters.apple.com/support/5316-transcripts-on-apple-podcasts)

Publication uploads transcript HTML before RSS. Transcript URLs use `YOUR-RANDOM-PREFIX/media/transcripts/*`, covered by the
publisher's existing `media/*` S3 permissions. Allow CloudFront to read that path. The
[example IAM policy](docs/iam-podcast-publisher.json) includes audio, feed, and transcript permissions;
replace its placeholders before attaching it to your publishing group. The separate
`SignInLocalDevelopmentAccess` managed policy is still needed for `aws login`.

Episode publication dates now follow the date in the filename/title, rather than the time the MP3
was generated or copied. Rebuilding corrects existing dated entries while preserving their IDs and
audio links. Undated episodes keep their original dates. For playback from the first lesson, select
**Show → ⋯ → Settings → Episode Order → Oldest to Newest** in Apple Podcasts. The feed itself is
newest first. See [transcript and ordering details](docs/apple-podcasts.md#transcripts-and-chronological-order).
