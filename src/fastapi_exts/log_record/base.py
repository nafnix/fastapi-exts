from typing import Generic

from ._types import ContextT, EndpointT, ExceptionT, P, T
from .context import AsyncLogRecordContext, LogRecordContext
from .interfaces import AbstractAsyncLogRecord, AbstractLogRecord
from .models import (
    LogRecordFailureDetail,
    LogRecordFailureSummary,
    LogRecordSuccessDetail,
    LogRecordSuccessSummary,
)


class LogRecord(
    AbstractLogRecord[
        LogRecordSuccessDetail[T, ContextT | None, EndpointT],
        LogRecordFailureDetail[ExceptionT, ContextT | None, EndpointT],
        P,
        T,
        ExceptionT,
        LogRecordContext[ContextT],
        ContextT,
        EndpointT,
    ],
    Generic[P, T, ExceptionT, ContextT, EndpointT],
):
    def get_success_detail(
        self,
        *,
        summary: LogRecordSuccessSummary[T],
        context: ContextT | None,
        message: str,
        endpoint: EndpointT,
        extra,
    ) -> LogRecordSuccessDetail[T, ContextT | None, EndpointT]:
        return LogRecordSuccessDetail(
            message=message,
            context=context,
            result=summary.result,
            args=summary.args,
            kwds=summary.kwds,
            start=summary.start,
            endpoint=endpoint,
            extra=extra,
        )

    def get_failure_detail(
        self,
        *,
        summary: LogRecordFailureSummary[ExceptionT],
        context: ContextT | None,
        message: str,
        endpoint: EndpointT,
        extra,
    ) -> LogRecordFailureDetail[ExceptionT, ContextT | None, EndpointT]:
        return LogRecordFailureDetail(
            message=message,
            context=context,
            exception=summary.exception,
            args=summary.args,
            kwds=summary.kwds,
            start=summary.start,
            endpoint=endpoint,
            extra=extra,
        )


class AsyncLogRecord(
    AbstractAsyncLogRecord[
        LogRecordSuccessDetail[T, ContextT | None, EndpointT],
        LogRecordFailureDetail[ExceptionT, ContextT | None, EndpointT],
        P,
        T,
        ExceptionT,
        AsyncLogRecordContext[ContextT],
        ContextT,
        EndpointT,
    ],
    Generic[P, T, ExceptionT, ContextT, EndpointT],
):
    async def get_success_detail(
        self,
        *,
        summary: LogRecordSuccessSummary[T],
        context: ContextT | None,
        message: str,
        endpoint: EndpointT,
        extra,
    ) -> LogRecordSuccessDetail[T, ContextT | None, EndpointT]:
        return LogRecordSuccessDetail(
            message=message,
            context=context,
            result=summary.result,
            args=summary.args,
            kwds=summary.kwds,
            start=summary.start,
            endpoint=endpoint,
            extra=extra,
        )

    async def get_failure_detail(
        self,
        *,
        summary: LogRecordFailureSummary[ExceptionT],
        context: ContextT | None,
        message: str,
        endpoint: EndpointT,
        extra,
    ) -> LogRecordFailureDetail[ExceptionT, ContextT | None, EndpointT]:
        return LogRecordFailureDetail(
            message=message,
            context=context,
            exception=summary.exception,
            args=summary.args,
            kwds=summary.kwds,
            start=summary.start,
            endpoint=endpoint,
            extra=extra,
        )
