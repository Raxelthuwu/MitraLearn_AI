from typing import Any, Dict, List, Optional

from forum.interfaces import (
    IForumCategoryService,
    IForumSubcategoryService,
    IForumTopicService,
    IForumPostService,
    IForumReplyService,
    IForumVoteService,
    IForumBookmarkService,
    IForumNotificationService,
)

from forum.models import (
    ForumCategory,
    ForumSubcategory,
    ForumTopic,
    ForumPost,
    ForumReply,
    ForumVote,
    ForumBookmark,
    ForumNotification,
    User,
)


# Serializers
class Serializer:

    @staticmethod
    def category(obj: dict) -> Dict[str, Any]:
        return {
            "id": str(obj["_id"]),
            "name": obj["name"],
            "description": obj.get("description", ""),
            "createdAt": obj["createdAt"].isoformat(),
        }

    @staticmethod
    def subcategory(obj: dict) -> Dict[str, Any]:
        return {
            "id": str(obj["_id"]),
            "categoryId": str(obj["categoryId"]),
            "name": obj["name"],
            "createdAt": obj["createdAt"].isoformat(),
        }

    @staticmethod
    def topic(obj: dict) -> Dict[str, Any]:
        return {
            "id": str(obj["_id"]),
            "subcategoryId": str(obj["subcategoryId"]),
            "name": obj["name"],
            "createdAt": obj["createdAt"].isoformat(),
        }

    @staticmethod
    def post(obj: dict) -> Dict[str, Any]:
        return {
            "id": str(obj["_id"]),
            "authorId": str(obj["authorId"]),
            "title": obj["title"],
            "content": obj["content"],
            "categoryId": str(obj["categoryId"]),
            "subcategoryId": str(obj["subcategoryId"]) if obj.get("subcategoryId") else None,
            "topicId": str(obj["topicId"]) if obj.get("topicId") else None,
            "tags": obj.get("tags", []),
            "answersCount": obj.get("answersCount", 0),
            "score": obj.get("score", 0.0),
            "status": obj.get("status", "open"),
            "duplicatedFrom": str(obj["duplicatedFrom"]) if obj.get("duplicatedFrom") else None,
            "aiSuggested": obj.get("aiSuggested", False),
            "createdAt": obj["createdAt"].isoformat(),
            "updatedAt": obj["updatedAt"].isoformat(),
        }

    @staticmethod
    def reply(obj: dict) -> Dict[str, Any]:
        return {
            "id": str(obj["_id"]),
            "postId": str(obj["postId"]),
            "authorId": str(obj["authorId"]),
            "content": obj["content"],
            "isAccepted": obj.get("isAccepted", False),
            "score": obj.get("score", 0.0),
            "aiGenerated": obj.get("aiGenerated", False),
            "createdAt": obj["createdAt"].isoformat(),
            "updatedAt": obj["updatedAt"].isoformat(),
        }

    @staticmethod
    def vote(obj: dict) -> Dict[str, Any]:
        return {
            "id": str(obj["_id"]),
            "userId": str(obj["userId"]),
            "targetId": str(obj["targetId"]),
            "rating": obj["rating"],
            "createdAt": obj["createdAt"].isoformat(),
        }

    @staticmethod
    def bookmark(obj: dict) -> Dict[str, Any]:
        return {
            "id": str(obj["_id"]),
            "userId": str(obj["userId"]),
            "postId": str(obj["postId"]),
            "createdAt": obj["createdAt"].isoformat(),
        }

    @staticmethod
    def notification(obj: dict) -> Dict[str, Any]:
        return {
            "id": str(obj["_id"]),
            "userId": str(obj["userId"]),
            "type": obj["type"],
            "referenceId": str(obj["referenceId"]),
            "read": obj.get("read", False),
            "createdAt": obj["createdAt"].isoformat(),
        }


