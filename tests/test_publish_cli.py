import json
import sys
from pathlib import Path

import pytest

from commute_podcast import cli


def configure(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["commute-podcast", *args])
    monkeypatch.setenv("PODCAST_BASE_URL", "https://example.com/private")
    monkeypatch.setenv("PODCAST_S3_URI", "s3://test-bucket/private")
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)


@pytest.mark.parametrize("failed", [True, False])
def test_batch_publication_requires_success(monkeypatch, capsys, failed):
    configure(monkeypatch, "generate-all", "--publish", "--finished-directory", "custom-finished")
    monkeypatch.setattr(cli, "OpenAITTSProvider", lambda: object())
    monkeypatch.setattr(
        cli,
        "generate_pending_episodes",
        lambda *a, **k: {
            "failed": [{"error": "failed"}] if failed else [],
            "created": [],
        },
    )
    calls = []
    monkeypatch.setattr(cli, "_publish", lambda *a, **k: calls.append(a) or {"uploaded": 1})
    if failed:
        with pytest.raises(SystemExit) as error:
            cli.main()
        assert error.value.code == 1
        assert not calls
    else:
        cli.main()
        assert calls[0][0] == Path("custom-finished")
    assert "publication" in json.loads(capsys.readouterr().out)


def test_batch_dry_run_never_publishes_or_constructs_provider(monkeypatch, capsys):
    configure(monkeypatch, "generate-all", "--publish", "--dry-run")
    monkeypatch.delenv("PODCAST_S3_URI")
    monkeypatch.setattr(cli, "_publish", lambda *a, **k: pytest.fail("Published in dry run"))
    monkeypatch.setattr(cli, "OpenAITTSProvider", lambda: pytest.fail("Provider in dry run"))
    monkeypatch.setattr(cli, "generate_pending_episodes", lambda *a, **k: {"failed": []})
    cli.main()
    assert json.loads(capsys.readouterr().out)["publication"]["status"] == "skipped_dry_run"


def test_invalid_hosting_fails_before_paid_generation(monkeypatch):
    configure(monkeypatch, "generate-all", "--publish")
    monkeypatch.delenv("PODCAST_S3_URI")
    monkeypatch.setattr(
        cli, "OpenAITTSProvider", lambda: pytest.fail("Paid work before validation")
    )
    with pytest.raises(SystemExit, match="PODCAST_S3_URI"):
        cli.main()


def test_publish_only_never_constructs_provider(monkeypatch, capsys):
    configure(monkeypatch, "publish", "--dry-run")
    monkeypatch.setattr(cli, "OpenAITTSProvider", lambda: pytest.fail("Provider in publish-only"))
    monkeypatch.setattr(cli, "build_feed", lambda *a, **k: None)
    monkeypatch.setattr(cli, "publish_feed", lambda *a, **k: {"dry_run": k["dry_run"]})
    cli.main()
    assert json.loads(capsys.readouterr().out) == {"dry_run": True}
