import json
import datetime

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from assistant.services.chat_service import ChatService

_chat_svc = None


def _get_chat_service() -> ChatService:
    global _chat_svc
    if _chat_svc is None:
        _chat_svc = ChatService()
    return _chat_svc


def getUserId(request: HttpRequest) -> str:
    return request.session.get("userId", "")


def loginRequired(request: HttpRequest) -> bool:
    return not getUserId(request)


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"ok": False, "error": message}, status=status)


def _parse_json_body(request: HttpRequest) -> dict:
    content_type = request.content_type or ""
    if "application/json" not in content_type:
        return {}
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


# --- HTML stubs (optional manual testing until front connects) ---

def chatConfigView(request: HttpRequest) -> HttpResponse:
    if loginRequired(request):
        return redirect("login:login")
    return render(request, "assistant/config_stub.html", {
        "apiBase": "/assistant/api/",
    })


def chatInterfaceView(request: HttpRequest, chatId: str) -> HttpResponse:
    if loginRequired(request):
        return redirect("login:login")
    detail = _get_chat_service().get_session_detail(chatId, getUserId(request))
    if not detail:
        return redirect("assistant:config")

    subject_name = ""
    topic_name = ""
    session = detail.get("session", {})
    try:
        from bson import ObjectId
        from forum.models import ForumSubcategory, ForumTopic

        sub_id = session.get("subcategoryId")
        if sub_id and ObjectId.is_valid(sub_id):
            sub_doc = ForumSubcategory.collection.find_one({"_id": ObjectId(sub_id)})
            if sub_doc:
                subject_name = sub_doc.get("name", "")

        topic_id = session.get("topicId")
        if topic_id and ObjectId.is_valid(topic_id):
            topic_doc = ForumTopic.collection.find_one({"_id": ObjectId(topic_id)})
            if topic_doc:
                topic_name = topic_doc.get("name", "")
    except Exception:
        pass

    def _default(obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return str(obj)

    return render(request, "assistant/chat_stub.html", {
        "chat": detail,
        "chat_json": json.dumps(detail, default=_default),
        "apiBase": f"/assistant/api/sessions/{chatId}/",
        "subject_name": subject_name,
        "topic_name": topic_name,
    })


# --- JSON API (frontend-ready) ---

@require_http_methods(["GET"])
def apiConfig(request: HttpRequest) -> HttpResponse:
    if loginRequired(request):
        return _json_error("No autenticado", 401)

    user_id = getUserId(request)
    subjects = _get_chat_service().get_subjects()

    topics_by_subject = {}
    for sub in subjects:
        topics_by_subject[sub["id"]] = _get_chat_service().get_topics_by_subject(sub["id"])

    books_by_subject = {}
    for sub in subjects:
        books_by_subject[sub["id"]] = _get_chat_service().get_books_for_subject(sub["id"])

    return JsonResponse({
        "ok": True,
        "subjects": subjects,
        "topicsBySubject": topics_by_subject,
        "sessions": _get_chat_service().get_user_sessions(user_id),
        "booksBySubject": books_by_subject,
    })


@csrf_exempt
@require_http_methods(["POST"])
def apiCreateSession(request: HttpRequest) -> HttpResponse:
    if loginRequired(request):
        return _json_error("No autenticado", 401)

    user_id = getUserId(request)
    data = _parse_json_body(request)

    chat_name = request.POST.get("chatName") or data.get("chatName", "Nueva consulta")
    subcategory_id = request.POST.get("subcategoryId") or data.get("subcategoryId", "")
    topic_id = request.POST.get("topicId") or data.get("topicId") or None
    pdf_file = request.FILES.get("pdf") or None

    if not subcategory_id:
        return _json_error("subcategoryId es obligatorio")

    try:
        result = _get_chat_service().create_session(
            user_id=user_id,
            chat_name=chat_name,
            subcategory_id=subcategory_id,
            topic_id=topic_id,
            pdf_file=pdf_file,
        )
        return JsonResponse({"ok": True, **result})
    except Exception as e:
        return _json_error(str(e), 500)


@require_http_methods(["GET"])
def apiSessionDetail(request: HttpRequest, chatId: str) -> HttpResponse:
    if loginRequired(request):
        return _json_error("No autenticado", 401)

    detail = _get_chat_service().get_session_detail(chatId, getUserId(request))
    if not detail:
        return _json_error("Chat no encontrado", 404)

    return JsonResponse({"ok": True, **detail})


@csrf_exempt
@require_http_methods(["POST"])
def apiSendMessage(request: HttpRequest, chatId: str) -> HttpResponse:
    if loginRequired(request):
        return _json_error("No autenticado", 401)

    data = _parse_json_body(request)
    prompt = data.get("message") or data.get("prompt") or request.POST.get("message", "")

    try:
        result = _get_chat_service().send_message(chatId, getUserId(request), prompt)
        return JsonResponse({"ok": True, **result})
    except PermissionError as e:
        return _json_error(str(e), 403)
    except ValueError as e:
        return _json_error(str(e), 400)
    except Exception as e:
        return _json_error(str(e), 500)


@csrf_exempt
@require_http_methods(["POST"])
def apiExternalSearch(request: HttpRequest, chatId: str) -> HttpResponse:
    if loginRequired(request):
        return _json_error("No autenticado", 401)

    data = _parse_json_body(request)
    prompt = data.get("message") or data.get("prompt", "")
    source = data.get("source", "wikipedia")

    try:
        result = _get_chat_service().external_search(chatId, getUserId(request), prompt, source)
        return JsonResponse({"ok": True, **result})
    except PermissionError as e:
        return _json_error(str(e), 403)
    except ValueError as e:
        return _json_error(str(e), 400)
    except Exception as e:
        return _json_error(str(e), 500)


@csrf_exempt
@require_http_methods(["POST"])
def apiRateMessage(request: HttpRequest, chatId: str) -> HttpResponse:
    if loginRequired(request):
        return _json_error("No autenticado", 401)

    data = _parse_json_body(request)
    message_ref = data.get("messageId") or data.get("timestamp", "")
    rating = data.get("rating")

    if not message_ref or rating is None:
        return _json_error("messageId y rating son obligatorios")

    try:
        ok = _get_chat_service().rate_message(chatId, getUserId(request), message_ref, rating)
        if not ok:
            return _json_error("No se encontró el mensaje para calificar", 404)
        return JsonResponse({"ok": True})
    except PermissionError as e:
        return _json_error(str(e), 403)
    except ValueError as e:
        return _json_error(str(e), 400)


@csrf_exempt
@require_http_methods(["POST"])
def apiIngestPdf(request: HttpRequest) -> HttpResponse:
    if loginRequired(request):
        return _json_error("No autenticado", 401)

    subcategory_id = request.POST.get("subcategoryId", "")
    topic_id = request.POST.get("topicId") or None
    pdf_file = request.FILES.get("pdf")

    if not subcategory_id or not pdf_file:
        return _json_error("subcategoryId y pdf son obligatorios")

    try:
        result = _get_chat_service().ingestion.process_pdf(
            pdf_file,
            subcategory_id=subcategory_id,
            topic_id=topic_id,
            uploaded_by=getUserId(request),
        )
        return JsonResponse({"ok": True, "ingestion": result})
    except Exception as e:
        return _json_error(str(e), 500)
