from typing import Any, Dict, List, Optional

from django.conf import settings

from assistant.models import ChatSession, ChatSummary, Conversation, IndexedBook
from assistant.services.external_search_service import ExternalSearchService
from assistant.services.ingestion_service import IngestionService
from assistant.services.rag_service import RAGService
from forum.models import ForumSubcategory, ForumTopic
from core.ai_manager import AIManager


class ChatService:
    """Business logic for the academic chat assistant (mirrors forum service layer)."""

    def __init__(self):
        self.rag = RAGService()
        self.ingestion = IngestionService()
        self.external = ExternalSearchService()

    # --- Config ---

    def get_subjects(self) -> List[Dict[str, Any]]:
        subs = ForumSubcategory.get_all()
        return [
            {
                "id": str(s["_id"]),
                "categoryId": str(s["categoryId"]),
                "name": s.get("name", ""),
            }
            for s in subs
        ]

    def get_topics_by_subject(self, subcategory_id: str) -> List[Dict[str, Any]]:
        topics = ForumTopic.get_by_subcategory(subcategory_id)
        return [
            {
                "id": str(t["_id"]),
                "subcategoryId": str(t["subcategoryId"]),
                "name": t.get("name", ""),
            }
            for t in topics
        ]

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        sessions = ChatSession.get_by_user(user_id)
        return [self._serialize_session(s) for s in sessions]

    def get_books_for_subject(self, subcategory_id: str) -> List[Dict[str, Any]]:
        return self.ingestion.get_uploaded_books(subcategory_id)

    # --- Sessions ---

    def create_session(
        self,
        user_id: str,
        chat_name: str,
        subcategory_id: str,
        topic_id: str = None,
        pdf_file=None,
    ) -> Dict[str, Any]:
        if not chat_name.strip():
            chat_name = "Nueva consulta académica"

        chat_id = ChatSession.create(
            userId=user_id,
            chatName=chat_name.strip(),
            subcategoryId=subcategory_id,
            topicId=topic_id,
        )

        ingestion_result = None
        if pdf_file:
            ingestion_result = self.ingestion.process_pdf(
                pdf_file,
                subcategory_id=subcategory_id,
                topic_id=topic_id,
                uploaded_by=user_id,
            )

        session = ChatSession.get_by_id(chat_id)
        return {
            "session": self._serialize_session(session),
            "ingestion": ingestion_result,
        }

    def get_session_detail(self, chat_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if not ChatSession.belongs_to_user(chat_id, user_id):
            return None

        session = ChatSession.get_by_id(chat_id)
        messages = self.get_messages(chat_id)
        summary = ChatSummary.get_by_chat(chat_id)

        return {
            "session": self._serialize_session(session),
            "messages": messages,
            "summary": self._serialize_summary(summary) if summary else None,
        }

    # --- Messages ---

    def get_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        rows = Conversation.get_by_chat(chat_id)
        return [self._serialize_message(r) for r in rows]

    def send_message(self, chat_id: str, user_id: str, prompt: str) -> Dict[str, Any]:
        session = ChatSession.get_by_id(chat_id)
        if not session or not ChatSession.belongs_to_user(chat_id, user_id):
            raise PermissionError("Sesión de chat no encontrada o sin permiso.")

        prompt = prompt.strip()
        if not prompt:
            raise ValueError("El mensaje no puede estar vacío.")

        subcategory_id = str(session["subcategoryId"])
        topic_id = str(session["topicId"]) if session.get("topicId") else None

        rag_result = self.rag.generate_augmented_response(
            query=prompt,
            subcategory_id=subcategory_id,
            topic_id=topic_id,
        )

        ChatSession.touch(chat_id)
        chat_name = session.get("chatName", "Chat")

        if rag_result.get("contextInsufficient"):
            message_id, _ = Conversation.create(
                chatId=chat_id,
                chatName=chat_name,
                promptSent=prompt,
                aiResponse="",
                sources=rag_result.get("sourceFragments", []),
                contextInsufficient=True,
            )
            summary = self._maybe_refresh_summary(chat_id, chat_name)
            return {
                "messageId": message_id,
                "answer": "",
                "sources": rag_result.get("sourceFragments", []),
                "sourcesLabel": rag_result.get("sources", ""),
                "contextInsufficient": True,
                "summary": summary,
            }

        message_id, _ = Conversation.create(
            chatId=chat_id,
            chatName=chat_name,
            promptSent=prompt,
            aiResponse=rag_result["answer"],
            sources=rag_result.get("sourceFragments", []),
            contextInsufficient=False,
        )

        summary = self._maybe_refresh_summary(chat_id, chat_name)

        return {
            "messageId": message_id,
            "answer": rag_result["answer"],
            "sources": rag_result.get("sourceFragments", []),
            "sourcesLabel": rag_result.get("sources", ""),
            "contextInsufficient": False,
            "summary": summary,
        }

    def external_search(self, chat_id: str, user_id: str, prompt: str, source: str = "wikipedia") -> Dict[str, Any]:
        session = ChatSession.get_by_id(chat_id)
        if not session or not ChatSession.belongs_to_user(chat_id, user_id):
            raise PermissionError("Sesión de chat no encontrada o sin permiso.")

        prompt = prompt.strip()
        if not prompt:
            raise ValueError("El mensaje no puede estar vacío.")

        ext = self.external.generate_external_response(prompt, source=source)
        chat_name = session.get("chatName", "Chat")

        message_id, _ = Conversation.create(
            chatId=chat_id,
            chatName=chat_name,
            promptSent=prompt,
            aiResponse=ext["answer"],
            sources=[],
            contextInsufficient=ext.get("contextInsufficient", False),
            externalSource=ext.get("externalSource"),
        )

        ChatSession.touch(chat_id)
        summary = self._maybe_refresh_summary(chat_id, chat_name)

        return {
            "messageId": message_id,
            "answer": ext["answer"],
            "externalSource": ext.get("externalSource"),
            "contextInsufficient": ext.get("contextInsufficient", False),
            "summary": summary,
        }

    def rate_message(self, chat_id: str, user_id: str, message_ref: str, rating: int) -> bool:
        if not ChatSession.belongs_to_user(chat_id, user_id):
            raise PermissionError("Sesión de chat no encontrada o sin permiso.")

        rating = int(rating)
        if rating < 1 or rating > 10:
            raise ValueError("La calificación debe estar entre 1 y 10.")

        return Conversation.update_rating(chat_id, message_ref, rating)

    # --- Summary ---

    def _maybe_refresh_summary(self, chat_id: str, chat_name: str) -> Optional[Dict[str, Any]]:
        count = Conversation.count_by_chat(chat_id)
        every_n = getattr(settings, "CHAT_SUMMARY_EVERY_N", 3)
        if count == 0 or count % every_n != 0:
            return self._serialize_summary(ChatSummary.get_by_chat(chat_id))

        messages = Conversation.get_by_chat(chat_id)
        transcript = []
        for m in messages[-every_n * 2:]:
            transcript.append(f"Estudiante: {m.get('promptSent', '')}")
            transcript.append(f"Asistente: {m.get('aiResponse', '')}")

        llm = AIManager.get_llm_service()
        prompt = (
            "Resume en español (máximo 120 palabras) la conversación académica siguiente. "
            "Destaca conceptos clave y preguntas pendientes.\n\n"
            + "\n".join(transcript)
        )
        summary_text = llm.generate(prompt)
        ChatSummary.upsert(chat_id, chat_name, summary_text)
        return self._serialize_summary(ChatSummary.get_by_chat(chat_id))

    # --- Serializers ---

    @staticmethod
    def _serialize_session(obj: dict) -> Dict[str, Any]:
        if not obj:
            return {}
        return {
            "chatId": obj["chatId"],
            "chatName": obj.get("chatName", ""),
            "userId": str(obj["userId"]),
            "subcategoryId": str(obj["subcategoryId"]),
            "topicId": str(obj["topicId"]) if obj.get("topicId") else None,
            "createdAt": obj["createdAt"].isoformat(),
            "updatedAt": obj["updatedAt"].isoformat(),
            "messageCount": Conversation.count_by_chat(obj["chatId"]),
        }

    @staticmethod
    def _serialize_message(obj: dict) -> Dict[str, Any]:
        return {
            "messageId": obj.get("messageId", str(obj.get("_id", ""))),
            "chatId": obj["chatId"],
            "promptSent": obj.get("promptSent", ""),
            "aiResponse": obj.get("aiResponse", ""),
            "sources": obj.get("sources", []),
            "contextInsufficient": obj.get("contextInsufficient", False),
            "externalSource": obj.get("externalSource"),
            "userRating": obj.get("userRating"),
            "timestamp": obj["timestamp"].isoformat(),
        }

    @staticmethod
    def _serialize_summary(obj: dict) -> Optional[Dict[str, Any]]:
        if not obj:
            return None
        return {
            "chatId": obj["chatId"],
            "summaryText": obj.get("summaryText", ""),
            "lastUpdated": obj["lastUpdated"].isoformat(),
        }
