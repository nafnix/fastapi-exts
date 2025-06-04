import inspect
from collections.abc import Callable, Iterable
from typing import Any


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

    setattr(
        fn,
        "__signature__",
        signature.replace(parameters=parameters),
    )
    return inject_index


class _Undefined: ...


def update_signature(
    fn: Callable,
    *,
    parameters: Iterable[inspect.Parameter]
    | None
    | type[_Undefined] = _Undefined,
    return_annotation: type | None = _Undefined,
):
    signature = inspect.signature(fn)
    kwds = {}
    if parameters != _Undefined:
        kwds.setdefault("parameters", parameters)

    if return_annotation != _Undefined:
        kwds.setdefault("return_annotation", return_annotation)

    signature = signature.replace(**kwds)
    setattr(fn, "__signature__", signature)
