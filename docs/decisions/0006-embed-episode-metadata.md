# ADR 0006: Embed episode metadata in generated MP3s

- Status: Accepted
- Date: 2026-08-23
- Stage: v0.3

## Context

The generated MP3s played correctly but appeared without useful title, artist, album, or genre
information when imported into Music or iTunes. That makes a commute library difficult to browse.

## Decision

Pass ID3 metadata to FFmpeg during final MP3 assembly. Use the episode title as the track title,
the configured show author as artist and album artist, the configured show name as album, and
`Podcast` as genre. Write ID3v2.3 tags for broad player compatibility.

## Consequences

Future episodes are self-describing when moved between Music, iTunes, Finder, and other players.
The metadata is derived from existing configuration and does not require a new database. Existing
files need a one-time retagging pass, and richer podcast fields such as episode number can be added
later if the configuration models them.

## Revisit when

The project adds explicit seasons, episode numbers, publication dates, descriptions, or RSS feed
generation.
