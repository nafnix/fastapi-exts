from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_exts.cbv import CBV
from fastapi_exts.exceptions import NamedHTTPError
from fastapi_exts.provider import Provider


app = FastAPI()

cbv = CBV(app)
path = "/"


value = id(object())


class AError(NamedHTTPError):
    status = 401


class BError(NamedHTTPError):
    status = 403


provider = Provider(
    lambda: value,
    exceptions=[AError, BError],
)


@cbv
class Routes:
    @cbv.get(path)
    def api(self, an_value=provider):
        return an_value.value


path2 = "/2"


@cbv
class Routes2:
    an_value = provider

    @cbv.get(path2)
    def api(self):
        return self.an_value.value


def test_api_router():
    test_client = TestClient(app)

    res = test_client.get(path)
    assert res.json() == value

    res = test_client.get(path2)
    assert res.json() == value

    openapi = app.openapi()

    assert str(AError.status) in openapi["paths"][path]["get"]["responses"]
    assert str(BError.status) in openapi["paths"][path]["get"]["responses"]

    assert str(AError.status) in openapi["paths"][path2]["get"]["responses"]
    assert str(BError.status) in openapi["paths"][path2]["get"]["responses"]
