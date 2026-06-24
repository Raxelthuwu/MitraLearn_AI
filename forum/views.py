from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse

from forum import (
    ForumCategoryService,
    ForumSubcategoryService,
    ForumTopicService,
    ForumPostService,
    ForumReplyService,
    ForumVoteService,
    ForumBookmarkService,
    ForumNotificationService,
    SemanticIndexService,
    SemanticSearchService,
    DuplicateDetectionService,
    AnswerSuggestionService,
    QueryExpansionService,
)


# Service singletons (The "Pipeline" engines)
categorySvc    = ForumCategoryService()
subcategorySvc = ForumSubcategoryService()
topicSvc       = ForumTopicService()
postSvc        = ForumPostService()
replySvc       = ForumReplyService()
voteSvc        = ForumVoteService()
bookmarkSvc    = ForumBookmarkService()
notifSvc       = ForumNotificationService()
indexSvc       = SemanticIndexService()
searchSvc      = SemanticSearchService()
duplicateSvc   = DuplicateDetectionService()
suggestionSvc  = AnswerSuggestionService()
expansionSvc   = QueryExpansionService()


def _hydrateSearchResults(similarityResults):
    """Enriches similarity service results (postId/snippet) with full post data.
    Returns a list of post dicts compatible with post_list.html / search_results.html.
    """
    hydrated = []
    for item in similarityResults:
        postId = item.get("postId", "")
        if not postId:
            continue
        post = postSvc.getPostById(postId)
        if post:
            post["similarity"] = item.get("similarity", 0.0)
            hydrated.append(post)
    return hydrated



# Get current user id from session
def getUserId(request: HttpRequest) -> str:
    return request.session.get("userId", "")


# Check if user is not logged in
def loginRequired(request: HttpRequest) -> bool:
    return not getUserId(request)


# Sentinel author id for AI-generated replies
AI_AUTHOR_ID = "000000000000000000000000"


def canDeleteReply(userId: str, reply: dict, post: dict) -> bool:
    """Reply author or post author may delete a reply (including AI suggestions)."""
    if not userId or not reply or not post:
        return False
    return reply["authorId"] == userId or post["authorId"] == userId


def canEditReply(userId: str, reply: dict) -> bool:
    """Only the human author may edit; AI replies are not editable."""
    if not userId or not reply:
        return False
    if reply.get("aiGenerated"):
        return False
    return reply["authorId"] == userId



def forumHome(request: HttpRequest) -> HttpResponse:
    # Shows all categories (unreadCount comes from context processor)
    categories = categorySvc.getAllCategories()

    return render(request, "forum/home.html", {
        "categories": categories,
    })



def notificationList(request: HttpRequest) -> HttpResponse:
    # Lists all notifications for the current user
    if loginRequired(request):
        return redirect("forum:home")

    userId        = getUserId(request)
    notifications = notifSvc.getNotificationsByUser(userId)

    return render(request, "forum/notifications.html", {
        "notifications": notifications,
    })


def notificationMarkRead(request: HttpRequest, notificationId: str) -> HttpResponse:
    # Marks a single notification as read and redirects back to the list
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        notifSvc.markAsRead(notificationId)

    return redirect("forum:notification_list")


def notificationMarkAllRead(request: HttpRequest) -> HttpResponse:
    # Marks every unread notification as read for the current user
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        userId = getUserId(request)
        notifSvc.markAllAsRead(userId)

    return redirect("forum:notification_list")


def notificationUnreadApi(request: HttpRequest) -> HttpResponse:
    # JSON endpoint for live notification badge updates (polled from the browser)
    if loginRequired(request):
        return JsonResponse({"error": "unauthorized"}, status=401)

    user_id = getUserId(request)
    unread  = notifSvc.getUnreadNotifications(user_id)

    return JsonResponse({
        "unreadCount":   len(unread),
        "notifications": unread,
    })



def categoryList(request: HttpRequest) -> HttpResponse:
    # Lists all categories; admins can create new ones via POST
    if request.method == "POST":
        if loginRequired(request):
            return redirect("forum:home")

        name        = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if name:
            categorySvc.createCategory(name, description)
            messages.success(request, "Category created.")

        return redirect("forum:category_list")

    categories = categorySvc.getAllCategories()
    return render(request, "forum/category_list.html", {
        "categories": categories,
    })


