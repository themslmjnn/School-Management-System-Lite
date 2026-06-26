from typing import TypeVar

from pydantic.generics import GenericModel

T = TypeVar("T")


class PaginatedResponse[T](GenericModel):
    items: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool
