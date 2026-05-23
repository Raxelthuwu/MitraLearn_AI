from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpRequest, HttpResponse

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


# Singletons de servicios
categorySvc   = ForumCategoryService()
subcategorySvc = ForumSubcategoryService()
topicSvc      = ForumTopicService()
postSvc       = ForumPostService()
replySvc      = ForumReplyService()
voteSvc       = ForumVoteService()
bookmarkSvc   = ForumBookmarkService()
notifSvc      = ForumNotificationService()
indexSvc      = SemanticIndexService()
searchSvc     = SemanticSearchService()
duplicateSvc  = DuplicateDetectionService()
suggestionSvc = AnswerSuggestionService()
expansionSvc  = QueryExpansionService()


# Retorna el userId de la sesión activa
def getUserId(request: HttpRequest) -> str:
    return request.session.get("userId", "")


# Verdadero si el usuario no está autenticado
def loginRequired(request: HttpRequest) -> bool:
    return not getUserId(request)


# Home

def forumHome(request: HttpRequest) -> HttpResponse:
    # Muestra todas las categorías y el contador de notificaciones no leídas
    categories  = categorySvc.getAllCategories()
    userId      = getUserId(request)
    unreadCount = 0

    if userId:
        unreadCount = len(notifSvc.getUnreadNotifications(userId))

    return render(request, "forum/home.html", {
        "categories":  categories,
        "unreadCount": unreadCount,
    })


# Notificaciones

def notificationList(request: HttpRequest) -> HttpResponse:
    # Lista todas las notificaciones del usuario actual
    if loginRequired(request):
        return redirect("forum:home")

    userId        = getUserId(request)
    notifications = notifSvc.getNotificationsByUser(userId)

    return render(request, "forum/notifications.html", {
        "notifications": notifications,
    })


def notificationMarkRead(request: HttpRequest, notificationId: str) -> HttpResponse:
    # Marca una notificación como leída y redirige a la lista
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        notifSvc.markAsRead(notificationId)

    return redirect("forum:notification_list")


def notificationMarkAllRead(request: HttpRequest) -> HttpResponse:
    # Marca todas las notificaciones del usuario como leídas
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        userId = getUserId(request)
        notifSvc.markAllAsRead(userId)

    return redirect("forum:notification_list")


# Categorías

def categoryList(request: HttpRequest) -> HttpResponse:
    # Lista todas las categorías; permite crear nuevas vía POST
    if request.method == "POST":
        if loginRequired(request):
            return redirect("forum:home")

        name        = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if name:
            categorySvc.createCategory(name, description)
            messages.success(request, "Categoría creada.")

        return redirect("forum:category_list")

    categories = categorySvc.getAllCategories()
    return render(request, "forum/category_list.html", {
        "categories": categories,
    })


def categoryDetail(request: HttpRequest, categoryId: str) -> HttpResponse:
    # Muestra una categoría y sus subcategorías; permite crear subcategorías vía POST
    category      = categorySvc.getCategoryById(categoryId)
    subcategories = subcategorySvc.getSubcategoriesByCategory(categoryId)

    if not category:
        return redirect("forum:category_list")

    if request.method == "POST":
        if loginRequired(request):
            return redirect("forum:home")

        name = request.POST.get("name", "").strip()
        if name:
            subcategorySvc.createSubcategory(categoryId, name)
            messages.success(request, "Subcategoría creada.")

        return redirect("forum:category_detail", categoryId=categoryId)

    return render(request, "forum/category_detail.html", {
        "category":      category,
        "subcategories": subcategories,
    })


# ─── Subcategorías ───────────────────────────────────────────────────────────

def subcategoryDetail(request: HttpRequest, subcategoryId: str) -> HttpResponse:
    # Muestra una subcategoría y sus topics; permite crear topics vía POST
    subcategory = subcategorySvc.getSubcategoryById(subcategoryId)
    topics      = topicSvc.getTopicsBySubcategory(subcategoryId)

    if not subcategory:
        return redirect("forum:category_list")

    if request.method == "POST":
        if loginRequired(request):
            return redirect("forum:home")

        name = request.POST.get("name", "").strip()
        if name:
            topicSvc.createTopic(subcategoryId, name)
            messages.success(request, "Topic creado.")

        return redirect("forum:subcategory_detail", subcategoryId=subcategoryId)

    return render(request, "forum/subcategory_detail.html", {
        "subcategory": subcategory,
        "topics":      topics,
    })


# ─── Topics ──────────────────────────────────────────────────────────────────

