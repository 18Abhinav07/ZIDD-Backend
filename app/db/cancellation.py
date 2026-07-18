"""Cancellation-safe cleanup for database resources."""
import asyncio
from collections.abc import Awaitable
from typing import TypeVar

_T = TypeVar("_T")


async def finish_cleanup(awaitable: Awaitable[_T]) -> _T:
    """Finish cleanup work before propagating any caller cancellation."""
    cleanup_task = asyncio.create_task(awaitable)
    cancellation: asyncio.CancelledError | None = None
    while not cleanup_task.done():
        try:
            await asyncio.shield(cleanup_task)
        except asyncio.CancelledError as exc:
            cancellation = exc
    if cancellation is not None:
        try:
            cleanup_task.result()
        except BaseException:
            pass
        raise cancellation
    return cleanup_task.result()
