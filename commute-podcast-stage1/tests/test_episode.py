from pathlib import Path

from commute_podcast.config import load_config
from commute_podcast.episode import generate_episode, slugify


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
    assert (tmp_path / "test-episode" / "manifest.json").exists()