def topicDetail(request: HttpRequest, topicId: str) -> HttpResponse:
    # Muestra un topic y los posts que contiene
    topic = topicSvc.getTopicById(topicId)
    if not topic:
        return redirect("forum:category_list")

    posts = postSvc.getPostsByCategory(topic["subcategoryId"])

    return render(request, "forum/topic_detail.html", {
        "topic": topic,
        "posts": posts,
    })


# ─── Posts ───────────────────────────────────────────────────────────────────

def postList(request: HttpRequest, categoryId: str) -> HttpResponse:
    # Lista posts de una categoría con búsqueda semántica y filtrado por tags
    # Flujo: si hay tags → searchByTags; si hay query → expandQuery + findSimilarPosts; sino → listado paginado
    category = categorySvc.getCategoryById(categoryId)
    if not category:
        return redirect("forum:category_list")

    query = request.GET.get("q", "").strip()
    tags  = [t.strip() for t in request.GET.get("tags", "").split(",") if t.strip()]
    page  = int(request.GET.get("page", 1))

    if tags:
        # Búsqueda por etiquetas semánticas (RF-futuro: searchByTags en flujo)
        posts = searchSvc.searchByTags(
            tags      = tags,
            queryText = query or None,
            topK      = 20,
        )
    elif query:
        # Expande la query con LLM antes de buscar por similitud semántica
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
        "tags":     tags,
        "page":     page,
    })


def postDetail(request: HttpRequest, postId: str) -> HttpResponse:
    # Muestra un post con sus replies rankeadas y posts relacionados
    # Flujo: obtenerPost → obtenerReplies → rankReplies → findSimilarPostById
    #        → sugerirSimilaresSiNoHayReplies → verificarBookmark → verificarVoto
    post = postSvc.getPostById(postId)
    if not post:
        return redirect("forum:category_list")

    userId  = getUserId(request)
    replies = replySvc.getRepliesByPost(postId)

    # Re-rankea respuestas por relevancia semántica + votos + aceptada (parte del flujo de visualización)
    if replies:
        replies = suggestionSvc.rankReplies(postId, replies)

    # Si no hay respuestas, sugiere replies similares de otros posts como referencia
    suggestedReplies = []
    if not replies:
        suggestedReplies = suggestionSvc.suggestAnswersForPost(postId, topK=3)

    # Recupera posts relacionados semánticamente para el panel lateral
    relatedPosts = searchSvc.findSimilarPostById(
        postId         = postId,
        topK           = 5,
        scoreThreshold = 0.50,
    )
    # Excluye el post actual de los relacionados
    relatedPosts = [p for p in relatedPosts if p.get("postId") != postId]

    isBookmarked = False
    userVote     = None
    if userId:
        isBookmarked = bookmarkSvc.isBookmarked(userId, postId)
        userVote     = voteSvc.getUserVoteOnTarget(userId, postId)

    return render(request, "forum/post_detail.html", {
        "post":             post,
        "replies":          replies,
        "suggestedReplies": suggestedReplies,
        "relatedPosts":     relatedPosts,
        "isBookmarked":     isBookmarked,
        "userVote":         userVote,
    })


def postCreate(request: HttpRequest) -> HttpResponse:
    # Crea un nuevo post con detección de duplicados antes de guardar
    # Flujo: validar → detectarDuplicados (SOFT, una sola vez) → extraerTags → crearPost
    #        → indexar → marcarDuplicadoHard si aplica
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
            messages.error(request, "Título, contenido y categoría son obligatorios.")
            return render(request, "forum/post_create.html", {"categories": categories})

        # Detección de duplicados SOFT: se hace una sola vez con SOFT_THRESHOLD
        # Si el usuario ya confirmó, se omite y se verifica HARD en memoria con los mismos candidatos
        softCandidates = []
        if not confirmPost:
            softCandidates = duplicateSvc.detectDuplicates(
                title          = title,
                content        = content,
                scoreThreshold = duplicateSvc.SOFT_THRESHOLD,
            )
            if softCandidates:
                # Muestra advertencia y pide confirmación al usuario antes de publicar
                return render(request, "forum/post_create.html", {
                    "categories": categories,
                    "duplicates": softCandidates,
                    "formData": {
                        "title":         title,
                        "content":       content,
                        "categoryId":    categoryId,
                        "subcategoryId": subcategoryId,
                        "topicId":       topicId,
                        "tags":          ", ".join(tags),
                    },
                })

        # Sugerencia automática de tags si el usuario no ingresó ninguno
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

        # Indexa en ChromaDB; notifica si falla (RF-2)
        indexed = indexSvc.indexPost(post["id"], title, content, tags)
        if not indexed:
            messages.warning(request, "El post se publicó pero no pudo vectorizarse para búsqueda semántica.")

        # Verifica duplicado HARD filtrando los candidatos SOFT ya obtenidos en memoria
        # No se hace una segunda llamada a ChromaDB
        hardCandidates = [
            c for c in softCandidates
            if c.get("similarity", 0) >= duplicateSvc.HARD_THRESHOLD
        ]
        if hardCandidates:
            duplicateSvc.confirmDuplicate(post["id"], hardCandidates[0]["postId"])

        messages.success(request, "Post publicado.")
        return redirect("forum:post_detail", postId=post["id"])

    return render(request, "forum/post_create.html", {
        "categories": categories,
    })


