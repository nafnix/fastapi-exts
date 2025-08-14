from fastapi import FastAPI

from .base import BaseHTTPError
from .handler import ext_http_error_handler


class ExceptionExtension:
    def setup(self, app: FastAPI):
        app.add_exception_handler(
            BaseHTTPError,
            ext_http_error_handler,
        )
