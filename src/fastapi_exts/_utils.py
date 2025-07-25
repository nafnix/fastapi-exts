import inspect
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import UTC, datetime
from functools import partial, update_wrapper
from typing import Any, cast, overload


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


def _merge_dict(
    target: dict,
    source: Mapping,
):
    for ok, ov in source.items():
        v = target.get(ok)
        # 如果两边都是映射类型, 就可以合并
        if isinstance(v, dict) and isinstance(ov, Mapping):
            _merge_dict(v, ov)
        elif isinstance(v, list) and isinstance(ov, Iterable):
            _merge_list(v, ov)
        # 如果当前值允许进行相加的操作
        # 并且不是字符串和数字
        # 并且旧字典与当前值类型相同
        elif (
            hasattr(v, "__add__")
            and not isinstance(v, str | int)
            and type(v) is type(ov)
        ):
            target[ok] = v + ov
        # 否则使用有效的值
        else:
            target[ok] = v or ov


def _merge_list(target: list, source: Iterable):
    for oi, ov in enumerate(source):
        try:
            v = target[oi]
        except IndexError:
            target[oi] = ov
            break

        if isinstance(v, dict) and isinstance(ov, Mapping):
            merge(v, ov)

        elif isinstance(v, list) and isinstance(ov, Iterable):
            _merge_list(v, ov)
        # 如果当前值允许进行相加的操作
        # 并且不是字符串和数字
        # 并且旧字典与当前值类型相同
        elif (
            hasattr(v, "__add__")
            and not isinstance(v, str | int)
            and type(v) is type(ov)
        ):
            target[oi] = v + ov
        else:
            target[oi] = v or ov


@overload
def merge(target: list, source: Iterable): ...
@overload
def merge(target: dict, source: Mapping): ...


def merge(target, source):
    for ok, ov in source.items():
        v = target.get(ok)

        # 如果两边都是映射类型, 就可以合并
        if isinstance(v, dict) and isinstance(ov, Mapping):
            _merge_dict(v, ov)

        # 如果当前值允许进行相加的操作
        # 并且不是字符串和数字
        # 并且旧字典与当前值类型相同
        elif (
            hasattr(v, "__add__")
            and not isinstance(v, str | int)
            and type(v) is type(ov)
        ):
            target[ok] = v + ov

        # 否则使用有效的值
        else:
            target[ok] = v or ov


def naive_datetime(dt: datetime):
    return dt.replace(tzinfo=None)


def utc_datetime(dt: datetime):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
