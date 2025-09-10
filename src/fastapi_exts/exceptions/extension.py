from fastapi import FastAPI

from .base import BaseHTTPError
from .handler import fastapi_exts_exception_handler


class ExceptionExtension:
    def setup(self, app: FastAPI):
        app.add_exception_handler(
            BaseHTTPError,
            fastapi_exts_exception_handler,
        )
