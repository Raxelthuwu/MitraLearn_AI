import datetime
import bcrypt
from bson import ObjectId
from core.db import users


class User:

    collection = users

    @staticmethod
    def serialize(obj: dict) -> dict:
        # convert MongoDB document to serializable dict
        return {
            "id":         str(obj["_id"]),
            "fullName":   obj["fullName"],
            "email":      obj["email"],
            "career":     obj["career"],
            "role":       obj["role"],
            "phone":      obj.get("phone", ""),
            "reputation": obj.get("reputation", 0),
            "createdAt":  obj["createdAt"].isoformat(),
        }

    @staticmethod
    def create(fullName: str, email: str, password: str, career: str, role: str, phone: str) -> str:
        # hash password before inserting into MongoDB
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        doc = {
            "fullName":   fullName,
            "email":      email.lower().strip(),
            "password":   hashed.decode("utf-8"),
            "career":     career,
            "role":       role,
            "phone":      phone,
            "reputation": 0,
            "createdAt":  datetime.datetime.utcnow(),
        }

        result = User.collection.insert_one(doc)
        return str(result.inserted_id)

    @staticmethod
    def getByEmail(email: str):
        # find user by email case-insensitive
        return User.collection.find_one({"email": email.lower().strip()})

    @staticmethod
    def getById(userId: str):
        # find user by ObjectId string
        return User.collection.find_one({"_id": ObjectId(userId)})

    @staticmethod
    def getAll():
        # return all users sorted by creation date
        return list(User.collection.find().sort("createdAt", -1))

    @staticmethod
    def update(userId: str, payload: dict):
        # update only allowed fields
        allowed = {"fullName", "career", "phone", "role"}
        update  = {k: v for k, v in payload.items() if k in allowed and v}

        if "email" in payload and payload["email"]:
            update["email"] = payload["email"].lower().strip()

        if "password" in payload and payload["password"]:
            hashed = bcrypt.hashpw(payload["password"].encode("utf-8"), bcrypt.gensalt())
            update["password"] = hashed.decode("utf-8")

        if not update:
            return User.collection.find_one({"_id": ObjectId(userId)})

        update["updatedAt"] = datetime.datetime.utcnow()
        User.collection.update_one({"_id": ObjectId(userId)}, {"$set": update})
        return User.collection.find_one({"_id": ObjectId(userId)})

    @staticmethod
    def delete(userId: str) -> bool:
        # permanently remove user document
        result = User.collection.delete_one({"_id": ObjectId(userId)})
        return result.deleted_count > 0

    @staticmethod
    def verifyPassword(plainPassword: str, hashedPassword: str) -> bool:
        # compare plain text against stored bcrypt hash
        return bcrypt.checkpw(
            plainPassword.encode("utf-8"),
            hashedPassword.encode("utf-8"),
        )

    @staticmethod
    def emailExists(email: str) -> bool:
        # true if email is already registered
        return User.collection.find_one({"email": email.lower().strip()}) is not None

    @staticmethod
    def addReputation(userId: str, delta: int) -> None:
        # increment or decrement reputation score
        User.collection.update_one(
            {"_id": ObjectId(userId)},
            {"$inc": {"reputation": delta}},
        )