from typing import Protocol, TypeVar, cast

from pydantic import BaseModel


BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


class ResponseProtocol(Protocol):
    status: int


class ResponseDataProtocol(
    ResponseProtocol,
    Protocol[BaseModelT],
):
    data: BaseModelT

    @classmethod
    def get_schema(cls) -> type[BaseModelT]: ...


def _merge_responses(
    target: dict,
    source: dict,
):
    for status, response in target.items():
        if response and status in source:
            model_class = response.get("model")
            source_schema = source[status].get("model")
            if source_schema and model_class:
                target[status]["model"] = model_class | source_schema

    for status, response in source.items():
        if status not in target:
            target[status] = response


def _info_responses(
    *infos: type[ResponseProtocol | ResponseDataProtocol[BaseModel]],
):
    result: dict[int, None | dict] = {}

    for info in infos:
        if hasattr(info, "get_schema"):
            info = cast(type[ResponseDataProtocol[BaseModel]], info)
            schema = info.get_schema()
            current: None | dict
            if (current := result.get(info.status)) and current.get("model"):
                current["model"] = current["model"] | schema
            elif result.get(info.status) is None:
                result[info.status] = {"model": schema}
        else:
            result.setdefault(info.status, None)

    return result


Response = (
    int
    | tuple[int, type[BaseModel]]
    | type[ResponseProtocol | ResponseDataProtocol]
)


class Responses:
    def __init__(self, *args: Response) -> None:
        self.data = args


def build_responses(*responses: Response):
    result = {}
    infos: list[type[ResponseProtocol]] = []

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
            infos.append(arg)
            continue

        result[status] = {"model": response} if response else None

    _merge_responses(result, _info_responses(*infos))
    return result
