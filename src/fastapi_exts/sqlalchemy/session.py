from collections.abc import AsyncGenerator, Callable, Generator
from typing import overload

import sqlalchemy as sa
from sqlalchemy.ext import asyncio as asa
from sqlalchemy.orm import Session, sessionmaker


@overload
def create_engine_dependency(
    engine: sa.Engine,
) -> Callable[[], Generator[sa.Connection, None]]: ...
@overload
def create_engine_dependency(
    engine: asa.AsyncEngine,
) -> Callable[[], AsyncGenerator[asa.AsyncConnection, None]]: ...


def create_engine_dependency(
    engine: sa.Engine | asa.AsyncEngine,
):
    if isinstance(engine, asa.AsyncEngine):

        async def get_async_connection() -> AsyncGenerator[
            asa.AsyncConnection, None
        ]:
            async with engine.connect() as connection:
                yield connection

        return get_async_connection

    def get_connection() -> Generator[sa.Connection, None]:
        with engine.connect() as connection:
            yield connection

    return get_connection


@overload
def create_session_dependency(
    sessionmaker: sessionmaker,
) -> Callable[[], Generator[Session, None]]: ...
@overload
def create_session_dependency(
    sessionmaker: asa.async_sessionmaker,
) -> Callable[[], AsyncGenerator[asa.AsyncSession, None]]: ...


def create_session_dependency(
    sessionmaker: sessionmaker | asa.async_sessionmaker,
):
    if isinstance(sessionmaker, asa.AsyncEngine):

        async def get_async_session() -> AsyncGenerator[
            asa.AsyncSession, None
        ]:
            async with sessionmaker() as session:
                yield session

        return get_async_session

    def get_session() -> Generator[Session, None]:
        with sessionmaker() as session:
            yield session

    return get_session
