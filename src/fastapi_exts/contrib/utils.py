from collections.abc import Callable
from copy import copy
from typing import Any, NamedTuple

from fastapi import params
from fastapi.dependencies.utils import get_typed_signature

from fastapi_exts._typing import (
    get_annotated_metadata,
    is_annotated,
    is_response_info,
)

from .provider import Provider
from .responses import ResponseInfoInterface
from .signature import update_signature


class ParamInfo(NamedTuple):
    responses: list[type[ResponseInfoInterface]]
    provider: Provider | None


def analyze_param(*, annotation: Any, value: Any) -> ParamInfo:
    responses = (
        [
            arg
            for arg in get_annotated_metadata(annotation)
            if is_response_info(arg)
        ]
        if is_annotated(annotation)
        else []
    )

    provider = None
    if isinstance(value, Provider):
        provider = value

    return ParamInfo(responses, provider)


def create_dependency(provider: Provider):
    provider = copy(provider)

    def set_provider_value(value=provider.depends):
        provider.value = value
        return provider

    return set_provider_value


def analyze_and_update(fn: Callable[..., Any]) -> list[ParamInfo]:
    """分析并更新函数签名"""

    endpoint_signature = get_typed_signature(fn)
    signature_params = dict(endpoint_signature.parameters.copy())
    result: list[ParamInfo] = []

    for name, param in signature_params.items():
        extra = analyze_param(annotation=param.annotation, value=param.default)
        result.append(extra)
        if extra.provider is not None:
            dependency = create_dependency(extra.provider)
            signature_params[name] = signature_params[name].replace(
                default=params.Depends(
                    dependency,
                    use_cache=extra.provider.depends.use_cache,
                )
            )

            provider_dep = extra.provider.depends.dependency
            assert provider_dep is not None
            result.extend(analyze_and_update(provider_dep))
            continue

    update_signature(fn, parameters=signature_params.values())
    return result
