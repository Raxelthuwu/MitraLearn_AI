import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Database connection
client = MongoClient(os.environ.get("MONGODB_URI"))
db = client["mingenially_learn"]

# Assistant Collections
conversations = db["conversations"]
chatSummaries = db["chatSummaries"]

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