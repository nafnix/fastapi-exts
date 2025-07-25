from abc import abstractmethod
from typing import Protocol, TypeVar, cast, runtime_checkable

from pydantic import BaseModel


BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


@runtime_checkable
class ResponseInfoInterface(Protocol):
    status: int


@runtime_checkable
class ResponseInfoSchemaInterface(
    ResponseInfoInterface,
    Protocol[BaseModelT],
):
    data: BaseModelT

    @classmethod
    @abstractmethod
    def get_schema(cls) -> type[BaseModelT]: ...


def _merge_responses(
    target: dict,
    source: dict,
):
    for status, response in target.items():
        if response:
            model_class = response.get("model")
            if status in source:
                source_schema = source[status].get("model")
                if source_schema and model_class:
                    target[status]["model"] = model_class | source_schema

    for status, response in source.items():
        if status not in target:
            target[status] = response


def _info_responses(
    *infos: type[
        ResponseInfoInterface | ResponseInfoSchemaInterface[BaseModel]
    ],
):
    result: dict[int, None | dict] = {}

    for info in infos:
        if hasattr(info, "get_schema"):
            info = cast(type[ResponseInfoSchemaInterface[BaseModel]], info)
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
    | type[ResponseInfoInterface | ResponseInfoSchemaInterface]
)


class Responses:
    def __init__(self, *args: Response) -> None:
        self.data = args


def build_responses(*responses: Response):
    result = {}
    infos: list[type[ResponseInfoInterface]] = []

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
