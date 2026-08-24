from __future__ import annotations

import re

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def _split_oversized(text: str, maximum: int) -> list[str]:
    sentences = _SENTENCE_BOUNDARY.split(text.strip())
    pieces: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > maximum:
            if current:
                pieces.append(current)
                current = ""
            words = sentence.split()
            word_chunk = ""
            for word in words:
                candidate = f"{word_chunk} {word}".strip()
                if word_chunk and len(candidate) > maximum:
                    pieces.append(word_chunk)
                    word_chunk = word
                else:
                    word_chunk = candidate
            if word_chunk:
                pieces.append(word_chunk)
            continue

        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > maximum:
            pieces.append(current)
            current = sentence
        else:
            current = candidate

    if current:
        pieces.append(current)
    return pieces


def chunk_script(text: str, target: int = 3000, maximum: int = 3800) -> list[str]:
    """Split text on natural boundaries while enforcing a hard character ceiling."""
    if target <= 0 or maximum <= 0 or target > maximum:
        raise ValueError("target and maximum must be positive, with target <= maximum")

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    units: list[str] = []
    for paragraph in paragraphs:
        units.extend(_split_oversized(paragraph, maximum))

    chunks: list[str] = []
    current = ""
    for unit in units:
        separator = "\n\n" if current else ""
        candidate = f"{current}{separator}{unit}"
        if current and len(candidate) > target:
            chunks.append(current)
            current = unit
        else:
            current = candidate
    if current:
        chunks.append(current)

    return chunks

