from core.db import (
    conversations,
    chat_summaries as chatSummaries,
    chat_sessions as chatSessions,
    indexed_books as indexedBooks,
)
from bson import ObjectId
import datetime
import uuid


class ChatSession:
    collection = chatSessions

    @staticmethod
    def create(userId, chatName, subcategoryId, topicId=None):
        chat_id = str(uuid.uuid4())
        doc = {
            "chatId": chat_id,
            "userId": ObjectId(userId),
            "chatName": chatName,
            "subcategoryId": ObjectId(subcategoryId),
            "topicId": ObjectId(topicId) if topicId else None,
            "createdAt": datetime.datetime.utcnow(),
            "updatedAt": datetime.datetime.utcnow(),
        }
        chatSessions.insert_one(doc)
        print("[DEBUG] ChatSession.create ->", chat_id)
        return chat_id

    @staticmethod
    def get_by_id(chatId):
        return chatSessions.find_one({"chatId": chatId})

    @staticmethod
    def get_by_user(userId):
        return list(
            chatSessions.find({"userId": ObjectId(userId)}).sort("updatedAt", -1)
        )

    @staticmethod
    def touch(chatId):
        chatSessions.update_one(
            {"chatId": chatId},
            {"$set": {"updatedAt": datetime.datetime.utcnow()}},
        )

    @staticmethod
    def belongs_to_user(chatId, userId):
        session = ChatSession.get_by_id(chatId)
        if not session:
            return False
        return str(session["userId"]) == str(userId)


class IndexedBook:
    collection = indexedBooks

    @staticmethod
    def create(filename, subcategoryId, topicId, chunkCount, uploadedBy, storedPath):
        book_id = str(uuid.uuid4())
        doc = {
            "bookId": book_id,
            "filename": filename,
            "subcategoryId": ObjectId(subcategoryId),
            "topicId": ObjectId(topicId) if topicId else None,
            "chunkCount": int(chunkCount),
            "storedPath": storedPath,
            "createdAt": datetime.datetime.utcnow(),
        }
        if uploadedBy and ObjectId.is_valid(str(uploadedBy)):
            doc["uploadedBy"] = ObjectId(uploadedBy)
        indexedBooks.insert_one(doc)
        print("[DEBUG] IndexedBook.create ->", book_id, "chunks:", chunkCount)
        return book_id

    @staticmethod
    def get_by_subcategory(subcategoryId):
        return list(
            indexedBooks.find({"subcategoryId": ObjectId(subcategoryId)}).sort("createdAt", -1)
        )

    @staticmethod
    def get_by_id(bookId):
        return indexedBooks.find_one({"bookId": bookId})


class Conversation:
    collection = conversations

    @staticmethod
    def create(chatId, chatName, promptSent, aiResponse, userRating=None, sources=None, contextInsufficient=False, externalSource=None):
        message_id = str(uuid.uuid4())
        doc = {
            "messageId": message_id,
            "chatId": chatId,
            "chatName": chatName,
            "timestamp": datetime.datetime.utcnow(),
            "promptSent": promptSent,
            "aiResponse": aiResponse,
            "sources": sources or [],
            "contextInsufficient": bool(contextInsufficient),
            "externalSource": externalSource,
        }

        if userRating is not None:
            doc["userRating"] = int(userRating)

        result = conversations.insert_one(doc)
        print("[DEBUG] Conversation.create -> messageId:", message_id)
        return message_id, result.inserted_id

    @staticmethod
    def get_by_chat(chatId):
        return list(
            conversations.find({"chatId": chatId}).sort("timestamp", 1)
        )

    @staticmethod
    def count_by_chat(chatId):
        return conversations.count_documents({"chatId": chatId})

    @staticmethod
    def update_rating(chatId, timestamp, userRating):
        ts = timestamp
        if isinstance(ts, str):
            ts = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00").replace("+00:00", ""))

        result = conversations.update_one(
            {"chatId": chatId, "timestamp": ts},
            {"$set": {"userRating": int(userRating)}},
        )
        if result.modified_count == 0:
            result = conversations.update_one(
                {"chatId": chatId, "messageId": timestamp},
                {"$set": {"userRating": int(userRating)}},
            )
        print("[DEBUG] Conversation.update_rating -> modified:", result.modified_count)
        return result.modified_count > 0


class ChatSummary:
    collection = chatSummaries

    @staticmethod
    def create(chatId, chatName, summaryText):
        doc = {
            "chatId": chatId,
            "chatName": chatName,
            "lastUpdated": datetime.datetime.utcnow(),
            "summaryText": summaryText,
        }
        result = chatSummaries.insert_one(doc)
        print("[DEBUG] ChatSummary.create -> chatId:", chatId)
        return str(result.inserted_id)

    @staticmethod
    def get_by_chat(chatId):
        return chatSummaries.find_one({"chatId": chatId})

    @staticmethod
    def upsert(chatId, chatName, summaryText):
        existing = ChatSummary.get_by_chat(chatId)
        if existing:
            ChatSummary.update_chat_summary(chatId, summaryText)
            return str(existing["_id"])
        return ChatSummary.create(chatId, chatName, summaryText)

    @staticmethod
    def update_chat_summary(chatId, summaryText):
        result = chatSummaries.update_one(
            {"chatId": chatId},
            {
                "$set": {
                    "summaryText": summaryText,
                    "lastUpdated": datetime.datetime.utcnow(),
                }
            },
        )
        print("[DEBUG] ChatSummary.update_chat_summary -> modified:", result.modified_count)
