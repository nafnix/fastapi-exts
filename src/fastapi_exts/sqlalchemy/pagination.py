from math import ceil
from typing import overload

from sqlalchemy import MappingResult, ScalarResult

from fastapi_exts.pagination import BaseModelT, Page, PageParamsModel


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


def page(
    model_class: type[BaseModelT],
    pagination: PageParamsModel,
    count: int,
    results,
) -> Page[BaseModelT]:
    results_ = [model_class.model_validate(i) for i in results]
    return Page[BaseModelT](
        page_size=pagination.page_size,
        page_no=pagination.page_no,
        page_count=ceil(count / pagination.page_size),
        count=count,
        results=results_,
    )
