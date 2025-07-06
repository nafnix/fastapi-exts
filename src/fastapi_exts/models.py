from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from fastapi_exts._utils import naive_datetime, utc_datetime


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


class AuditModel(Model):
    created_at: datetime = Field()
    updated_at: datetime | None = Field(None)


class UTCAuditModel(AuditModel):
    """时间转为 UTC"""

    @model_validator(mode="after")
    def _to_utc(self):
        self.created_at = utc_datetime(self.created_at)
        if self.updated_at is not None:
            self.updated_at = utc_datetime(self.updated_at)
        return self


class NaiveAuditModel(AuditModel):
    """去除时间上的时区信息"""

    @model_validator(mode="after")
    def _to_utc(self):
        self.created_at = naive_datetime(self.created_at)
        if self.updated_at is not None:
            self.updated_at = naive_datetime(self.updated_at)
        return self


class NaiveUTCAuditModel(AuditModel):
    """将时间转为 UTC 时区后去除其时区信息"""

    @model_validator(mode="after")
    def _to_utc(self):
        self.created_at = naive_datetime(utc_datetime(self.created_at))
        if self.updated_at is not None:
            self.updated_at = naive_datetime(utc_datetime(self.updated_at))
        return self
