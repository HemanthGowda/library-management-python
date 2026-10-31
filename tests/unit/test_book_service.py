from datetime import datetime, timezone

import pytest

from app.book.dto import UpdateBookRequest
from app.book.models import Book
from app.book.service import BookService
from app.exception.errors import BadRequestException, ConflictException, ResourceNotFoundException


class FakeBooks:
    def __init__(self, book: Book | None = None, isbn_conflict: bool = False) -> None:
        self.book = book
        self.isbn_conflict = isbn_conflict
        self.checked_isbn: str | None = None
        self.saved: Book | None = None

    def find_by_id(self, book_id: str) -> Book | None:
        if self.book is not None and self.book.id == book_id:
            return self.book
        return None

    def exists_by_isbn_and_id_not(self, isbn: str, book_id: str) -> bool:
        self.checked_isbn = isbn
        return self.isbn_conflict

    def save(self, book: Book) -> Book:
        self.saved = book
        return book


def _book() -> Book:
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return Book(
        id="book-1",
        title="Old Title",
        author_name="Old Author",
        isbn="9780134685991",
        description="Old",
        publication_year=2018,
        total_copies=2,
        available_copies=1,
        created_at=now,
        updated_at=now,
    )


def _request(**overrides) -> UpdateBookRequest:
    payload = {
        "title": "New Title",
        "authorName": "New Author",
        "isbn": "9780596009205",
        "description": "Updated description",
        "publicationYear": 2020,
        "totalCopies": 5,
        "availableCopies": 4,
    }
    payload.update(overrides)
    return UpdateBookRequest.model_validate(payload)


def test_update_replaces_mutable_fields():
    books = FakeBooks(_book())
    response = BookService(books).update("book-1", _request())

    assert response.title == "New Title"
    assert response.authorName == "New Author"
    assert response.isbn == "9780596009205"
    assert response.totalCopies == 5
    assert response.availableCopies == 4


def test_update_normalizes_isbn():
    books = FakeBooks(_book())
    request = UpdateBookRequest.model_construct(
        title="Title",
        authorName="Author",
        isbn="978-059600920x",
        description="Desc",
        publicationYear=2020,
        totalCopies=5,
        availableCopies=4,
    )

    response = BookService(books).update("book-1", request)

    assert books.checked_isbn == "978059600920X"
    assert response.isbn == "978059600920X"


def test_update_fails_when_book_missing():
    books = FakeBooks()
    with pytest.raises(ResourceNotFoundException, match="Book not found: missing"):
        BookService(books).update("missing", _request())


def test_update_fails_when_isbn_conflicts():
    books = FakeBooks(_book(), isbn_conflict=True)
    with pytest.raises(ConflictException, match="ISBN"):
        BookService(books).update("book-1", _request())


def test_update_fails_when_available_exceeds_total():
    books = FakeBooks(_book())
    request = _request(totalCopies=2, availableCopies=3)
    with pytest.raises(BadRequestException, match="Available copies"):
        BookService(books).update("book-1", request)
