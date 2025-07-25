from typing import Protocol

from fastapi import FastAPI


class Extension(Protocol):
    def setup(self, app: FastAPI) -> None: ...


class ExtensionManager:
    def __init__(self) -> None:
        self.extensions: list[Extension] = []

    def register(self, extension: Extension):
        self.extensions.append(extension)

    def install(self, app: FastAPI):
        for ext in self.extensions:
            ext.setup(app)
