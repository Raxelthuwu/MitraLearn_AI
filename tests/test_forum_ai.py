import unittest
import os
import sys
from pathlib import Path
from bson import ObjectId

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')
django.setup()

from forum.models import ForumVote, ForumPost
from forum.ForumVectorModels import ForumEmbedding
from core import AIManager

class TestForumAIFeatures(unittest.TestCase):
    """
    Test suite for Forum-specific AI and Rating features.
    Verifies similarity search and rating averages.
    """

    def test_01_rating_average(self):
        """Verify that the rating system calculates averages correctly."""
        test_post_id = ObjectId()
        user_1 = ObjectId()
        user_2 = ObjectId()
        
        # Create two votes for the same post
        ForumVote.create(userId=user_1, targetId=test_post_id, rating=5)
        ForumVote.create(userId=user_2, targetId=test_post_id, rating=3)
        
        # Calculate average
        avg = ForumVote.get_average(test_post_id)
        
        # 5 + 3 = 8 / 2 = 4.0
        self.assertEqual(avg, 4.0, f"Expected average 4.0, got {avg}")
        print(f"[SUCCESS] Rating average verified: {avg}")

    def test_02_forum_similarity_search(self):
        """Verify the Forum's similarity search using embeddings."""
        # 1. Initialize AI Motor
        emb_service = AIManager.get_embedding_service()
        
        # 2. Add a sample question to the forum vector DB
        test_id = "test_q_123"
        test_text = "How to implement inheritance in Python?"
        embedding = emb_service.embed_query(test_text)
        
        ForumEmbedding.add(
            embed_id=test_id,
            embedding=embedding,
            document_text=test_text,
            post_id=ObjectId(),
            type_="question",
            topic="Python",
            category="Academic"
        )
        
        # 3. Search for a similar question
        query_text = "inheritance examples in python"
        query_emb = emb_service.embed_query(query_text)
        
        results = ForumEmbedding.search(query_emb, n_results=1)
        
        # Verify results
        self.assertIn(test_id, results['ids'][0], "Search should find the related question")
        print(f"[SUCCESS] Forum similarity search found the correct item.")

if __name__ == '__main__':
    unittest.main()
