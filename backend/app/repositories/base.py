from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, session: Session, model: type[ModelType]) -> None:
        self.session = session
        self.model = model

    def get(self, id: Any) -> ModelType | None:
        return self.session.get(self.model, id)

    def get_or_raise(self, id: Any) -> ModelType:
        instance = self.get(id)
        if instance is None:
            raise NotFoundError(f"{self.model.__name__} with id={id} not found")
        return instance

    def list(self, offset: int = 0, limit: int = 100) -> list[ModelType]:
        statement: Select[tuple[ModelType]] = select(self.model).offset(offset).limit(limit)
        return list(self.session.scalars(statement).all())

    def create(self, obj_in: CreateSchemaType) -> ModelType:
        payload = obj_in.model_dump(exclude_unset=True)
        obj = self.model(**payload)
        self.session.add(obj)
        self.session.flush()
        self.session.refresh(obj)
        return obj

    def update(self, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        payload = obj_in.model_dump(exclude_unset=True)
        for field, value in payload.items():
            setattr(db_obj, field, value)
        self.session.add(db_obj)
        self.session.flush()
        self.session.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: ModelType) -> None:
        self.session.delete(db_obj)
        self.session.flush()
