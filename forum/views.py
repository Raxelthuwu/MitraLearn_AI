from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpRequest, HttpResponse

from forum.services.forumService import (
    ForumCategoryService,
    ForumSubcategoryService,
    ForumTopicService,
    ForumPostService,
    ForumReplyService,
    ForumVoteService,
    ForumBookmarkService,
    ForumNotificationService,
)
from forum.services.semanticService import (
    SemanticIndexService,
    SemanticSearchService,
    DuplicateDetectionService,
    AnswerSuggestionService,
    QueryExpansionService,
)
from assistant.services.rag_service import RAGService


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
ragSvc         = RAGService()


# Get current user id from session
def getUserId(request: HttpRequest) -> str:
    return request.session.get("userId", "")


# Check if user is not logged in
def loginRequired(request: HttpRequest) -> bool:
    return not getUserId(request)



def forumHome(request: HttpRequest) -> HttpResponse:
    # Shows all categories and unread notification count for the current user
    categories = categorySvc.getAllCategories()
    userId     = getUserId(request)

    unreadCount = 0
    if userId:
        unreadCount = len(notifSvc.getUnreadNotifications(userId))

    return render(request, "forum/home.html", {
        "categories":  categories,
        "unreadCount": unreadCount,
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
        # Expand the query before searching
        expandedQuery = expansionSvc.expandQuery(query)
        posts         = searchSvc.findSimilarPosts(
            queryText      = expandedQuery,
            topK           = 20,
            scoreThreshold = 0.40,
        )
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

        # --- PIPELINE: POST PUBLICATION ---
        
        # 1. Core Creation
        post = postSvc.createPost(
            authorId      = userId,
            title         = title,
            content       = content,
            categoryId    = categoryId,
            subcategoryId = subcategoryId,
            topicId       = topicId,
            tags          = tags,
        )

        # 2. Duplicate Resolution (Automatic)
        is_hard_duplicate = False
        if duplicateSvc.isClearDuplicate(title, content, duplicateSvc.HARD_THRESHOLD):
            candidates = duplicateSvc.detectDuplicates(title, content, duplicateSvc.HARD_THRESHOLD)
            # Make sure it's not matching itself if it was somehow indexed
            valid_candidates = [c for c in candidates if c["postId"] != str(post["id"])]
            if valid_candidates:
                duplicateSvc.confirmDuplicate(post["id"], valid_candidates[0]["postId"])
                is_hard_duplicate = True

        # 3. Semantic Indexing (Automatic)
        if not is_hard_duplicate:
            indexSvc.indexPost(post["id"], title, content, tags)
        # 4. AI Early Support (Automatic for Academic Category)
        # If the category is academic, the RAG system tries to provide context
        category = categorySvc.getCategoryById(categoryId)
        if category and "Academic" in category["name"]:
            rag_response = ragSvc.generate_augmented_response(f"{title} {content}")
            if rag_response and rag_response["answer"]:
                # Save AI suggestion as a special reply
                replySvc.createReply(
                    postId      = post["id"],
                    authorId    = "000000000000000000000000", # Special identifier (24 hex chars)
                    content     = f"[Sugerencia de IA basada en libros]:\n\n{rag_response['answer']}\n\nFuentes: {rag_response['sources']}",
                    aiGenerated = True
                )
                postSvc.flagAsAiSuggested(post["id"])

        messages.success(request, "Post published. AI has indexed your content.")
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
            # --- PIPELINE: REPLY CREATION ---
            
            # 1. Create Reply
            reply = replySvc.createReply(
                postId   = postId,
                authorId = userId,
                content  = content,
            )

            # 2. Semantic Indexing (Automatic)
            indexSvc.indexReply(reply["id"], postId, content)

            # 3. Notification Pipeline (Automatic)
            if post["authorId"] != userId:
                notifSvc.createNotification(
                    userId           = post["authorId"],
                    notificationType = "nueva respuesta",
                    referenceId      = postId,
                )
                
            # 4. Update Answer Ranking (Automatic Re-calculation)
            suggestionSvc.rankReplies(postId, replySvc.getRepliesByPost(postId))

            messages.success(request, "Reply published and indexed.")

    return redirect("forum:post_detail", postId=postId)


def replyEdit(request: HttpRequest, replyId: str) -> HttpResponse:
    # Allows the author to edit a reply's content
    if loginRequired(request):
        return redirect("forum:home")

    reply  = replySvc.getReplyById(replyId)
    userId = getUserId(request)

    if not reply or reply["authorId"] != userId:
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

    if not reply or reply["authorId"] != userId:
        return redirect("forum:category_list")

    postId = reply["postId"]

    if request.method == "POST":
        replySvc.deleteReply(replyId)
        indexSvc.removeIndexedReply(replyId)
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
                referenceId      = replyId,
            )

        messages.success(request, "Reply accepted. The post has been marked as RESOLVED.")

    return redirect("forum:post_detail", postId=postId)



def replyAiSuggest(request: HttpRequest, postId: str) -> HttpResponse:
    # Runs the RAG pipeline and saves an AI-generated reply to the post
    if loginRequired(request):
        return redirect("forum:home")

    post = postSvc.getPostById(postId)
    if not post:
        return redirect("forum:category_list")

    if request.method == "POST":
        result = suggestionSvc.generateAiAnswer(
            postId  = postId,
            title   = post["title"],
            content = post["content"],
        )

        # Flag the post as having received an AI suggestion
        postSvc.flagAsAiSuggested(postId)

        messages.success(request, "AI suggestion generated and added as a reply.")

    return redirect("forum:post_detail", postId=postId)



def vote(request: HttpRequest, targetId: str) -> HttpResponse:
    # Casts or updates a vote on a post or reply
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        userId  = getUserId(request)
        rating  = int(request.POST.get("rating", 1))
        postId  = request.POST.get("postId", "").strip()

        # --- PIPELINE: VOTING & REPUTATION ---
        
        # 1. Cast Vote and Calculate Average Score (Automatic)
        vote_data = voteSvc.castVote(userId, targetId, rating)
        
        # 2. Reputation Update (The castVote service already handles this internally)
        # but we ensure the pipeline is clear.

        # 3. Notification Pipeline (Automatic)
        target_post = postSvc.getPostById(targetId)
        authorId = target_post["authorId"] if target_post else None
        
        if not authorId:
            target_reply = replySvc.getReplyById(targetId)
            if target_reply:
                authorId = target_reply["authorId"]
                postId   = target_reply["postId"]

        if authorId and authorId != userId:
            notifSvc.createNotification(
                userId           = authorId,
                notificationType = "voto",
                referenceId      = targetId,
            )

        messages.success(request, f"Vote registered. New score: {vote_data.get('score', 0)}")
        
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
        expandedQuery = expansionSvc.expandQuery(query)
        results       = searchSvc.findSimilarPosts(
            queryText      = expandedQuery,
            topK           = 20,
            scoreThreshold = 0.40,
        )

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