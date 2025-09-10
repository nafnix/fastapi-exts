from typing import (
    Annotated,
    TypeGuard,
    get_origin,
)


def is_annotated(value) -> TypeGuard[Annotated]:
    return get_origin(value) is Annotated


def get_annotated_metadata(value: Annotated) -> tuple:
    return value.__metadata__