def postEdit(request: HttpRequest, postId: str) -> HttpResponse:
    # Permite al autor editar título, contenido y tags del post
    # Flujo: validar autoría → actualizar en BD → re-indexar en ChromaDB
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
            # Mantiene el índice vectorial sincronizado con el contenido editado; notifica si falla (RF-2)
            reIndexed = indexSvc.updateIndexedPost(postId, title, content, tags)
            if not reIndexed:
                messages.warning(request, "Post actualizado, pero el índice semántico no pudo sincronizarse.")
            else:
                messages.success(request, "Post actualizado.")

        return redirect("forum:post_detail", postId=postId)

    return render(request, "forum/post_edit.html", {
        "post": post,
    })


def postDelete(request: HttpRequest, postId: str) -> HttpResponse:
    # Elimina un post y su embedding de ChromaDB
    # Flujo: validar autoría → eliminar en BD → eliminar embedding
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
        messages.success(request, "Post eliminado.")
        return redirect("forum:post_list", categoryId=categoryId)

    return render(request, "forum/post_confirm_delete.html", {
        "post": post,
    })


def postUpdateStatus(request: HttpRequest, postId: str) -> HttpResponse:
    # Cambia el estado del post: open | resolved | closed
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        status = request.POST.get("status", "").strip()
        if status in ("open", "resolved", "closed"):
            postSvc.updatePostStatus(postId, status)
            messages.success(request, f"Estado actualizado a '{status}'.")

    return redirect("forum:post_detail", postId=postId)


# ─── Replies ─────────────────────────────────────────────────────────────────

def replyCreate(request: HttpRequest, postId: str) -> HttpResponse:
    # Agrega una respuesta al post e indexa en ChromaDB
    # Flujo: validar → crear reply → indexar embedding → notificar al autor del post
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
                postId      = postId,
                authorId    = userId,
                content     = content,
            )

            # Indexa el reply para búsqueda semántica futura; notifica si falla (RF-2)
            indexed = indexSvc.indexReply(reply["id"], postId, content)
            if not indexed:
                messages.warning(request, "Respuesta publicada, pero no pudo indexarse para búsqueda semántica.")

            # Notifica al autor del post si es otra persona
            if post["authorId"] != userId:
                notifSvc.createNotification(
                    userId           = post["authorId"],
                    notificationType = "nueva respuesta",
                    referenceId      = postId,
                )

            messages.success(request, "Respuesta publicada.")

    return redirect("forum:post_detail", postId=postId)


def replyEdit(request: HttpRequest, replyId: str) -> HttpResponse:
    # Permite al autor editar el contenido de una respuesta
    # Flujo: validar autoría → actualizar en BD → re-indexar embedding
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

            # Re-indexa el embedding con el contenido actualizado; notifica si falla (RF-2)
            indexSvc.removeIndexedReply(replyId)
            reIndexed = indexSvc.indexReply(replyId, reply["postId"], content)
            if not reIndexed:
                messages.warning(request, "Respuesta actualizada, pero el índice semántico no pudo sincronizarse.")
            else:
                messages.success(request, "Respuesta actualizada.")

        return redirect("forum:post_detail", postId=reply["postId"])

    return render(request, "forum/reply_edit.html", {
        "reply": reply,
    })


def replyDelete(request: HttpRequest, replyId: str) -> HttpResponse:
    # Elimina una respuesta y su embedding de ChromaDB
    # Flujo: validar autoría → eliminar en BD → eliminar embedding → redirigir al post
    if loginRequired(request):
        return redirect("forum:home")

    reply  = replySvc.getReplyById(replyId)
    userId = getUserId(request)

    if not reply or reply["authorId"] != userId:
        # Redirección uniforme al post (RF-13: consistencia en redirecciones de error)
        return redirect("forum:post_detail", postId=reply["postId"] if reply else "")

    postId = reply["postId"]

    if request.method == "POST":
        replySvc.deleteReply(replyId)
        indexSvc.removeIndexedReply(replyId)
        messages.success(request, "Respuesta eliminada.")

    return redirect("forum:post_detail", postId=postId)


