from __future__ import annotations

import os
from pathlib import Path

from commute_podcast.config import VoiceConfig


class OpenAITTSProvider:
    def __init__(self) -> None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI speech generation")

    def synthesize(self, text: str, destination: Path, config: VoiceConfig) -> None:
        from openai import OpenAI

        client = OpenAI()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with client.audio.speech.with_streaming_response.create(
            model=config.model,
            voice=config.voice,
            input=text,
            instructions=config.instructions,
            response_format=config.format,
        ) as response:
            response.stream_to_file(destination)

