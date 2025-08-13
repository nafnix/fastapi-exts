# from logging import getLogger

# from fastapi_exts.core.manager import ExtensionManager
# from fastapi_exts.core.types import Extension


# exts = ExtensionManager()


# class AExtension(Extension):
#     name = "A"

#     def setup(self, app): ...


# class BExtension(Extension):
#     name = "B"
#     dependencies = ({"name": "A"},)

#     def setup(self, app): ...


# exts.register(AExtension())
# exts.register(BExtension())
# from fastapi import FastAPI


# app = FastAPI()
# exts.install(app)

# logger = getLogger()
# logger.info("233")

import logging

from fastapi import FastAPI

from fastapi_exts.core import ExtensionManager
from fastapi_exts.correlation_id.extension import CorrelationIDExtension
from fastapi_exts.openapi.extension import OpenAPIExtension


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

manager = ExtensionManager()


manager.register(CorrelationIDExtension())
manager.register(OpenAPIExtension())
app = FastAPI()
manager.install(app)


@app.get("/")
async def demo(q: str):
    print(q)
