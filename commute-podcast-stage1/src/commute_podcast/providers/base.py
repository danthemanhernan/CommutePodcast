from __future__ import annotations

from pathlib import Path
from typing import Protocol

from commute_podcast.config import VoiceConfig


class SpeechProvider(Protocol):
    def synthesize(self, text: str, destination: Path, config: VoiceConfig) -> None: ...

