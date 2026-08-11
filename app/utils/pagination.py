from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int


def get_page(db: Session, statement, page: int, page_size: int):
    """Execute a select statement with pagination and return (items, total)."""
    total = db.scalar(select(func.count()).select_from(statement.subquery()))
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return items, total
