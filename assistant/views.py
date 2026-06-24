import uuid
import json
import os
from datetime import datetime

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from assistant.models import Conversation, ChatSummary
from assistant.services.rag_service import RAGService


# Service singleton
ragSvc = RAGService()

# Mensajes sin respuesta para activar síntesis de resumen (RF-7)
SUMMARY_THRESHOLD = 3

# Configuración de subida de documentos (RF-1, RF-2)
ALLOWED_DOC_EXTENSIONS = {".pdf"}
MAX_DOC_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
DOCUMENTS_ROOT = os.path.join(settings.BASE_DIR, "media", "documents")


# ──────────────────────────────────────────────
# Helpers de sesión (mismo patrón que forum/views.py y login/viewsLogin.py)
# ──────────────────────────────────────────────

def getUserId(request: HttpRequest) -> str:
    return request.session.get("userId", "")


def loginRequired(request: HttpRequest) -> bool:
    return not getUserId(request)


# ──────────────────────────────────────────────
# Vista principal del chat (RF-1, RF-3, RF-4)
# ──────────────────────────────────────────────

def chatHome(request: HttpRequest) -> HttpResponse:
    # Muestra la interfaz del chatbot; requiere sesión activa
    if loginRequired(request):
        return redirect("login:login")

    # Genera un chatId nuevo si no existe en sesión (cada sesión = un chat)
    if "chatId" not in request.session:
        request.session["chatId"] = str(uuid.uuid4())

    chatId   = request.session["chatId"]
    fullName = request.session.get("fullName", "Estudiante")

    # Historial de la sesión actual para renderizar los mensajes existentes
    history = Conversation.get_by_chat(chatId)

    # Resumen de contexto acumulado (legado de conversaciones anteriores)
    summary = ChatSummary.get_by_chat(chatId)

    return render(request, "assistant/chat.html", {
        "chatId":    chatId,
        "fullName":  fullName,
        "history":   history,
        "summary":   summary,
    })


# ──────────────────────────────────────────────
# Endpoint: enviar prompt y recibir respuesta RAG (RF-3, RF-5, RF-7, RF-8)
# ──────────────────────────────────────────────

@csrf_exempt
@require_POST
def chatSend(request: HttpRequest) -> JsonResponse:
    # Recibe { prompt, chatId, chatName } y devuelve { response, sources }
    if loginRequired(request):
        return JsonResponse({"error": "Sesión requerida."}, status=401)

    try:
        body     = json.loads(request.body)
        prompt   = body.get("prompt", "").strip()
        chatId   = body.get("chatId", request.session.get("chatId", ""))
        chatName = body.get("chatName", "Chat sin título").strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Cuerpo JSON inválido."}, status=400)

    if not prompt:
        return JsonResponse({"error": "El prompt no puede estar vacío."}, status=400)

    if not chatId:
        return JsonResponse({"error": "chatId requerido."}, status=400)

    # Construir contexto de legado si existe resumen previo
    legacySummary = ""
    existingSummary = ChatSummary.get_by_chat(chatId)
    if existingSummary:
        legacySummary = existingSummary.get("summaryText", "")

    # Construir prompt aumentado con resumen de legado si aplica (RF-4, RF-7)
    augmentedPrompt = prompt
    if legacySummary:
        augmentedPrompt = (
            f"[Contexto de conversación previa]\n{legacySummary}\n\n"
            f"[Nueva consulta]\n{prompt}"
        )

    # Invocar pipeline RAG: retrieval + generación
    try:
        aiResponse = ragSvc.generate_augmented_response(augmentedPrompt)
    except Exception as e:
        return JsonResponse({"error": f"Error en el modelo: {str(e)}"}, status=500)

    # Persistir interacción en MongoDB (RF-8)
    Conversation.create(
        chatId     = chatId,
        chatName   = chatName,
        promptSent = prompt,
        aiResponse = aiResponse,
    )

    # Activar síntesis de resumen cada SUMMARY_THRESHOLD mensajes (RF-7)
    history = Conversation.get_by_chat(chatId)
    if len(history) % SUMMARY_THRESHOLD == 0:
        _updateSummary(chatId, chatName, history)

    return JsonResponse({
        "response": aiResponse,
        "chatId":   chatId,
    })


# ──────────────────────────────────────────────
# Endpoint: historial de un chat (RF-8)
# ──────────────────────────────────────────────

@require_GET
def chatHistory(request: HttpRequest, chatId: str) -> JsonResponse:
    # Devuelve todos los mensajes de un chatId ordenados por timestamp
    if loginRequired(request):
        return JsonResponse({"error": "Sesión requerida."}, status=401)

    history = Conversation.get_by_chat(chatId)

    # Serializar ObjectId y datetime a string para JSON
    serialized = []
    for doc in history:
        serialized.append({
            "id":          str(doc.get("_id", "")),
            "chatId":      doc.get("chatId", ""),
            "chatName":    doc.get("chatName", ""),
            "timestamp":   doc.get("timestamp", "").isoformat() if doc.get("timestamp") else "",
            "promptSent":  doc.get("promptSent", ""),
            "aiResponse":  doc.get("aiResponse", ""),
            "userRating":  doc.get("userRating", None),
        })

    return JsonResponse({"history": serialized})


# ──────────────────────────────────────────────
# Endpoint: calificar una respuesta (RF-10)
# ──────────────────────────────────────────────

