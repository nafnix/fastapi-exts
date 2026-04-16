from typing import Annotated

from fastapi import Depends, FastAPI, Query
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


VALUE2 = 2333


def get_value():
    return VALUE2


GetValue = Annotated[int, Depends(get_value)]

path3 = "/3"


class Obj:
    def __init__(self, s: str = Query()) -> None:
        self.s = s


@cbv
class Routes3:
    obj: Obj = Depends()
    value2: GetValue

    @cbv.get(path3)
    def api(self):
        return {"s": self.obj.s, "value2": self.value2}


def test_api_router():
    test_client = TestClient(app)

    res = test_client.get(path)
    assert res.json() == value

    res = test_client.get(path2)
    assert res.json() == value

    s = str(id(object()))
    res = test_client.get(path3, params={"s": s})
    res_json = res.json()
    assert res_json["s"] == s
    assert res_json["value2"] == VALUE2

    openapi = app.openapi()

    assert str(AError.status) in openapi["paths"][path]["get"]["responses"]
    assert str(BError.status) in openapi["paths"][path]["get"]["responses"]

    assert str(AError.status) in openapi["paths"][path2]["get"]["responses"]
    assert str(BError.status) in openapi["paths"][path2]["get"]["responses"]
