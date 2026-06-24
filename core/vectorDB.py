import os

import chromadb
from django.conf import settings

CHAT_COLLECTION = "chat_embeddings"
FORUM_COLLECTION = "forum_embeddings"

CHAT_COLLECTION_META = {
    "description": "Vectorized fragments of books and academic guides for Systems Engineering program",
    "embedding_model": "BAAI/bge-m3",
    "embedding_dimensions": 1024,
    "hnsw:space": "cosine",
}

FORUM_COLLECTION_META = {
    "description": "Vectorized forum questions, answers, and summaries for semantic search and duplicate detection",
    "embedding_model": "BAAI/bge-m3",
    "embedding_dimensions": 1024,
    "hnsw:space": "cosine",
}

_client = None


def resolve_chroma_path() -> str:
    path = settings.CHROMA_PATH
    if not os.path.isabs(path):
        path = os.path.join(settings.BASE_DIR, path)
    return path


def get_client():
    """Singleton ChromaDB client (path absoluto al proyecto)."""
    global _client
    if _client is None:
        chroma_path = resolve_chroma_path()
        print("[DEBUG] Initializing ChromaDB client with path:", chroma_path)
        _client = chromadb.PersistentClient(path=chroma_path)
    return _client


def get_chat_embeddings():
    """Obtiene la colección actual; evita IDs obsoletos tras limpiar/recrear."""
    print("[DEBUG] Resolving collection:", CHAT_COLLECTION)
    return get_client().get_or_create_collection(
        name=CHAT_COLLECTION,
        metadata=CHAT_COLLECTION_META,
    )


def get_forum_embeddings():
    print("[DEBUG] Resolving collection:", FORUM_COLLECTION)
    return get_client().get_or_create_collection(
        name=FORUM_COLLECTION,
        metadata=FORUM_COLLECTION_META,
    )


class _CollectionProxy:
    """Redirige cada operación a una referencia fresca de la colección."""

    def __init__(self, getter):
        self._getter = getter

    def __getattr__(self, name):
        return getattr(self._getter(), name)


chat_embeddings = _CollectionProxy(get_chat_embeddings)
forum_embeddings = _CollectionProxy(get_forum_embeddings)

print("[DEBUG] ChromaDB collection proxies ready")
