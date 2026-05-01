from core.db import (
    users,
    forum_categories,
    forum_subcategories,
    forum_topics,
    forum_posts,
    forum_replies,
    forum_votes,
    forum_bookmarks,
    forum_notifications,
)
from bson import ObjectId
import datetime


class User:

    collection = users

    @staticmethod
    def create(full_name, email, role, career):
        doc = {
            "fullName":   full_name,
            "email":      email,
            "role":       role,
            "career":     career,
            "createdAt":  datetime.datetime.utcnow(),
            "reputation": 0,
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
    def get_by_id(user_id):
        result = users.find_one({"_id": ObjectId(user_id)})

        print("[DEBUG] User.get_by_id -> user_id:", user_id)
        print("[DEBUG] Result:", result)

        return result



    @staticmethod
    def add_reputation(user_id, points):
        result = users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"reputation": points}}
        )

        print("[DEBUG] User.add_reputation -> user_id:", user_id)
        print("[DEBUG] points:", points)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)


    @staticmethod
    def get_all():
        result = list(users.find())

        print("[DEBUG] User.get_all -> total:", len(result))

        return result


    @staticmethod
    def get_by_name(full_name):
        result = list(users.find({"fullName": {"$regex": full_name, "$options": "i"}}))

        print("[DEBUG] User.get_by_name -> full_name:", full_name)
        print("[DEBUG] Result count:", len(result))

        return result



class ForumCategory:
    collection = forum_categories

    @staticmethod
    def create(name, description=""):
        doc = {
            "name":        name,
            "description": description,
            "createdAt":   datetime.datetime.utcnow(),
        }
        result = forum_categories.insert_one(doc)

        print("[DEBUG] ForumCategory.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_all():
        result = list(forum_categories.find())

        print("[DEBUG] ForumCategory.get_all -> total:", len(result))

        return result

    @staticmethod
    def get_by_name(name):
        result = list(forum_categories.find({"name": {"$regex": name, "$options": "i"}}))

        print("[DEBUG] ForumCategory.get_by_name -> name:", name)
        print("[DEBUG] Result count:", len(result))

        return result





class ForumSubcategory:
    collection = forum_subcategories

    @staticmethod
    def create(category_id, name):
        doc = {
            "categoryId": ObjectId(category_id),
            "name":       name,
            "createdAt":  datetime.datetime.utcnow(),
        }
        result = forum_subcategories.insert_one(doc)

        print("[DEBUG] ForumSubcategory.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)



    @staticmethod
    def get_by_category(category_id):
        result = list(forum_subcategories.find({"categoryId": ObjectId(category_id)}))

        print("[DEBUG] ForumSubcategory.get_by_category -> category_id:", category_id)
        print("[DEBUG] Result count:", len(result))

        return result


    @staticmethod
    def get_all():
        result = list(forum_subcategories.find())

        print("[DEBUG] ForumSubcategory.get_all -> total:", len(result))

        return result




class ForumTopic:
    collection = forum_topics

    @staticmethod
    def create(subcategory_id, name):
        doc = {
            "subcategoryId": ObjectId(subcategory_id),
            "name":          name,
            "createdAt":     datetime.datetime.utcnow(),
        }
        result = forum_topics.insert_one(doc)

        print("[DEBUG] ForumTopic.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_by_subcategory(subcategory_id):
        result = list(forum_topics.find({"subcategoryId": ObjectId(subcategory_id)}))

        print("[DEBUG] ForumTopic.get_by_subcategory -> subcategory_id:", subcategory_id)
        print("[DEBUG] Result count:", len(result))

        return result

    @staticmethod
    def get_all():
        result = list(forum_posts.find().sort("createdAt", -1))

        print("[DEBUG] ForumTopic.get_all -> total:", len(result))

        return result

    @staticmethod
    def get_by_title(title):
        result = list(forum_posts.find({"title": {"$regex": title, "$options": "i"}}))

        print("[DEBUG] ForumTopic.get_by_title -> title:", title)
        print("[DEBUG] Result count:", len(result))

        return result





class ForumPost:
    collection = forum_posts

    @staticmethod
    def create(author_id, title, content, category_id,
               subcategory_id=None, topic_id=None, tags=None):
        doc = {
            "authorId":      ObjectId(author_id),
            "title":         title,
            "content":       content,
            "categoryId":    ObjectId(category_id),
            "subcategoryId": ObjectId(subcategory_id) if subcategory_id else None,
            "topicId":       ObjectId(topic_id) if topic_id else None,
            "tags":          tags or [],
            "answersCount":  0,
            "score":         0.0,
            "status":        "open",
            "duplicatedFrom": None,
            "aiSuggested":   False,
            "createdAt":     datetime.datetime.utcnow(),
            "updatedAt":     datetime.datetime.utcnow(),
        }
        result = forum_posts.insert_one(doc)

        print("[DEBUG] ForumPost.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)


    @staticmethod
    def get_by_id(post_id):
        result = forum_posts.find_one({"_id": ObjectId(post_id)})

        print("[DEBUG] ForumPost.get_by_id -> post_id:", post_id)
        print("[DEBUG] Result:", result)

        return result



    @staticmethod
    def get_by_category(category_id, status="open"):
        result = list(
            forum_posts.find({"categoryId": ObjectId(category_id), "status": status})
            .sort("createdAt", -1)
        )

        print("[DEBUG] ForumPost.get_by_category -> category_id:", category_id, "status:", status)
        print("[DEBUG] Result count:", len(result))

        return result



    @staticmethod
    def update_status(post_id, status):
        result = forum_posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"status": status, "updatedAt": datetime.datetime.utcnow()}}
        )

        print("[DEBUG] ForumPost.update_status -> post_id:", post_id, "status:", status)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)




    @staticmethod
    def increment_answers(post_id):
        result = forum_posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"answersCount": 1}}
        )

        print("[DEBUG] ForumPost.increment_answers -> post_id:", post_id)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)


    @staticmethod
    def mark_as_duplicate(post_id, original_post_id):
        result = forum_posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {
                "duplicatedFrom": ObjectId(original_post_id),
                "status":         "closed",
                "updatedAt":      datetime.datetime.utcnow(),
            }}
        )

        print("[DEBUG] ForumPost.mark_as_duplicate -> post_id:", post_id, "original_post_id:", original_post_id)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)

    @staticmethod
    def get_all():
        result = list(forum_replies.find().sort("createdAt", -1))

        print("[DEBUG] ForumPost.get_all -> total:", len(result))

        return result

    @staticmethod
    def get_by_content(text):
        result = list(forum_replies.find({"content": {"$regex": text, "$options": "i"}}))

        print("[DEBUG] ForumPost.get_by_content -> text:", text)
        print("[DEBUG] Result count:", len(result))

        return result







