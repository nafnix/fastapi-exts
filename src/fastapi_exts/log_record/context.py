from typing import Generic, TypeVar

from ._types import ContextT


class _LogRecordContext(Generic[ContextT]):
    def __init__(self, *args, **kwds) -> None:  # noqa: ARG002
        self.data: ContextT | None = None


class LogRecordContext(
    _LogRecordContext[ContextT],
    Generic[ContextT],
):
    def start(self):
        raise NotImplementedError

    def end(self):
        raise NotImplementedError


LogRecordContextT = TypeVar("LogRecordContextT", bound=LogRecordContext)


class AsyncLogRecordContext(
    _LogRecordContext[ContextT],
    Generic[ContextT],
):
    async def start(self):
        raise NotImplementedError

    async def end(self):
        raise NotImplementedError


AsyncLogRecordContextT = TypeVar(
    "AsyncLogRecordContextT", bound=AsyncLogRecordContext
)

AnyLogRecordContextT = TypeVar(
    "AnyLogRecordContextT",
    bound=LogRecordContext | AsyncLogRecordContext,
)
