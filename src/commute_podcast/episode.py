from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from commute_podcast.audio import combine_audio, validate_audio
from commute_podcast.chunking import chunk_script
from commute_podcast.config import AppConfig
from commute_podcast.job import EpisodeJob, JobStatus
from commute_podcast.observability import log_event
from commute_podcast.providers.base import SpeechProvider
from commute_podcast.retry import retry_transient


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "episode"


def estimate_minutes(text: str, words_per_minute: int = 150) -> float:
    return len(text.split()) / words_per_minute


def apply_pronunciation_replacements(text: str, replacements: dict[str, str]) -> str:
    for source, replacement in replacements.items():
        text = text.replace(source, replacement)
    return text


@dataclass
class EpisodePlan:
    script: str
    title: str
    config: AppConfig
    chunks: list[str]
    job: EpisodeJob
    work_directory: Path
    final_path: Path

    @property
    def part_paths(self) -> list[Path]:
        return [
            self.work_directory / f"part-{index:03d}.{self.config.voice.format}"
            for index in range(1, len(self.chunks) + 1)
        ]


def plan_episode(script: str, title: str, config: AppConfig) -> EpisodePlan:
    speech_script = apply_pronunciation_replacements(
        script, config.generation.pronunciation_replacements
    )
    chunks = chunk_script(
        speech_script,
        target=config.generation.target_chunk_characters,
        maximum=config.generation.max_chunk_characters,
    )
    if not chunks:
        raise ValueError("The script is empty")
    slug = slugify(title)
    work_directory = config.generation.output_directory / slug
    work_directory.mkdir(parents=True, exist_ok=True)
    return EpisodePlan(
        script=script,
        title=title,
        config=config,
        chunks=chunks,
        job=EpisodeJob(title=title, slug=slug, chunk_count=len(chunks)),
        work_directory=work_directory,
        final_path=config.generation.output_directory / f"{slug}.mp3",
    )


def _synthesize_atomically(
    provider: SpeechProvider,
    text: str,
    destination: Path,
    plan: EpisodePlan,
    chunk_number: int,
) -> None:
    temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
    try:
        retry_transient(
            lambda: provider.synthesize(text, temporary, plan.config.voice),
            attempts=plan.config.generation.retry_max_attempts,
            base_delay_seconds=plan.config.generation.retry_base_delay_seconds,
            episode_id=plan.job.slug,
            chunk_id=chunk_number,
        )
        validate_audio(temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def synthesize_episode(
    plan: EpisodePlan, provider: SpeechProvider | None, *, dry_run: bool
) -> None:
    plan.job.transition_to(JobStatus.SYNTHESIZING)
    for index, chunk in enumerate(plan.chunks, start=1):
        text_path = plan.work_directory / f"part-{index:03d}.txt"
        audio_path = plan.part_paths[index - 1]
        text_path.write_text(chunk, encoding="utf-8")
        log_event(
            "chunk_synthesis_started",
            episode_id=plan.job.slug,
            chunk_id=index,
            phase="synthesis",
        )
        if dry_run:
            continue
        if audio_path.exists():
            try:
                validate_audio(audio_path)
                log_event(
                    "chunk_reused",
                    episode_id=plan.job.slug,
                    chunk_id=index,
                    phase="synthesis",
                )
                continue
            except (OSError, ValueError):
                log_event(
                    "chunk_invalidated",
                    episode_id=plan.job.slug,
                    chunk_id=index,
                    phase="synthesis",
                )
        if provider is None:
            raise ValueError("A speech provider is required unless dry_run is enabled")
        _synthesize_atomically(provider, chunk, audio_path, plan, index)
        log_event(
            "chunk_synthesis_completed",
            episode_id=plan.job.slug,
            chunk_id=index,
            phase="synthesis",
        )


def assemble_episode(plan: EpisodePlan, *, dry_run: bool) -> Path:
    plan.job.transition_to(JobStatus.ASSEMBLING)
    assembled_path = plan.work_directory / "episode.mp3"
    log_event("assembly_started", episode_id=plan.job.slug, phase="assembly")
    if not dry_run:
        combine_audio(
            plan.part_paths,
            assembled_path,
            normalize=plan.config.audio.normalize_loudness,
            loudness_lufs=plan.config.audio.integrated_loudness_lufs,
            metadata={
                "title": plan.title,
                "artist": plan.config.show.author,
                "album": plan.config.show.name,
                "album_artist": plan.config.show.author,
                "genre": "Podcast",
                "comment": "Generated by Commute Podcast",
                "date": str(datetime.now(UTC).year),
            },
        )
        validate_audio(assembled_path)
    log_event("assembly_completed", episode_id=plan.job.slug, phase="assembly")
    return assembled_path


def publish_episode(plan: EpisodePlan, assembled_path: Path, *, dry_run: bool) -> float | None:
    if not dry_run:
        shutil.copy2(assembled_path, plan.final_path)
        metadata = validate_audio(plan.final_path)
        duration = float(metadata["format"]["duration"])
    else:
        duration = None
    plan.job.transition_to(JobStatus.COMPLETED)
    log_event("publication_completed", episode_id=plan.job.slug, phase="publication")
    return duration


def _manifest(
    plan: EpisodePlan,
    *,
    dry_run: bool,
    actual_duration_seconds: float | None,
    error: Exception | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "job": plan.job.as_dict(),
        "title": plan.title,
        "show": plan.config.show.name,
        "created_at": datetime.now(UTC).isoformat(),
        "dry_run": dry_run,
        "word_count": len(plan.script.split()),
        "character_count": len(plan.script),
        "estimated_minutes": round(estimate_minutes(plan.script), 1),
        "actual_duration_seconds": actual_duration_seconds,
        "chunk_count": len(plan.chunks),
        "voice": asdict(plan.config.voice),
        "pronunciation_replacements": plan.config.generation.pronunciation_replacements,
        "media_metadata": {
            "title": plan.title,
            "artist": plan.config.show.author,
            "album": plan.config.show.name,
            "album_artist": plan.config.show.author,
            "genre": "Podcast",
        },
        "estimated_cost_usd": round(
            len(plan.script) / 1000 * plan.config.generation.estimated_cost_per_1k_characters_usd,
            6,
        ),
        "actual_cost_usd": None,
        "output": None if dry_run else str(plan.final_path),
    }
    if error is not None:
        result["error"] = {"type": type(error).__name__, "message": str(error)}
    return result


def generate_episode(
    script: str,
    title: str,
    config: AppConfig,
    provider: SpeechProvider | None,
    *,
    dry_run: bool = False,
) -> dict[str, object]:
    plan = plan_episode(script, title, config)
    log_event("planning_completed", episode_id=plan.job.slug, phase="planning")
    if not dry_run and provider is None:
        raise ValueError("A speech provider is required unless dry_run is enabled")
    try:
        synthesize_episode(plan, provider, dry_run=dry_run)
        assembled_path = assemble_episode(plan, dry_run=dry_run)
        actual_duration = publish_episode(plan, assembled_path, dry_run=dry_run)
    except Exception as error:
        if plan.job.status not in {JobStatus.COMPLETED, JobStatus.FAILED}:
            plan.job.transition_to(JobStatus.FAILED)
        log_event("episode_failed", episode_id=plan.job.slug, phase=plan.job.status.value)
        manifest = _manifest(plan, dry_run=dry_run, actual_duration_seconds=None, error=error)
        (plan.work_directory / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        raise

    manifest = _manifest(plan, dry_run=dry_run, actual_duration_seconds=actual_duration)
    (plan.work_directory / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest
