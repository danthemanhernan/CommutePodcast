import pytest

from commute_podcast.chunking import chunk_script


def test_preserves_paragraph_order() -> None:
    script = "First paragraph has a sentence.\n\nSecond paragraph follows it."
    chunks = chunk_script(script, target=35, maximum=50)
    assert " ".join(" ".join(chunks).split()) == " ".join(script.split())


def test_respects_maximum_for_long_paragraph() -> None:
    script = " ".join(["engineering"] * 100)
    chunks = chunk_script(script, target=80, maximum=100)
    assert chunks
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_rejects_invalid_limits() -> None:
    with pytest.raises(ValueError):
        chunk_script("hello", target=20, maximum=10)

