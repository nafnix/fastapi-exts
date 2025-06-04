from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_exts.provider import Provider
from fastapi_exts.routing import ExtAPIRouter


def test_ext_api_router():
    value = id(object())

    def dependency1() -> int:
        return value

    def dependency2(dependency=Provider(dependency1)) -> int:
        return dependency.value

    router = ExtAPIRouter()

    path = "/"

    @router.get(path)
    def api(an_value=Provider(dependency2)):
        return an_value.value

    app = FastAPI()
    app.include_router(router)

    test_client = TestClient(app)

    res = test_client.get(path)
    assert res.json() == value
