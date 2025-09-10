from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator
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
        serialize_by_alias=True,
        populate_by_name=True,
        from_attributes=True,
        field_title_generator=lambda field, _info: to_camel(field),
    )


def nested_transform(transform, instance: BaseModel):
    for i in instance.__pydantic_fields__:
        value = getattr(instance, i)
        if isinstance(value, datetime):
            value = transform(value)
            setattr(instance, i, value)
        elif isinstance(value, BaseModel):
            nested_transform(transform, value)


class UTCDatetimeModel(Model):
    @model_validator(mode="after")
    def _to_utc(self):
        nested_transform(utc_datetime, self)
        return self


class NaiveDatetimeModel(Model):
    @model_validator(mode="after")
    def _naive_datetime(self):
        nested_transform(naive_datetime, self)
        return self


class NaiveUTCDatetimeModel(Model):
    @model_validator(mode="after")
    def _naive_utc_datetime(self):
        nested_transform(lambda x: naive_datetime(utc_datetime(x)), self)
        return self
