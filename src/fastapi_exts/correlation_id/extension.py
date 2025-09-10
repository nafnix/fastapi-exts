from fastapi import Depends, FastAPI

from fastapi_exts.core import ExtensionManager, ExtensionWithDepsProtocol
from fastapi_exts.openapi.extension import OpenAPIExtension
from fastapi_exts.utils.merge import merge

from .constants import HEADER_NAME
from .deps import get_correlation_id
from .middleware import CorrelationIDMiddleware


OPENAPI_EXTRA = {
    "headers": {
        HEADER_NAME: {"schema": {"type": "string", "title": HEADER_NAME}},
    }
}


def add_correlation_id_headers(openapi: dict) -> dict:
    for obj in openapi["paths"].values():
        for data in obj.values():
            for data_ in data["responses"].values():
                merge(data_, OPENAPI_EXTRA)
    return openapi


class CorrelationIDExtension(ExtensionWithDepsProtocol):
    name = "correlation_id"
    dependencies = ({"name": OpenAPIExtension.name, "required": False},)

    def setup(self, app: FastAPI):
        app.add_middleware(CorrelationIDMiddleware)

        app.router.dependencies.append(Depends(get_correlation_id))

        manager: ExtensionManager | None = getattr(
            app.state,
            ExtensionManager.STATE_KEY,
            None,
        )
        if manager and (openapi_ext := manager.get(OpenAPIExtension.name)):
            assert isinstance(openapi_ext, OpenAPIExtension)

            openapi_ext.add_modifier(add_correlation_id_headers)
