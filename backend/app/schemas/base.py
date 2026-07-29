from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully."
    data: Optional[T] = None


class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


def success_response(data: Any = None, message: str = "Operation completed successfully.") -> dict:
    return {"success": True, "message": message, "data": data}


def error_response(message: str, data: Any = None) -> dict:
    return {"success": False, "message": message, "data": data}
