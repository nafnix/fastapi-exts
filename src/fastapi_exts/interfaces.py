from abc import ABC, abstractmethod

from pydantic import BaseModel


class BaseHTTPError(Exception, ABC):
    status: int

    @classmethod
    @abstractmethod
    def response_class(cls) -> type[BaseModel]:
        raise NotImplementedError
