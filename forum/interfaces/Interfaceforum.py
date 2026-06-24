from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


# Category management interface

class IForumCategoryService(ABC):

    @abstractmethod
    def createCategory(self, name: str, description: Optional[str]) -> Dict[str, Any]:
        # Create a new forum category and return its data
        pass

    @abstractmethod
    def getCategoryById(self, categoryId: str) -> Optional[Dict[str, Any]]:
        # Retrieve a single category by its ObjectId string
        pass

    @abstractmethod
    def getAllCategories(self) -> List[Dict[str, Any]]:
        # Return all available forum categories
        pass

    @abstractmethod
    def updateCategory(self, categoryId: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Update name or description of an existing category
        pass

    @abstractmethod
    def deleteCategory(self, categoryId: str) -> bool:
        # Delete a category; returns True if the operation succeeded
        pass



# Subcategory management interface
class IForumSubcategoryService(ABC):

    @abstractmethod
    def createSubcategory(self, categoryId: str, name: str) -> Dict[str, Any]:
        # Create a subcategory under a given category
        pass

    @abstractmethod
    def getSubcategoriesByCategory(self, categoryId: str) -> List[Dict[str, Any]]:
        # Return all subcategories that belong to a specific category
        pass

    @abstractmethod
    def getSubcategoryById(self, subcategoryId: str) -> Optional[Dict[str, Any]]:
        # Retrieve a single subcategory by its ObjectId string
        pass

    @abstractmethod
    def deleteSubcategory(self, subcategoryId: str) -> bool:
        # Delete a subcategory and cascade-remove its topics
        pass



# Topic management interface

class IForumTopicService(ABC):

    @abstractmethod
    def createTopic(self, subcategoryId: str, name: str) -> Dict[str, Any]:
        # Create a discussion topic inside a subcategory
        pass

    @abstractmethod
    def getTopicsBySubcategory(self, subcategoryId: str) -> List[Dict[str, Any]]:
        # List all topics that belong to a given subcategory
        pass

    @abstractmethod
    def getTopicById(self, topicId: str) -> Optional[Dict[str, Any]]:
        # Retrieve a single topic by its ObjectId string
        pass

    @abstractmethod
    def deleteTopic(self, topicId: str) -> bool:
        # Delete a topic; returns True if the operation succeeded
        pass


# Post (question) management interface

class IForumPostService(ABC):

    @abstractmethod
    def createPost(
        self,
        authorId: str,
        title: str,
        content: str,
        categoryId: str,
        subcategoryId: Optional[str],
        topicId: Optional[str],
        tags: Optional[List[str]],
    ) -> Dict[str, Any]:
        # Persist a new forum post and return its full data
        pass

    @abstractmethod
    def getPostById(self, postId: str) -> Optional[Dict[str, Any]]:
        # Fetch a single post with its metadata by ObjectId
        pass

    @abstractmethod
    def getPostsByCategory(
        self, categoryId: str, page: int, pageSize: int
    ) -> List[Dict[str, Any]]:
        # Return paginated posts for a given category
        pass

    @abstractmethod
    def getPostsByAuthor(self, authorId: str) -> List[Dict[str, Any]]:
        # Return all posts created by a specific user
        pass

    @abstractmethod
    def updatePostStatus(self, postId: str, status: str) -> Optional[Dict[str, Any]]:
        # Change the status of a post: open | resolved | closed
        pass

    @abstractmethod
    def updatePost(self, postId: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Edit the content or tags of an existing post
        pass

    @abstractmethod
    def deletePost(self, postId: str) -> bool:
        # Hard-delete a post and all its replies
        pass

    @abstractmethod
    def markAsDuplicate(self, postId: str, originalPostId: str) -> Optional[Dict[str, Any]]:
        # Flag a post as a duplicate and link it to the original
        pass

    @abstractmethod
    def flagAsAiSuggested(self, postId: str) -> Optional[Dict[str, Any]]:
        # Mark a post as generated or suggested by the AI layer
        pass

    @abstractmethod
    def incrementAnswersCount(self, postId: str) -> None:
        # Increment the denormalized answers counter on the post document
        pass

    @abstractmethod
    def updateScore(self, postId: str, newScore: float) -> None:
        # Recalculate and persist the aggregated vote score of a post
        pass



# Reply (answer) management interface
class IForumReplyService(ABC):

    @abstractmethod
    def createReply(
        self,
        postId: str,
        authorId: str,
        content: str,
        aiGenerated: bool,
    ) -> Dict[str, Any]:
        # Add a reply to a post; aiGenerated marks AI-authored answers
        pass

    @abstractmethod
    def getRepliesByPost(self, postId: str) -> List[Dict[str, Any]]:
        # Return all replies for a given post ordered by creation date
        pass

    @abstractmethod
    def getReplyById(self, replyId: str) -> Optional[Dict[str, Any]]:
        # Retrieve a single reply by its ObjectId string
        pass

    @abstractmethod
    def acceptReply(self, replyId: str, postId: str) -> Optional[Dict[str, Any]]:
        # Mark a reply as the accepted answer and close the post if needed
        pass

    @abstractmethod
    def updateReply(self, replyId: str, content: str) -> Optional[Dict[str, Any]]:
        # Edit the text content of an existing reply
        pass

    @abstractmethod
    def deleteReply(self, replyId: str) -> bool:
        # Remove a reply and decrement the post answers counter
        pass

    @abstractmethod
    def updateScore(self, replyId: str, newScore: float) -> None:
        # Recalculate and persist the aggregated vote score of a reply
        pass



# Vote management interface
class IForumVoteService(ABC):

    @abstractmethod
    def castVote(self, userId: str, targetId: str, rating: int) -> Dict[str, Any]:
        # Register or overwrite a vote from a user on a post or reply
        pass

    @abstractmethod
    def getVotesByTarget(self, targetId: str) -> List[Dict[str, Any]]:
        # Return all votes cast on a specific post or reply
        pass

    @abstractmethod
    def getUserVoteOnTarget(self, userId: str, targetId: str) -> Optional[Dict[str, Any]]:
        # Retrieve the vote a user cast on a particular target
        pass

    @abstractmethod
    def removeVote(self, userId: str, targetId: str) -> bool:
        # Delete a previously cast vote; returns True on success
        pass

    @abstractmethod
    def computeScore(self, targetId: str) -> float:
        # Aggregate all ratings for a target and return the computed score
        pass




# Bookmark management interface

class IForumBookmarkService(ABC):

    @abstractmethod
    def addBookmark(self, userId: str, postId: str) -> Dict[str, Any]:
        # Save a post to a user's bookmark list
        pass

    @abstractmethod
    def getBookmarksByUser(self, userId: str) -> List[Dict[str, Any]]:
        # Return all bookmarked posts for a given user
        pass

    @abstractmethod
    def removeBookmark(self, userId: str, postId: str) -> bool:
        # Delete a specific bookmark; returns True if it existed
        pass

    @abstractmethod
    def isBookmarked(self, userId: str, postId: str) -> bool:
        # Check whether a user has bookmarked a specific post
        pass



# Notification management interface

class IForumNotificationService(ABC):

    @abstractmethod
    def createNotification(
        self,
        userId: str,
        notificationType: str,
        referenceId: str,
    ) -> Dict[str, Any]:
        # Dispatch a notification of type: nueva respuesta | voto | mención | respuesta aceptada
        pass

    @abstractmethod
    def getNotificationsByUser(self, userId: str) -> List[Dict[str, Any]]:
        # Return all notifications belonging to a user
        pass

    @abstractmethod
    def getUnreadNotifications(self, userId: str) -> List[Dict[str, Any]]:
        # Return only unread notifications for a user
        pass

    @abstractmethod
    def markAsRead(self, notificationId: str) -> Optional[Dict[str, Any]]:
        # Mark a single notification as read
        pass

    @abstractmethod
    def markAllAsRead(self, userId: str) -> int:
        # Mark every unread notification for a user as read; returns count updated
        pass

    @abstractmethod
    def deleteNotification(self, notificationId: str) -> bool:
        # Remove a notification document permanently
        pass