def replyAccept(request: HttpRequest, replyId: str, postId: str) -> HttpResponse:
    # Marca una respuesta como aceptada y establece el post como resuelto
    # Flujo: validar que sea el autor del post → acceptReply → notificar al autor de la respuesta
    if loginRequired(request):
        return redirect("forum:home")

    post   = postSvc.getPostById(postId)
    userId = getUserId(request)

    if not post or post["authorId"] != userId:
        return redirect("forum:post_detail", postId=postId)

    if request.method == "POST":
        replySvc.acceptReply(replyId, postId)

        reply = replySvc.getReplyById(replyId)
        if reply and reply["authorId"] != userId:
            notifSvc.createNotification(
                userId           = reply["authorId"],
                notificationType = "respuesta aceptada",
                referenceId      = replyId,
            )

        messages.success(request, "Respuesta aceptada como solución.")

    return redirect("forum:post_detail", postId=postId)


def replyAiSuggest(request: HttpRequest, postId: str) -> HttpResponse:
    # Ejecuta el pipeline RAG y guarda una respuesta generada por IA
    # Flujo (RF-15): solo se genera si el post no tiene respuestas → embed → retrieve → prompt → LLM → persist → indexar → flagear
    if loginRequired(request):
        return redirect("forum:home")

    post = postSvc.getPostById(postId)
    if not post:
        return redirect("forum:category_list")

    if request.method == "POST":
        # Guarda únicamente si no existe ninguna respuesta humana (RF-15)
        if post.get("answersCount", 0) > 0:
            messages.info(request, "El post ya tiene respuestas. La sugerencia IA solo aplica cuando no hay ninguna.")
            return redirect("forum:post_detail", postId=postId)

        result = suggestionSvc.generateAiAnswer(
            postId  = postId,
            title   = post["title"],
            content = post["content"],
        )

        # Marca el post como receptor de sugerencia IA para trazabilidad
        postSvc.flagAsAiSuggested(postId)

        messages.success(request, "Sugerencia IA generada y agregada como respuesta.")

    return redirect("forum:post_detail", postId=postId)


# ─── Votos ───────────────────────────────────────────────────────────────────

def vote(request: HttpRequest, targetId: str) -> HttpResponse:
    # Registra o actualiza un voto sobre un post o reply
    # Flujo: castVote → resolver autor → notificar → redirigir al post
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        userId = getUserId(request)
        rating = int(request.POST.get("rating", 1))
        postId = request.POST.get("postId", "").strip()

        voteSvc.castVote(userId, targetId, rating)

        # Resuelve el autor del target para notificarlo
        target   = postSvc.getPostById(targetId)
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
    # Elimina el voto del usuario sobre un post o reply
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        userId = getUserId(request)
        postId = request.POST.get("postId", "").strip()
        voteSvc.removeVote(userId, targetId)

        if postId:
            return redirect("forum:post_detail", postId=postId)

    return redirect("forum:home")


# ─── Bookmarks ───────────────────────────────────────────────────────────────

def bookmarkAdd(request: HttpRequest, postId: str) -> HttpResponse:
    # Guarda un post en la lista de favoritos del usuario
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        userId = getUserId(request)
        bookmarkSvc.addBookmark(userId, postId)
        messages.success(request, "Post guardado en favoritos.")

    return redirect("forum:post_detail", postId=postId)


def bookmarkRemove(request: HttpRequest, postId: str) -> HttpResponse:
    # Elimina un post de la lista de favoritos del usuario
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        userId = getUserId(request)
        bookmarkSvc.removeBookmark(userId, postId)
        messages.success(request, "Favorito eliminado.")

    return redirect("forum:post_detail", postId=postId)


def bookmarkList(request: HttpRequest) -> HttpResponse:
    # Muestra todos los posts guardados como favoritos del usuario actual
    if loginRequired(request):
        return redirect("forum:home")

    userId    = getUserId(request)
    bookmarks = bookmarkSvc.getBookmarksByUser(userId)

    return render(request, "forum/bookmark_list.html", {
        "bookmarks": bookmarks,
    })


# ─── Búsqueda global ─────────────────────────────────────────────────────────

def semanticSearch(request: HttpRequest) -> HttpResponse:
    # Búsqueda semántica global sobre todos los posts usando expansión de query
    # Flujo: expandQuery → findSimilarPosts con umbral 0.40
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


# Administración del índice 

def rebuildIndex(request: HttpRequest) -> HttpResponse:
    # Elimina y reconstruye completamente el índice ChromaDB desde MongoDB
    if loginRequired(request):
        return redirect("forum:home")

    if request.method == "POST":
        count = indexSvc.rebuildIndex()
        messages.success(request, f"Índice reconstruido. {count} documentos indexados.")

    return redirect("forum:home")