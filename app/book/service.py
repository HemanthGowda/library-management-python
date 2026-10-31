from app.book.dto import BookResponse, UpdateBookRequest
from app.book.mapper import to_response
from app.book.repository import BookRepository
from app.exception.errors import BadRequestException, ConflictException, ResourceNotFoundException


class BookService:
    def __init__(self, books: BookRepository) -> None:
        self._books = books

    def update(self, book_id: str, request: UpdateBookRequest) -> BookResponse:
        book = self._books.find_by_id(book_id)
        if book is None:
            raise ResourceNotFoundException(f"Book not found: {book_id}")

        isbn = normalize_isbn(request.isbn)
        if self._books.exists_by_isbn_and_id_not(isbn, book_id):
            raise ConflictException("ISBN is already assigned to another book")
        if request.availableCopies > request.totalCopies:
            raise BadRequestException("Available copies cannot exceed total copies")

        book.title = request.title.strip()
        book.author_name = request.authorName.strip()
        book.isbn = isbn
        book.description = None if request.description is None else request.description.strip()
        book.publication_year = request.publicationYear
        book.total_copies = request.totalCopies
        book.available_copies = request.availableCopies
        saved = self._books.save(book)
        return to_response(saved)


def normalize_isbn(isbn: str) -> str:
    return isbn.replace("-", "").strip().upper()
