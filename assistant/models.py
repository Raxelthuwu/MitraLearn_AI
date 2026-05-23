from core.db import conversations, chat_summaries as chatSummaries
import datetime


class Conversation:
    collection = conversations

    @staticmethod
    def create(chatId, chatName, promptSent, aiResponse, userRating=None):
        doc = {
            "chatId": chatId,
            "chatName": chatName,
            "timestamp": datetime.datetime.utcnow(),
            "promptSent": promptSent,
            "aiResponse": aiResponse,
        }

        if userRating is not None:
            doc["userRating"] = int(userRating)

        result = conversations.insert_one(doc)

        print("[DEBUG] Conversation.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_by_chat(chatId):
        result = list(
            conversations.find({"chatId": chatId}).sort("timestamp", 1)
        )

        print("[DEBUG] Conversation.get_by_chat -> chatId:", chatId)
        print("[DEBUG] Result:", result)

        return result

    @staticmethod
    def update_rating(chatId, timestamp, userRating):
        result = conversations.update_one(
            {
                "chatId": chatId,
                "timestamp": timestamp
            },
            {
                "$set": {
                    "userRating": int(userRating)
                }
            }
        )

        print("[DEBUG] Conversation.update_rating -> chatId:", chatId)
        print("[DEBUG] timestamp:", timestamp)
        print("[DEBUG] userRating:", userRating)
        print(
            "[DEBUG] matched:",
            result.matched_count,
            "modified:",
            result.modified_count
        )


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

        print("[DEBUG] ChatSummary.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)

    @staticmethod
    def get_by_chat(chatId):
        result = chatSummaries.find_one({"chatId": chatId})

        print("[DEBUG] ChatSummary.get_by_chat -> chatId:", chatId)
        print("[DEBUG] Result:", result)

        return result

    @staticmethod
    def update_chat_summary(chatId, summaryText):
        result = chatSummaries.update_one(
            {"chatId": chatId},
            {
                "$set": {
                    "summaryText": summaryText,
                    "lastUpdated": datetime.datetime.utcnow(),
                }
            }
        )

        print("[DEBUG] ChatSummary.update_chat_summary -> chatId:", chatId)
        print("[DEBUG] summaryText:", summaryText)
        print(
            "[DEBUG] matched:",
            result.matched_count,
            "modified:",
            result.modified_count
        )