import os
from django.conf import settings
from langchain_chroma import Chroma

class RAGService:
    """
    RAG (Retrieval-Augmented Generation) Service.
    Orchestrates the retrieval of documents from ChromaDB and 
    generates responses with academic references.
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
            embedding_function=self.embedding_service.embeddings,
            collection_name="chat_embeddings"
        )

    def retrieve_with_sources(self, query: str, k: int = 4):
        """
        Retrieves relevant documents and extracts their metadata (source and page).
        """
        docs = self.vector_db.similarity_search(query, k=k)
        
        context_text = ""
        sources = []
        
        for doc in docs:
            context_text += f"\n{doc.page_content}\n"
            
            # Extract metadata (filename and page)
            source_path = doc.metadata.get("source", "Unknown Source")
            source_name = os.path.basename(source_path)
            page_number = doc.metadata.get("page", "Unknown Page")
            
            # Add unique sources
            source_info = {"book": source_name, "page": page_number}
            if source_info not in sources:
                sources.append(source_info)
                
        return context_text, sources

    def generate_augmented_response(self, query: str):
        """
        Generates a response including a list of academic sources.
        Returns: Dict { 'answer': str, 'sources': list }
        """
        context, sources = self.retrieve_with_sources(query)
        
        # Build the RAG prompt
        prompt = f"""
        You are an academic assistant. Use the following pieces of context to answer the user question.
        If the answer is not in the context, say that you don't know based on the books.
        Always be precise and professional.

        Context:
        {context}

        Question: {query}
        Answer:
        """
        
        answer = self.llm_service.generate_response(prompt)
        
        return {
            "answer": answer,
            "sources": sources
        }
