import inspect
from collections.abc import (
    Awaitable,
    Callable,
    Coroutine,
    Iterable,
    Mapping,
    Sequence,
)
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from datetime import UTC, datetime
from functools import partial, update_wrapper
from typing import (
    Annotated,
    Any,
    NamedTuple,
    ParamSpec,
    TypeGuard,
    TypeVar,
    get_origin,
    # overload,
    overload,
)


class Datetime:
    @staticmethod
    def to_utc(dt: datetime, /) -> datetime:
        """转成 UTC 时间

        :param dt: 时间
        :return: UTC 时间
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    @staticmethod
    def to_naive(dt: datetime, /) -> datetime:
        """去除时区标识

        :param v: 时间
        :return: 不带时区标识的时间
        """
        return dt.replace(tzinfo=None)

    @classmethod
    def to_utc_naive(cls, dt: datetime, /) -> datetime:
        """将时间转换成不带时区标识的 UTC 时间

        :param v: 时间
        :return: 不带时区标识的 UTC 时间
        """
        return cls.to_naive(cls.to_utc(dt))


# from fastapi.params import Depends
# from pydantic.fields import FieldInfo


_P = ParamSpec("_P")
_T = TypeVar("_T")


class _Undefined:
    def __new__(cls):
        k = "_singleton"
        if not hasattr(cls, k):
            setattr(cls, k, super().__new__(cls))
        return getattr(cls, k)

    @classmethod
    def ne(cls, v):
        return v is not cls()


_undefined = _Undefined()


class Is:
    @staticmethod
    def awaitable(v: _T) -> TypeGuard[Awaitable[_T]]:
        return inspect.isawaitable(v)

    @staticmethod
    def coroutine_function(
        v: Callable[_P, _T],
    ) -> TypeGuard[Callable[_P, Coroutine[Any, Any, _T]]]:
        return inspect.iscoroutinefunction(v)

    @staticmethod
    def annotated(value) -> TypeGuard[Annotated]:
        return get_origin(value) is Annotated

    @staticmethod
    def async_context(value) -> TypeGuard[AbstractAsyncContextManager]:
        return hasattr(value, "__aenter__") and hasattr(value, "__aexit__")

    @staticmethod
    def context(value) -> TypeGuard[AbstractContextManager]:
        return hasattr(value, "__enter__") and hasattr(value, "__exit__")


def add_document(fn: Callable, document: str):
    if fn.__doc__ is None:
        fn.__doc__ = document
    else:
        fn.__doc__ += f"\n\n{document}"


def list_parameters(fn: Callable, /) -> list[inspect.Parameter]:
    signature = inspect.signature(fn)
    return list(signature.parameters.values())


class WithParameterResult(NamedTuple):
    parameters: list[inspect.Parameter]
    parameter: inspect.Parameter
    parameter_index: int


@overload
def with_parameter(
    fn: Callable,
    *,
    name: str,
    annotation: type | Annotated,
) -> WithParameterResult: ...
@overload
def with_parameter(
    fn: Callable,
    *,
    name: str,
    default: Any,
) -> WithParameterResult: ...
@overload
def with_parameter(
    fn: Callable,
    *,
    name: str,
    annotation: type | Annotated,
    default: Any,
) -> WithParameterResult: ...


def with_parameter(
    fn: Callable,
    *,
    name: str,
    annotation: type | Annotated | _Undefined = _undefined,
    default: Any = _undefined,
) -> WithParameterResult:
    kwargs = {}
    if annotation is not _undefined:
        kwargs["annotation"] = annotation
    if default is not _undefined:
        kwargs["default"] = default

    parameters = list_parameters(fn)
    parameter = inspect.Parameter(
        name=name,
        kind=inspect.Parameter.KEYWORD_ONLY,
        **kwargs,
    )
    index = -1
    if parameters and parameters[index].kind == inspect.Parameter.VAR_KEYWORD:
        parameters.insert(index, parameter)
        index = -2
    else:
        parameters.append(parameter)

    return WithParameterResult(parameters, parameter, index)


def add_parameter(
    parameters: list[inspect.Parameter],
    *,
    name: str,
    annotation: type | Annotated | _Undefined = _undefined,
    default: Any = _undefined,
) -> list[inspect.Parameter]:
    parameters = parameters[::]
    kwargs = {}
    if annotation is not _undefined:
        kwargs["annotation"] = annotation
    if default is not _undefined:
        kwargs["default"] = default

    parameter = inspect.Parameter(
        name=name,
        kind=inspect.Parameter.KEYWORD_ONLY,
        **kwargs,
    )
    index = -1
    if parameters and parameters[index].kind == inspect.Parameter.VAR_KEYWORD:
        parameters.insert(index, parameter)
        index = -2
    else:
        parameters.append(parameter)
    return parameters


def update_signature(
    fn: Callable,
    *,
    parameters: Sequence[inspect.Parameter] | None | _Undefined = _undefined,
    return_annotation: type | None | _Undefined = _undefined,
):
    signature = inspect.signature(fn)

    if not isinstance(parameters, _Undefined):
        signature = signature.replace(parameters=parameters)

    if not isinstance(return_annotation, _Undefined):
        signature = signature.replace(return_annotation=return_annotation)

    setattr(fn, "__signature__", signature)


def new_function(
    fn: Callable,
    *,
    parameters: Sequence[inspect.Parameter] | None | _Undefined = _undefined,
    return_annotation: type | None | _Undefined = _undefined,
):
    result = update_wrapper(partial(fn), fn)
    update_signature(
        result,
        parameters=parameters,
        return_annotation=return_annotation,
    )
    return result


def get_annotated_type(value: Annotated) -> type:
    return value.__origin__


def get_annotated_metadata(value: Annotated) -> tuple:
    return value.__metadata__


def _merge_dict(
    target: dict,
    source: Mapping,
):
    """深层合并两个字典

    :param target: 存放合并内容的字典
    :param source: 来源, 因为不会修改, 所以只读映射就可以
    :param exclude_keys: 需要排除的 keys
    """

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
