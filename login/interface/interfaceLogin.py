from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IAuthService(ABC):

    @abstractmethod
    def register(
        self,
        fullName: str,
        email:    str,
        password: str,
        career:   str,
        role:     str,
        phone:    str,
    ) -> Dict[str, Any]:
        # create a new user account
        pass

    @abstractmethod
    def login(self, email: str, password: str) -> Dict[str, Any]:
        # verify credentials and return session data
        pass

    @abstractmethod
    def getSessionUser(self, userId: str) -> Optional[Dict[str, Any]]:
        # return minimal user data for an active session
        pass

    @abstractmethod
    def getUserById(self, userId: str) -> Optional[Dict[str, Any]]:
        # return full user profile by id
        pass

    @abstractmethod
    def getAllUsers(self) -> List[Dict[str, Any]]:
        # return all registered users
        pass

    @abstractmethod
    def updateUser(self, userId: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # update allowed user fields and return updated document
        pass

    @abstractmethod
    def deleteUser(self, userId: str) -> bool:
        # permanently delete a user account
        pass