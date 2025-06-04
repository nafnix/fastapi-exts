from typing import Protocol

from pydantic import BaseModel


class HTTPError(Protocol):
    status: int

    @classmethod
    def response_class(cls) -> type[BaseModel]: ...
