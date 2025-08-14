from typing import cast

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from fastapi.utils import is_body_allowed_for_status_code
from pydantic import BaseModel

from .base import BaseHTTPError


def ext_http_error_handler(request, exc):  # noqa: ARG001
    exc = cast(BaseHTTPError, exc)
    headers = exc.headers

    if not is_body_allowed_for_status_code(exc.status):
        return Response(status_code=exc.status, headers=headers)

    data = getattr(exc, "data", None)
    if isinstance(data, BaseModel):
        data = data.model_dump(exclude_unset=True)

    media_type = getattr(exc, "media_type", None)

    return JSONResponse(
        data,
        status_code=exc.status,
        headers=headers,
        media_type=media_type,
    )


class ExceptionExtension:
    def setup(self, app: FastAPI):
        app.add_exception_handler(
            BaseHTTPError,
            ext_http_error_handler,
        )
