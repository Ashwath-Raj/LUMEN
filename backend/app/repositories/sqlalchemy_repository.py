"""
SQLAlchemyRepository — generic CRUD base for all ORM models.
Follows the repository pattern: routers never touch the session directly.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class SQLAlchemyRepository(Generic[T]):
    def __init__(self, session: Session, model_cls: type[T]):
        self.session = session
        self.model_cls = model_cls

    def get(self, identifier: str) -> T | None:
        return self.session.get(self.model_cls, identifier)

    def list(self) -> list[T]:
        return list(self.session.query(self.model_cls).all())

    def filter_by(self, **kwargs) -> list[T]:
        return list(self.session.query(self.model_cls).filter_by(**kwargs).all())

    def first_by(self, **kwargs) -> T | None:
        return self.session.query(self.model_cls).filter_by(**kwargs).first()

    def add(self, instance: T) -> T:
        self.session.add(instance)
        self.session.flush()
        return instance

    def add_all(self, instances: list[T]) -> None:
        self.session.add_all(instances)
        self.session.flush()

    def delete(self, instance: T) -> None:
        self.session.delete(instance)
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
