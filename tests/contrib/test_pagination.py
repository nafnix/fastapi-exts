from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from fastapi_exts.contrib.pagination import (
    APIPage,
    APIPageParams,
    APIPageParamsModel,
    Page,
    PageParams,
    PageParamsModel,
    api_page,
    page,
)


class TestPagination:
    def test_page(self):
        class M(BaseModel):
            a_1: int

        params = PageParamsModel()
        count = 10
        result = page(M, params, count, results=[{"a_1": 1}])
        assert isinstance(result, Page)
        assert result.count == count
        assert all(isinstance(i, M) for i in result.results)
        assert result.page_count == 1

    def test_api_page(self):
        class M(BaseModel):
            a_1: int

        params = PageParamsModel()
        count = 10
        result = api_page(M, params, count, results=[{"a_1": 1}])
        assert isinstance(result, APIPage)
        assert result.count == count
        assert all(isinstance(i, M) for i in result.results)
        assert result.page_count == 1

    def test_api_params(self):
        size = 1
        no = 2
        result = APIPageParamsModel(page_size=size, page_no=no).model_dump()
        assert result["pageSize"] == size
        assert result["pageNo"] == no

    def test_deps(self):
        app = FastAPI()

        @app.get("/")
        def demo(params: PageParams, api_params: APIPageParams):
            return [params.model_dump(), api_params.model_dump()]

        client = TestClient(app)

        res = client.get("/")
        assert res.is_success
        default_params = PageParamsModel()
        default_api_params = APIPageParamsModel()
        params, api_params = res.json()
        assert params["page_size"] == default_params.page_size
        assert params["page_no"] == default_params.page_no
        assert api_params["pageSize"] == default_api_params.page_size
        assert api_params["pageNo"] == default_api_params.page_no

        size = 1
        no = 2
        res = client.get(
            "/",
            params={
                "page_no": no,
                "page_size": size,
                "pageNo": no,
                "pageSize": size,
            },
        )
        assert res.is_success
        params, api_params = res.json()
        assert params["page_size"] == size
        assert params["page_no"] == no
        assert api_params["pageSize"] == size
        assert api_params["pageNo"] == no
