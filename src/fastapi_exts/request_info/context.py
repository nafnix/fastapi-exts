from contextvars import ContextVar

from .types import RequestInfo


request_info_var = ContextVar[RequestInfo | None](
    "request_info",
    default=None,
)
