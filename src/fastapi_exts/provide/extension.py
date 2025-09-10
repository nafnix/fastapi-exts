from fastapi import FastAPI

from fastapi_exts.core import ExtensionProtocol
from fastapi_exts.provide.routing import APIRouter


class ProvideExtension(ExtensionProtocol):
    name = "provide"

    def setup(self, app: FastAPI):
        router = APIRouter()
        router.include_router(app.router)
        app.routes.clear()
        app.include_router(router)