class ForumReply:
    collection = forum_replies

    @staticmethod
    def create(post_id, author_id, content, ai_generated=False):
        doc = {
            "postId":       ObjectId(post_id),
            "authorId":     ObjectId(author_id),
            "content":      content,
            "isAccepted":   False,
            "score":        0.0,
            "aiGenerated":  ai_generated,
            "createdAt":    datetime.datetime.utcnow(),
            "updatedAt":    datetime.datetime.utcnow(),
        }
        result = forum_replies.insert_one(doc)
        ForumPost.increment_answers(post_id)

        print("[DEBUG] ForumReply.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)



    @staticmethod
    def get_by_post(post_id):
        result = list(
            forum_replies.find({"postId": ObjectId(post_id)}).sort("createdAt", 1)
        )

        print("[DEBUG] ForumReply.get_by_post -> post_id:", post_id)
        print("[DEBUG] Result count:", len(result))

        return result


    @staticmethod
    def accept(reply_id, post_id):
        result = forum_replies.update_one(
            {"_id": ObjectId(reply_id)},
            {"$set": {"isAccepted": True}}
        )
        ForumPost.update_status(post_id, "resolved")

        print("[DEBUG] ForumReply.accept -> reply_id:", reply_id, "post_id:", post_id)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)

    @staticmethod
    def get_all():
        result = list(forum_replies.find().sort("createdAt", -1))

        print("[DEBUG] ForumReply.get_all -> total:", len(result))

        return result

    @staticmethod
    def get_by_content(text):
        result = list(forum_replies.find({"content": {"$regex": text, "$options": "i"}}))

        print("[DEBUG] ForumReply.get_by_content -> text:", text)
        print("[DEBUG] Result count:", len(result))

        return result







class ForumVote:
    collection = forum_votes

    @staticmethod
    def create(user_id, target_id, rating):
        doc = {
            "userId":    ObjectId(user_id),
            "targetId":  ObjectId(target_id),
            "rating":    rating,
            "createdAt": datetime.datetime.utcnow(),
        }
        result = forum_votes.insert_one(doc)

        print("[DEBUG] ForumVote.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)



    @staticmethod
    def get_average(target_id):
        pipeline = [
            {"$match": {"targetId": ObjectId(target_id)}},
            {"$group": {"_id": "$targetId", "avg": {"$avg": "$rating"}}}
        ]
        result = list(forum_votes.aggregate(pipeline))

        avg = result[0]["avg"] if result else 0.0

        print("[DEBUG] ForumVote.get_average -> target_id:", target_id)
        print("[DEBUG] average:", avg)

        return avg





class ForumBookmark:
    collection = forum_bookmarks

    @staticmethod
    def create(user_id, post_id):
        doc = {
            "userId":    ObjectId(user_id),
            "postId":    ObjectId(post_id),
            "createdAt": datetime.datetime.utcnow(),
        }
        result = forum_bookmarks.insert_one(doc)

        print("[DEBUG] ForumBookmark.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)


    @staticmethod
    def get_by_user(user_id):
        result = list(forum_bookmarks.find({"userId": ObjectId(user_id)}))

        print("[DEBUG] ForumBookmark.get_by_user -> user_id:", user_id)
        print("[DEBUG] Result count:", len(result))

        return result


    @staticmethod
    def delete(user_id, post_id):
        result = forum_bookmarks.delete_one({
            "userId": ObjectId(user_id),
            "postId": ObjectId(post_id),
        })

        print("[DEBUG] ForumBookmark.delete -> user_id:", user_id, "post_id:", post_id)
        print("[DEBUG] deleted:", result.deleted_count)




class ForumNotification:
    collection = forum_notifications

    @staticmethod
    def create(user_id, type_, reference_id):
        doc = {
            "userId":      ObjectId(user_id),
            "type":        type_,
            "referenceId": ObjectId(reference_id),
            "read":        False,
            "createdAt":   datetime.datetime.utcnow(),
        }
        result = forum_notifications.insert_one(doc)

        print("[DEBUG] ForumNotification.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_unread(user_id):
        result = list(
            forum_notifications.find({"userId": ObjectId(user_id), "read": False})
            .sort("createdAt", -1)
        )

        print("[DEBUG] ForumNotification.get_unread -> user_id:", user_id)
        print("[DEBUG] Result count:", len(result))

        return result

    @staticmethod
    def mark_as_read(notification_id):
        result = forum_notifications.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"read": True}}
        )

        print("[DEBUG] ForumNotification.mark_as_read -> notification_id:", notification_id)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)