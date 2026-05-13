from typing import Any, Dict, List, Optional

from login.interface import IAuthService
from login.models import User


class AuthService(IAuthService):

    def register(
        self,
        fullName: str,
        email:    str,
        password: str,
        career:   str,
        role:     str,
        phone:    str,
    ) -> Dict[str, Any]:
        # reject if email already taken
        if User.emailExists(email):
            return {"ok": False, "error": "Email is already registered."}

        if len(password) < 6:
            return {"ok": False, "error": "Password must be at least 6 characters."}

        if role not in ("student", "teacher", "admin"):
            role = "student"

        userId = User.create(
            fullName = fullName,
            email    = email,
            password = password,
            career   = career,
            role     = role,
            phone    = phone,
        )

        return {"ok": True, "userId": userId}

    def login(self, email: str, password: str) -> Dict[str, Any]:
        # find user and verify bcrypt hash
        user = User.getByEmail(email)

        if not user:
            return {"ok": False, "error": "Invalid email or password."}

        if not User.verifyPassword(password, user["password"]):
            return {"ok": False, "error": "Invalid email or password."}

        return {
            "ok":       True,
            "userId":   str(user["_id"]),
            "fullName": user["fullName"],
            "role":     user["role"],
            "career":   user["career"],
        }

    def getSessionUser(self, userId: str) -> Optional[Dict[str, Any]]:
        # return minimal profile for the active session
        user = User.getById(userId)
        if not user:
            return None
        return User.serialize(user)

    def getUserById(self, userId: str) -> Optional[Dict[str, Any]]:
        # return full user profile by id
        user = User.getById(userId)
        return User.serialize(user) if user else None

    def getAllUsers(self) -> List[Dict[str, Any]]:
        # return all users as serialized list
        return [User.serialize(u) for u in User.getAll()]

    def updateUser(self, userId: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # update user fields and return updated profile
        updated = User.update(userId, payload)
        return User.serialize(updated) if updated else None

    def deleteUser(self, userId: str) -> bool:
        # permanently delete user account
        return User.delete(userId)