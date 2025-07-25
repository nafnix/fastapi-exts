from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_exts.correlation_id import CorrelationIDExtension
from fastapi_exts.correlation_id.constants import HEADER_NAME
from fastapi_exts.manager import ExtensionManager


def test_response_correlation_id():
    app = FastAPI()

    mng = ExtensionManager()
    mng.register(CorrelationIDExtension())
    mng.install(app)

    @app.get("/")
    def _(): ...

    client = TestClient(app)

    res = client.get("/")
    assert res.is_success
    assert res.headers[HEADER_NAME] is not None


def test_request_correlation_id():
    app = FastAPI()

    mng = ExtensionManager()
    mng.register(CorrelationIDExtension())
    mng.install(app)

    @app.get("/")
    def _(): ...

    client = TestClient(app)

    value = str(uuid4())
    res = client.get("/", headers={HEADER_NAME: value})
    assert res.is_success
    assert res.headers[HEADER_NAME] == value


def test_request_with_invalid_correlation_id():
    app = FastAPI()

    mng = ExtensionManager()
    mng.register(CorrelationIDExtension())
    mng.install(app)

    @app.get("/")
    def _(): ...

    client = TestClient(app)

    value = "123"
    res = client.get("/", headers={HEADER_NAME: value})
    assert res.is_success
    assert res.headers[HEADER_NAME] != value
