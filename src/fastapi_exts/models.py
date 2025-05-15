from datetime import UTC, datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from pydantic.alias_generators import to_camel


class Model(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class APIModel(Model):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        field_title_generator=lambda field, _info: to_camel(field),
    )


class DB:
    DBSmallInt = Annotated[int, Field(ge=-32768, le=32767)]
    DBInt = Annotated[int, Field(ge=-2147483648, le=2147483647)]
    DBBigInt = Annotated[
        int, Field(ge=-9223372036854775808, le=9223372036854775807)
    ]
    DBSmallSerial = Annotated[int, Field(ge=1, le=32767)]
    DBIntSerial = Annotated[int, Field(ge=1, le=2147483647)]
    DBBigintSerial = Annotated[int, Field(ge=1, le=9223372036854775807)]


def _naive_datetime(dt: datetime):
    return dt.replace(tzinfo=None)


def _utc_datetime(dt: datetime):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


# 去除时区信息
NaiveDatetime = Annotated[datetime, AfterValidator(_naive_datetime)]
# 将时区转成 UTC
UTCDateTime = Annotated[datetime, AfterValidator(_utc_datetime)]
# 将时间转成 UTC, 并且去除时区信息
UTCNaiveDateTime = Annotated[
    datetime,
    AfterValidator(lambda x: _naive_datetime(_utc_datetime(x))),
]


class AuditModel(Model):
    created_at: datetime = Field()
    updated_at: datetime | None = Field(None)


class UTCAuditModel(AuditModel):
    @model_validator(mode="after")
    def _to_utc(self):
        self.created_at = _utc_datetime(self.created_at)
        if self.updated_at is not None:
            self.updated_at = _utc_datetime(self.updated_at)
        return self


class NaiveAuditModel(AuditModel):
    @model_validator(mode="after")
    def _to_utc(self):
        self.created_at = _naive_datetime(self.created_at)
        if self.updated_at is not None:
            self.updated_at = _naive_datetime(self.updated_at)
        return self


class UTCNaiveAuditModel(AuditModel):
    @model_validator(mode="after")
    def _to_utc(self):
        self.created_at = _naive_datetime(_utc_datetime(self.created_at))
        if self.updated_at is not None:
            self.updated_at = _naive_datetime(_utc_datetime(self.updated_at))
        return self
