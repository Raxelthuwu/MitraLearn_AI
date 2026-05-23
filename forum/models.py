from core.db import (
    users,
    forum_categories as forumCategories,
    forum_subcategories as forumSubcategories,
    forum_topics as forumTopics,
    forum_posts as forumPosts,
    forum_replies as forumReplies,
    forum_votes as forumVotes,
    forum_bookmarks as forumBookmarks,
    forum_notifications as forumNotifications,
)

from bson import ObjectId
import datetime


class User:

    collection = users

    @staticmethod
    def create(fullName, email, role, career):
        doc = {
            "fullName": fullName,
            "email": email,
            "role": role,
            "career": career,
            "createdAt": datetime.datetime.utcnow(),
            "reputation": int(0),
        }

        result = users.insert_one(doc)

        print("[DEBUG] User.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_by_email(email):
        result = users.find_one({"email": email})

        print("[DEBUG] User.get_by_email -> email:", email)
        print("[DEBUG] Result:", result)

        return result

    @staticmethod
    def get_by_id(userId):
        result = users.find_one({"_id": ObjectId(userId)})

        print("[DEBUG] User.get_by_id -> userId:", userId)
        print("[DEBUG] Result:", result)

        return result

    @staticmethod
    def add_reputation(userId, points):
        result = users.update_one(
            {"_id": ObjectId(userId)},
            {"$inc": {"reputation": int(points)}}
        )

        print("[DEBUG] User.add_reputation -> userId:", userId)
        print("[DEBUG] points:", points)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)

    @staticmethod
    def get_all():
        result = list(users.find())

        print("[DEBUG] User.get_all -> total:", len(result))

        return result

    @staticmethod
    def get_by_name(fullName):
        result = list(
            users.find({"fullName": {"$regex": fullName, "$options": "i"}})
        )

        print("[DEBUG] User.get_by_name -> fullName:", fullName)
        print("[DEBUG] Result count:", len(result))

        return result


