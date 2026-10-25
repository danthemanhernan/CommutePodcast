from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from commute_podcast.audio import validate_audio
from commute_podcast.batch import generate_pending_episodes
from commute_podcast.chunking import chunk_script
from commute_podcast.config import ShowConfig, load_config
from commute_podcast.episode import estimate_minutes, generate_episode
from commute_podcast.feed import build_feed
from commute_podcast.observability import configure_logging
from commute_podcast.providers import OpenAITTSProvider
from commute_podcast.publishing import HostingSettings, publish_feed


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

    batch = subparsers.add_parser(
        "generate-all", help="Create every dated transcript not already in the finished folder"
    )
    batch.add_argument("--source-directory", type=Path, default=Path("content/episodes"))
    batch.add_argument("--finished-directory", type=Path, default=Path("episodes/finished"))
    batch.add_argument("--dry-run", action="store_true")
    batch.add_argument(
        "--publish", action="store_true", help="Publish to S3 after a successful batch"
    )
    batch.add_argument("--feed-directory", type=Path, default=Path("episodes/podcast-feed"))

    publish = subparsers.add_parser("publish", help="Build and publish existing finished episodes")
    publish.add_argument("--source-directory", type=Path, default=Path("episodes/finished"))
    publish.add_argument("--feed-directory", type=Path, default=Path("episodes/podcast-feed"))
    publish.add_argument("--dry-run", action="store_true")

    feed = subparsers.add_parser("build-feed", help="Prepare existing MP3s for Apple Podcasts")
    feed.add_argument("--source-directory", type=Path, default=Path("episodes/finished"))
    feed.add_argument("--output-directory", type=Path, default=Path("episodes/podcast-feed"))
    feed.add_argument("--description", default="Technical learning for your commute.")

    validate = subparsers.add_parser("validate", help="Validate a generated MP3 with ffprobe")
    validate.add_argument("audio", type=Path)
    return parser


def _hosting_settings() -> HostingSettings:
    try:
        return HostingSettings.parse(
            os.environ.get("PODCAST_BASE_URL", ""), os.environ.get("PODCAST_S3_URI", "")
        )
    except ValueError as error:
        raise SystemExit(str(error)) from None


def _publish(
    source: Path, directory: Path, show: ShowConfig, settings: HostingSettings, *, dry_run: bool
) -> dict:
    try:
        build_feed(
            source,
            directory,
            show,
            base_url=settings.base_url,
            description="Technical learning for your commute.",
        )
        return publish_feed(directory, settings, dry_run=dry_run)
    except (ValueError, RuntimeError, OSError) as error:
        raise SystemExit(str(error)) from None


def main() -> None:
    load_dotenv()
    configure_logging()
    args = _parser().parse_args()
    if args.command == "validate":
        print(json.dumps(validate_audio(args.audio), indent=2))
        return
    config = load_config(args.config)
    if args.command == "publish":
        result = _publish(
            args.source_directory,
            args.feed_directory,
            config.show,
            _hosting_settings(),
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2))
        return
    if args.command == "build-feed":
        base_url = os.environ.get("PODCAST_BASE_URL")
        if not base_url:
            raise SystemExit("Set PODCAST_BASE_URL to the HTTPS directory hosting your feed")
        count = build_feed(
            args.source_directory,
            args.output_directory,
            config.show,
            base_url=base_url,
            description=args.description,
        )
        # The base URL may contain a subscriber token: never print it.
        print(json.dumps({"episodes": count, "output_directory": str(args.output_directory)}))
        return
    if args.command == "generate-all":
        # Catch configuration errors before starting paid speech requests.
        hosting = _hosting_settings() if args.publish and not args.dry_run else None
        provider = None if args.dry_run else OpenAITTSProvider()
        result = generate_pending_episodes(
            args.source_directory,
            args.finished_directory,
            config,
            provider,
            dry_run=args.dry_run,
        )
        if args.publish:
            if args.dry_run:
                result["publication"] = {"status": "skipped_dry_run"}
            elif not result["failed"] and hosting is not None:
                result["publication"] = _publish(
                    args.finished_directory,
                    args.feed_directory,
                    config.show,
                    hosting,
                    dry_run=False,
                )
            else:
                result["publication"] = {"status": "skipped_generation_failed"}
        print(json.dumps(result, indent=2))
        if result["failed"]:
            raise SystemExit(1)
        return

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