def categoryDetail(request: HttpRequest, categoryId: str) -> HttpResponse:
    # Shows one category and its subcategories
    category      = categorySvc.getCategoryById(categoryId)
    subcategories = subcategorySvc.getSubcategoriesByCategory(categoryId)

    if not category:
        return redirect("forum:category_list")

    # Create subcategory via POST
    if request.method == "POST":
        if loginRequired(request):
            return redirect("forum:home")

        name = request.POST.get("name", "").strip()
        if name:
            subcategorySvc.createSubcategory(categoryId, name)
            messages.success(request, "Subcategory created.")

        return redirect("forum:category_detail", categoryId=categoryId)

    return render(request, "forum/category_detail.html", {
        "category":      category,
        "subcategories": subcategories,
    })



def subcategoryDetail(request: HttpRequest, subcategoryId: str) -> HttpResponse:
    # Shows one subcategory and its topics
    subcategory = subcategorySvc.getSubcategoryById(subcategoryId)
    topics      = topicSvc.getTopicsBySubcategory(subcategoryId)

    if not subcategory:
        return redirect("forum:category_list")

    # Create topic via POST
    if request.method == "POST":
        if loginRequired(request):
            return redirect("forum:home")

        name = request.POST.get("name", "").strip()
        if name:
            topicSvc.createTopic(subcategoryId, name)
            messages.success(request, "Topic created.")

        return redirect("forum:subcategory_detail", subcategoryId=subcategoryId)

    return render(request, "forum/subcategory_detail.html", {
        "subcategory": subcategory,
        "topics":      topics,
    })



def topicDetail(request: HttpRequest, topicId: str) -> HttpResponse:
    # Shows one topic and the posts inside it
    topic = topicSvc.getTopicById(topicId)
    if not topic:
        return redirect("forum:category_list")

    posts = postSvc.getPostsByCategory(topic["subcategoryId"])

    return render(request, "forum/topic_detail.html", {
        "topic": topic,
        "posts": posts,
    })



def postList(request: HttpRequest, categoryId: str) -> HttpResponse:
    # Lists posts for a category with optional semantic search
    category  = categorySvc.getCategoryById(categoryId)
    if not category:
        return redirect("forum:category_list")

    query = request.GET.get("q", "").strip()
    page  = int(request.GET.get("page", 1))

    if query:
        searchQuery = expansionSvc.normalizeQuery(query)
        rawResults  = searchSvc.findSimilarPosts(
            queryText      = searchQuery,
            topK           = 20,
            scoreThreshold = searchSvc.DEFAULT_SEARCH_THRESHOLD,
        )
        posts = _hydrateSearchResults(rawResults)
    else:
        posts = postSvc.getPostsByCategory(categoryId, page=page, pageSize=20)

    return render(request, "forum/post_list.html", {
        "category": category,
        "posts":    posts,
        "query":    query,
        "page":     page,
    })


def postDetail(request: HttpRequest, postId: str) -> HttpResponse:
    # Shows a post, its ranked replies, and a reply form
    post = postSvc.getPostById(postId)
    if not post:
        return redirect("forum:category_list")

    userId  = getUserId(request)
    replies = replySvc.getRepliesByPost(postId)

    # Re-rank replies by semantic relevance + votes + accepted status
    if replies:
        replies = suggestionSvc.rankReplies(postId, replies)

    isBookmarked = False
    userVote     = None
    if userId:
        isBookmarked = bookmarkSvc.isBookmarked(userId, postId)
        userVote     = voteSvc.getUserVoteOnTarget(userId, postId)

    return render(request, "forum/post_detail.html", {
        "post":        post,
        "replies":     replies,
        "isBookmarked": isBookmarked,
        "userVote":    userVote,
    })