class ForumCategory:

    collection = forumCategories

    @staticmethod
    def create(name, description=""):
        doc = {
            "name": name,
            "description": description,
            "createdAt": datetime.datetime.utcnow(),
        }

        result = forumCategories.insert_one(doc)

        print("[DEBUG] ForumCategory.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_all():
        result = list(forumCategories.find())

        print("[DEBUG] ForumCategory.get_all -> total:", len(result))

        return result

    @staticmethod
    def get_by_name(name):
        result = list(
            forumCategories.find({"name": {"$regex": name, "$options": "i"}})
        )

        print("[DEBUG] ForumCategory.get_by_name -> name:", name)
        print("[DEBUG] Result count:", len(result))

        return result


class ForumSubcategory:

    collection = forumSubcategories

    @staticmethod
    def create(categoryId, name):
        doc = {
            "categoryId": ObjectId(categoryId),
            "name": name,
            "createdAt": datetime.datetime.utcnow(),
        }

        result = forumSubcategories.insert_one(doc)

        print("[DEBUG] ForumSubcategory.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_by_category(categoryId):
        result = list(
            forumSubcategories.find({"categoryId": ObjectId(categoryId)})
        )

        print("[DEBUG] ForumSubcategory.get_by_category -> categoryId:", categoryId)
        print("[DEBUG] Result count:", len(result))

        return result

    @staticmethod
    def get_all():
        result = list(forumSubcategories.find())

        print("[DEBUG] ForumSubcategory.get_all -> total:", len(result))

        return result


class ForumTopic:

    collection = forumTopics

    @staticmethod
    def create(subcategoryId, name):
        doc = {
            "subcategoryId": ObjectId(subcategoryId),
            "name": name,
            "createdAt": datetime.datetime.utcnow(),
        }

        result = forumTopics.insert_one(doc)

        print("[DEBUG] ForumTopic.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_by_subcategory(subcategoryId):
        result = list(
            forumTopics.find({"subcategoryId": ObjectId(subcategoryId)})
        )

        print("[DEBUG] ForumTopic.get_by_subcategory -> subcategoryId:", subcategoryId)
        print("[DEBUG] Result count:", len(result))

        return result

    @staticmethod
    def get_all():
        result = list(forumTopics.find().sort("createdAt", -1))

        print("[DEBUG] ForumTopic.get_all -> total:", len(result))

        return result

    @staticmethod
    def get_by_name(name):
        result = list(
            forumTopics.find({"name": {"$regex": name, "$options": "i"}})
        )

        print("[DEBUG] ForumTopic.get_by_name -> name:", name)
        print("[DEBUG] Result count:", len(result))

        return result


class ForumPost:

    collection = forumPosts

    @staticmethod
    def create(
        authorId,
        title,
        content,
        categoryId,
        subcategoryId=None,
        topicId=None,
        tags=None
    ):
        doc = {
            "authorId": ObjectId(authorId),
            "title": title,
            "content": content,
            "categoryId": ObjectId(categoryId),
            "subcategoryId": ObjectId(subcategoryId) if subcategoryId else None,
            "topicId": ObjectId(topicId) if topicId else None,
            "tags": tags or [],
            "answersCount": int(0),
            "score": float(0.0),
            "status": "open",
            "duplicatedFrom": None,
            "aiSuggested": False,
            "createdAt": datetime.datetime.utcnow(),
            "updatedAt": datetime.datetime.utcnow(),
        }

        result = forumPosts.insert_one(doc)

        print("[DEBUG] ForumPost.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_by_id(postId):
        result = forumPosts.find_one({"_id": ObjectId(postId)})

        print("[DEBUG] ForumPost.get_by_id -> postId:", postId)
        print("[DEBUG] Result:", result)

        return result

    @staticmethod
    def get_by_category(categoryId, status="open"):
        result = list(
            forumPosts.find({
                "categoryId": ObjectId(categoryId),
                "status": status
            }).sort("createdAt", -1)
        )

        print("[DEBUG] ForumPost.get_by_category -> categoryId:", categoryId, "status:", status)
        print("[DEBUG] Result count:", len(result))

        return result

    @staticmethod
    def update_status(postId, status):
        result = forumPosts.update_one(
            {"_id": ObjectId(postId)},
            {
                "$set": {
                    "status": status,
                    "updatedAt": datetime.datetime.utcnow()
                }
            }
        )

        print("[DEBUG] ForumPost.update_status -> postId:", postId, "status:", status)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)

    @staticmethod
    def increment_answers(postId):
        result = forumPosts.update_one(
            {"_id": ObjectId(postId)},
            {"$inc": {"answersCount": int(1)}}
        )

        print("[DEBUG] ForumPost.increment_answers -> postId:", postId)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)

    @staticmethod
    def mark_as_duplicate(postId, originalPostId):
        result = forumPosts.update_one(
            {"_id": ObjectId(postId)},
            {
                "$set": {
                    "duplicatedFrom": ObjectId(originalPostId),
                    "status": "closed",
                    "updatedAt": datetime.datetime.utcnow(),
                }
            }
        )

        print("[DEBUG] ForumPost.mark_as_duplicate -> postId:", postId, "originalPostId:", originalPostId)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)

    @staticmethod
    def get_all():
        result = list(forumPosts.find().sort("createdAt", -1))

        print("[DEBUG] ForumPost.get_all -> total:", len(result))

        return result

    @staticmethod
    def get_by_content(text):
        result = list(
            forumPosts.find({"content": {"$regex": text, "$options": "i"}})
        )

        print("[DEBUG] ForumPost.get_by_content -> text:", text)
        print("[DEBUG] Result count:", len(result))

        return result


class ForumReply:

    collection = forumReplies

    @staticmethod
    def create(postId, authorId, content, aiGenerated=False):
        doc = {
            "postId": ObjectId(postId),
            "authorId": ObjectId(authorId),
            "content": content,
            "isAccepted": False,
            "score": float(0.0),
            "aiGenerated": aiGenerated,
            "createdAt": datetime.datetime.utcnow(),
            "updatedAt": datetime.datetime.utcnow(),
        }

        result = forumReplies.insert_one(doc)

        ForumPost.increment_answers(postId)

        print("[DEBUG] ForumReply.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_by_post(postId):
        result = list(
            forumReplies.find({"postId": ObjectId(postId)})
            .sort("createdAt", 1)
        )

        print("[DEBUG] ForumReply.get_by_post -> postId:", postId)
        print("[DEBUG] Result count:", len(result))

        return result

    @staticmethod
    def accept(replyId, postId):
        result = forumReplies.update_one(
            {"_id": ObjectId(replyId)},
            {"$set": {"isAccepted": True}}
        )

        ForumPost.update_status(postId, "resolved")

        print("[DEBUG] ForumReply.accept -> replyId:", replyId, "postId:", postId)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)

    @staticmethod
    def get_all():
        result = list(forumReplies.find().sort("createdAt", -1))

        print("[DEBUG] ForumReply.get_all -> total:", len(result))

        return result

    @staticmethod
    def get_by_content(text):
        result = list(
            forumReplies.find({"content": {"$regex": text, "$options": "i"}})
        )

        print("[DEBUG] ForumReply.get_by_content -> text:", text)
        print("[DEBUG] Result count:", len(result))

        return result


class ForumVote:

    collection = forumVotes

    @staticmethod
    def create(userId, targetId, rating):
        doc = {
            "userId": ObjectId(userId),
            "targetId": ObjectId(targetId),
            "rating": int(rating),
            "createdAt": datetime.datetime.utcnow(),
        }

        result = forumVotes.insert_one(doc)

        print("[DEBUG] ForumVote.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_average(targetId):
        pipeline = [
            {"$match": {"targetId": ObjectId(targetId)}},
            {"$group": {"_id": "$targetId", "avg": {"$avg": "$rating"}}}
        ]

        result = list(forumVotes.aggregate(pipeline))

        avg = result[0]["avg"] if result else 0.0

        print("[DEBUG] ForumVote.get_average -> targetId:", targetId)
        print("[DEBUG] average:", avg)

        return avg
    
    @staticmethod
    def get_user_vote_on_target(userId, targetId):
        return forumVotes.find_one({
            "userId": ObjectId(userId),
            "targetId": ObjectId(targetId)
        })

    @staticmethod
    def update_vote(voteId, rating):
        forumVotes.update_one(
            {"_id": ObjectId(voteId)},
            {"$set": {"rating": int(rating)}}
        )

    @staticmethod
    def delete_vote(userId, targetId):
        forumVotes.delete_one({
            "userId": ObjectId(userId),
            "targetId": ObjectId(targetId)
        })

class ForumBookmark:

    collection = forumBookmarks

    @staticmethod
    def create(userId, postId):
        doc = {
            "userId": ObjectId(userId),
            "postId": ObjectId(postId),
            "createdAt": datetime.datetime.utcnow(),
        }

        result = forumBookmarks.insert_one(doc)

        print("[DEBUG] ForumBookmark.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_by_user(userId):
        result = list(
            forumBookmarks.find({"userId": ObjectId(userId)})
        )

        print("[DEBUG] ForumBookmark.get_by_user -> userId:", userId)
        print("[DEBUG] Result count:", len(result))

        return result

    @staticmethod
    def delete(userId, postId):
        result = forumBookmarks.delete_one({
            "userId": ObjectId(userId),
            "postId": ObjectId(postId),
        })

        print("[DEBUG] ForumBookmark.delete -> userId:", userId, "postId:", postId)
        print("[DEBUG] deleted:", result.deleted_count)


class ForumNotification:

    collection = forumNotifications

    @staticmethod
    def create(userId, type, referenceId):
        doc = {
            "userId": ObjectId(userId),
            "type": type,
            "referenceId": ObjectId(referenceId),
            "read": False,
            "createdAt": datetime.datetime.utcnow(),
        }

        result = forumNotifications.insert_one(doc)

        print("[DEBUG] ForumNotification.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_unread(userId):
        result = list(
            forumNotifications.find({
                "userId": ObjectId(userId),
                "read": False
            }).sort("createdAt", -1)
        )

        print("[DEBUG] ForumNotification.get_unread -> userId:", userId)
        print("[DEBUG] Result count:", len(result))

        return result

    @staticmethod
    def mark_as_read(notificationId):
        result = forumNotifications.update_one(
            {"_id": ObjectId(notificationId)},
            {"$set": {"read": True}}
        )

        print("[DEBUG] ForumNotification.mark_as_read -> notificationId:", notificationId)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)