import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Database connection
client = MongoClient(os.environ.get("MONGODB_URI"))
db = client["mingenially_learn"]

# Assistant Collections
conversations = db["conversations"]
chatSummaries = db["chatSummaries"]
chat_summaries = chatSummaries
chatSessions = db["chatSessions"]
chat_sessions = chatSessions
indexedBooks = db["indexedBooks"]
indexed_books = indexedBooks

# Forum Collections
users = db["users"]
forumCategories = db["forumCategories"]
forumSubcategories = db["forumSubcategories"]
forumTopics = db["forumTopics"]
forumPosts = db["forumPosts"]
forumReplies = db["forumReplies"]
forumVotes = db["forumVotes"]
forumBookmarks = db["forumBookmarks"]
forumNotifications = db["forumNotifications"]