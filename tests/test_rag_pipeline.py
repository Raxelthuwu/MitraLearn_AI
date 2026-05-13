import unittest
import os
import django
from django.conf import settings

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')
django.setup()

from assistant.services.rag_service import RAGService

class TestRAGPipeline(unittest.TestCase):
    """
    Test suite for the RAG (Retrieval-Augmented Generation) pipeline.
    """

    def setUp(self):
        """Initialize the RAG service."""
        try:
            self.rag_service = RAGService()
        except Exception as e:
            self.skipTest(f"RAG Service initialization failed: {e}. Check if ChromaDB path is valid.")

    def test_rag_initialization(self):
        """
        Verify that RAG service initializes with the correct dependencies.
        """
        self.assertIsNotNone(self.rag_service.llm_service, "LLM service should be initialized")
        self.assertIsNotNone(self.rag_service.embedding_service, "Embedding service should be initialized")
        self.assertIsNotNone(self.rag_service.vector_db, "Vector database should be initialized")

    def test_retrieve_context_structure(self):
        """
        Test that retrieve_context returns a string (even if empty if no docs are indexed).
        """
        query = "How to use MitraLearn?"
        context = self.rag_service.retrieve_context(query, k=1)
        self.assertIsInstance(context, str, "Context should be a string")

if __name__ == '__main__':
    unittest.main()
