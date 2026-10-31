from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from app.api.time import as_utc, utc_now
from app.exception.errors import ConflictException
from app.user.models import User


class UserRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def exists_by_email_ignore_case(self, email: str) -> bool:
        return self._collection.find_one({"email": email.lower()}, {"_id": 1}) is not None

    def find_by_email_ignore_case(self, email: str) -> User | None:
        document = self._collection.find_one({"email": email.lower()})
        if document is None:
            return None
        return self._to_user(document)

    def save(self, user: User) -> User:
        now = utc_now()
        document = {
            "email": user.email,
            "passwordHash": user.password_hash,
            "fullName": user.full_name,
            "roles": list(user.roles),
            "enabled": user.enabled,
            "createdAt": user.created_at or now,
            "updatedAt": now,
        }
        try:
            if user.id is None:
                inserted = self._collection.insert_one(document)
                user.id = str(inserted.inserted_id)
                user.created_at = as_utc(document["createdAt"])
                user.updated_at = as_utc(document["updatedAt"])
                return user
            self._collection.update_one({"_id": ObjectId(user.id)}, {"$set": document})
            user.updated_at = as_utc(document["updatedAt"])
            return user
        except DuplicateKeyError as exc:
            raise ConflictException("Email is already registered") from exc

    @staticmethod
    def _to_user(document: dict) -> User:
        return User(
            id=str(document["_id"]),
            email=document["email"],
            password_hash=document["passwordHash"],
            full_name=document["fullName"],
            roles=list(document.get("roles", [])),
            enabled=bool(document.get("enabled", True)),
            created_at=as_utc(document["createdAt"]) if document.get("createdAt") else None,
            updated_at=as_utc(document["updatedAt"]) if document.get("updatedAt") else None,
        )
