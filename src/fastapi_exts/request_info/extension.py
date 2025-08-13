from fastapi import FastAPI

from fastapi_exts.core import ExtensionBase

from .middleware import RequestInfoMiddleware
from .types import GetClientIP


class RequestInfoExtension(ExtensionBase):
    name = "request_info"

    def setup(self, app: FastAPI, get_client_ip: GetClientIP):
        app.add_middleware(RequestInfoMiddleware, get_client_ip=get_client_ip)
