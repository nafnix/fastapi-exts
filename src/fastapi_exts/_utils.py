import inspect
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from functools import partial, update_wrapper
from typing import Any, cast


class _Undefined: ...


_undefined = cast(Any, _Undefined)


def update_signature(
    fn: Callable,
    *,
    parameters: Sequence[inspect.Parameter] | None = _undefined,
    return_annotation: type | None = _undefined,
):
    signature = inspect.signature(fn)

    if parameters != _undefined:
        signature = signature.replace(parameters=parameters)

    if return_annotation != _undefined:
        signature = signature.replace(return_annotation=return_annotation)

    setattr(fn, "__signature__", signature)


def new_function(
    fn: Callable,
    *,
    parameters: Sequence[inspect.Parameter] | None = _undefined,
    return_annotation: type | None = _undefined,
):
    result = update_wrapper(partial(fn), fn)
    update_signature(
        result,
        parameters=parameters,
        return_annotation=return_annotation,
    )
    return result


def naive_datetime(dt: datetime):
    return dt.replace(tzinfo=None)


def utc_datetime(dt: datetime):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