def postCreate(request: HttpRequest) -> HttpResponse:
    # Handles new post creation with duplicate detection before saving
    if loginRequired(request):
        return redirect("forum:home")

    userId     = getUserId(request)
    categories = categorySvc.getAllCategories()

    if request.method == "POST":
        title         = request.POST.get("title", "").strip()
        content       = request.POST.get("content", "").strip()
        categoryId    = request.POST.get("categoryId", "").strip()
        subcategoryId = request.POST.get("subcategoryId", "").strip() or None
        topicId       = request.POST.get("topicId", "").strip() or None
        tags          = [t.strip() for t in request.POST.get("tags", "").split(",") if t.strip()]
        confirmPost   = request.POST.get("confirmPost", "")

        # Validate that optional IDs are actual ObjectIds; ignore invalid text values
        from bson import ObjectId as BsonObjectId
        if subcategoryId and not BsonObjectId.is_valid(subcategoryId):
            subcategoryId = None
        if topicId and not BsonObjectId.is_valid(topicId):
            topicId = None

        if not title or not content or not categoryId:
            messages.error(request, "Title, content and category are required.")
            return render(request, "forum/post_create.html", {"categories": categories})

        # Detect duplicates before saving unless the user confirmed they want to post anyway
        if not confirmPost:
            duplicates = duplicateSvc.detectDuplicates(
                title          = title,
                content        = content,
                scoreThreshold = duplicateSvc.SOFT_THRESHOLD,
            )
            if duplicates:
                # Show warnings and ask for confirmation
                return render(request, "forum/post_create.html", {
                    "categories": categories,
                    "duplicates": duplicates,
                    "formData": {
                        "title":         title,
                        "content":       content,
                        "categoryId":    categoryId,
                        "subcategoryId": subcategoryId,
                        "topicId":       topicId,
                        "tags":          ", ".join(tags),
                    },
                })

        # Suggest tags automatically if none were provided
        if not tags:
            tags = expansionSvc.extractKeyTerms(f"{title} {content}")

        post = postSvc.createPost(
            authorId      = userId,
            title         = title,
            content       = content,
            categoryId    = categoryId,
            subcategoryId = subcategoryId,
            topicId       = topicId,
            tags          = tags,
        )

        # Index in ChromaDB for future similarity searches
        indexSvc.indexPost(post["id"], title, content, tags)

        # Mark as hard duplicate if it is clearly one
        if duplicateSvc.isClearDuplicate(title, content, duplicateSvc.HARD_THRESHOLD):
            candidates = duplicateSvc.detectDuplicates(title, content, duplicateSvc.HARD_THRESHOLD)
            if candidates:
                duplicateSvc.confirmDuplicate(post["id"], candidates[0]["postId"])

        messages.success(request, "Post published.")
        return redirect("forum:post_detail", postId=post["id"])

    return render(request, "forum/post_create.html", {
        "categories": categories,
    })


def postEdit(request: HttpRequest, postId: str) -> HttpResponse:
    # Allows the author to edit title, content, and tags
    if loginRequired(request):
        return redirect("forum:home")

    post   = postSvc.getPostById(postId)
    userId = getUserId(request)

    if not post or post["authorId"] != userId:
        return redirect("forum:post_detail", postId=postId)

    if request.method == "POST":
        title   = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        tags    = [t.strip() for t in request.POST.get("tags", "").split(",") if t.strip()]

        updated = postSvc.updatePost(postId, {
            "title":   title,
            "content": content,
            "tags":    tags,
        })

        if updated:
            # Keep the vector store in sync with the edited content
            indexSvc.updateIndexedPost(postId, title, content, tags)
            messages.success(request, "Post updated.")

        return redirect("forum:post_detail", postId=postId)

    return render(request, "forum/post_edit.html", {
        "post": post,
    })


def postDelete(request: HttpRequest, postId: str) -> HttpResponse:
    # Deletes a post and removes its embedding from ChromaDB
    if loginRequired(request):
        return redirect("forum:home")

    post   = postSvc.getPostById(postId)
    userId = getUserId(request)

    if not post or post["authorId"] != userId:
        return redirect("forum:post_detail", postId=postId)

    if request.method == "POST":
        categoryId = post["categoryId"]
        postSvc.deletePost(postId)
        indexSvc.removeIndexedPost(postId)
        messages.success(request, "Post deleted.")
        return redirect("forum:post_list", categoryId=categoryId)

    return render(request, "forum/post_confirm_delete.html", {
        "post": post,
    })


