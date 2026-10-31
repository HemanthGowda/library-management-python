from app.api.time import utc_now
from app.auth.password import BcryptPasswordEncoder
from app.config import Settings

_BOOKS = (
    (
        "Effective Java",
        "Joshua Bloch",
        "9780134685991",
        "Best practices for the Java platform.",
        2018,
        5,
        5,
    ),
    (
        "Head First Design Patterns",
        "Eric Freeman",
        "9780596009205",
        "A brain-friendly guide to design patterns.",
        2004,
        3,
        3,
    ),
    (
        "Designing Data-Intensive Applications",
        "Martin Kleppmann",
        "9781492078005",
        "The big ideas behind reliable, scalable data systems.",
        2017,
        4,
        4,
    ),
)


def run_migrations(database, settings: Settings, password_encoder: BcryptPasswordEncoder) -> None:
    _apply(database, "v001-create-indexes", _create_indexes)
    _apply(
        database,
        "v002-seed-admin-and-books",
        lambda db: _seed(db, settings, password_encoder),
    )


def _apply(database, change_id: str, action) -> None:
    if database.changelog.find_one({"_id": change_id}):
        return
    action(database)
    database.changelog.insert_one(
        {
            "_id": change_id,
            "author": "library-starter",
            "appliedAt": utc_now(),
        }
    )


def _create_indexes(database) -> None:
    database.users.create_index([("email", 1)], unique=True, name="uk_users_email")
    database.books.create_index([("isbn", 1)], unique=True, name="uk_books_isbn")
    database.books.create_index([("title", 1)], name="idx_books_title")


def _seed(database, settings: Settings, password_encoder: BcryptPasswordEncoder) -> None:
    _seed_admin(database, settings, password_encoder)
    _seed_books(database)


def _seed_admin(database, settings: Settings, password_encoder: BcryptPasswordEncoder) -> None:
    email = settings.seed_admin_email.strip().lower()
    if database.users.find_one({"email": email}, {"_id": 1}):
        return
    now = utc_now()
    database.users.insert_one(
        {
            "email": email,
            "passwordHash": password_encoder.encode(settings.seed_admin_password),
            "fullName": settings.seed_admin_full_name,
            "roles": ["ADMIN"],
            "enabled": True,
            "createdAt": now,
            "updatedAt": now,
        }
    )


def _seed_books(database) -> None:
    now = utc_now()
    for title, author_name, isbn, description, year, total_copies, available_copies in _BOOKS:
        if database.books.find_one({"isbn": isbn}, {"_id": 1}):
            continue
        database.books.insert_one(
            {
                "title": title,
                "authorName": author_name,
                "isbn": isbn,
                "description": description,
                "publicationYear": year,
                "totalCopies": total_copies,
                "availableCopies": available_copies,
                "createdAt": now,
                "updatedAt": now,
            }
        )
