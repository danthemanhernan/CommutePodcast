from pathlib import Path

from commute_podcast.config import load_config


def test_loads_default_config() -> None:
    config = load_config(Path("podcast.toml"))
    assert config.voice.model == "gpt-4o-mini-tts"
    assert config.voice.voice == "cedar"
    assert config.generation.output_directory.is_absolute()

