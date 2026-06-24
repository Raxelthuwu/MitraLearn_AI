from core.vectorDB import chat_embeddings
import datetime


class ChatEmbedding:
    collection = chat_embeddings

    @staticmethod
    def add(chunk_id, embedding, document_text, source, page, subcategory_id=None, topic_id=None, book_id=None):
        metadata = {
            "source": source,
            "page": int(page) if page is not None else 0,
            "subcategory_id": str(subcategory_id) if subcategory_id else "",
            "topic_id": str(topic_id) if topic_id else "",
            "book_id": str(book_id) if book_id else "",
            "createdAt": datetime.datetime.utcnow().isoformat(),
        }

        chat_embeddings.add(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[document_text],
            metadatas=[metadata],
        )

    @staticmethod
    def _build_where(subcategory_id=None, topic_id=None, source=None):
        clauses = []
        if subcategory_id:
            clauses.append({"subcategory_id": str(subcategory_id)})
        if topic_id:
            clauses.append({"topic_id": str(topic_id)})
        if source:
            clauses.append({"source": source})

        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    @staticmethod
    def search(query_embedding, n_results=5, subcategory_id=None, topic_id=None, source=None):
        where = ChatEmbedding._build_where(subcategory_id, topic_id, source)

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        return chat_embeddings.query(**kwargs)

    @staticmethod
    def delete(chunk_id):
        chat_embeddings.delete(ids=[chunk_id])

    @staticmethod
    def count():
        return chat_embeddings.count()
