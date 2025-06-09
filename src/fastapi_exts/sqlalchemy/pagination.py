from typing import overload

from sqlalchemy import MappingResult, ScalarResult

from fastapi_exts.pagination import (
    APIPage,
    APIPageParamsModel,
    BaseModelT,
    Page,
    PageParamsModel,
)
from fastapi_exts.pagination import api_page as _api_page
from fastapi_exts.pagination import page as _page


@overload
def page(
    model_class: type[BaseModelT],
    pagination: PageParamsModel,
    count: int,
    results: ScalarResult,
) -> Page[BaseModelT]: ...


@overload
def page(
    model_class: type[BaseModelT],
    pagination: PageParamsModel,
    count: int,
    results: MappingResult,
) -> Page[BaseModelT]: ...


def page(*args, **kwds):
    return _page(*args, *kwds)


@overload
def api_page(
    model_class: type[BaseModelT],
    pagination: PageParamsModel | APIPageParamsModel,
    count: int,
    results: ScalarResult,
) -> APIPage[BaseModelT]: ...


@overload
def api_page(
    model_class: type[BaseModelT],
    pagination: PageParamsModel | APIPageParamsModel,
    count: int,
    results: MappingResult,
) -> APIPage[BaseModelT]: ...


def api_page(*args, **kwds):
    return _api_page(*args, *kwds)
