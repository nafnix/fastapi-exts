from collections.abc import Iterable, Mapping
from math import ceil
from typing import Annotated, Generic, NamedTuple, Protocol, TypeVar, overload

from fastapi import Depends, Query
from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt

from .models import APIModel


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


class PageParamsInterface(Protocol):
    page_size: int
    page_no: int


@overload
def page(
    model_class: type[BaseModelT],
    pagination: PageParamsInterface,
    count: int,
    results: Iterable[Mapping],
) -> Page[BaseModelT]: ...


@overload
def page(
    model_class: type[BaseModelT],
    pagination: PageParamsInterface,
    count: int,
    results: Iterable[NamedTuple],
) -> Page[BaseModelT]: ...


@overload
def page(
    model_class: type[BaseModelT],
    pagination: PageParamsInterface,
    count: int,
    results: Iterable,
) -> Page[BaseModelT]: ...


def page(
    model_class: type[BaseModelT],
    pagination: PageParamsInterface,
    count: int,
    results,
) -> Page[BaseModelT]:
    return Page(
        page_size=pagination.page_size,
        page_no=pagination.page_no,
        page_count=ceil(count / pagination.page_size),
        count=count,
        results=[model_class.model_validate(i) for i in results],
    )


class APIPage(Page[BaseModelT], APIModel, Generic[BaseModelT]): ...


class APIPageParamsModel(PageParamsModel, APIModel): ...


APIPageParams = Annotated[APIPageParamsModel, Depends()]


@overload
def api_page(
    model_class: type[BaseModelT],
    pagination: PageParamsInterface,
    count: int,
    results: Iterable[Mapping],
) -> APIPage[BaseModelT]: ...


@overload
def api_page(
    model_class: type[BaseModelT],
    pagination: PageParamsInterface,
    count: int,
    results: Iterable[NamedTuple],
) -> APIPage[BaseModelT]: ...


@overload
def api_page(
    model_class: type[BaseModelT],
    pagination: PageParamsInterface,
    count: int,
    results: Iterable,
) -> APIPage[BaseModelT]: ...


def api_page(
    model_class: type[BaseModelT],
    pagination: PageParamsInterface,
    count: int,
    results,
) -> APIPage[BaseModelT]:
    return APIPage[BaseModelT](
        page_size=pagination.page_size,
        page_no=pagination.page_no,
        page_count=ceil(count / pagination.page_size),
        count=count,
        results=[model_class.model_validate(i) for i in results],
    )
