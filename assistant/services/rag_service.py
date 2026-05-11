import os
from django.conf import settings
from langchain_chroma import Chroma

class RAGService:
    """
    RAG (Retrieval-Augmented Generation) Service.
    Orchestrates the retrieval of documents from ChromaDB and 
    generates responses using the global LLM service.
    """

    def __init__(self):
        # Local import to avoid circular dependency
        from core.ai_manager import AIManager
        
        # Get global singleton instances from AIManager
        self.embedding_service = AIManager.get_embedding_service()
        self.llm_service = AIManager.get_llm_service()
        
        # Initialize Vector Database (ChromaDB)
        self.vector_db = Chroma(
            persist_directory=settings.CHROMA_PATH,
            embedding_function=self.embedding_service.embeddings
        )

    def retrieve_context(self, query: str, k: int = 3):
        """
        Retrieves the top k most relevant document chunks for the given query.
        """
        docs = self.vector_db.similarity_search(query, k=k)
        return "\n\n".join([doc.page_content for doc in docs])

    def generate_augmented_response(self, query: str):
        """
        Generates a response by combining retrieved context with the user query.
        """
        context = self.retrieve_context(query)
        
        # Build the RAG prompt
        prompt = f"""
        Use the following pieces of context to answer the question at the end.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.

        Context:
        {context}

        Question: {query}
        Answer:
        """
        
        return self.llm_service.generate_response(prompt)
