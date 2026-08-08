from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from app.core.exceptions import NotFoundError
from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, repository: BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]) -> None:
        self.repository = repository

    def get(self, id: Any) -> ModelType | None:
        return self.repository.get(id)

    def get_or_raise(self, id: Any) -> ModelType:
        instance = self.get(id)
        if instance is None:
            raise NotFoundError(f"Resource with id={id} not found")
        return instance

    def list(self, offset: int = 0, limit: int = 100) -> list[ModelType]:
        return self.repository.list(offset=offset, limit=limit)

    def create(self, obj_in: CreateSchemaType) -> ModelType:
        return self.repository.create(obj_in)

    def update(self, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        return self.repository.update(db_obj, obj_in)

    def delete(self, db_obj: ModelType) -> None:
        self.repository.delete(db_obj)
