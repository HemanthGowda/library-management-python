from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from app.api.time import as_utc, utc_now
from app.book.models import Book
from app.exception.errors import ConflictException


class BookRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def find_by_id(self, book_id: str) -> Book | None:
        try:
            object_id = ObjectId(book_id)
        except InvalidId:
            return None
        document = self._collection.find_one({"_id": object_id})
        if document is None:
            return None
        return self._to_book(document)

    def exists_by_isbn_and_id_not(self, isbn: str, book_id: str) -> bool:
        query: dict = {"isbn": isbn}
        try:
            query["_id"] = {"$ne": ObjectId(book_id)}
        except InvalidId:
            pass
        return self._collection.find_one(query, {"_id": 1}) is not None

    def save(self, book: Book) -> Book:
        now = utc_now()
        fields = {
            "title": book.title,
            "authorName": book.author_name,
            "isbn": book.isbn,
            "description": book.description,
            "publicationYear": book.publication_year,
            "totalCopies": book.total_copies,
            "availableCopies": book.available_copies,
            "updatedAt": now,
        }
        try:
            if book.id is None:
                fields["createdAt"] = book.created_at or now
                inserted = self._collection.insert_one(fields)
                book.id = str(inserted.inserted_id)
                book.created_at = as_utc(fields["createdAt"])
                book.updated_at = as_utc(fields["updatedAt"])
                return book

            object_id = ObjectId(book.id)
            if book.created_at is not None:
                fields["createdAt"] = book.created_at
            updated = self._collection.find_one_and_update(
                {"_id": object_id},
                {"$set": fields},
                return_document=ReturnDocument.AFTER,
            )
            if updated is None:
                return book
            return self._to_book(updated)
        except DuplicateKeyError as exc:
            raise ConflictException("ISBN is already assigned to another book") from exc

    @staticmethod
    def _to_book(document: dict) -> Book:
        return Book(
            id=str(document["_id"]),
            title=document["title"],
            author_name=document["authorName"],
            isbn=document["isbn"],
            description=document.get("description"),
            publication_year=document["publicationYear"],
            total_copies=document["totalCopies"],
            available_copies=document["availableCopies"],
            created_at=as_utc(document["createdAt"]) if document.get("createdAt") else None,
            updated_at=as_utc(document["updatedAt"]) if document.get("updatedAt") else None,
        )
