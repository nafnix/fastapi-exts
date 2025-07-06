from abc import abstractmethod
from typing import ClassVar, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel


BaseModelT_co = TypeVar("BaseModelT_co", bound=BaseModel, covariant=True)


@runtime_checkable
class HTTPErrorInterface(Protocol):
    status: ClassVar[int]
    headers: dict[str, str] | None


@runtime_checkable
class HTTPSchemaErrorInterface(
    HTTPErrorInterface,
    Protocol[BaseModelT_co],
):
    @classmethod
    @abstractmethod
    def build_schema(cls) -> type[BaseModelT_co]: ...