def postUpdateStatus(request: HttpRequest, postId: str) -> HttpResponse:
    # Changes post status: open | resolved | closed
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        status = request.POST.get("status", "").strip()
        if status in ("open", "resolved", "closed"):
            postSvc.updatePostStatus(postId, status)
            messages.success(request, f"Status updated to '{status}'.")

    return redirect("forum:post_detail", postId=postId)



def replyCreate(request: HttpRequest, postId: str) -> HttpResponse:
    # Adds a reply to a post and indexes it in ChromaDB
    if loginRequired(request):
        return redirect("forum:home")

    post = postSvc.getPostById(postId)
    if not post:
        return redirect("forum:category_list")

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        userId  = getUserId(request)

        if content:
            reply = replySvc.createReply(
                postId  = postId,
                authorId = userId,
                content  = content,
            )

            # Index the new reply for semantic search
            indexSvc.indexReply(reply["id"], postId, content)

            # Notify the post author
            if post["authorId"] != userId:
                notifSvc.createNotification(
                    userId           = post["authorId"],
                    notificationType = "nueva respuesta",
                    referenceId      = postId,
                )

            messages.success(request, "Reply published.")

    return redirect("forum:post_detail", postId=postId)


def replyEdit(request: HttpRequest, replyId: str) -> HttpResponse:
    # Allows the author to edit a reply's content
    if loginRequired(request):
        return redirect("forum:home")

    reply  = replySvc.getReplyById(replyId)
    userId = getUserId(request)

    post = postSvc.getPostById(reply["postId"]) if reply else None
    if not reply or not canEditReply(userId, reply):
        messages.error(request, "You cannot edit this reply.")
        return redirect("forum:post_detail", postId=reply["postId"] if reply else "")

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            replySvc.updateReply(replyId, content)
            # Keep the vector store in sync
            indexSvc.removeIndexedReply(replyId)
            indexSvc.indexReply(replyId, reply["postId"], content)
            messages.success(request, "Reply updated.")

        return redirect("forum:post_detail", postId=reply["postId"])

    return render(request, "forum/reply_edit.html", {
        "reply": reply,
    })


def replyDelete(request: HttpRequest, replyId: str) -> HttpResponse:
    # Deletes a reply and removes its embedding from ChromaDB
    if loginRequired(request):
        return redirect("forum:home")

    reply  = replySvc.getReplyById(replyId)
    userId = getUserId(request)
    postId = reply["postId"] if reply else ""
    post   = postSvc.getPostById(postId) if postId else None

    if not reply or not post or not canDeleteReply(userId, reply, post):
        messages.error(request, "You do not have permission to delete this reply.")
        if postId:
            return redirect("forum:post_detail", postId=postId)
        return redirect("forum:category_list")

    if request.method == "POST":
        replySvc.deleteReply(replyId)
        indexSvc.removeIndexedReply(replyId)

        remaining = replySvc.getRepliesByPost(postId)
        if not any(r.get("aiGenerated") for r in remaining):
            postSvc.clearAiSuggested(postId)

        messages.success(request, "Reply deleted.")

    return redirect("forum:post_detail", postId=postId)


def replyAccept(request: HttpRequest, replyId: str, postId: str) -> HttpResponse:
    # Marks a reply as the accepted answer and sets the post to resolved
    if loginRequired(request):
        return redirect("forum:home")

    post   = postSvc.getPostById(postId)
    userId = getUserId(request)

    # Only the post author can accept a reply
    if not post or post["authorId"] != userId:
        return redirect("forum:post_detail", postId=postId)

    if request.method == "POST":
        # --- PIPELINE: ACCEPT SOLUTION ---
        try:
            # 1. Accept Reply
            replySvc.acceptReply(replyId, postId)

            # 2. Automate Post Status (Set to Resolved)
            postSvc.updatePostStatus(postId, "resolved")

            # 3. Notification Pipeline (Automatic)
            reply = replySvc.getReplyById(replyId)
            if reply and reply["authorId"] != userId:
                notifSvc.createNotification(
                    userId           = reply["authorId"],
                    notificationType = "respuesta aceptada",
                    referenceId      = postId,
                )

            messages.success(request, "Reply accepted. The post has been marked as RESOLVED.")
        except Exception as e:
            messages.error(request, f"Could not accept the reply: {e}")

    return redirect("forum:post_detail", postId=postId)