@csrf_exempt
@require_POST
def chatRate(request: HttpRequest) -> JsonResponse:
    # Recibe { chatId, timestamp, userRating } y actualiza el documento
    if loginRequired(request):
        return JsonResponse({"error": "Sesión requerida."}, status=401)

    try:
        body       = json.loads(request.body)
        chatId     = body.get("chatId", "").strip()
        timestamp  = body.get("timestamp", "").strip()
        userRating = body.get("userRating")
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Cuerpo JSON inválido."}, status=400)

    if not chatId or not timestamp or userRating is None:
        return JsonResponse({"error": "chatId, timestamp y userRating son requeridos."}, status=400)

    try:
        rating = int(userRating)
        if not (1 <= rating <= 10):
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({"error": "userRating debe ser un entero entre 1 y 10."}, status=400)

    # Convertir timestamp string a datetime para la query de Mongo
    try:
        ts = datetime.fromisoformat(timestamp)
    except ValueError:
        return JsonResponse({"error": "Formato de timestamp inválido. Usa ISO 8601."}, status=400)

    Conversation.update_rating(chatId, ts, rating)

    return JsonResponse({"ok": True, "userRating": rating})


# ──────────────────────────────────────────────
# Endpoint: iniciar nuevo chat (limpia sesión) (RF-8)
# ──────────────────────────────────────────────

@require_POST
def chatNew(request: HttpRequest) -> JsonResponse:
    # Genera un nuevo chatId en sesión y lo devuelve al frontend
    if loginRequired(request):
        return JsonResponse({"error": "Sesión requerida."}, status=401)

    newChatId = str(uuid.uuid4())
    request.session["chatId"] = newChatId

    return JsonResponse({"chatId": newChatId})


# ──────────────────────────────────────────────
# Endpoint: subir documento PDF e indexarlo en el RAG (RF-1, RF-2)
# ──────────────────────────────────────────────

@csrf_exempt
@require_POST
def documentUpload(request: HttpRequest) -> JsonResponse:
    # Recibe multipart/form-data: file=<pdf>, subject=<str>
    if loginRequired(request):
        return JsonResponse({"error": "Sesión requerida."}, status=401)

    uploadedFile = request.FILES.get("file")
    subject = request.POST.get("subject", "general").strip() or "general"

    if not uploadedFile:
        return JsonResponse({"error": "No se recibió ningún archivo."}, status=400)

    originalName = uploadedFile.name
    ext = os.path.splitext(originalName)[1].lower()

    if ext not in ALLOWED_DOC_EXTENSIONS:
        return JsonResponse({"error": "Solo se permiten archivos PDF."}, status=400)

    if uploadedFile.size > MAX_DOC_SIZE_BYTES:
        return JsonResponse({"error": "El archivo supera el tamaño máximo permitido (20MB)."}, status=400)

    # Sanear el nombre de la asignatura para usarlo como carpeta
    safeSubject = "".join(c for c in subject if c.isalnum() or c in (" ", "_", "-")).strip() or "general"

    # Directorio local organizado por asignatura: media/documents/<subject>/
    subjectDir = os.path.join(DOCUMENTS_ROOT, safeSubject)
    os.makedirs(subjectDir, exist_ok=True)

    # Evitar colisiones de nombre con prefijo uuid corto
    safeFileName = f"{uuid.uuid4().hex[:8]}_{originalName}"
    destPath = os.path.join(subjectDir, safeFileName)

    try:
        with open(destPath, "wb") as destination:
            for chunk in uploadedFile.chunks():
                destination.write(chunk)
    except OSError as e:
        return JsonResponse({"error": f"No se pudo guardar el archivo: {str(e)}"}, status=500)

    # Procesar y vectorizar el documento (RF-2)
    try:
        result = ragSvc.index_document(destPath, safeSubject, originalName)
    except Exception as e:
        # El archivo quedó guardado pero falló la vectorización
        return JsonResponse({
            "error": f"El archivo se guardó pero no se pudo vectorizar: {str(e)}"
        }, status=500)

    return JsonResponse({
        "ok": True,
        "fileName": originalName,
        "subject": safeSubject,
        "chunksIndexed": result["chunks_indexed"],
        "pages": result["pages"],
        "message": f"'{originalName}' fue procesado y vectorizado correctamente ({result['chunks_indexed']} fragmentos de {result['pages']} páginas).",
    })


# ──────────────────────────────────────────────
# Helpers privados
# ──────────────────────────────────────────────

def _updateSummary(chatId: str, chatName: str, history: list) -> None:
    # Sintetiza resumen ejecutivo del historial usando el LLM (RF-7)
    # Se llama internamente; los errores se silencian para no bloquear la respuesta al usuario

    try:
        # Construir texto del historial para sintetizar
        historyText = "\n".join([
            f"Usuario: {doc.get('promptSent', '')}\nAsistente: {doc.get('aiResponse', '')}"
            for doc in history
        ])

        summaryPrompt = (
            "Resume de forma concisa los temas clave tratados en la siguiente "
            "conversación académica, en máximo 5 oraciones:\n\n"
            f"{historyText}"
        )

        summaryText = ragSvc.llm_service.generate_response(summaryPrompt)

        existing = ChatSummary.get_by_chat(chatId)
        if existing:
            ChatSummary.update_chat_summary(chatId, summaryText)
        else:
            ChatSummary.create(chatId, chatName, summaryText)

    except Exception as e:
        print(f"[WARN] _updateSummary failed for chatId={chatId}: {e}")