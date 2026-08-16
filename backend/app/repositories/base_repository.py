"""
Generic base repository.

Every entity repository (DepartmentRepository, UserRepository, ...)
subclasses this to get find/list/create/update/delete for free, and only
adds the query logic that's actually specific to that entity (custom
finders, uniqueness checks, etc). This is what keeps the ten CRUD
modules in this project from duplicating the same Mongo boilerplate ten
times over.
"""
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import DuplicateException, NotFoundException, ValidationException
from app.models.base import utcnow
from app.utils.pagination import PaginationParams, resolve_sort_field, sort_direction


def to_object_id(id_str: str, entity_name: str = "Resource") -> ObjectId:
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise ValidationException(f"'{id_str}' is not a valid {entity_name} id")


def serialize_doc(doc: dict | None) -> dict | None:
    """Convert a raw Mongo document into API/schema-friendly shape: `_id`
    (ObjectId) becomes `id` (str). Every other field passes through
    untouched."""
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


class BaseRepository:
    #: Fields eligible for `?sort_by=`. Subclasses override this.
    sortable_fields: set[str] = {"created_at", "updated_at"}
    #: Fallback sort field when `sort_by` is absent/invalid.
    default_sort_field: str = "created_at"
    #: Fields scanned by the free-text `?search=` query param. Subclasses override this.
    searchable_fields: list[str] = []
    entity_name: str = "Resource"

    def __init__(self, collection: AsyncCollection):
        self.collection = collection

    # --- reads -----------------------------------------------------------

    async def find_by_id(self, id_str: str) -> dict | None:
        oid = to_object_id(id_str, self.entity_name)
        doc = await self.collection.find_one({"_id": oid})
        return serialize_doc(doc)

    async def get_by_id_or_404(self, id_str: str) -> dict:
        doc = await self.find_by_id(id_str)
        if doc is None:
            raise NotFoundException(f"{self.entity_name} not found")
        return doc

    async def find_one(self, filter_: dict) -> dict | None:
        doc = await self.collection.find_one(filter_)
        return serialize_doc(doc)

    async def exists(self, filter_: dict) -> bool:
        return await self.collection.count_documents(filter_, limit=1) > 0

    def _build_search_filter(self, search: str | None) -> dict:
        if not search or not self.searchable_fields:
            return {}
        pattern = {"$regex": search, "$options": "i"}
        return {"$or": [{field: pattern} for field in self.searchable_fields]}

    async def list_paginated(
        self,
        pagination: PaginationParams,
        extra_filter: dict | None = None,
        include_inactive: bool = False,
    ) -> tuple[list[dict], int]:
        filter_ = dict(extra_filter or {})
        if not include_inactive and "is_active" not in filter_:
            filter_["is_active"] = True

        search_filter = self._build_search_filter(pagination.search)
        if search_filter:
            filter_ = {"$and": [filter_, search_filter]} if filter_ else search_filter

        sort_field = resolve_sort_field(pagination.sort_by, self.sortable_fields, self.default_sort_field)
        direction = sort_direction(pagination.sort_order)

        total = await self.collection.count_documents(filter_)
        cursor = (
            self.collection.find(filter_)
            .sort(sort_field, direction)
            .skip(pagination.skip)
            .limit(pagination.limit)
        )
        docs = await cursor.to_list(length=pagination.limit)
        return [serialize_doc(d) for d in docs], total

    async def list_all(self, filter_: dict | None = None, limit: int = 500) -> list[dict]:
        """Unpaginated fetch used for dropdown/lookup lists (departments,
        academic years, ...) where the full active set is small enough to
        load in one call."""
        cursor = self.collection.find(filter_ or {}).sort(self.default_sort_field, 1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [serialize_doc(d) for d in docs]

    # --- writes ------------------------------------------------------------

    async def insert(self, data: dict, actor_id: str | None = None) -> dict:
        now = utcnow()
        data = {**data, "created_at": now, "updated_at": now}
        if actor_id:
            data["created_by"] = actor_id
            data["updated_by"] = actor_id
        try:
            result = await self.collection.insert_one(data)
        except DuplicateKeyError as exc:
            raise DuplicateException(f"{self.entity_name} with these details already exists") from exc
        return await self.find_by_id(str(result.inserted_id))

    async def update(self, id_str: str, data: dict, actor_id: str | None = None) -> dict:
        if not data:
            return await self.get_by_id_or_404(id_str)
        oid = to_object_id(id_str, self.entity_name)
        data = {**data, "updated_at": utcnow()}
        if actor_id:
            data["updated_by"] = actor_id
        try:
            result = await self.collection.update_one({"_id": oid}, {"$set": data})
        except DuplicateKeyError as exc:
            raise DuplicateException(f"{self.entity_name} with these details already exists") from exc
        if result.matched_count == 0:
            raise NotFoundException(f"{self.entity_name} not found")
        return await self.find_by_id(id_str)

    async def soft_delete(self, id_str: str, actor_id: str | None = None) -> dict:
        """The standard user-facing "delete": marks the record inactive
        and stamps when/who, but keeps the document (and its history/
        references) intact and reversible via restore()."""
        return await self.update(id_str, {"is_active": False, "deleted_at": utcnow()}, actor_id=actor_id)

    async def restore(self, id_str: str, actor_id: str | None = None) -> dict:
        existing = await self.get_by_id_or_404(id_str)
        if existing["is_active"]:
            raise ValidationException(f"{self.entity_name} is not deleted")
        return await self.update(id_str, {"is_active": True, "deleted_at": None}, actor_id=actor_id)

    async def delete(self, id_str: str) -> None:
        """Permanent, irreversible removal. Not used by the standard CRUD
        DELETE endpoints (which call soft_delete instead) - kept
        available for maintenance/cleanup use since some things
        legitimately do need to be purged rather than archived."""
        oid = to_object_id(id_str, self.entity_name)
        result = await self.collection.delete_one({"_id": oid})
        if result.deleted_count == 0:
            raise NotFoundException(f"{self.entity_name} not found")

    async def count(self, filter_: dict | None = None) -> int:
        return await self.collection.count_documents(filter_ or {})
