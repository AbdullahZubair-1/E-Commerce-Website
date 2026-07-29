import math
from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


def paginate(total: int, page: int, page_size: int) -> dict:
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
