from core.db import conversations, chat_summaries
import datetime


class Conversation:
    collection = conversations

    @staticmethod
    def create(chat_id, chat_name, prompt_sent, ai_response, user_rating=None):
        doc = {
            "chatId":     chat_id,
            "chatName":   chat_name,
            "timestamp":  datetime.datetime.utcnow(),
            "promptSent": prompt_sent,
            "aiResponse": ai_response,
        }
        if user_rating is not None:
            doc["userRating"] = user_rating

        result = conversations.insert_one(doc)

        print("[DEBUG] Conversation.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)


    @staticmethod
    def get_by_chat(chat_id):
        result = list(
            conversations.find({"chatId": chat_id}).sort("timestamp", 1)
        )

        print("[DEBUG] Conversation.get_by_chat -> chat_id:", chat_id)
        print("[DEBUG] Result:", result)

        return result


    @staticmethod
    def update_rating(chat_id, timestamp, rating):
        result = conversations.update_one(
            {"chatId": chat_id, "timestamp": timestamp},
            {"$set": {"userRating": rating}}
        )

        print("[DEBUG] Conversation.update_rating -> chat_id:", chat_id)
        print("[DEBUG] timestamp:", timestamp)
        print("[DEBUG] rating:", rating)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)





class ChatSummary:
    collection = chat_summaries

    @staticmethod
    def create(chat_id, chat_name, summary_text):
        doc = {
            "chatId":      chat_id,
            "chatName":    chat_name,
            "lastUpdated": datetime.datetime.utcnow(),
            "summaryText": summary_text,
        }
        result = chat_summaries.insert_one(doc)

        print("[DEBUG] ChatSummary.create -> Inserted document:", doc)
        print("[DEBUG] Generated ID:", result.inserted_id)

        return str(result.inserted_id)





    @staticmethod
    def get_by_chat(chat_id):
        result = chat_summaries.find_one({"chatId": chat_id})

        print("[DEBUG] ChatSummary.get_by_chat -> chat_id:", chat_id)
        print("[DEBUG] Result:", result)

        return result



    @staticmethod
    def update_chat_summary(chat_id, summary_text):
        result = chat_summaries.update_one(
            {"chatId": chat_id},
            {"$set": {
                "summaryText": summary_text,
                "lastUpdated": datetime.datetime.utcnow(),
            }}
        )

        print("[DEBUG] ChatSummary.update_chat_summary -> chat_id:", chat_id)
        print("[DEBUG] summary_text:", summary_text)
        print("[DEBUG] matched:", result.matched_count, "modified:", result.modified_count)