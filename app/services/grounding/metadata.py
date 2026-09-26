"""Regex-only document-control metadata extraction."""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date

from app.services.grounding.sources import SourceDocument


METADATA_FIELD_NAMES = (
    "version",
    "approver",
    "owner",
    "document_date",
    "effective_date",
    "review_date",
    "next_review_date",
)

_LABELS = {
    "next_review_date": r"next review(?: date| due)?",
    "review_date": r"(?:last )?review(?:ed)?(?: date| on)?|review date",
    "effective_date": r"effective(?: date| from)?",
    "document_date": r"(?:issue|publication|document|release) date|date of issue|dated?",
    "version": r"(?:document )?version(?: no\.?| number)?|rev(?:ision)?(?: no\.?)?",
    "approver": r"approved by|approver|approval authority",
    "owner": r"(?:document|policy|process) owner|owner",
}
_VERSION = re.compile(r"v?\d+(?:\.\d+){0,3}[a-z]?\Z", re.I)
_MONTHS = {name.lower(): number for number, name in enumerate(calendar.month_name) if name}
_MONTHS.update({name.lower(): number for number, name in enumerate(calendar.month_abbr) if name})


@dataclass(frozen=True)
class MetadataField:
    name: str
    label: str
    value: str
    start: int
    end: int
    iso_date: str | None


@dataclass(frozen=True)
class DocumentMetadata:
    fields: tuple[MetadataField, ...]
    method: str = "regex"


def _without_line_ending(line: str) -> str:
    end = len(line)
    while end and line[end - 1] in "\r\n\v\f\x1c\x1d\x1e\x1f\x85\u2028\u2029":
        end -= 1
    return line[:end]


def _date_iso(value: str) -> str | None:
    raw = value.strip()
    iso = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if iso:
        year, month, day = map(int, iso.groups())
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None

    numeric = re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})", raw)
    if numeric:
        first, second, year = map(int, numeric.groups())
        if first > 12 and second <= 12:
            day, month = first, second
        elif second > 12 and first <= 12:
            month, day = first, second
        elif first <= 12 and second <= 12 and first != second:
            return None
        else:
            day, month = first, second
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None

    named = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})", raw, re.I)
    if named:
        day, month_name, year = named.groups()
        month = _MONTHS.get(month_name.lower())
        if month is None:
            return None
        try:
            return date(int(year), month, int(day)).isoformat()
        except ValueError:
            return None

    named = re.fullmatch(r"([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,\s+(\d{4})", raw, re.I)
    if named:
        month_name, day, year = named.groups()
        month = _MONTHS.get(month_name.lower())
        if month is None:
            return None
        try:
            return date(int(year), month, int(day)).isoformat()
        except ValueError:
            return None
    return None


def _window_lines(text: str) -> list[tuple[int, str]]:
    if len(text) <= 6000:
        windows = [(0, len(text))]
    else:
        windows = [(0, 4000), (len(text) - 2000, len(text))]
    result: list[tuple[int, str]] = []
    for start, end in windows:
        for match in re.finditer(r".*(?:\r\n|\r|\n|\Z)", text[start:end]):
            line = match.group(0)
            if not line:
                continue
            actual_start = start + match.start()
            if actual_start == start and start > 0 and text[start - 1] not in "\r\n\u2028\u2029":
                continue
            result.append((actual_start, line))
    return result


def extract_metadata(source: SourceDocument) -> DocumentMetadata:
    found: dict[str, MetadataField] = {}
    for line_start, line in _window_lines(source.text):
        body = _without_line_ending(line)
        for name in METADATA_FIELD_NAMES:
            if name in found:
                continue
            match = re.match(
                rf"^[ \t]*(?:[|*•-][ \t]*)?(?P<label>{_LABELS[name]})(?:[ \t]*)(?P<separator>[:\-–|])[ \t]*(?P<value>.*)$",
                body,
                re.I,
            )
            if not match:
                continue
            value_text = match.group("value")
            stop = re.search(r"\|| {2,}", value_text)
            if stop:
                value_text = value_text[:stop.start()]
            value_text = value_text[:80]
            trimmed = value_text.strip()
            if not trimmed or (name == "version" and not _VERSION.fullmatch(trimmed)):
                continue
            value_start_in_body = match.start("value") + (len(value_text) - len(value_text.lstrip()))
            value_start = line_start + value_start_in_body
            value_end = value_start + len(trimmed)
            found[name] = MetadataField(
                name=name,
                label=match.group("label"),
                value=source.text[value_start:value_end],
                start=value_start,
                end=value_end,
                iso_date=None if name not in {"document_date", "effective_date", "review_date", "next_review_date"} else _date_iso(trimmed),
            )
    return DocumentMetadata(
        fields=tuple(found[name] for name in METADATA_FIELD_NAMES if name in found)
    )
