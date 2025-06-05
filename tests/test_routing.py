from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_exts.exceptions import NamedHTTPError
from fastapi_exts.provider import Provider
from fastapi_exts.routing import ExtAPIRouter


class AError(NamedHTTPError):
    status = 401


class BError(NamedHTTPError):
    status = 403


def test_ext_api_router():
    value = id(object())

    def dependency2(
        dependency=Provider(lambda: value, exceptions=[BError]),
    ) -> int:
        return dependency.value

    router = ExtAPIRouter()

    path = "/"

    @router.get(path)
    def api(an_value=Provider(dependency2, exceptions=[AError])):
        return an_value.value

    app = FastAPI()
    app.include_router(router)

    test_client = TestClient(app)

    res = test_client.get(path)
    assert res.json() == value

    openapi = app.openapi()
    assert str(AError.status) in openapi["paths"][path]["get"]["responses"]
    assert str(BError.status) in openapi["paths"][path]["get"]["responses"]
