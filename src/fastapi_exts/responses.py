from typing import cast

from pydantic import BaseModel

from fastapi_exts.interfaces import (
    HTTPErrorInterface,
    HTTPSchemaErrorInterface,
)


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


def error_responses(
    *errors: type[HTTPErrorInterface | HTTPSchemaErrorInterface[BaseModel]],
):
    result: dict[int, None | dict] = {}

    for e in errors:
        if hasattr(e, "build_schema"):
            e = cast(type[HTTPSchemaErrorInterface[BaseModel]], e)
            schema = e.build_schema()
            current: None | dict
            if (current := result.get(e.status)) and current.get("model"):
                current["model"] = current["model"] | schema
            elif result.get(e.status) is None:
                result[e.status] = {"model": schema}
            else:
                cast(dict, result[e.status]).update({"model": schema})
        else:
            result[e.status] = None

    return result


Response = (
    tuple[int, type[BaseModel]]
    | int
    | type[HTTPErrorInterface | HTTPSchemaErrorInterface]
)


def build_responses(*responses: Response):
    result = {}
    errors: list[type[HTTPErrorInterface]] = []

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
