# ADR 0010: Publish a portable private podcast feed before cloud orchestration

- Status: Accepted
- Date: 2026-10-22
- Stage: Early v1.0 distribution slice

## Context

Finished local MP3s need to play in Apple Podcasts. Cloud workers and scheduled generation are
not prerequisites for subscribing to a feed.

## Decision

Build RSS from a dedicated directory of ffprobe-validated MP3s in a separate publishing module.
Store persistent GUIDs and dates in a private local catalog. Address media by SHA-256 hash and
replace the feed atomically after preparing media. Keep hosting outside generation. Use an
unguessable HTTPS directory and the iTunes directory-blocking tag for personal link privacy.

## Consequences

Existing audio is reusable without paid generation. The portable output can use S3/CloudFront or
another HTTPS host with HEAD and byte-range support. Catalog backups and stable source filenames
are required. Publish media before RSS, retain old media, and serialize builds. Link holders can
access the feed; token rotation requires moving the entire prefix and following the new URL.
This does not complete authenticated distribution, cloud deployment, artwork, or retention policy.

## Revisit when

Multiple listeners require revocation, generation runs remotely, or publication needs automation.
