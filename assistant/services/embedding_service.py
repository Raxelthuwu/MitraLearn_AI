from django.conf import settings
from langchain_huggingface import HuggingFaceEmbeddings
from assistant.interfaces.embedding_interface import IEmbeddingService

class HuggingFaceEmbeddingService(IEmbeddingService):
    """
    Concrete implementation of the Embedding Service using HuggingFace.
    """

    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self._embeddings = None

    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
        return self._embeddings

    def embed_query(self, text: str):
        """Generates embedding for a single query."""
        return self.embeddings.embed_query(text)

    def embed(self, text: str):
        """Alias for embed_query — used by forum similarity services."""
        return self.embed_query(text)

    def embed_documents(self, texts: list):
        """Generates embeddings for a list of documents."""
        return self.embeddings.embed_documents(texts)

    def get_model_name(self):
        """Returns the configured model name."""
        return self.model_name
