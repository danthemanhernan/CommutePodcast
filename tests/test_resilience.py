from pathlib import Path

from commute_podcast import episode
from commute_podcast.config import load_config
from commute_podcast.episode import _synthesize_atomically, plan_episode
from commute_podcast.retry import retry_transient


def test_retry_transient_uses_exponential_backoff() -> None:
    attempts = 0
    delays: list[float] = []

    def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("temporary failure")
        return "ok"

    result = retry_transient(
        operation,
        attempts=3,
        base_delay_seconds=1.0,
        episode_id="test-episode",
        chunk_id=1,
        sleep=delays.append,
    )

    assert result == "ok"
    assert attempts == 3
    assert delays == [1.0, 2.0]


def test_synthesis_replaces_destination_atomically(tmp_path: Path, monkeypatch) -> None:
    source = Path("podcast.toml").read_text(encoding="utf-8")
    source = source.replace('output_directory = "episodes"', f'output_directory = "{tmp_path}"')
    config_path = tmp_path / "podcast.toml"
    config_path.write_text(source, encoding="utf-8")
    config = load_config(config_path)
    plan = plan_episode("A short script.", "Atomic Episode", config)

    class FakeProvider:
        def synthesize(self, text, destination, config):
            destination.write_bytes(b"fake audio")

    monkeypatch.setattr(episode, "validate_audio", lambda path: {})
    destination = plan.part_paths[0]
    _synthesize_atomically(FakeProvider(), plan.chunks[0], destination, plan, 1)

    assert destination.read_bytes() == b"fake audio"
    assert not list(destination.parent.glob(".*.tmp"))


def test_pronunciation_replacements_are_applied_before_chunking(tmp_path: Path) -> None:
    source = Path("podcast.toml").read_text(encoding="utf-8")
    source = source.replace('output_directory = "episodes"', f'output_directory = "{tmp_path}"')
    source = source.replace(
        "pronunciation_replacements = {}", 'pronunciation_replacements = { "SQL" = "sequel" }'
    )
    config_path = tmp_path / "podcast.toml"
    config_path.write_text(source, encoding="utf-8")
    config = load_config(config_path)

    plan = plan_episode("We use SQL today.", "Pronunciation Episode", config)

    assert "sequel" in plan.chunks[0]
