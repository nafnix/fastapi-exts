from abc import ABC, abstractmethod

from pydantic import BaseModel


class BaseHTTPError(Exception, ABC):
    status: int
    data: BaseModel
    headers: dict[str, str] | None

    @classmethod
    @abstractmethod
    def response_class(cls) -> type[BaseModel]:
        raise NotImplementedError
