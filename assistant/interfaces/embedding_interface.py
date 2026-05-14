from abc import ABC, abstractmethod

class IEmbeddingService(ABC):
    """
    Interface for Embedding Services.
    Defines the contract for generating text embeddings.
    """

    @abstractmethod
    def embed_query(self, text: str):
        """Generates embedding for a single query string."""
        pass

    @abstractmethod
    def embed_documents(self, texts: list):
        """Generates embeddings for a list of document strings."""
        pass

    @abstractmethod
    def get_model_name(self):
        """Returns the name of the model being used."""
        pass
