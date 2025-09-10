from typing import cast

from fastapi.responses import JSONResponse, Response
from fastapi.utils import is_body_allowed_for_status_code
from pydantic import BaseModel

from .base import BaseHTTPError


def fastapi_exts_exception_handler(request, exc):  # noqa: ARG001
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
