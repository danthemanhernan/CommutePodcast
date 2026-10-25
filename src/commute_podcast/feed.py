"""Build a portable podcast directory without coupling generation to hosting."""

from __future__ import annotations

import hashlib
import html
import json
import math
import os
import shutil
import uuid
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urlsplit

from commute_podcast.audio import validate_audio
from commute_podcast.config import ShowConfig
from commute_podcast.feed_metadata import PODCAST, episode_date, narration_script, write_transcript

ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ET.register_namespace("itunes", ITUNES)
ET.register_namespace("podcast", PODCAST)


def build_feed(
    source: Path,
    destination: Path,
    show: ShowConfig,
    *,
    base_url: str,
    description: str,
) -> int:
    """Validate finished MP3s and publish the feed last; preserve the local catalog.

    The catalog is local state, not a file to upload. Keep it for stable dates and IDs.
    Existing media is immutable and addressed by content hash.
    """
    url = urlsplit(base_url)
    if (
        url.scheme != "https"
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
    ):
        raise ValueError("Base URL must be HTTPS without credentials, query, or fragment")
    if not description.strip():
        raise ValueError("Show description cannot be empty")
    paths = sorted(source.glob("*.mp3"))
    if not paths:
        raise ValueError("No finished MP3s found")
    if source.resolve() == destination.resolve():
        raise ValueError("Feed output must differ from the finished audio directory")
    catalog_path = destination / "catalog.json"
    catalog = json.loads(catalog_path.read_text()) if catalog_path.exists() else {}
    entries = []
    for path in paths:
        metadata = validate_audio(path)
        duration = float(metadata["format"]["duration"])
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError(f"Invalid duration: {path.name}")
        with path.open("rb") as audio:
            digest = hashlib.file_digest(audio, "sha256").hexdigest()
        record = catalog.setdefault(
            path.name,
            {
                "guid": f"urn:uuid:{uuid.uuid4()}",
                "published": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
            },
        )
        tags = metadata["format"].get("tags", {})
        title = tags.get("title") or path.stem.replace("-", " ").title()
        dated = episode_date(path, title)
        if dated is not None:
            record["published"] = dated.isoformat()
            record["date_source"] = "episode_date"
        else:
            record.setdefault("date_source", "original_file_time")
        entries.append((path, digest, duration, title, record))

    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")
    base_url = base_url.rstrip("/")
    for name, value in {
        "title": show.name,
        "link": base_url + "/feed.xml",
        "description": description,
        "language": "en-us",
        f"{{{ITUNES}}}author": show.author,
        f"{{{ITUNES}}}explicit": "false",
        f"{{{ITUNES}}}block": "Yes",
        f"{{{ITUNES}}}type": "episodic",
    }.items():
        ET.SubElement(channel, name).text = value
    media = destination / "media"
    media.mkdir(parents=True, exist_ok=True)
    for path, digest, duration, title, record in sorted(
        entries,
        key=lambda entry: (datetime.fromisoformat(entry[4]["published"]), entry[0].name),
        reverse=True,
    ):
        filename = digest + ".mp3"
        target = media / filename
        if not target.exists():
            temporary = media / (filename + ".tmp")
            shutil.copyfile(path, temporary)
            os.replace(temporary, target)
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        script = narration_script(path)
        if script:
            transcript = write_transcript(destination / "transcripts", title, script)
            transcript_url = base_url + "/media/transcripts/" + transcript
            ET.SubElement(
                item,
                f"{{{PODCAST}}}transcript",
                {
                    "url": transcript_url,
                    "type": "text/html",
                    "language": "en",
                },
            )
            ET.SubElement(item, "description").text = (
                f"<p>{html.escape(title)}</p>"
                f'<p><a href="{html.escape(transcript_url, quote=True)}">'
                "Read the transcript</a></p>"
            )
        else:
            ET.SubElement(item, "description").text = title
        ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = record["guid"]
        ET.SubElement(item, "pubDate").text = format_datetime(
            datetime.fromisoformat(record["published"])
        )
        ET.SubElement(item, f"{{{ITUNES}}}duration").text = str(round(duration))
        ET.SubElement(
            item,
            "enclosure",
            {
                "url": base_url + "/media/" + filename,
                "length": str(target.stat().st_size),
                "type": "audio/mpeg",
            },
        )
    # Save identity before the feed so an interrupted build cannot expose unrecorded IDs.
    temporary_catalog = destination / "catalog.json.tmp"
    temporary_catalog.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    os.replace(temporary_catalog, catalog_path)
    temporary_feed = destination / "feed.xml.tmp"
    ET.ElementTree(root).write(temporary_feed, encoding="utf-8", xml_declaration=True)
    os.replace(temporary_feed, destination / "feed.xml")
    return len(entries)
