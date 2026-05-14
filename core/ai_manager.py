from django.conf import settings

class AIManager:
    """
    Global manager for AI services using the Singleton pattern.
    Provides centralized access to Embedding and LLM services.
    Imports are done inside methods to avoid circular dependencies.
    """
    _embedding_instance = None
    _llm_instance = None

    @classmethod
    def get_embedding_service(cls):
        """
        Returns the global singleton instance of the Embedding Service.
        """
        if cls._embedding_instance is None:
            # Local import to avoid circular dependency
            from assistant.services.embedding_service import HuggingFaceEmbeddingService
            cls._embedding_instance = HuggingFaceEmbeddingService()
        return cls._embedding_instance

    @classmethod
    def get_llm_service(cls):
        """
        Returns the global singleton instance of the LLM Service.
        """
        if cls._llm_instance is None:
            # Local import to avoid circular dependency
            from assistant.services.llm_service import OllamaLLMService
            cls._llm_instance = OllamaLLMService()
        return cls._llm_instance
