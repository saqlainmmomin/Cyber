"""Small bounded-concurrency helpers used by framework-scoped LLM work."""

from __future__ import annotations

from contextvars import copy_context
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Iterable


def _run_item(fn: Callable[[Any], Any], item: Any) -> tuple[Any, BaseException | None]:
    try:
        return fn(item), None
    except BaseException as exc:
        return None, exc


def _run_in_context(
    context, fn: Callable[[Any], Any], item: Any
) -> tuple[Any, BaseException | None]:
    return context.run(_run_item, fn, item)


def run_bounded(
    fn: Callable[[Any], Any],
    items: Iterable[Any],
    *,
    max_workers: int,
) -> list[tuple[Any, BaseException | None]]:
    """Run one function per item, returning results and errors in input order."""
    items = list(items)
    if max_workers <= 1 or len(items) <= 1:
        return [_run_item(fn, item) for item in items]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_run_in_context, copy_context(), fn, item)
            for item in items
        ]
        return [future.result() for future in futures]
