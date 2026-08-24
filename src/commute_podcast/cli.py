from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from commute_podcast.audio import validate_audio
from commute_podcast.chunking import chunk_script
from commute_podcast.config import load_config
from commute_podcast.episode import estimate_minutes, generate_episode
from commute_podcast.observability import configure_logging
from commute_podcast.providers import OpenAITTSProvider


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="commute-podcast")
    parser.add_argument("--config", type=Path, default=Path("podcast.toml"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Inspect generation without creating files")
    plan.add_argument("script", type=Path)

    generate = subparsers.add_parser("generate", help="Create an MP3 episode")
    generate.add_argument("script", type=Path)
    generate.add_argument("--title")
    generate.add_argument("--dry-run", action="store_true")

    validate = subparsers.add_parser("validate", help="Validate a generated MP3 with ffprobe")
    validate.add_argument("audio", type=Path)
    return parser


def main() -> None:
    load_dotenv()
    configure_logging()
    args = _parser().parse_args()
    if args.command == "validate":
        print(json.dumps(validate_audio(args.audio), indent=2))
        return
    config = load_config(args.config)
    script = args.script.read_text(encoding="utf-8").strip()
    if not script:
        raise SystemExit("Script cannot be empty")

    if args.command == "plan":
        chunks = chunk_script(
            script,
            target=config.generation.target_chunk_characters,
            maximum=config.generation.max_chunk_characters,
        )
        result = {
            "script": str(args.script),
            "words": len(script.split()),
            "characters": len(script),
            "estimated_minutes": round(estimate_minutes(script), 1),
            "chunks": len(chunks),
            "chunk_characters": [len(chunk) for chunk in chunks],
            "provider": config.voice.provider,
            "model": config.voice.model,
            "voice": config.voice.voice,
        }
    else:
        title = args.title or args.script.stem.replace("-", " ").title()
        provider = None if args.dry_run else OpenAITTSProvider()
        result = generate_episode(
            script,
            title,
            config,
            provider,
            dry_run=args.dry_run,
        )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
