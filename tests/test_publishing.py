import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from botocore.exceptions import ClientError

from commute_podcast.publishing import HostingSettings, publish_feed

SETTINGS = HostingSettings.parse("https://example.com/private", "s3://test-bucket/private")


def prepared_feed(tmp_path):
    media = tmp_path / "media"
    media.mkdir()
    root = ET.Element("rss")
    channel = ET.SubElement(root, "channel")
    names = []
    for audio in [b"first audio", b"second audio"]:
        name = hashlib.sha256(audio).hexdigest() + ".mp3"
        (media / name).write_bytes(audio)
        item = ET.SubElement(channel, "item")
        ET.SubElement(
            item,
            "enclosure",
            {
                "url": SETTINGS.base_url + "/media/" + name,
                "length": str(len(audio)),
            },
        )
        names.append(name)
    ET.ElementTree(root).write(tmp_path / "feed.xml")
    (tmp_path / "catalog.json").write_text("private")
    (media / "unreferenced.mp3").write_bytes(b"old")
    return names


class FakeS3:
    def __init__(self):
        self.objects = {}
        self.uploads = []
        self.fail = False
        self.denied = False

    def head_object(self, *, Bucket, Key):
        if self.denied:
            raise ClientError({"Error": {"Code": "403"}}, "HeadObject")
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        return self.objects[Key]

    def upload_file(self, path, bucket, key, *, ExtraArgs):
        if self.fail:
            raise RuntimeError("sensitive-bucket/private-secret")
        self.uploads.append((key, ExtraArgs))
        self.objects[key] = {
            "ContentLength": Path(path).stat().st_size,
            "ContentType": ExtraArgs["ContentType"],
        }


def test_uploads_only_referenced_audio_then_feed_and_skips_existing(tmp_path):
    names = prepared_feed(tmp_path)
    s3 = FakeS3()
    result = publish_feed(tmp_path, SETTINGS, client=s3)
    assert result["uploaded"] == 2
    assert [key for key, _ in s3.uploads] == [
        *["private/media/" + name for name in names],
        "private/feed.xml",
    ]
    assert s3.uploads[0][1]["ContentType"] == "audio/mpeg"
    assert s3.uploads[-1][1] == {
        "ContentType": "application/rss+xml",
        "CacheControl": "public,max-age=60",
    }
    s3.uploads.clear()
    result = publish_feed(tmp_path, SETTINGS, client=s3)
    assert result["uploaded"] == 0
    assert result["skipped"] == 2
    assert [key for key, _ in s3.uploads] == ["private/feed.xml"]


@pytest.mark.parametrize("denied", [True, False])
def test_upload_failure_never_replaces_feed_and_redacts_details(tmp_path, denied):
    prepared_feed(tmp_path)
    s3 = FakeS3()
    s3.denied = denied
    s3.fail = not denied
    with pytest.raises(RuntimeError, match="S3 publication failed") as error:
        publish_feed(tmp_path, SETTINGS, client=s3)
    assert "private-secret" not in str(error.value)
    assert not s3.uploads


def test_dry_run_never_creates_aws_client(tmp_path, monkeypatch):
    prepared_feed(tmp_path)
    monkeypatch.setattr(
        "commute_podcast.publishing.create_s3_client", lambda: pytest.fail("Network during dry run")
    )
    result = publish_feed(tmp_path, SETTINGS, dry_run=True)
    assert result["media_candidates"] == 2
    assert result["uploaded"] == 0


def test_corrupt_media_blocks_all_uploads(tmp_path):
    names = prepared_feed(tmp_path)
    (tmp_path / "media" / names[-1]).write_bytes(b"bad")
    s3 = FakeS3()
    with pytest.raises(ValueError, match="hash or enclosure"):
        publish_feed(tmp_path, SETTINGS, client=s3)
    assert not s3.uploads


def test_mismatched_remote_audio_is_not_overwritten(tmp_path):
    names = prepared_feed(tmp_path)
    s3 = FakeS3()
    s3.objects["private/media/" + names[0]] = {"ContentLength": 1}
    with pytest.raises(RuntimeError):
        publish_feed(tmp_path, SETTINGS, client=s3)
    assert not s3.uploads


@pytest.mark.parametrize(
    "uri",
    [
        "",
        "s3://test-bucket",
        "https://test-bucket/private",
        "s3://test-bucket/private?token=x",
        "s3://test-bucket/a/../b",
    ],
)
def test_invalid_destination(uri):
    with pytest.raises(ValueError, match="PODCAST_S3_URI"):
        HostingSettings.parse("https://example.com/private", uri)


def add_transcript(tmp_path):
    from commute_podcast.feed_metadata import PODCAST

    data = b"<html>Readable transcript</html>"
    name = hashlib.sha256(data).hexdigest() + ".html"
    (tmp_path / "transcripts").mkdir()
    (tmp_path / "transcripts" / name).write_bytes(data)
    tree = ET.parse(tmp_path / "feed.xml")
    ET.SubElement(
        tree.find("channel/item"),
        f"{{{PODCAST}}}transcript",
        {
            "url": SETTINGS.base_url + "/media/transcripts/" + name,
            "type": "text/html",
        },
    )
    tree.write(tmp_path / "feed.xml")
    return name


def test_transcripts_uploaded_before_feed(tmp_path):
    prepared_feed(tmp_path)
    name = add_transcript(tmp_path)
    s3 = FakeS3()
    result = publish_feed(tmp_path, SETTINGS, client=s3)
    assert result["transcripts_uploaded"] == 1
    assert s3.uploads[-2][0] == "private/media/transcripts/" + name
    assert s3.uploads[-2][1]["ContentType"] == "text/html; charset=utf-8"
    assert s3.uploads[-1][0] == "private/feed.xml"


def test_failed_transcript_upload_preserves_hosted_feed(tmp_path):
    prepared_feed(tmp_path)
    add_transcript(tmp_path)
    s3 = FakeS3()
    original = s3.upload_file

    def upload(path, bucket, key, **kwargs):
        if "/transcripts/" in key:
            raise RuntimeError("Access denied")
        original(path, bucket, key, **kwargs)

    s3.upload_file = upload
    with pytest.raises(RuntimeError, match="S3 publication failed"):
        publish_feed(tmp_path, SETTINGS, client=s3)
    assert all(key != "private/feed.xml" for key, _ in s3.uploads)
