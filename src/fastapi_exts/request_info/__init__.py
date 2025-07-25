from fastapi import FastAPI

from .middleware import RequestInfoMiddleware
from .types import GetClientIP


class RequestInfoExtension:
    def setup(self, app: FastAPI, get_client_ip: GetClientIP):
        app.add_middleware(RequestInfoMiddleware, get_client_ip=get_client_ip)
