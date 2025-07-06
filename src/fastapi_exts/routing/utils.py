from collections.abc import Callable
from copy import copy
from typing import Annotated, Any, NamedTuple, get_args, get_origin

from fastapi import params
from fastapi.dependencies.utils import get_typed_signature

from fastapi_exts.exceptions import BaseHTTPError
from fastapi_exts.provider import Provider, create_provider_dependency
from fastapi_exts.utils import update_signature


class ParamExtra(NamedTuple):
    exceptions: list[type[BaseHTTPError]]
    provider: Provider | None


def analyze_param(*, annotation: Any, value: Any) -> ParamExtra:
    exceptions: list[type[BaseHTTPError]] = []

    # 提取注解中声明的异常
    if get_origin(annotation) is Annotated:
        annotated_args = get_args(annotation)
        # 获取注解是异常的值
        exceptions = [
            arg
            for arg in annotated_args[1:]
            if type(arg) is type and issubclass(arg, BaseHTTPError)
        ]

    provider = None
    if isinstance(value, Provider):
        provider = copy(value)

    return ParamExtra(exceptions, provider)


def analyze_and_update(fn: Callable[..., Any]) -> list[ParamExtra]:
    """分析并更新函数签名"""

    endpoint_signature = get_typed_signature(fn)
    signature_params = dict(endpoint_signature.parameters.copy())
    result: list[ParamExtra] = []

    for name, param in signature_params.items():
        extra = analyze_param(
            annotation=param.annotation,
            value=param.default,
        )
        result.append(extra)
        if extra.provider is not None:
            dependency = create_provider_dependency(extra.provider)
            signature_params[name] = signature_params[name].replace(
                default=params.Depends(
                    dependency,
                    use_cache=extra.provider.depends.use_cache,
                )
            )

            result.extend(
                # 递归更新并获取依赖签名
                analyze_and_update(extra.provider.dependency)
            )
            continue

    update_signature(fn, parameters=signature_params.values())
    return result
