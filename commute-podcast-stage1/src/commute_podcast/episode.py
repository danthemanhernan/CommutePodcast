from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from commute_podcast.audio import combine_audio
from commute_podcast.chunking import chunk_script
from commute_podcast.config import AppConfig
from commute_podcast.providers.base import SpeechProvider


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "episode"


def estimate_minutes(text: str, words_per_minute: int = 150) -> float:
    return len(text.split()) / words_per_minute


def generate_episode(
    script: str,
    title: str,
    config: AppConfig,
    provider: SpeechProvider | None,
    *,
    dry_run: bool = False,
) -> dict[str, object]:
    chunks = chunk_script(
        script,
        target=config.generation.target_chunk_characters,
        maximum=config.generation.max_chunk_characters,
    )
    if not chunks:
        raise ValueError("The script is empty")

    slug = slugify(title)
    work_directory = config.generation.output_directory / slug
    work_directory.mkdir(parents=True, exist_ok=True)
    final_path = config.generation.output_directory / f"{slug}.mp3"
    part_paths: list[Path] = []

    if not dry_run and provider is None:
        raise ValueError("A speech provider is required unless dry_run is enabled")

    for index, chunk in enumerate(chunks, start=1):
        text_path = work_directory / f"part-{index:03d}.txt"
        audio_path = work_directory / f"part-{index:03d}.{config.voice.format}"
        text_path.write_text(chunk, encoding="utf-8")
        part_paths.append(audio_path)
        if not dry_run and not audio_path.exists():
            assert provider is not None
            provider.synthesize(chunk, audio_path, config.voice)

    if not dry_run:
        combine_audio(
            part_paths,
            work_directory / "episode.mp3",
            normalize=config.audio.normalize_loudness,
            loudness_lufs=config.audio.integrated_loudness_lufs,
        )
        shutil.copy2(work_directory / "episode.mp3", final_path)

    manifest: dict[str, object] = {
        "title": title,
        "show": config.show.name,
        "created_at": datetime.now(UTC).isoformat(),
        "dry_run": dry_run,
        "word_count": len(script.split()),
        "character_count": len(script),
        "estimated_minutes": round(estimate_minutes(script), 1),
        "chunk_count": len(chunks),
        "voice": asdict(config.voice),
        "output": None if dry_run else str(final_path),
    }
    manifest_path = work_directory / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest

