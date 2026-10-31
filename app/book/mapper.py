from app.book.dto import BookResponse
from app.book.models import Book


def to_response(book: Book) -> BookResponse:
    if book.id is None or book.created_at is None or book.updated_at is None:
        raise RuntimeError("Book must be persisted before it is returned")
    return BookResponse(
        id=book.id,
        title=book.title,
        authorName=book.author_name,
        isbn=book.isbn,
        description=book.description,
        publicationYear=book.publication_year,
        totalCopies=book.total_copies,
        availableCopies=book.available_copies,
        createdAt=book.created_at,
        updatedAt=book.updated_at,
    )
