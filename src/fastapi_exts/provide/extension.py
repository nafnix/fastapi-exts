from fastapi import FastAPI

from .routing import APIRouter


class ProvideExtension:
    name = "provide"

    def setup(self, app: FastAPI):
        router = APIRouter()
        router.include_router(app.router)
        app.routes.clear()
        app.include_router(router)
