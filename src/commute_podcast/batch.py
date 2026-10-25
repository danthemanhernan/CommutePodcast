from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from commute_podcast.config import AppConfig
from commute_podcast.episode import generate_episode, slugify
from commute_podcast.providers.base import SpeechProvider
from commute_podcast.retry import is_quota_exhausted

DATE_NAMED_SCRIPT = re.compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")
MARKDOWN_TITLE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def discover_scripts(source_directory: Path) -> list[Path]:
    """Return dated, top-level transcript files in stable filename order."""
    return sorted(
        path
        for path in source_directory.iterdir()
        if path.is_file() and DATE_NAMED_SCRIPT.match(path.name)
    )


def title_for_script(script_path: Path, script: str) -> str:
    """Use a Markdown H1 when present, otherwise derive a title from the filename."""
    match = MARKDOWN_TITLE.search(script)
    if match:
        return match.group(1).strip()
    return script_path.stem.replace("-", " ").title()


def finished_paths(script_path: Path, title: str, finished_directory: Path) -> tuple[Path, ...]:
    """Return supported output names, including the transcript filename convention."""
    return (
        finished_directory / f"{script_path.stem}.mp3",
        finished_directory / f"{slugify(title)}.mp3",
    )


def pending_scripts(
    source_directory: Path, finished_directory: Path
) -> tuple[list[Path], list[Path]]:
    """Return (pending, skipped) based on the published MP3's slug."""
    pending: list[Path] = []
    skipped: list[Path] = []
    for script_path in discover_scripts(source_directory):
        script = script_path.read_text(encoding="utf-8").strip()
        title = title_for_script(script_path, script)
        if any(path.is_file() for path in finished_paths(script_path, title, finished_directory)):
            skipped.append(script_path)
        else:
            pending.append(script_path)
    return pending, skipped


def generate_pending_episodes(
    source_directory: Path,
    finished_directory: Path,
    config: AppConfig,
    provider: SpeechProvider | None,
    *,
    dry_run: bool = False,
    generate: Callable[..., dict[str, object]] = generate_episode,
) -> dict[str, object]:
    """Generate every uncreated dated transcript and return a JSON-safe summary."""
    source_directory = source_directory.resolve()
    finished_directory = finished_directory.resolve()
    finished_directory.mkdir(parents=True, exist_ok=True)
    pending, skipped = pending_scripts(source_directory, finished_directory)
    batch_config = replace(
        config,
        generation=replace(
            config.generation,
            output_directory=finished_directory.parent,
            finished_directory=finished_directory,
        ),
    )
    created: list[dict[str, object]] = []
    failed: list[dict[str, str]] = []
    deferred: list[str] = []
    for index, script_path in enumerate(pending):
        try:
            script = script_path.read_text(encoding="utf-8").strip()
            if not script:
                raise ValueError("Script cannot be empty")
            result = generate(
                script,
                title_for_script(script_path, script),
                batch_config,
                provider,
                dry_run=dry_run,
                output_slug=script_path.stem,
            )
            created.append({"script": str(script_path), "manifest": result})
        except Exception as error:  # batch work should report all failures in one run
            failed.append({"script": str(script_path), "error": f"{type(error).__name__}: {error}"})
            if is_quota_exhausted(error):
                deferred = [str(path) for path in pending[index + 1 :]]
                break
    return {
        "deferred": deferred,
        "source_directory": str(source_directory),
        "finished_directory": str(finished_directory),
        "dry_run": dry_run,
        "discovered": len(pending) + len(skipped),
        "created": created,
        "skipped": [str(path) for path in skipped],
        "failed": failed,
    }
