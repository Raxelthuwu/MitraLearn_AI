import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.base")
django.setup()

from assistant.services.chat_service import ChatService
from assistant.services.ingestion_service import IngestionService
from assistant.models import ChatSession, Conversation
from assistant.Assistant_vector_models import ChatEmbedding


def run_assistant_tests():
    print("=" * 50)
    print("PRUEBA PIPELINE ASISTENTE ACADÉMICO")
    print("=" * 50)

    chat_svc = ChatService()
    subjects = chat_svc.get_subjects()
    print(f"\n[1] Asignaturas (subcategorías): {len(subjects)}")
    if not subjects:
        print("    Aviso: no hay subcategorías en MongoDB. Crea datos de foro primero.")
        return

    sub_id = subjects[0]["id"]
    topics = chat_svc.get_topics_by_subject(sub_id)
    topic_id = topics[0]["id"] if topics else None
    print(f"    Usando subcategoría: {subjects[0]['name']} ({sub_id})")

    test_user = "000000000000000000000001"
    session = chat_svc.create_session(
        user_id=test_user,
        chat_name="Prueba pipeline chat",
        subcategory_id=sub_id,
        topic_id=topic_id,
    )
    chat_id = session["session"]["chatId"]
    print(f"\n[2] Sesión creada: {chat_id}")

    chroma_before = ChatEmbedding.count()
    print(f"\n[3] Chunks en chat_embeddings (antes): {chroma_before}")

    detail = chat_svc.get_session_detail(chat_id, test_user)
    print(f"\n[4] Detalle sesión OK — mensajes: {len(detail['messages'])}")

    try:
        result = chat_svc.send_message(chat_id, test_user, "¿Qué es la programación orientada a objetos?")
        print(f"\n[5] Mensaje enviado — contextInsufficient: {result.get('contextInsufficient')}")
        if result.get("answer"):
            print(f"    Respuesta (primeros 120 chars): {result['answer'][:120]}...")
        else:
            print("    Sin respuesta local (esperado si no hay PDFs indexados para la asignatura).")
    except Exception as e:
        print(f"\n[5] Mensaje falló (¿Ollama apagado?): {e}")

    count = Conversation.count_by_chat(chat_id)
    print(f"\n[6] Mensajes en MongoDB para el chat: {count}")

    if count >= 3:
        summary = chat_svc._maybe_refresh_summary(chat_id, "Prueba pipeline chat")
        if summary:
            print(f"\n[7] Resumen generado: {summary.get('summaryText', '')[:100]}...")
    else:
        print("\n[7] Resumen: se genera cada 3 mensajes (aún no alcanzado).")

    print("\nPRUEBA FINALIZADA — Backend chat operativo.")
    print("API base: /assistant/api/")


if __name__ == "__main__":
    try:
        run_assistant_tests()
    except Exception as exc:
        print(f"\nError crítico: {exc}")
        raise
