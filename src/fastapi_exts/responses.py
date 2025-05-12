from typing import Protocol

from pydantic import BaseModel

from ._utils import merge


class _HTTPErrorInterface(Protocol):
    status: int

    @classmethod
    def response_class(cls) -> type[BaseModel]: ...


def _merge_responses(
    target: dict,
    source: dict,
):
    for status, response in target.items():
        model_class = response.get("model")
        if status in source:
            source_model_class = source[status].get("model")
            if source_model_class and model_class:
                target[status]["model"] = model_class | source_model_class

    for status, response in source.items():
        if status not in target:
            target[status] = response


def error_responses(*errors: type[_HTTPErrorInterface]):
    source = {}

    for e in errors:
        model_class = e.response_class()
        if e.status in source:
            current: type[BaseModel] = source[e.status]["model"]

            source[e.status] = {"model": current | model_class}
        else:
            merge(source, {e.status: {"model": model_class}})
    return source


Response = tuple[int, type[BaseModel]] | int | type[_HTTPErrorInterface]


def build_responses(*responses: Response):
    result = {}
    errors: list[type[_HTTPErrorInterface]] = []

    for arg in responses:
        status = None
        response = {}
        if isinstance(arg, tuple):
            status, response = arg
        elif isinstance(arg, dict):
            for status_, response_ in arg.items():
                result[status_] = {"model": response_}
        elif isinstance(arg, int):
            status = arg
        else:
            errors.append(arg)
            continue

        result[status] = {"model": response}

    _merge_responses(result, error_responses(*errors))
    return result
