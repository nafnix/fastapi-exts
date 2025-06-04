from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from fastapi_exts.provider import Provider, transform_providers


def test_api_router():
    value = id(object())

    def dependency() -> int:
        return value

    provider = Provider(dependency)

    router = APIRouter()

    path = "/"

    @router.get(path)
    @transform_providers
    def api(an_value=provider):
        return an_value.value

    app = FastAPI()
    app.include_router(router)

    test_client = TestClient(app)

    res = test_client.get(path)
    assert res.json() == value
