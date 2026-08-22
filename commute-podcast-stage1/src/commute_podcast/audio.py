from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def require_ffmpeg() -> str:
    executable = shutil.which("ffmpeg")
    if not executable:
        raise RuntimeError("ffmpeg is required but was not found on PATH")
    return executable


def combine_audio(
    parts: list[Path],
    destination: Path,
    *,
    normalize: bool,
    loudness_lufs: int,
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
    command.extend(["-codec:a", "libmp3lame", "-b:a", "160k", str(destination)])
    subprocess.run(command, check=True)

