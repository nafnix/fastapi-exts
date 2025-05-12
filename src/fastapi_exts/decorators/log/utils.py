from collections.abc import Callable
from datetime import UTC, datetime
from typing import ParamSpec, TypeGuard, TypeVar

from fastapi_exts._utils import Is

from .models import (
    LogRecordFailureSummary,
    LogRecordResultSummary,
    LogRecordSuccessSummary,
)


_P = ParamSpec("_P")
_T = TypeVar("_T")


def is_success(
    summary: LogRecordResultSummary,
) -> TypeGuard[LogRecordSuccessSummary]:
    return summary.success


def is_failure(
    summary: LogRecordResultSummary,
) -> TypeGuard[LogRecordFailureSummary]:
    return not summary.success


async def async_execute(
    fn: Callable[_P, _T],
    *args: _P.args,
    **kwds: _P.kwargs,
) -> LogRecordSuccessSummary[_T] | LogRecordFailureSummary:
    start = datetime.now(UTC)

    try:
        result = fn(*args, **kwds)
        if Is.awaitable(result):
            result = await result

        return LogRecordSuccessSummary(
            start=start, result=result, args=args, kwds=kwds
        )
    except Exception as exception:  # noqa: BLE001
        return LogRecordFailureSummary(
            start=start, exception=exception, args=args, kwds=kwds
        )


def sync_execute(
    fn: Callable[_P, _T], *args: _P.args, **kwds: _P.kwargs
) -> LogRecordSuccessSummary[_T] | LogRecordFailureSummary:
    start = datetime.now(UTC)

    try:
        result = fn(*args, **kwds)
        return LogRecordSuccessSummary(
            start=start, result=result, args=args, kwds=kwds
        )
    except Exception as exception:  # noqa: BLE001
        return LogRecordFailureSummary(
            start=start, exception=exception, args=args, kwds=kwds
        )
