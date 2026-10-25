from dataclasses import replace
from pathlib import Path

from commute_podcast.batch import generate_pending_episodes, pending_scripts, title_for_script
from commute_podcast.config import load_config
from commute_podcast.episode import plan_episode


def test_batch_discovers_dated_scripts_and_skips_finished_by_title(tmp_path: Path) -> None:
    source = tmp_path / "content" / "episodes"
    finished = tmp_path / "episodes" / "finished"
    source.mkdir(parents=True)
    finished.mkdir(parents=True)
    (source / "README.md").write_text("ignore", encoding="utf-8")
    (source / "2026-09-08-new-topic.md").write_text("# New Topic\n\nScript", encoding="utf-8")
    (source / "2026-09-07-old-topic.md").write_text("# Old Topic\n\nScript", encoding="utf-8")
    (finished / "old-topic.mp3").write_bytes(b"finished")

    pending, skipped = pending_scripts(source, finished)

    assert pending == [source / "2026-09-08-new-topic.md"]
    assert skipped == [source / "2026-09-07-old-topic.md"]


def test_batch_skips_existing_transcript_filename_output(tmp_path: Path) -> None:
    source = tmp_path / "content" / "episodes"
    finished = tmp_path / "episodes" / "finished"
    source.mkdir(parents=True)
    finished.mkdir(parents=True)
    transcript = source / "2026-09-03-agent-access.md"
    transcript.write_text(
        "# The Engineering Commute — September 3, 2026\n\nScript", encoding="utf-8"
    )
    (finished / "2026-09-03-agent-access.mp3").write_bytes(b"finished")

    pending, skipped = pending_scripts(source, finished)

    assert pending == []
    assert skipped == [transcript]


def test_title_uses_first_h1_or_filename() -> None:
    assert (
        title_for_script(Path("2026-09-08-a-topic.md"), "# A Better Title\nbody")
        == "A Better Title"
    )
    assert title_for_script(Path("2026-09-08-a-topic.md"), "body") == "2026 09 08 A Topic"


def test_batch_generates_pending_and_reports_failures(tmp_path: Path) -> None:
    source = tmp_path / "source"
    finished = tmp_path / "finished"
    source.mkdir()
    (source / "2026-09-08-good.md").write_text("# Good\n\nScript", encoding="utf-8")
    (source / "2026-09-09-bad.md").write_text("# Bad\n\nScript", encoding="utf-8")
    config = load_config(Path("podcast.toml"))
    calls: list[tuple[str, Path]] = []

    def fake_generate(
        script: str, title: str, config, provider, *, dry_run: bool, output_slug: str
    ):
        calls.append((title, config.generation.output_directory))
        if title == "Bad":
            raise RuntimeError("simulated failure")
        return {"title": title}

    result = generate_pending_episodes(
        source, finished, config, None, dry_run=True, generate=fake_generate
    )

    assert result["discovered"] == 2
    assert [entry["manifest"] for entry in result["created"]] == [{"title": "Good"}]
    assert result["failed"] == [
        {
            "script": str(source / "2026-09-09-bad.md"),
            "error": "RuntimeError: simulated failure",
        }
    ]
    assert calls == [("Good", finished.parent), ("Bad", finished.parent)]


def test_batch_plan_keeps_working_files_outside_finished_directory(tmp_path: Path) -> None:
    config = load_config(Path("podcast.toml"))
    finished = tmp_path / "episodes" / "finished"
    batch_config = replace(
        config,
        generation=replace(
            config.generation,
            output_directory=finished.parent,
            finished_directory=finished,
        ),
    )

    plan = plan_episode("A short script.", "A New Episode", batch_config)

    assert plan.work_directory == tmp_path / "episodes" / "a-new-episode"
    assert plan.final_path == finished / "a-new-episode.mp3"


def test_batch_uses_transcript_filename_for_final_mp3(tmp_path: Path) -> None:
    config = load_config(Path("podcast.toml"))
    finished = tmp_path / "episodes" / "finished"
    batch_config = replace(
        config,
        generation=replace(
            config.generation,
            output_directory=finished.parent,
            finished_directory=finished,
        ),
    )

    plan = plan_episode(
        "A short script.",
        "The Engineering Commute — September 8, 2026",
        batch_config,
        output_slug="2026-09-08-jetstream-reconciliation-multicluster",
    )

    assert plan.final_path == finished / "2026-09-08-jetstream-reconciliation-multicluster.mp3"


def test_batch_stops_on_quota_exhaustion_and_defers_remaining(tmp_path):
    from types import SimpleNamespace

    from openai import RateLimitError

    source = tmp_path / "source"
    source.mkdir()
    for name in ["2026-10-01-first.md", "2026-10-02-next.md"]:
        (source / name).write_text("# Episode\nScript")
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise RateLimitError(
            "No credits",
            response=SimpleNamespace(status_code=429, request=None, headers={}),
            body={"error": {"code": "credit_balance_exhausted"}},
        )

    result = generate_pending_episodes(
        source, tmp_path / "finished", load_config(Path("podcast.toml")), None, generate=fail
    )
    assert len(calls) == 1
    assert len(result["failed"]) == 1
    assert result["deferred"] == [str(source / "2026-10-02-next.md")]
