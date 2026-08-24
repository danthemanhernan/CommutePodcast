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
    retry_max_attempts: int
    retry_base_delay_seconds: float
    estimated_cost_per_1k_characters_usd: float
    pronunciation_replacements: dict[str, str]


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

    retry_max_attempts = int(generation.get("retry_max_attempts", 3))
    retry_base_delay_seconds = float(generation.get("retry_base_delay_seconds", 1.0))
    estimated_cost = float(generation.get("estimated_cost_per_1k_characters_usd", 0.0))
    if retry_max_attempts <= 0 or retry_base_delay_seconds < 0 or estimated_cost < 0:
        raise ValueError("Retry settings and estimated cost must be non-negative")

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
            retry_max_attempts=retry_max_attempts,
            retry_base_delay_seconds=retry_base_delay_seconds,
            estimated_cost_per_1k_characters_usd=estimated_cost,
            pronunciation_replacements=dict(generation.get("pronunciation_replacements", {})),
        ),
        audio=AudioConfig(**raw["audio"]),
    )
