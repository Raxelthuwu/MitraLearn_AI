from django.conf import settings
from langchain_huggingface import HuggingFaceEmbeddings
from assistant.interfaces.embedding_interface import IEmbeddingService

class HuggingFaceEmbeddingService(IEmbeddingService):
    """
    Concrete implementation of the Embedding Service using HuggingFace.
    """

    def __init__(self):
        # Load model name from global Django settings
        self.model_name = settings.EMBEDDING_MODEL
        self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)

    def embed_query(self, text: str):
        """Generates embedding for a single query."""
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: list):
        """Generates embeddings for a list of documents."""
        return self.embeddings.embed_documents(texts)

    def get_model_name(self):
        """Returns the configured model name."""
        return self.model_name
