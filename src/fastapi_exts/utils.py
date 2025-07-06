import inspect
from collections.abc import Callable, Iterable
from typing import Any

from fastapi_exts._utils import _undefined


def list_parameters(fn: Callable, /) -> list[inspect.Parameter]:
    signature = inspect.signature(fn)
    return list(signature.parameters.values())


def update_signature(
    fn: Callable,
    *,
    parameters: Iterable[inspect.Parameter] | None = _undefined,
    return_annotation: type | None = _undefined,
):
    signature = inspect.signature(fn)

    if parameters != _undefined:
        parameters = list(parameters) if parameters is not None else parameters
        signature = signature.replace(parameters=parameters)

    if return_annotation != _undefined:
        signature = signature.replace(return_annotation=return_annotation)

    setattr(fn, "__signature__", signature)


def inject_parameter(
    fn,
    *,
    name: str,
    default: Any = inspect.Signature.empty,
    annotation: Any = inspect.Signature.empty,
):
    """添加一个关键字参数"""

    signature = inspect.signature(fn)
    parameters: list[inspect.Parameter] = list(signature.parameters.values())
    parameters_len = len(parameters)
    parameter = inspect.Parameter(
        name=name,
        kind=inspect.Parameter.KEYWORD_ONLY,
        default=default,
        annotation=annotation,
    )

    if name in signature.parameters:
        msg = f"Parameter name `{name}` is already used"
        raise ValueError(msg)

    inject_index = 0

    for index, p in enumerate(signature.parameters.values()):
        if p.kind == inspect.Parameter.VAR_KEYWORD:
            inject_index = index
            break

        if index + 1 == parameters_len:
            inject_index = parameters_len

    parameters.insert(inject_index, parameter)

    update_signature(fn, parameters=parameters)

    return inject_index
