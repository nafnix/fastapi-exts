from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_exts.exceptions import (
    ExceptionExtension,
    HTTPCodeError,
    HTTPProblem,
)
from fastapi_exts.manager import ExtensionManager


def test_http_code_error():
    app = FastAPI()

    mng = ExtensionManager()
    mng.register(ExceptionExtension())
    mng.install(app)

    @app.get("/")
    def _():
        raise HTTPCodeError

    client = TestClient(app)

    res = client.get("/")
    assert res.is_error
    assert res.json()["code"] == HTTPCodeError.__name__


def test_http_problem():
    app = FastAPI()

    mng = ExtensionManager()
    mng.register(ExceptionExtension())
    mng.install(app)

    @app.get("/")
    def _():
        raise HTTPProblem

    client = TestClient(app)

    res = client.get("/")
    assert res.is_error
    assert res.json()["title"] == HTTPProblem.__name__
