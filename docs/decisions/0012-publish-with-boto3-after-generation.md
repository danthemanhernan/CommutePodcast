# ADR 0012: Publish through Boto3 after a successful generation batch

- Status: Accepted
- Date: 2026-10-25
- Stage: Early podcast distribution slice

## Context

Manual AWS CLI uploads require exporting variables separately from the CLI's dotenv loader.
Listeners need a repeatable workflow that refreshes the feed when generation finishes.

## Decision

The generation shell script selects `generate-all --publish`. The CLI composes generation, local
feed building, and a separate Boto3 publishing module; no AWS details enter `episode.py` or the
speech provider protocol. Hosting variables are loaded by dotenv; AWS authentication uses the SDK
credential chain with CRT support for AWS login profiles.

Validate hosting syntax before paid generation. Publish only after the entire generation batch
succeeds, including when no generation is pending. A failed batch keeps the previous hosted feed.
Offer a separate `publish` command for upload retries without TTS. Dry runs do no AWS work.

Validate local hashes/lengths, HEAD each referenced immutable object, upload only missing audio,
and replace RSS last. Never delete remote media, upload the catalog, or set public ACLs. Treat
permission failures differently from missing objects. Stop on mismatched remote size/content type.
Log correlation IDs and counts without private destination details or raw SDK exceptions.

## Consequences

A retry reuses successfully uploaded media and completed local audio. Publishing RSS is the commit
point; an interrupted media upload leaves the previous hosted feed usable. This is not a distributed
transaction or concurrent writer solution: run one workflow at a time. The publisher assumes that
existing hash-addressed objects with matching size/type contain their originally uploaded bytes.
Bucket/KMS/IAM and CloudFront setup remain operator responsibilities, including device playback QA.
CRT adds a platform dependency but supports the user's existing `aws login` authentication.
