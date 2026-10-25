"""Publish a prepared feed to S3 independently of speech generation."""

from __future__ import annotations

import hashlib
import re
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from commute_podcast.feed_metadata import PODCAST
from commute_podcast.observability import log_event


@dataclass(frozen=True)
class HostingSettings:
    base_url: str
    bucket: str
    prefix: str

    @classmethod
    def parse(cls, base_url: str, s3_uri: str) -> HostingSettings:
        https = urlsplit(base_url)
        s3 = urlsplit(s3_uri)
        if (
            https.scheme != "https"
            or not https.hostname
            or https.username
            or https.password
            or https.query
            or https.fragment
        ):
            raise ValueError(
                "Set PODCAST_BASE_URL to an HTTPS directory without query or credentials"
            )
        prefix = s3.path.strip("/")
        if (
            s3.scheme != "s3"
            or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", s3.netloc)
            or not prefix
            or s3.query
            or s3.fragment
            or not re.fullmatch(r"[a-zA-Z0-9_/-]+", prefix)
            or any(part in {"", ".", ".."} for part in prefix.split("/"))
        ):
            raise ValueError("Set PODCAST_S3_URI to s3://bucket/private-prefix")
        return cls(base_url.rstrip("/"), s3.netloc, prefix)


def create_s3_client() -> Any:
    import boto3
    from botocore.config import Config

    return boto3.Session().client(
        "s3",
        config=Config(
            retries={"mode": "standard", "total_max_attempts": 3},
            connect_timeout=10,
            read_timeout=60,
        ),
    )


def publish_feed(
    directory: Path,
    settings: HostingSettings,
    *,
    dry_run: bool = False,
    client: Any = None,
) -> dict[str, int | bool]:
    """Verify local media; skip matching immutable objects; upload RSS only after all media.

    Never upload catalog, manifests, secrets, or unreferenced media. Never delete remote objects.
    Dry runs require no AWS client or credentials and perform no network requests.
    """
    feed = directory / "feed.xml"
    root = ET.parse(feed).getroot()
    enclosures = root.findall("channel/item/enclosure")
    if not enclosures:
        raise ValueError("Cannot publish a feed with no episodes")
    media: dict[str, Path] = {}
    for enclosure in enclosures:
        url = enclosure.get("url", "")
        name = url.removeprefix(settings.base_url + "/media/")
        if not re.fullmatch(r"[0-9a-f]{64}\.mp3", name):
            raise ValueError("Feed media URL does not match PODCAST_BASE_URL or a hashed MP3")
        path = directory / "media" / name
        with path.open("rb") as audio:
            digest = hashlib.file_digest(audio, "sha256").hexdigest()
        if digest != path.stem or str(path.stat().st_size) != enclosure.get("length"):
            raise ValueError("Feed media hash or enclosure length is invalid; rebuild the feed")
        media[name] = path
    transcripts: dict[str, Path] = {}
    for tag in root.findall(f"channel/item/{{{PODCAST}}}transcript"):
        name = tag.get("url", "").removeprefix(settings.base_url + "/media/transcripts/")
        if not re.fullmatch(r"[0-9a-f]{64}\.html", name) or tag.get("type") != "text/html":
            raise ValueError("Invalid transcript URL or type; rebuild the feed")
        path = directory / "transcripts" / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != path.stem:
            raise ValueError("Invalid transcript content hash; rebuild the feed")
        transcripts[name] = path
    if dry_run:
        return {
            "dry_run": True,
            "media_candidates": len(media),
            "transcript_candidates": len(transcripts),
            "uploaded": 0,
            "skipped": 0,
        }

    from botocore.exceptions import ClientError

    correlation_id = uuid.uuid4().hex
    log_event("s3_publication_started", episode_id=correlation_id, phase="publication")
    uploaded = skipped = 0
    try:
        s3 = client if client is not None else create_s3_client()
        for name, path in media.items():
            key = f"{settings.prefix}/media/{name}"
            try:
                existing = s3.head_object(Bucket=settings.bucket, Key=key)
            except ClientError as error:
                if error.response.get("Error", {}).get("Code") not in {
                    "404",
                    "NoSuchKey",
                    "NotFound",
                }:
                    raise
            else:
                if existing["ContentLength"] != path.stat().st_size:
                    raise ValueError("Remote immutable audio size mismatch")
                if existing.get("ContentType") != "audio/mpeg":
                    raise ValueError("Remote audio Content-Type must be audio/mpeg")
                skipped += 1
                continue
            s3.upload_file(
                str(path),
                settings.bucket,
                key,
                ExtraArgs={
                    "ContentType": "audio/mpeg",
                    "CacheControl": "public,max-age=31536000,immutable",
                },
            )
            uploaded += 1
        for name, path in transcripts.items():
            s3.upload_file(
                str(path),
                settings.bucket,
                f"{settings.prefix}/media/transcripts/{name}",
                ExtraArgs={
                    "ContentType": "text/html; charset=utf-8",
                    "CacheControl": "public,max-age=31536000,immutable",
                },
            )
        s3.upload_file(
            str(feed),
            settings.bucket,
            f"{settings.prefix}/feed.xml",
            ExtraArgs={
                "ContentType": "application/rss+xml",
                "CacheControl": "public,max-age=60",
            },
        )
    except Exception:
        log_event("s3_publication_failed", episode_id=correlation_id, phase="publication")
        # SDK exception strings may expose the private prefix or bucket. Keep CLI output safe.
        raise RuntimeError(
            "S3 publication failed. Check AWS login, bucket region, permissions, and remote "
            "audio metadata. Local files are preserved; rerun publish to retry."
        ) from None
    log_event("s3_publication_completed", episode_id=correlation_id, phase="publication")
    return {
        "dry_run": False,
        "media_candidates": len(media),
        "transcript_candidates": len(transcripts),
        "transcripts_uploaded": len(transcripts),
        "uploaded": uploaded,
        "skipped": skipped,
    }
