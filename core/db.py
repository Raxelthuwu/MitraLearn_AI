import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
#conexion con la base de datos
client = MongoClient(os.environ.get("MONGODB_URI"))
db = client["mingenially_learn"]

#Colecciones del asistente 
conversations  = db["conversations"]
chat_summaries = db["chatSummaries"]

#Colecciones del foro 
users               = db["users"]
forum_categories    = db["forumCategories"]
forum_subcategories = db["forumSubcategories"]
forum_topics        = db["forumTopics"]
forum_posts         = db["forumPosts"]
forum_replies       = db["forumReplies"]
forum_votes         = db["forumVotes"]
forum_bookmarks     = db["forumBookmarks"]
forum_notifications = db["forumNotifications"]