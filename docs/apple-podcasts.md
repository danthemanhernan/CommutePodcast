# Listen in Apple Podcasts

The `build-feed` command packages existing, validated MP3s into an RSS feed. It never calls a
speech provider. You need an HTTPS host before the feed will work on your phone.

## Automatic generation and publication

Configure `PODCAST_BASE_URL` and `PODCAST_S3_URI` in `.env`, authenticate with `aws login`, and run:

```bash
./scripts/generate-pending-episodes.sh
```

The script selects `generate-all --publish`. After a successful batch, the CLI calls the separate
`publishing.py` module through Boto3. It packages finished audio, verifies local content hashes,
checks referenced S3 objects with HEAD, uploads missing media, and uploads RSS last. Existing
objects must match size and `audio/mpeg`; mismatches stop publication rather than overwrite
immutable media. Only 404/missing-object errors trigger uploads; permission errors stop safely.
An S3 failure leaves local artifacts intact. Retry with `uv run commute-podcast publish` to avoid
speech generation. `publish --dry-run` validates/builds locally without creating an AWS client.
The generation script's `--dry-run` skips publication entirely. Failed generation skips publishing.

A successful batch with no pending scripts still publishes, allowing upload retries after earlier
failures. Boto3 and CRT use the AWS login profile, optionally selected by `AWS_PROFILE` in `.env`.
AWS SDK retries are bounded. No feed URLs, bucket names, private prefixes, or SDK exception strings
are printed by publication logs; logs use a generated publication correlation ID. Run one workflow
at a time. See the [README](../README.md#s3-hosting-and-apple-podcasts) for complete setup.

## Build the portable directory

Set `PODCAST_BASE_URL` in your ignored `.env` to the HTTPS directory where you will host the feed,
including a long random path for link privacy. Do not commit or share that value. For a local
rehearsal only, use `https://example.invalid/private-demo` (this address cannot play on a phone).

```bash
uv run commute-podcast build-feed
```

Defaults read `episodes/finished/*.mp3` and write `episodes/podcast-feed/`. Use
`--source-directory episodes` for older episodes stored directly in `episodes/`, or collect finished
MP3s in one dedicated directory. The source must contain only finished episodes. Invalid MP3s abort
before replacing the previous feed. Missing titles fall back to filenames; publication dates use episode dates when present, with file modification time as the undated fallback. Existing ID3 titles are preferred.

The output contains `feed.xml`, `media/`, and a local `catalog.json`. Preserve the catalog: it stores
stable episode IDs and dates. Back it up privately. The Boto3 publisher uploads referenced `media/` audio and local `transcripts/` HTML (hosted under
`media/transcripts/`), then `feed.xml`; do not upload
the catalog, source transcripts, manifests, or chunk directories. Run one build at a time.

## Hosting with S3 and CloudFront

A suitable AWS setup is a private S3 bucket behind a CloudFront HTTPS distribution using Origin
Access Control. Keep S3 Block Public Access enabled and grant the distribution read access to its
origin. Use the S3 REST origin, not the website endpoint. Configure CloudFront to forward HEAD and
GET and support range requests. No worker, queue, MCP server, or TTS changes are required.

Choose a long random prefix, generated with `openssl rand -hex 24`. Your base URL will look like
`https://YOUR-DISTRIBUTION.cloudfront.net/YOUR-RANDOM-PREFIX`. Store the real URL in `.env` and
rebuild. The prefix is a bearer secret: anyone with the URL can listen. This is link privacy,
not individual account authentication. `<itunes:block>Yes</itunes:block>` discourages directory
indexing; it does not enforce access control.

After configuring AWS CLI credentials through your normal AWS login, set `PODCAST_S3_URI` locally
to `s3://YOUR-BUCKET/YOUR-RANDOM-PREFIX` and upload **media first, feed last**:

```bash
aws s3 sync episodes/podcast-feed/media/ "$PODCAST_S3_URI/media/" \
  --content-type audio/mpeg --cache-control 'public,max-age=31536000,immutable' --only-show-errors
aws s3 cp episodes/podcast-feed/feed.xml "$PODCAST_S3_URI/feed.xml" \
  --content-type application/rss+xml --cache-control 'public,max-age=60' --only-show-errors
```

Configure the CloudFront cache policy with minimum TTL 0 so the feed's cache header is respected.
Do not use `--delete`: older downloaded feeds can still reference old media. Audio filenames are
content hashes, so replacing a recording cannot overwrite audio already referenced by a feed.
Review AWS storage and transfer pricing before creating hosting. This repository does not provision
AWS resources. The commands above are an optional manual alternative to Boto3 publication.

## Verify and follow

Check the hosted feed returns XML, media HEAD returns `Content-Type: audio/mpeg` and a correct
`Content-Length`, and a GET with `Range: bytes=0-99` returns `206 Partial Content`. Use your HTTP
client privately; the URLs contain your subscriber prefix. Test streaming and seeking on the phone.

On iPhone: Podcasts → Library → ⋯ → Follow a Show by URL. Enter the HTTPS URL ending in
`/feed.xml`. On Mac, use File → Follow a Show by URL. No public directory submission is needed.

The generation shell script rebuilds and publishes automatically. With manual generation, run
`commute-podcast publish` afterward, or rebuild and repeat the two manual uploads. Updates appear when the client
refreshes; they are not pushed immediately. Removing a source MP3 removes it from the next feed,
but leaves hosted media intact. Renaming a source file gives it a new identity; keep names stable.
Cover artwork and richer show metadata can be added later; this slice targets direct URL following,
not public catalog submission.

## Learning and acceptance

You should be able to explain the separation between RSS metadata and hosted audio, stable GUIDs
versus content-addressed media, link privacy versus authentication, and why uploads publish the feed
last. Reproduce a build without API access and prove IDs/dates survive a second build.

Local tests cover XML escaping, metadata, stable identities, immutable media, invalid audio recovery,
and URL validation. The remaining end-to-end exit criteria are HTTPS HEAD/range validation and
successful streaming, seeking, and refresh in Apple Podcasts after hosting is configured.

References: [Apple feed requirements](https://podcasters.apple.com/support/823-podcast-requirements)
and [private feed distribution](https://podcasters.apple.com/support/5108-how-apple-podcasts-distributes-your-shows-to-listeners).

## Transcripts and chronological order

Each available saved narration script becomes a mobile-readable, content-addressed HTML page under
`transcripts/`. The feed adds a Podcasting 2.0 `podcast:transcript` tag and a **Read the transcript**
link in the episode description. Text comes from the saved `part-*.txt` generation artifacts, using
the manifest chunk count to exclude stale parts. Imported recordings can provide an explicit
`<audio-stem>.transcript.txt` sidecar next to the finished MP3. A current repository draft is not
silently substituted for missing original narration. Missing scripts are omitted from transcript
metadata. These are narration scripts, not word-aligned ASR results; no timestamps are fabricated.

Apple explicitly does not display its native transcript view for episodes distributed only through
private RSS feeds. Open the transcript link from the episode notes instead. Other clients may use
the standard transcript tag. Making the show public just to enable native transcripts is a separate
distribution decision, not part of this change.

The publisher uploads referenced transcript HTML before replacing RSS. The uploading IAM policy
already covers the hosted `YOUR-PREFIX/media/transcripts/*` pages through its existing
`media/*` permissions. CloudFront must be able to read objects under that same media prefix. See [the policy template](iam-podcast-publisher.json).
For manual uploads, also sync `episodes/podcast-feed/transcripts/` to the destination's `media/transcripts/`
with Content-Type `text/html; charset=utf-8`, before uploading RSS.

Previously, publication dates came from MP3 modification times. Batch generation, copying, and
regeneration changed their order relative to the dates in the episode titles. Builds now derive dates
from ISO dates in audio filenames, then English month/day/year dates in filenames or titles. Dates
are set to 08:00 America/Los_Angeles, avoiding the previous-day display caused by UTC midnight.
Existing catalog publication dates are corrected for dated episodes while GUIDs and audio URLs
remain unchanged. Undated episodes retain their original catalog date. Equal dates use filename
order as a deterministic tie-breaker; clients may choose another tie order.

RSS remains newest first for an episodic show. To play lessons from the beginning, open the show
in Apple Podcasts → ⋯ → Settings → Episode Order → Oldest to Newest. An app's existing preference
cannot be overridden by the feed. Allow the app and CloudFront to refresh after republishing.

References: [Apple transcript limitations](https://podcasters.apple.com/support/5316-transcripts-on-apple-podcasts),
[episode ordering](https://podcasters.apple.com/support/3143-how-to-set-the-order-of-podcast-episodes),
and [Podcasting 2.0 transcript specification](https://podcasting2.org/docs/podcast-namespace/tags/transcript).
