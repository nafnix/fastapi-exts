from fastapi import FastAPI

from fastapi_exts.core import ExtensionProtocol

from .middleware import RequestInfoMiddleware
from .types import GetClientIP


class RequestInfoExtension(ExtensionProtocol):
    name = "request_info"

    def __init__(self, get_client_ip: GetClientIP) -> None:
        self.get_client_ip = get_client_ip

    def setup(self, app: FastAPI):
        app.add_middleware(
            RequestInfoMiddleware,
            get_client_ip=self.get_client_ip,
        )
