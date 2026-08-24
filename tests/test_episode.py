from pathlib import Path

import pytest

from commute_podcast.config import load_config
from commute_podcast.episode import generate_episode, slugify
from commute_podcast.job import EpisodeJob, JobStatus


def test_slugify() -> None:
    assert slugify("AI & Data: Episode 1!") == "ai-data-episode-1"


def test_dry_run_writes_manifest(tmp_path: Path) -> None:
    source = Path("podcast.toml").read_text(encoding="utf-8")
    source = source.replace('output_directory = "episodes"', f'output_directory = "{tmp_path}"')
    config_path = tmp_path / "podcast.toml"
    config_path.write_text(source, encoding="utf-8")
    config = load_config(config_path)

    manifest = generate_episode(
        "A short but useful technical podcast script.",
        "Test Episode",
        config,
        provider=None,
        dry_run=True,
    )

    assert manifest["dry_run"] is True
    assert manifest["chunk_count"] == 1
    assert manifest["job"]["status"] == "completed"
    assert manifest["actual_cost_usd"] is None
    assert manifest["estimated_cost_usd"] > 0
    assert manifest["media_metadata"]["title"] == "Test Episode"
    assert (tmp_path / "test-episode" / "manifest.json").exists()


def test_episode_job_allows_forward_progression() -> None:
    job = EpisodeJob(title="Test Episode", slug="test-episode", chunk_count=2)

    job.transition_to(JobStatus.SYNTHESIZING)
    job.transition_to(JobStatus.ASSEMBLING)
    job.transition_to(JobStatus.COMPLETED)

    assert job.as_dict()["status"] == "completed"


def test_episode_job_rejects_invalid_transition() -> None:
    job = EpisodeJob(title="Test Episode", slug="test-episode", chunk_count=2)

    with pytest.raises(ValueError, match="Cannot transition"):
        job.transition_to(JobStatus.ASSEMBLING)
