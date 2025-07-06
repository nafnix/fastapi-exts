from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Annotated, Generic, TypeVar, get_args, get_origin

import sqlalchemy as sa
from sqlalchemy import orm as saorm
from sqlalchemy.sql.type_api import TypeEngine
from typing_extensions import get_original_bases

from fastapi_exts._utils import _undefined


T = TypeVar("T", bound=Annotated)


class IDBase(saorm.DeclarativeBase, Generic[T]):
    __abstract__ = True
    IDPythonType = T  # type: ignore
    IDColumnType: TypeEngine[T] = _undefined
    id: saorm.Mapped[T]

    def __init_subclass__(cls, *args, **kwds) -> None:
        type_var = cls._infer_id_type()

        # TODO: 处理取不到 id 类型的问题
        if type_var is None:
            raise NotImplementedError

        setattr(cls, "IDPythonType", type_var)

        attr = "id"

        cls.__annotations__.update({attr: saorm.Mapped[type_var]})
        setattr(
            cls,
            attr,
            saorm.mapped_column(primary_key=True, sort_order=-9999),
        )

        super().__init_subclass__(*args, **kwds)

        if hasattr(cls, "__table__"):
            setattr(cls, "IDColumnType", cls.__table__.c[attr].type)

    @classmethod
    def _infer_id_type(cls) -> type[T] | None:
        factory_bases: Iterable[type[IDBase[T]]] = (
            b
            for b in get_original_bases(cls)
            if get_origin(b) and issubclass(get_origin(b), IDBase)
        )
        generic_args: Sequence[type[T]] = [
            arg
            for factory_base in factory_bases
            for arg in get_args(factory_base)
            if not isinstance(arg, TypeVar)
        ]
        if len(generic_args) != 1:
            return None

        return generic_args[0]


class AuditMixin:
    """当继承该类时, 会给表添加创建时间和更新时间字段"""

    created_at: saorm.Mapped[datetime] = saorm.mapped_column(
        server_default=sa.func.now(),
        sort_order=9998,
    )
    updated_at: saorm.Mapped[datetime | None] = saorm.mapped_column(
        server_default=sa.null(),
        onupdate=sa.func.now(),
        sort_order=9999,
    )
