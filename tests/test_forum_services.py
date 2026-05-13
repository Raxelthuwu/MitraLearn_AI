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

from forum.services.forumService import (
    ForumPostService, ForumReplyService, ForumVoteService, 
    ForumCategoryService, ForumSubcategoryService, ForumTopicService
)
from forum.models import User

class TestForumBusinessLogic(unittest.TestCase):
    """
    Fixed test suite for Forum Business Logic.
    Satisfies strict MongoDB Schema requirements (no null IDs).
    """

    def setUp(self):
        self.post_service = ForumPostService()
        self.reply_service = ForumReplyService()
        self.vote_service = ForumVoteService()
        self.cat_service = ForumCategoryService()
        self.sub_service = ForumSubcategoryService()
        self.topic_service = ForumTopicService()

    def test_01_reputation_and_vote_logic(self):
        """Test that voting updates user reputation and post score."""
        author_id = User.create("Author", "author_serv@test.com", "student", "CS")
        voter_id = User.create("Voter", "voter_serv@test.com", "student", "CS")
        
        # Build Hierarchy (Required for Schema)
        cat = self.cat_service.createCategory("Academic Service Test")
        sub = self.sub_service.createSubcategory(cat['id'], "Sub Service Test")
        topic = self.topic_service.createTopic(sub['id'], "Topic Service Test")
        
        # Create Post with all required IDs
        post = self.post_service.createPost(
            author_id, "Title", "Content", 
            categoryId=cat['id'], 
            subcategoryId=sub['id'], 
            topicId=topic['id']
        )
        
        # Cast a vote of 5
        self.vote_service.castVote(voter_id, post['id'], 5)
        
        # Check Author reputation
        author = User.get_by_id(author_id)
        self.assertEqual(author['reputation'], 5)
        print("[SUCCESS] Reputation verified.")

    def test_02_counters_on_delete(self):
        """Verify counters satisfy schema and logic."""
        author_id = User.create("CounterUser", "counter@test.com", "student", "CS")
        cat = self.cat_service.createCategory("Counter Cat")
        sub = self.sub_service.createSubcategory(cat['id'], "Counter Sub")
        topic = self.topic_service.createTopic(sub['id'], "Counter Topic")
        
        post = self.post_service.createPost(
            author_id, "Title", "Content", 
            categoryId=cat['id'], 
            subcategoryId=sub['id'], 
            topicId=topic['id']
        )
        
        # Create and delete reply
        reply = self.reply_service.createReply(post['id'], author_id, "Reply content")
        self.assertEqual(self.post_service.getPostById(post['id'])['answersCount'], 1)
        
        self.reply_service.deleteReply(reply['id'])
        self.assertEqual(self.post_service.getPostById(post['id'])['answersCount'], 0)
        print("[SUCCESS] Counter logic verified.")

if __name__ == '__main__':
    unittest.main()
