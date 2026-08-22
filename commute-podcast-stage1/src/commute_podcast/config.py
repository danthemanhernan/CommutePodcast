from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ShowConfig:
    name: str
    author: str


@dataclass(frozen=True)
class VoiceConfig:
    provider: str
    model: str
    voice: str
    format: str
    instructions: str


@dataclass(frozen=True)
class GenerationConfig:
    target_chunk_characters: int
    max_chunk_characters: int
    output_directory: Path


@dataclass(frozen=True)
class AudioConfig:
    normalize_loudness: bool
    integrated_loudness_lufs: int


@dataclass(frozen=True)
class AppConfig:
    show: ShowConfig
    voice: VoiceConfig
    generation: GenerationConfig
    audio: AudioConfig


def load_config(path: Path) -> AppConfig:
    with path.open("rb") as config_file:
        raw = tomllib.load(config_file)

    generation = raw["generation"]
    target = int(generation["target_chunk_characters"])
    maximum = int(generation["max_chunk_characters"])
    if target <= 0 or maximum <= 0 or target > maximum:
        raise ValueError("Chunk sizes must be positive and target must not exceed maximum")

    output_directory = Path(generation["output_directory"])
    if not output_directory.is_absolute():
        output_directory = (path.resolve().parent / output_directory).resolve()

    return AppConfig(
        show=ShowConfig(**raw["show"]),
        voice=VoiceConfig(**raw["voice"]),
        generation=GenerationConfig(
            target_chunk_characters=target,
            max_chunk_characters=maximum,
            output_directory=output_directory,
        ),
        audio=AudioConfig(**raw["audio"]),
    )
