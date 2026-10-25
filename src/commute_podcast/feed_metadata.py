"""Dates and readable narration scripts for locally generated episodes."""

from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

EPISODE_TIMEZONE = ZoneInfo("America/Los_Angeles")

PODCAST = "https://podcastindex.org/namespace/1.0"


def episode_date(path: Path, title: str) -> datetime | None:
    """Prefer the episode date over the time its MP3 was copied or regenerated."""
    for value in (path.stem, title):
        match = re.search(r"(?<!\d)(\d{4})[-_ ](\d{2})[-_ ](\d{2})(?!\d)", value)
        if match:
            return datetime(
                *(int(part) for part in match.groups()), hour=8, tzinfo=EPISODE_TIMEZONE
            )
        match = re.search(
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)"
            r"[ -]+(\d{1,2})[, -]+(\d{4})\b",
            value,
            re.IGNORECASE,
        )
        if match:
            return datetime.strptime(" ".join(match.groups()), "%B %d %Y").replace(
                hour=8, tzinfo=EPISODE_TIMEZONE
            )
    return None


def narration_script(audio: Path) -> str | None:
    """Use saved synthesis text; an explicit sidecar supports imported recordings.

    Never silently substitute a newer repository draft for an existing recording.
    """
    sidecar = audio.with_suffix(".transcript.txt")
    if sidecar.is_file():
        return sidecar.read_text(encoding="utf-8").strip() or None
    for directory in (audio.parent.parent / audio.stem, audio.parent / audio.stem):
        parts = sorted(directory.glob("part-*.txt"))
        if not parts:
            continue
        manifest = directory / "manifest.json"
        if manifest.exists():
            count = int(json.loads(manifest.read_text(encoding="utf-8"))["chunk_count"])
            parts = [directory / f"part-{index:03d}.txt" for index in range(1, count + 1)]
        if not all(path.is_file() for path in parts):
            raise ValueError("Missing narration text chunk; restore the episode working directory")
        return "\n\n".join(path.read_text(encoding="utf-8").strip() for path in parts)
    return None


def write_transcript(directory: Path, title: str, script: str) -> str:
    """Publish escaped, mobile-readable HTML without guessed word timestamps."""
    document = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)} — transcript</title>"
        "<style>body{max-width:48rem;margin:2rem auto;padding:0 1rem;"
        "font:18px/1.6 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere;"
        "font:inherit}</style></head><body>"
        f"<h1>{html.escape(title)}</h1><p>Narration script. "
        "Speech may differ slightly; this transcript has no synchronized timestamps.</p>"
        f"<pre>{html.escape(script)}</pre></body></html>\n"
    )
    data = document.encode("utf-8")
    filename = hashlib.sha256(data).hexdigest() + ".html"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_bytes(data)
    return filename