# CategoryService
class ForumCategoryService(IForumCategoryService):

    def createCategory(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        from bson import ObjectId
        categoryId = ForumCategory.create(
            name=name,
            description=description or ""
        )
        obj = ForumCategory.collection.find_one({"_id": ObjectId(categoryId)})
        return Serializer.category(obj)

    def getCategoryById(self, categoryId: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        obj = ForumCategory.collection.find_one({"_id": ObjectId(categoryId)})
        return Serializer.category(obj) if obj else None

    def getAllCategories(self) -> List[Dict[str, Any]]:
        return [Serializer.category(obj) for obj in ForumCategory.get_all()]

    def updateCategory(self, categoryId: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        allowed = {"name", "description"}
        update = {k: v for k, v in payload.items() if k in allowed}
        if not update:
            return None
        ForumCategory.collection.update_one(
            {"_id": ObjectId(categoryId)},
            {"$set": update}
        )
        obj = ForumCategory.collection.find_one({"_id": ObjectId(categoryId)})
        return Serializer.category(obj) if obj else None

    def deleteCategory(self, categoryId: str) -> bool:
        from bson import ObjectId
        result = ForumCategory.collection.delete_one({"_id": ObjectId(categoryId)})
        return result.deleted_count > 0


# SubcategoryService
class ForumSubcategoryService(IForumSubcategoryService):

    def createSubcategory(self, categoryId: str, name: str) -> Dict[str, Any]:
        from bson import ObjectId
        subcategoryId = ForumSubcategory.create(categoryId=categoryId, name=name)
        obj = ForumSubcategory.collection.find_one({"_id": ObjectId(subcategoryId)})
        return Serializer.subcategory(obj)

    def getSubcategoriesByCategory(self, categoryId: str) -> List[Dict[str, Any]]:
        return [Serializer.subcategory(obj) for obj in ForumSubcategory.get_by_category(categoryId)]

    def getSubcategoryById(self, subcategoryId: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        obj = ForumSubcategory.collection.find_one({"_id": ObjectId(subcategoryId)})
        return Serializer.subcategory(obj) if obj else None

    def deleteSubcategory(self, subcategoryId: str) -> bool:
        from bson import ObjectId
        result = ForumSubcategory.collection.delete_one({"_id": ObjectId(subcategoryId)})
        return result.deleted_count > 0


# TopicService
class ForumTopicService(IForumTopicService):

    def createTopic(self, subcategoryId: str, name: str) -> Dict[str, Any]:
        from bson import ObjectId
        topicId = ForumTopic.create(subcategoryId=subcategoryId, name=name)
        obj = ForumTopic.collection.find_one({"_id": ObjectId(topicId)})
        return Serializer.topic(obj)

    def getTopicsBySubcategory(self, subcategoryId: str) -> List[Dict[str, Any]]:
        return [Serializer.topic(obj) for obj in ForumTopic.get_by_subcategory(subcategoryId)]

    def getTopicById(self, topicId: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        obj = ForumTopic.collection.find_one({"_id": ObjectId(topicId)})
        return Serializer.topic(obj) if obj else None

    def deleteTopic(self, topicId: str) -> bool:
        from bson import ObjectId
        result = ForumTopic.collection.delete_one({"_id": ObjectId(topicId)})
        return result.deleted_count > 0


# PostService
class ForumPostService(IForumPostService):

    def createPost(
        self,
        authorId: str,
        title: str,
        content: str,
        categoryId: str,
        subcategoryId: Optional[str] = None,
        topicId: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        postId = ForumPost.create(
            authorId=authorId,
            title=title,
            content=content,
            categoryId=categoryId,
            subcategoryId=subcategoryId,
            topicId=topicId,
            tags=tags or [],
        )
        obj = ForumPost.get_by_id(postId)
        return Serializer.post(obj)

    def getPostById(self, postId: str) -> Optional[Dict[str, Any]]:
        obj = ForumPost.get_by_id(postId)
        return Serializer.post(obj) if obj else None

    def getPostsByCategory(
        self,
        categoryId: str,
        page: int = 1,
        pageSize: int = 20
    ) -> List[Dict[str, Any]]:
        all_posts = ForumPost.get_by_category(categoryId)
        offset = (page - 1) * pageSize
        return [Serializer.post(obj) for obj in all_posts[offset: offset + pageSize]]

    def getPostsByAuthor(self, authorId: str) -> List[Dict[str, Any]]:
        from bson import ObjectId
        objs = list(
            ForumPost.collection.find({"authorId": ObjectId(authorId)})
            .sort("createdAt", -1)
        )
        return [Serializer.post(obj) for obj in objs]

    def updatePostStatus(self, postId: str, status: str) -> Optional[Dict[str, Any]]:
        ForumPost.update_status(postId, status)
        obj = ForumPost.get_by_id(postId)
        return Serializer.post(obj) if obj else None

    def updatePost(self, postId: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        import datetime
        allowed = {"title", "content", "tags"}
        update = {k: v for k, v in payload.items() if k in allowed}
        if not update:
            return None
        update["updatedAt"] = datetime.datetime.utcnow()
        ForumPost.collection.update_one(
            {"_id": ObjectId(postId)},
            {"$set": update}
        )
        obj = ForumPost.get_by_id(postId)
        return Serializer.post(obj) if obj else None

    def deletePost(self, postId: str) -> bool:
        from bson import ObjectId
        result = ForumPost.collection.delete_one({"_id": ObjectId(postId)})
        return result.deleted_count > 0

    def markAsDuplicate(self, postId: str, originalPostId: str) -> Optional[Dict[str, Any]]:
        ForumPost.mark_as_duplicate(postId, originalPostId)
        obj = ForumPost.get_by_id(postId)
        return Serializer.post(obj) if obj else None

    def flagAsAiSuggested(self, postId: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        import datetime
        ForumPost.collection.update_one(
            {"_id": ObjectId(postId)},
            {"$set": {"aiSuggested": True, "updatedAt": datetime.datetime.utcnow()}}
        )
        obj = ForumPost.get_by_id(postId)
        return Serializer.post(obj) if obj else None

    def incrementAnswersCount(self, postId: str) -> None:
        ForumPost.increment_answers(postId)

    def updateScore(self, postId: str, newScore: float) -> None:
        from bson import ObjectId
        ForumPost.collection.update_one(
            {"_id": ObjectId(postId)},
            {"$set": {"score": float(newScore)}}
        )


# ReplyService
class ForumReplyService(IForumReplyService):

    def createReply(
        self,
        postId: str,
        authorId: str,
        content: str,
        aiGenerated: bool = False,
    ) -> Dict[str, Any]:
        from bson import ObjectId
        replyId = ForumReply.create(
            postId=postId,
            authorId=authorId,
            content=content,
            aiGenerated=aiGenerated,
        )
        obj = ForumReply.collection.find_one({"_id": ObjectId(replyId)})
        return Serializer.reply(obj)

    def getRepliesByPost(self, postId: str) -> List[Dict[str, Any]]:
        return [Serializer.reply(obj) for obj in ForumReply.get_by_post(postId)]

    def getReplyById(self, replyId: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        obj = ForumReply.collection.find_one({"_id": ObjectId(replyId)})
        return Serializer.reply(obj) if obj else None

    def acceptReply(self, replyId: str, postId: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        ForumReply.accept(replyId, postId)
        obj = ForumReply.collection.find_one({"_id": ObjectId(replyId)})
        return Serializer.reply(obj) if obj else None

    def updateReply(self, replyId: str, content: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        import datetime
        ForumReply.collection.update_one(
            {"_id": ObjectId(replyId)},
            {"$set": {"content": content, "updatedAt": datetime.datetime.utcnow()}}
        )
        obj = ForumReply.collection.find_one({"_id": ObjectId(replyId)})
        return Serializer.reply(obj) if obj else None

    def deleteReply(self, replyId: str) -> bool:
        from bson import ObjectId
        obj = ForumReply.collection.find_one({"_id": ObjectId(replyId)})
        if not obj:
            return False
        postId = str(obj["postId"])
        ForumReply.collection.delete_one({"_id": ObjectId(replyId)})
        ForumPost.collection.update_one(
            {"_id": ObjectId(postId)},
            {"$inc": {"answersCount": -1}}
        )
        return True

    def updateScore(self, replyId: str, newScore: float) -> None:
        from bson import ObjectId
        ForumReply.collection.update_one(
            {"_id": ObjectId(replyId)},
            {"$set": {"score": float(newScore)}}
        )


# VoteService
class ForumVoteService(IForumVoteService):

    def castVote(self, userId: str, targetId: str, rating: int) -> Dict[str, Any]:
        existing = ForumVote.get_user_vote_on_target(userId, targetId)

        if existing:
            old_rating = existing["rating"]
            ForumVote.update_vote(existing["_id"], rating)
            delta = rating - old_rating
        else:
            ForumVote.create(userId, targetId, rating)
            delta = rating

        score = ForumVote.get_average(targetId)

        self._updateScore(targetId, score)

        author_id = self._getAuthor(targetId)
        if author_id:
            User.add_reputation(author_id, delta)

        return {
            "userId": userId,
            "targetId": targetId,
            "rating": rating,
            "score": score,
        }

    def _getAuthor(self, targetId: str) -> Optional[str]:
        post = ForumPost.get_by_id(targetId)
        if post:
            return str(post["authorId"])
        from bson import ObjectId
        reply = ForumReply.collection.find_one({"_id": ObjectId(targetId)})
        if reply:
            return str(reply["authorId"])
        return None

    def _updateScore(self, targetId: str, score: float) -> None:
        from bson import ObjectId
        post = ForumPost.get_by_id(targetId)
        if post:
            ForumPost.collection.update_one(
                {"_id": ObjectId(targetId)},
                {"$set": {"score": float(score)}}
            )
            return
        reply = ForumReply.collection.find_one({"_id": ObjectId(targetId)})
        if reply:
            ForumReply.collection.update_one(
                {"_id": ObjectId(targetId)},
                {"$set": {"score": float(score)}}
            )

    def getVotesByTarget(self, targetId: str) -> List[Dict[str, Any]]:
        from bson import ObjectId
        objs = list(ForumVote.collection.find({"targetId": ObjectId(targetId)}))
        return [Serializer.vote(obj) for obj in objs]

    def getUserVoteOnTarget(self, userId: str, targetId: str) -> Optional[Dict[str, Any]]:
        obj = ForumVote.get_user_vote_on_target(userId, targetId)
        return Serializer.vote(obj) if obj else None

    def removeVote(self, userId: str, targetId: str) -> bool:
        existing = ForumVote.get_user_vote_on_target(userId, targetId)
        if not existing:
            return False

        rating = existing["rating"]
        ForumVote.delete_vote(userId, targetId)

        score = ForumVote.get_average(targetId)
        self._updateScore(targetId, score)

        author_id = self._getAuthor(targetId)
        if author_id:
            User.add_reputation(author_id, -rating)

        return True

    def computeScore(self, targetId: str) -> float:
        return ForumVote.get_average(targetId)


# BookmarkService
class ForumBookmarkService(IForumBookmarkService):

    def addBookmark(self, userId: str, postId: str) -> Dict[str, Any]:
        from bson import ObjectId
        existing = ForumBookmark.collection.find_one({
            "userId": ObjectId(userId),
            "postId": ObjectId(postId),
        })
        if existing:
            return Serializer.bookmark(existing)
        bookmarkId = ForumBookmark.create(userId=userId, postId=postId)
        obj = ForumBookmark.collection.find_one({"_id": ObjectId(bookmarkId)})
        return Serializer.bookmark(obj)

    def getBookmarksByUser(self, userId: str) -> List[Dict[str, Any]]:
        return [Serializer.bookmark(obj) for obj in ForumBookmark.get_by_user(userId)]

    def removeBookmark(self, userId: str, postId: str) -> bool:
        from bson import ObjectId
        result = ForumBookmark.collection.delete_one({
            "userId": ObjectId(userId),
            "postId": ObjectId(postId),
        })
        return result.deleted_count > 0

    def isBookmarked(self, userId: str, postId: str) -> bool:
        from bson import ObjectId
        return ForumBookmark.collection.find_one({
            "userId": ObjectId(userId),
            "postId": ObjectId(postId),
        }) is not None


# NotificationService
class ForumNotificationService(IForumNotificationService):

    def createNotification(
        self,
        userId: str,
        notificationType: str,
        referenceId: str,
    ) -> Dict[str, Any]:
        from bson import ObjectId
        notificationId = ForumNotification.create(
            userId=userId,
            type=notificationType,
            referenceId=referenceId,
        )
        obj = ForumNotification.collection.find_one({"_id": ObjectId(notificationId)})
        return Serializer.notification(obj)

    def getNotificationsByUser(self, userId: str) -> List[Dict[str, Any]]:
        from bson import ObjectId
        objs = list(
            ForumNotification.collection
            .find({"userId": ObjectId(userId)})
            .sort("createdAt", -1)
        )
        return [Serializer.notification(obj) for obj in objs]

    def getUnreadNotifications(self, userId: str) -> List[Dict[str, Any]]:
        return [Serializer.notification(obj) for obj in ForumNotification.get_unread(userId)]

    def markAsRead(self, notificationId: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        ForumNotification.mark_as_read(notificationId)
        obj = ForumNotification.collection.find_one({"_id": ObjectId(notificationId)})
        return Serializer.notification(obj) if obj else None

    def markAllAsRead(self, userId: str) -> int:
        from bson import ObjectId
        result = ForumNotification.collection.update_many(
            {"userId": ObjectId(userId), "read": False},
            {"$set": {"read": True}}
        )
        return result.modified_count

    def deleteNotification(self, notificationId: str) -> bool:
        from bson import ObjectId
        result = ForumNotification.collection.delete_one({"_id": ObjectId(notificationId)})
        return result.deleted_count > 0