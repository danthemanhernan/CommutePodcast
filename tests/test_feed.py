import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from commute_podcast.config import ShowConfig
from commute_podcast.feed import ITUNES, build_feed


def test_feed_is_stable_and_escapes_metadata(tmp_path, monkeypatch):
    source = tmp_path / "finished"
    source.mkdir()
    audio = source / "example.mp3"
    audio.write_bytes(b"audio")
    monkeypatch.setattr(
        "commute_podcast.feed.validate_audio",
        lambda _: {
            "format": {"duration": "12.5", "tags": {"title": "R&D <systems>"}},
        },
    )
    output = tmp_path / "feed"
    kwargs = dict(base_url="https://example.com/private", description="Learn & apply")
    assert build_feed(source, output, ShowConfig("Show", "Dan"), **kwargs) == 1
    first = (output / "feed.xml").read_bytes()
    root = ET.fromstring(first)
    assert root.findtext("channel/item/title") == "R&D <systems>"
    assert root.findtext(f"channel/{{{ITUNES}}}block") == "Yes"
    enclosure = root.find("channel/item/enclosure")
    assert enclosure.attrib["length"] == "5"
    assert enclosure.attrib["type"] == "audio/mpeg"
    assert len(list((output / "media").glob("*.mp3"))) == 1
    audio.touch()
    build_feed(source, output, ShowConfig("Show", "Dan"), **kwargs)
    assert (output / "feed.xml").read_bytes() == first
    audio.write_bytes(b"updated audio")
    build_feed(source, output, ShowConfig("Show", "Dan"), **kwargs)
    updated = ET.parse(output / "feed.xml")
    assert updated.findtext("channel/item/guid") == root.findtext("channel/item/guid")
    assert updated.find("channel/item/enclosure").attrib["url"] != enclosure.attrib["url"]


def test_invalid_audio_preserves_previous_feed(tmp_path, monkeypatch):
    source = tmp_path / "finished"
    source.mkdir()
    (source / "bad.mp3").write_bytes(b"invalid")
    output = tmp_path / "feed"
    output.mkdir()
    (output / "feed.xml").write_text("previous")

    def reject(path: Path):
        raise ValueError("Invalid audio")

    monkeypatch.setattr("commute_podcast.feed.validate_audio", reject)
    with pytest.raises(ValueError, match="Invalid audio"):
        build_feed(
            source,
            output,
            ShowConfig("Show", "Dan"),
            base_url="https://example.com",
            description="Learning",
        )
    assert (output / "feed.xml").read_text() == "previous"


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://u:p@example.com",
        "https://example.com?secret=token",
        "https://example.com/#x",
    ],
)
def test_rejects_unsafe_urls(tmp_path, url):
    with pytest.raises(ValueError, match="HTTPS"):
        build_feed(
            tmp_path,
            tmp_path / "feed",
            ShowConfig("Show", "Dan"),
            base_url=url,
            description="Learning",
        )


def test_dates_migrate_without_changing_identity_and_transcripts_escape_html(tmp_path, monkeypatch):
    import json
    from email.utils import parsedate_to_datetime

    from commute_podcast.feed_metadata import PODCAST

    source = tmp_path / "finished"
    source.mkdir()
    output = tmp_path / "feed"
    output.mkdir()
    names = ["2026-09-02-later", "2026-08-26-earlier"]
    for name in names:
        (source / (name + ".mp3")).write_bytes(name.encode())
        work = tmp_path / name
        work.mkdir()
        (work / "part-001.txt").write_text("Narration <script>alert('bad')</script> & details")
    (output / "catalog.json").write_text(
        json.dumps(
            {
                name + ".mp3": {"guid": name, "published": "2026-10-25T12:00:00+00:00"}
                for name in names
            }
        )
    )
    monkeypatch.setattr(
        "commute_podcast.feed.validate_audio",
        lambda _: {
            "format": {"duration": "12"},
        },
    )
    build_feed(
        source,
        output,
        ShowConfig("Show", "Dan"),
        base_url="https://example.com/private",
        description="Learn",
    )
    items = ET.parse(output / "feed.xml").findall("channel/item")
    assert [item.findtext("guid") for item in items] == names
    assert [
        parsedate_to_datetime(item.findtext("pubDate")).date().isoformat() for item in items
    ] == ["2026-09-02", "2026-08-26"]
    tag = items[0].find(f"{{{PODCAST}}}transcript")
    assert tag.get("type") == "text/html"
    assert "Read the transcript" in items[0].findtext("description")
    text = (output / "transcripts" / tag.get("url").rsplit("/", 1)[1]).read_text()
    assert "&lt;script&gt;" in text
    assert "<script>" not in text
    assert "&amp; details" in text


def test_legacy_dates_and_explicit_transcript_sidecar(tmp_path):
    from commute_podcast.feed_metadata import episode_date, narration_script

    dated = episode_date(Path("the-engineering-commute-august-25-2026.mp3"), "Unknown")
    assert dated.date().isoformat() == "2026-08-25"
    assert episode_date(Path("undated.mp3"), "October 2, 2026").day == 2
    assert episode_date(Path("undated.mp3"), "Pilot") is None
    audio = tmp_path / "imported.mp3"
    audio.with_suffix(".transcript.txt").write_text("Known source script")
    assert narration_script(audio) == "Known source script"