def replyAiSuggest(request: HttpRequest, postId: str) -> HttpResponse:
    # Runs the RAG pipeline and saves an AI-generated reply to the post
    if loginRequired(request):
        return redirect("forum:home")

    post = postSvc.getPostById(postId)
    if not post:
        return redirect("forum:category_list")

    if request.method == "POST":
        try:
            suggestionSvc.generateAiAnswer(
                postId  = postId,
                title   = post["title"],
                content = post["content"],
                tags    = post.get("tags", []),
            )
            postSvc.flagAsAiSuggested(postId)
            messages.success(request, "AI suggestion generated and added as a reply.")
        except Exception as e:
            messages.error(request, f"Could not generate AI suggestion: {e}")

    return redirect("forum:post_detail", postId=postId)



def vote(request: HttpRequest, targetId: str) -> HttpResponse:
    # Casts or updates a vote on a post or reply
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        userId  = getUserId(request)
        rating  = int(request.POST.get("rating", 1))
        postId  = request.POST.get("postId", "").strip()

        voteSvc.castVote(userId, targetId, rating)

        # Notify the target author
        target = postSvc.getPostById(targetId)
        authorId = target["authorId"] if target else None
        if not authorId:
            reply = replySvc.getReplyById(targetId)
            if reply:
                authorId = reply["authorId"]
                postId   = reply["postId"]

        if authorId and authorId != userId:
            notifSvc.createNotification(
                userId           = authorId,
                notificationType = "voto",
                referenceId      = targetId,
            )

        if postId:
            return redirect("forum:post_detail", postId=postId)

    return redirect("forum:home")


def voteRemove(request: HttpRequest, targetId: str) -> HttpResponse:
    # Removes the current user's vote from a post or reply
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        userId = getUserId(request)
        postId = request.POST.get("postId", "").strip()
        voteSvc.removeVote(userId, targetId)

        if postId:
            return redirect("forum:post_detail", postId=postId)

    return redirect("forum:home")



def bookmarkAdd(request: HttpRequest, postId: str) -> HttpResponse:
    # Saves a post to the user's bookmark list
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        userId = getUserId(request)
        bookmarkSvc.addBookmark(userId, postId)
        messages.success(request, "Post bookmarked.")

    return redirect("forum:post_detail", postId=postId)


def bookmarkRemove(request: HttpRequest, postId: str) -> HttpResponse:
    # Removes a post from the user's bookmark list
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        userId = getUserId(request)
        bookmarkSvc.removeBookmark(userId, postId)
        messages.success(request, "Bookmark removed.")

    return redirect("forum:post_detail", postId=postId)


def bookmarkList(request: HttpRequest) -> HttpResponse:
    # Shows all bookmarked posts for the current user
    if loginRequired(request):
        return redirect("forum:home")

    userId    = getUserId(request)
    bookmarks = bookmarkSvc.getBookmarksByUser(userId)

    return render(request, "forum/bookmark_list.html", {
        "bookmarks": bookmarks,
    })



def semanticSearch(request: HttpRequest) -> HttpResponse:
    # Global semantic search across all posts using query expansion
    query   = request.GET.get("q", "").strip()
    results = []

    if query:
        searchQuery = expansionSvc.normalizeQuery(query)
        rawResults  = searchSvc.findSimilarPosts(
            queryText      = searchQuery,
            topK           = 20,
            scoreThreshold = searchSvc.DEFAULT_SEARCH_THRESHOLD,
        )
        results = _hydrateSearchResults(rawResults)

    return render(request, "forum/search_results.html", {
        "query":   query,
        "results": results,
    })



def rebuildIndex(request: HttpRequest) -> HttpResponse:
    # Drops and fully rebuilds the ChromaDB index from MongoDB
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        count = indexSvc.rebuildIndex()
        messages.success(request, f"Index rebuilt. {count} documents indexed.")

    return redirect("forum:home")