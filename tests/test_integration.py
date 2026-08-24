import os
from pathlib import Path

import pytest

# from dotenv import load_dotenv
from commute_podcast.config import load_config
from commute_podcast.episode import generate_episode
from commute_podcast.providers import OpenAITTSProvider

# load_dotenv()


@pytest.mark.integration
def test_real_openai_generation_is_opt_in(tmp_path: Path) -> None:
    if os.environ.get("RUN_REAL_API_TESTS") != "1":
        pytest.skip("Set RUN_REAL_API_TESTS=1 to incur a real TTS API cost")

    source = Path("podcast.toml").read_text(encoding="utf-8")
    source = source.replace('output_directory = "episodes"', f'output_directory = "{tmp_path}"')
    config_path = tmp_path / "podcast.toml"
    config_path.write_text(source, encoding="utf-8")
    config = load_config(config_path)
    manifest = generate_episode(
        "This is a short paid integration test.",
        "Paid Integration Test",
        config,
        OpenAITTSProvider(),
    )

    assert manifest["job"]["status"] == "completed"
    assert Path(manifest["output"]).is_file()
