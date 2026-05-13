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

from core import AIManager

class TestAIServices(unittest.TestCase):
    """
    Test suite for AI Services and Global Manager.
    """

    def setUp(self):
        """Set up the AI Manager instance."""
        self.ai_manager = AIManager

    def test_singleton_behavior(self):
        """
        Verify that AIManager returns the same instance (Singleton).
        """
        llm_1 = self.ai_manager.get_llm_service()
        llm_2 = self.ai_manager.get_llm_service()
        self.assertIs(llm_1, llm_2, "LLM Service should be a singleton instance")

        emb_1 = self.ai_manager.get_embedding_service()
        emb_2 = self.ai_manager.get_embedding_service()
        self.assertIs(emb_1, emb_2, "Embedding Service should be a singleton instance")

    def test_embedding_dimension(self):
        """
        Verify that the embedding model returns the correct vector dimension (1024 for bge-m3).
        """
        emb_service = self.ai_manager.get_embedding_service()
        test_text = "Probing AI services dimension"
        vector = emb_service.embed_query(test_text)
        
        self.assertEqual(len(vector), 1024, f"Expected 1024 dimensions, got {len(vector)}")

    def test_llm_model_name(self):
        """
        Verify that the LLM is configured with the correct model name (gemma2).
        """
        llm_service = self.ai_manager.get_llm_service()
        self.assertEqual(llm_service.get_model_name(), "gemma2")

if __name__ == '__main__':
    unittest.main()
