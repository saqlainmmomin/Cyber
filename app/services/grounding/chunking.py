"""Deterministic line-based chunking with raw-text offsets."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Sequence

from app.config import settings
from app.services.grounding.sources import SourceDocument


_HEADING = re.compile(
    r"^(#{1,6}\s+\S.*|\d+(\.\d+)*[.)]?\s+[A-Z].*|[A-Z][A-Z0-9 &/,()'\-]{3,}:?)$"
)
_SENTENCE_END = re.compile(r"[.!?](?=\s)")


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source_id: str
    ordinal: int
    global_index: int
    start: int
    end: int
    word_count: int
    heading: str | None
    text_sha256: str


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    return len(stripped.split()) <= 12 and bool(_HEADING.fullmatch(stripped))


def _hard_split_line(line: str, start: int, max_words: int) -> list[tuple[int, int]]:
    words = list(re.finditer(r"\S+", line))
    pieces: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(words):
        cutoff = min(cursor + max_words, len(words))
        piece_end = words[cutoff - 1].end()
        if cutoff < len(words):
            final_window = max(1, int(max_words * 0.2))
            lower_word = max(cursor, cutoff - final_window)
            candidates = []
            for match in _SENTENCE_END.finditer(line, words[lower_word].start(), piece_end):
                word_number = sum(1 for word in words[cursor:cutoff] if word.end() <= match.end())
                if lower_word <= cursor + word_number - 1 < cutoff:
                    candidates.append(match)
            if candidates:
                piece_end = candidates[-1].end()
        while piece_end < len(line) and line[piece_end].isspace():
            piece_end += 1
        pieces.append((start, start + piece_end))
        consumed = 0
        for index, word in enumerate(words):
            if word.start() >= piece_end:
                break
            consumed = index + 1
        if consumed <= cursor:
            consumed = cutoff
        cursor = consumed
        start += piece_end
        line = line[piece_end:]
        words = list(re.finditer(r"\S+", line))
        cursor = 0
    return pieces


def _heading_for(text: str, start: int, end: int) -> str | None:
    for line in text[start:end].splitlines(keepends=True):
        if _is_heading(line):
            return line.strip()[:120]
    return None


def chunk_source(source: SourceDocument, *, min_words: int, max_words: int) -> tuple[Chunk, ...]:
    if not source.text.strip():
        return ()
    if min_words < 0 or max_words <= 0:
        raise ValueError("chunk word limits must be non-negative and max_words must be positive")

    lines: list[tuple[int, int, str]] = []
    offset = 0
    for line in source.text.splitlines(keepends=True):
        lines.append((offset, offset + len(line), line))
        offset += len(line)

    ranges: list[tuple[int, int]] = []
    current_start: int | None = None
    current_end = 0
    current_words = 0

    def close_current() -> None:
        nonlocal current_start, current_end, current_words
        if current_start is not None and current_end > current_start:
            ranges.append((current_start, current_end))
        current_start = None
        current_end = 0
        current_words = 0

    for line_start, line_end, line in lines:
        line_words = len(line.split())
        if current_start is not None and _is_heading(line) and current_words >= min_words:
            close_current()
        if line_words > max_words:
            close_current()
            ranges.extend(_hard_split_line(line, line_start, max_words))
            continue
        if current_start is not None and current_words + line_words > max_words:
            close_current()
        if current_start is None:
            current_start = line_start
        current_end = line_end
        current_words += line_words

    close_current()
    if len(ranges) > 1 and len(source.text[ranges[-1][0]:ranges[-1][1]].split()) < 200:
        ranges[-2] = (ranges[-2][0], ranges[-1][1])
        ranges.pop()

    chunks = []
    for ordinal, (start, end) in enumerate(ranges, start=1):
        chunk_text = source.text[start:end]
        chunks.append(
            Chunk(
                chunk_id=f"{source.source_id}#{ordinal}",
                source_id=source.source_id,
                ordinal=ordinal,
                global_index=ordinal,
                start=start,
                end=end,
                word_count=len(chunk_text.split()),
                heading=_heading_for(source.text, start, end),
                text_sha256=hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
            )
        )
    return tuple(chunks)


def chunk_sources(sources: Sequence[SourceDocument]) -> tuple[Chunk, ...]:
    result: list[Chunk] = []
    global_index = 1
    for source in sources:
        for chunk in chunk_source(
            source,
            min_words=settings.v2_chunk_min_words,
            max_words=settings.v2_chunk_max_words,
        ):
            result.append(
                Chunk(
                    chunk_id=chunk.chunk_id,
                    source_id=chunk.source_id,
                    ordinal=chunk.ordinal,
                    global_index=global_index,
                    start=chunk.start,
                    end=chunk.end,
                    word_count=chunk.word_count,
                    heading=chunk.heading,
                    text_sha256=chunk.text_sha256,
                )
            )
            global_index += 1
    return tuple(result)
