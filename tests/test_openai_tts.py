from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import openai

from commute_podcast.config import load_config
from commute_podcast.providers.openai_tts import OpenAITTSProvider


def test_provider_reuses_client_and_disables_nested_retries(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    constructed = []
    requests = []

    @contextmanager
    def create(**kwargs):
        requests.append(kwargs)
        yield SimpleNamespace(stream_to_file=lambda path: path.write_bytes(b"audio"))

    def client(**kwargs):
        constructed.append(kwargs)
        return SimpleNamespace(
            audio=SimpleNamespace(
                speech=SimpleNamespace(with_streaming_response=SimpleNamespace(create=create))
            )
        )

    monkeypatch.setattr(openai, "OpenAI", client)
    provider = OpenAITTSProvider()
    config = load_config(Path("podcast.toml")).voice
    provider.synthesize("First", tmp_path / "one.mp3", config)
    provider.synthesize("Second", tmp_path / "two.mp3", config)
    assert constructed == [{"max_retries": 0}]
    assert [request["input"] for request in requests] == ["First", "Second"]
    assert requests[0]["model"] == config.model
    assert (tmp_path / "two.mp3").read_bytes() == b"audio"
