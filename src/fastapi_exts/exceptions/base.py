from abc import ABC
from typing import TypeVar

from fastapi import status
from pydantic import BaseModel

from fastapi_exts.utils.responses import (
    ResponseDataProtocol,
    ResponseProtocol,
)


BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


class BaseHTTPError(ABC, ResponseProtocol, Exception):
    status = status.HTTP_400_BAD_REQUEST
    headers = None

    media_type: str


class BaseHTTPDataError(
    BaseHTTPError,
    ABC,
    ResponseDataProtocol[BaseModelT],
):
    data: BaseModelT
