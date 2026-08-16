"""
Reusable pagination support for list endpoints.

Usage in a route:

    @router.get("")
    async def list_departments(pagination: PaginationParams = Depends(get_pagination_params)):
        items, total = await department_service.list_departments(pagination)
        return success_response(data=items, meta=build_meta(pagination, total))
"""
from dataclasses import dataclass

from fastapi import Query

from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


@dataclass
class PaginationParams:
    page: int
    limit: int
    search: str | None
    sort_by: str | None
    sort_order: str  # "asc" | "desc"

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


def get_pagination_params(
    page: int = Query(DEFAULT_PAGE, ge=1, description="1-indexed page number"),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    search: str | None = Query(None, min_length=1, max_length=200, description="Free-text search"),
    sort_by: str | None = Query(None, description="Field to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit, search=search, sort_by=sort_by, sort_order=sort_order)


def build_meta(pagination: PaginationParams, total: int) -> dict:
    total_pages = (total + pagination.limit - 1) // pagination.limit if total > 0 else 0
    return {
        "page": pagination.page,
        "limit": pagination.limit,
        "total": total,
        "total_pages": total_pages,
        "has_next": pagination.page < total_pages,
        "has_prev": pagination.page > 1,
    }


def resolve_sort_field(sort_by: str | None, allowed_fields: set[str], default_field: str) -> str:
    """Whitelist the requested sort field to prevent sorting on arbitrary
    (and potentially expensive or sensitive) internal fields."""
    if sort_by and sort_by in allowed_fields:
        return sort_by
    return default_field


def sort_direction(sort_order: str) -> int:
    return 1 if sort_order == "asc" else -1
