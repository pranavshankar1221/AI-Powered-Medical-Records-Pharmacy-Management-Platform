"""
Pagination utility for list endpoints.
"""

from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams:
    """Parse pagination query parameters."""
    def __init__(self, page: int = 1, per_page: int = 20, search: Optional[str] = None):
        self.page = max(1, page)
        self.per_page = min(max(1, per_page), 100)
        self.offset = (self.page - 1) * self.per_page
        self.search = search


class PaginatedResponse(BaseModel):
    """Standard paginated response envelope."""
    success: bool = True
    data: list
    total: int
    page: int
    per_page: int
    total_pages: int

    @classmethod
    def create(cls, items: list, total: int, page: int, per_page: int):
        total_pages = max(1, (total + per_page - 1) // per_page)
        return cls(
            data=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )
