from collections.abc import Callable
from typing import Any, NamedTuple, get_args

from fastapi import params
from fastapi.dependencies.utils import get_typed_signature

from fastapi_exts._typing import get_annotated_metadata, is_annotated
from fastapi_exts.utils.responses import ResponseProtocol
from fastapi_exts.utils.signature import update_signature

from .core import Provide


class ParamInfo(NamedTuple):
    responses: list[type[ResponseProtocol]]
    provide: Provide | None
    depends: params.Depends | None


def analyze_param(*, annotation: Any, value: Any) -> ParamInfo:
    # TODO: 还没处理依赖是 annotation 的情况
    responses = (
        [
            arg
            for arg in get_annotated_metadata(annotation)
            if ResponseProtocol.check(arg)
        ]
        if is_annotated(annotation)
        else []
    )

    provider = None
    if isinstance(value, Provide):
        responses.extend(value.responses)
        provider = value

    depends = None
    if isinstance(value, params.Depends):
        depends = value

    return ParamInfo(responses, provider, depends)


def analyze_and_update(fn: Callable[..., Any]) -> list[ParamInfo]:
    """分析并更新函数签名"""

    endpoint_signature = get_typed_signature(fn)
    signature_params = endpoint_signature.parameters.copy()
    result: list[ParamInfo] = []

    for name, param in signature_params.items():
        extra = analyze_param(annotation=param.annotation, value=param.default)
        result.append(extra)
        if extra.provide is not None:
            updated_param = param.replace(default=extra.provide.depends)
            signature_params[name] = updated_param
            fn_ = extra.provide.depends.dependency

            if callable(fn_):
                result.extend(analyze_and_update(fn_))

        elif extra.depends is not None:
            if extra.depends.dependency:
                fn_ = extra.depends.dependency
            elif is_annotated(param.annotation):
                fn_ = get_args(param.annotation)[0]
            else:
                fn_ = param.annotation

            if callable(fn_):
                result.extend(analyze_and_update(fn_))

    update_signature(fn, parameters=signature_params.values())
    return result
