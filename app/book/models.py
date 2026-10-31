from dataclasses import dataclass
from datetime import datetime


@dataclass
class Book:
    id: str | None
    title: str
    author_name: str
    isbn: str
    description: str | None
    publication_year: int
    total_copies: int
    available_copies: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
