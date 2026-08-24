from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def require_ffmpeg() -> str:
    executable = shutil.which("ffmpeg")
    if not executable:
        raise RuntimeError("ffmpeg is required but was not found on PATH")
    return executable


def require_ffprobe() -> str:
    executable = shutil.which("ffprobe")
    if not executable:
        raise RuntimeError("ffprobe is required but was not found on PATH")
    return executable


def validate_audio(path: Path) -> dict[str, object]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Audio file is missing or empty: {path}")
    result = subprocess.run(
        [
            require_ffprobe(),
            "-v",
            "error",
            "-show_entries",
            "format=format_name,duration,size:stream=codec_name,codec_type,sample_rate,channels,bit_rate",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    metadata = json.loads(result.stdout)
    if metadata.get("format", {}).get("format_name") != "mp3":
        raise ValueError(f"Audio file is not an MP3: {path}")
    if not any(stream.get("codec_type") == "audio" for stream in metadata.get("streams", [])):
        raise ValueError(f"Audio file has no audio stream: {path}")
    return metadata


def combine_audio(
    parts: list[Path],
    destination: Path,
    *,
    normalize: bool,
    loudness_lufs: int,
    metadata: dict[str, str] | None = None,
) -> None:
    if not parts:
        raise ValueError("At least one audio part is required")
    ffmpeg = require_ffmpeg()
    destination.parent.mkdir(parents=True, exist_ok=True)
    concat_file = destination.parent / "concat.txt"
    concat_file.write_text(
        "".join(f"file '{part.resolve().as_posix()}'\n" for part in parts),
        encoding="utf-8",
    )

    command = [ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat_file)]
    if normalize:
        command.extend(["-af", f"loudnorm=I={loudness_lufs}:TP=-1.5:LRA=11"])
    command.extend(["-codec:a", "libmp3lame", "-b:a", "160k", "-id3v2_version", "3"])
    for key, value in (metadata or {}).items():
        command.extend(["-metadata", f"{key}={value}"])
    command.append(str(destination))
    subprocess.run(command, check=True)
