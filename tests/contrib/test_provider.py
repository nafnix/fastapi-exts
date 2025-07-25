from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_exts.contrib.provider import Provider
from fastapi_exts.contrib.routing import APIRouter


def test_provider():
    app = FastAPI()

    value = 1

    def get_number():
        return value

    provide_number = Provider(get_number)
    router = APIRouter()

    @router.get("/")
    def num(number=provide_number) -> bool:
        return number.value == value

    app.include_router(router)

    client = TestClient(app)

    res = client.get("/")
    assert res.is_success
    assert res.json()
