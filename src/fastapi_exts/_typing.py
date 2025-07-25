import inspect
from collections.abc import Awaitable, Callable, Coroutine
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ParamSpec,
    TypeGuard,
    TypeVar,
    get_origin,
)


if TYPE_CHECKING:
    from fastapi_exts.contrib.responses import (
        ResponseInfoInterface,
        ResponseInfoSchemaInterface,
    )

_P = ParamSpec("_P")
_T = TypeVar("_T")


def is_awaitable(v: _T) -> TypeGuard[Awaitable[_T]]:
    return inspect.isawaitable(v)


def is_coroutine_function(
    v: Callable[_P, _T],
) -> TypeGuard[Callable[_P, Coroutine[Any, Any, _T]]]:
    return inspect.iscoroutinefunction(v)


def is_annotated(value) -> TypeGuard[Annotated]:
    return get_origin(value) is Annotated


def is_async_context(value) -> TypeGuard[AbstractAsyncContextManager]:
    return hasattr(value, "__aenter__") and hasattr(value, "__aexit__")


def is_context(value) -> TypeGuard[AbstractContextManager]:
    return hasattr(value, "__enter__") and hasattr(value, "__exit__")


def get_annotated_type(value: Annotated) -> type:
    return get_origin(value)


def get_annotated_metadata(value: Annotated) -> tuple:
    return value.__metadata__


def is_response_info(value) -> TypeGuard[type["ResponseInfoInterface"]]:
    return isinstance(getattr(value, "status", None), int)


def is_response_schema_info(
    value,
) -> TypeGuard[type["ResponseInfoSchemaInterface"]]:
    return is_response_info(value) and callable(
        getattr(value, "get_schema", None)
    )
