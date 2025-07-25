from pydantic import BaseModel

from fastapi_exts.contrib.responses import build_responses


class Resp:
    status = 202


class DataResp:
    status = 401

    @classmethod
    def get_schema(cls):
        return BaseModel


def test_build_responses():
    result = build_responses(
        200, 201, 400, 500, (200, BaseModel), Resp, DataResp
    )
    assert result == {
        200: {"model": BaseModel},
        202: None,
        201: None,
        400: None,
        401: {"model": BaseModel},
        500: None,
    }
