from pathlib import Path

from commute_podcast import audio


def test_combine_audio_adds_itunes_metadata(tmp_path: Path, monkeypatch) -> None:
    part = tmp_path / "part.mp3"
    part.write_bytes(b"audio")
    commands: list[list[str]] = []

    monkeypatch.setattr(audio, "require_ffmpeg", lambda: "/usr/bin/ffmpeg")
    monkeypatch.setattr(
        audio.subprocess,
        "run",
        lambda command, check: commands.append(command),
    )

    audio.combine_audio(
        [part],
        tmp_path / "episode.mp3",
        normalize=False,
        loudness_lufs=-16,
        metadata={"title": "Pilot", "artist": "Dan"},
    )

    command = commands[0]
    assert "-id3v2_version" in command
    assert "title=Pilot" in command
    assert "artist=Dan" in command
