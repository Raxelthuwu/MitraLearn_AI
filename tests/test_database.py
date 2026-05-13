import unittest
import os
import django
import time
from bson import ObjectId

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')
django.setup()

from forum.models import (
    User, ForumCategory, ForumSubcategory, ForumTopic, 
    ForumPost, ForumReply, ForumVote, ForumBookmark, ForumNotification
)
from assistant.models import Conversation, ChatSummary

class TestFullDatabaseIntegrity(unittest.TestCase):
    """
    Comprehensive test suite updated to match strict MongoDB Schema validation.
    """

    @classmethod
    def setUpClass(cls):
        # Unique timestamp for each test run to avoid duplicate key errors
        cls.ts = int(time.time())
        cls.test_user_id = None
        cls.test_cat_id = None
        cls.test_sub_id = None
        cls.test_topic_id = None
        cls.test_post_id = None

    def test_01_user_crud(self):
        """Verify User creation with a unique email."""
        user_id = User.create(
            fullName="Test Engineer",
            email=f"test_{self.ts}@mitralearn.com", # Dynamic email
            role="student",
            career="AI Engineering"
        )
        self.assertIsNotNone(user_id)
        TestFullDatabaseIntegrity.test_user_id = user_id

    def test_02_forum_hierarchy(self):
        """Verify the hierarchy: Category -> Subcategory -> Topic."""
        # Category
        cat_id = ForumCategory.create(name=f"AI_{self.ts}", description="Core AI topics")
        self.assertIsNotNone(cat_id)
        TestFullDatabaseIntegrity.test_cat_id = cat_id
        
        # Subcategory
        sub_id = ForumSubcategory.create(categoryId=cat_id, name="Deep Learning")
        self.assertIsNotNone(sub_id)
        TestFullDatabaseIntegrity.test_sub_id = sub_id
        
        # Topic
        topic_id = ForumTopic.create(subcategoryId=sub_id, name="Neural Networks")
        self.assertIsNotNone(topic_id)
        TestFullDatabaseIntegrity.test_topic_id = topic_id

    def test_03_post_and_replies(self):
        """Verify Post creation satisfying schema requirements."""
        user_id = TestFullDatabaseIntegrity.test_user_id
        cat_id = TestFullDatabaseIntegrity.test_cat_id
        sub_id = TestFullDatabaseIntegrity.test_sub_id
        topic_id = TestFullDatabaseIntegrity.test_topic_id
        
        # Post (Adding subcategory and topic to satisfy MongoDB validation)
        post_id = ForumPost.create(
            authorId=user_id,
            title=f"Transformer Guide {self.ts}",
            content="How do attention mechanisms work?",
            categoryId=cat_id,
            subcategoryId=sub_id,
            topicId=topic_id
        )
        self.assertIsNotNone(post_id)
        TestFullDatabaseIntegrity.test_post_id = post_id
        
        # Reply
        reply_id = ForumReply.create(
            postId=post_id,
            authorId=user_id,
            content="They weight the importance of different parts of the input data."
        )
        self.assertIsNotNone(reply_id)

    def test_04_engagement_features(self):
        """Verify Votes and Bookmarks."""
        user_id = TestFullDatabaseIntegrity.test_user_id
        post_id = TestFullDatabaseIntegrity.test_post_id
        
        # Vote
        vote_id = ForumVote.create(userId=user_id, targetId=post_id, rating=5)
        self.assertIsNotNone(vote_id)
        
        # Bookmark
        bookmark_id = ForumBookmark.create(userId=user_id, postId=post_id)
        self.assertIsNotNone(bookmark_id)

    def test_05_notifications_and_assistant(self):
        """Verify Notifications satisfying ENUM validation."""
        user_id = TestFullDatabaseIntegrity.test_user_id
        
        # Notification (Using allowed types: 'nueva respuesta', 'voto', 'mención')
        notif_id = ForumNotification.create(
            userId=user_id,
            type="nueva respuesta", # Validating against your MongoDB Enum
            referenceId=TestFullDatabaseIntegrity.test_post_id
        )
        self.assertIsNotNone(notif_id)
        
        # Conversation
        conv_id = Conversation.create(
            chatId=f"chat_{self.ts}",
            chatName="Assistant Test",
            promptSent="Analyze this test",
            aiResponse="Test passed"
        )
        self.assertIsNotNone(conv_id)
        
        # Chat Summary
        summary_id = ChatSummary.create(
            chatId=f"chat_{self.ts}",
            chatName="Assistant Test",
            summaryText="This is a test summary"
        )
        self.assertIsNotNone(summary_id)

if __name__ == '__main__':
    unittest.main()
