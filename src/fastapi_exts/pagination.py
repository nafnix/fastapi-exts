from collections.abc import Mapping, Sequence
from math import ceil
from typing import Annotated, Generic, NamedTuple, TypeVar, overload

from fastapi import Depends, Query
from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt


BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


class Page(BaseModel, Generic[BaseModelT]):
    page_size: PositiveInt = Field(description="page size")
    page_no: PositiveInt = Field(description="page number")

    page_count: NonNegativeInt = Field(description="page count")
    count: NonNegativeInt = Field(description="result count")

    results: list[BaseModelT] = Field(description="results")


class PageParamsModel(BaseModel):
    page_size: int = Query(
        50,
        ge=1,
        le=100,
        description="page size",
    )
    page_no: int = Query(
        1,
        ge=1,
        description="page number",
    )


PageParams = Annotated[PageParamsModel, Depends()]


@overload
def page(
    model_class: type[BaseModelT],
    pagination: PageParamsModel,
    count: int,
    results: Sequence[Mapping],
) -> Page[BaseModelT]: ...


@overload
def page(
    model_class: type[BaseModelT],
    pagination: PageParamsModel,
    count: int,
    results: Sequence[NamedTuple],
) -> Page[BaseModelT]: ...


@overload
def page(
    model_class: type[BaseModelT],
    pagination: PageParamsModel,
    count: int,
    results,
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
