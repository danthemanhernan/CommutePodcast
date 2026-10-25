from __future__ import annotations

import os
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from commute_podcast.config import VoiceConfig

if TYPE_CHECKING:
    from openai import OpenAI


class OpenAITTSProvider:
    def __init__(self) -> None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI speech generation")

    @cached_property
    def client(self) -> OpenAI:
        from openai import OpenAI

        # The application owns bounded retries; SDK retries would multiply attempts.
        return OpenAI(max_retries=0)

    def synthesize(self, text: str, destination: Path, config: VoiceConfig) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self.client.audio.speech.with_streaming_response.create(
            model=config.model,
            voice=config.voice,
            input=text,
            instructions=config.instructions,
            response_format=config.format,
        ) as response:
            response.stream_to_file(destination)
