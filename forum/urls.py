from django.urls import path
from forum import views

app_name = "forum"

urlpatterns = [

    # Home
    path("", views.forumHome, name="home"),

    # Semantic search
    path("search/", views.semanticSearch, name="search"),

    # Notifications
    path("notifications/", views.notificationList, name="notification_list"),
    path("notifications/mark-all-read/", views.notificationMarkAllRead, name="notification_mark_all_read"),
    path("notifications/<str:notificationId>/read/", views.notificationMarkRead, name="notification_mark_read"),

    # Categories
    path("categories/", views.categoryList, name="category_list"),
    path("categories/<str:categoryId>/", views.categoryDetail, name="category_detail"),

    # Subcategories
    path("subcategories/<str:subcategoryId>/", views.subcategoryDetail, name="subcategory_detail"),

    # Topics
    path("topics/<str:topicId>/", views.topicDetail, name="topic_detail"),

    # Posts
    path("categories/<str:categoryId>/posts/", views.postList, name="post_list"),
    path("posts/create/", views.postCreate, name="post_create"),
    path("posts/<str:postId>/", views.postDetail, name="post_detail"),
    path("posts/<str:postId>/edit/", views.postEdit, name="post_edit"),
    path("posts/<str:postId>/delete/", views.postDelete, name="post_delete"),
    path("posts/<str:postId>/status/", views.postUpdateStatus, name="post_update_status"),

    # Replies
    path("posts/<str:postId>/replies/create/", views.replyCreate, name="reply_create"),
    path("posts/<str:postId>/replies/ai-suggest/", views.replyAiSuggest, name="reply_ai_suggest"),
    path("replies/<str:replyId>/edit/", views.replyEdit, name="reply_edit"),
    path("replies/<str:replyId>/delete/", views.replyDelete, name="reply_delete"),
    path("replies/<str:replyId>/accept/<str:postId>/", views.replyAccept, name="reply_accept"),

    # Votes
    path("vote/<str:targetId>/", views.vote, name="vote"),
    path("vote/<str:targetId>/remove/", views.voteRemove, name="vote_remove"),

    # Bookmarks
    path("bookmarks/", views.bookmarkList, name="bookmark_list"),
    path("bookmarks/<str:postId>/add/", views.bookmarkAdd, name="bookmark_add"),
    path("bookmarks/<str:postId>/remove/", views.bookmarkRemove, name="bookmark_remove"),

    # Admin utilities
    path("admin/rebuild-index/", views.rebuildIndex, name="rebuild_index"),

]