from contextlib import AsyncContextDecorator, ContextDecorator
from types import TracebackType
from typing import Generic, TypeVar

from ._types import ContextT


class LogRecordContext(ContextDecorator, Generic[ContextT]):
    def __init__(self) -> None:
        self.info: ContextT | None = None

    def __enter__(self):
        self.info: ContextT | None = None
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        self.info: ContextT | None = None
        return None


LogRecordContextT = TypeVar("LogRecordContextT", bound=LogRecordContext)


class AsyncLogRecordContext(AsyncContextDecorator, Generic[ContextT]):
    def __init__(self) -> None:
        self.info: ContextT | None = None

    async def __aenter__(self):
        self.info: ContextT | None = None
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        self.info: ContextT | None = None
        return None


AsyncLogRecordContextT = TypeVar(
    "AsyncLogRecordContextT", bound=AsyncLogRecordContext
)

AnyLogRecordContextT = TypeVar(
    "AnyLogRecordContextT",
    bound=LogRecordContext | AsyncLogRecordContext,
)
