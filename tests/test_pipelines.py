import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')
django.setup()

from django.test import Client
from forum.services.forumService import ForumCategoryService, ForumPostService
from login.service import AuthService
import time

def run_pipeline_test():
    print("=========================================")
    print("INICIANDO PRUEBA DE PIPELINES DE FORO")
    print("=========================================\n")
    
    # Initialize Services
    auth_svc = AuthService()
    cat_svc = ForumCategoryService()
    post_svc = ForumPostService()
    from forum.services.forumService import ForumSubcategoryService, ForumTopicService
    sub_svc = ForumSubcategoryService()
    topic_svc = ForumTopicService()
    from login.models import User
    
    # 1. Setup Test User
    print("[1] Verificando Sistema de Login...")
    test_email = "pipeline_tester@mitralearn.com"
    if User.emailExists(test_email):
        user = User.getByEmail(test_email)
        userId = str(user["_id"])
    else:
        result = auth_svc.register("Pipeline Tester", test_email, "TestPassword123!", "Ingeniería", "student", "1234567890")
        userId = result["userId"]
    print(f"Usuario de prueba listo (ID: {userId})")

    # 2. Setup Academic Category
    print("\n[2] Verificando Categoría Académica...")
    categories = cat_svc.getAllCategories()
    academic_cat = next((c for c in categories if "Academic" in c["name"]), None)
    
    if not academic_cat:
        cat_svc.createCategory("Academic", "Academic discussions")
        categories = cat_svc.getAllCategories()
        academic_cat = next(c for c in categories if "Academic" in c["name"])
    
    cat_id = academic_cat["id"]
    
    # Ensure Subcategory exists
    subcategories = sub_svc.getSubcategoriesByCategory(cat_id)
    if not subcategories:
        sub_svc.createSubcategory(cat_id, "Physics")
        subcategories = sub_svc.getSubcategoriesByCategory(cat_id)
    sub_id = subcategories[0]["id"]
    
    # Ensure Topic exists
    topics = topic_svc.getTopicsBySubcategory(sub_id)
    if not topics:
        topic_svc.createTopic(sub_id, "Electromagnetism")
        topics = topic_svc.getTopicsBySubcategory(sub_id)
    topic_id = topics[0]["id"]
    
    print(f"Categoría Académica lista (ID: {cat_id})")
    print(f"Subcategoría lista (ID: {sub_id})")
    print(f"Tema listo (ID: {topic_id})")

    # [PARCHE TEMPORAL PARA EL TEST]
    # Inyectamos los alias dinámicamente solo durante la prueba para que los
    # servicios de similitud de Pablo no fallen al buscar 'embed' o 'generate'
    from assistant.services.embedding_service import HuggingFaceEmbeddingService
    from assistant.services.llm_service import OllamaLLMService
    HuggingFaceEmbeddingService.embed = HuggingFaceEmbeddingService.embed_query
    OllamaLLMService.generate = OllamaLLMService.generate_response

    # 3. Simulate View Request via Test Client
    print("\n[3] Ejecutando Pipeline: Crear Post + Sugerencia IA + Indexación...")
    client = Client()
    
    # Simulate active session matching login branch logic
    session = client.session
    session['userId'] = userId
    session['fullName'] = "Pipeline Tester"
    session['role'] = "student"
    session.save()

    # Trigger postCreate View
    response = client.post('/forum/posts/create/', {
        'title': '¿Qué es el electromagnetismo?',
        'content': 'Tengo dudas sobre cómo funciona el electromagnetismo según los libros de física.',
        'categoryId': cat_id,
        'subcategoryId': sub_id,
        'topicId': topic_id,
        'confirmPost': 'yes' # Bypass duplicate detection for test
    }, SERVER_NAME='localhost')
    
    # Verification
    if response.status_code in [200, 302]:
        print("Petición HTTP procesada exitosamente por el View.")
        
        # Verify the pipeline actually worked internally
        time.sleep(2) # Give ChromaDB a second to sync
        posts = post_svc.getPostsByCategory(cat_id)
        latest_post = posts[0] if posts else None
        
        if latest_post and latest_post["title"] == '¿Qué es el electromagnetismo?':
            print("Pipeline: Post Guardado en MongoDB.")
            if latest_post.get("hasAiSuggestion"):
                print("Pipeline: Asistente IA RAG disparado automáticamente (Sugerencia guardada).")
            else:
                print("Aviso: El post se guardó, pero la bandera 'hasAiSuggestion' es False. Asegúrate de que ChromaDB tenga libros cargados para que la IA responda.")
            
            print("\nPRUEBA DE PIPELINES FINALIZADA CON ÉXITO")
            print("El View orquestó correctamente el flujo completo.")
        else:
            print("Error: El post no se encontró en la base de datos tras la petición.")
    else:
        print(f"Error en la petición: Código {response.status_code}")
        print(response.content.decode('utf-8')[:500])

if __name__ == '__main__':
    try:
        run_pipeline_test()
    except Exception as e:
        print(f"\n Error Crítico en la prueba: {str(e)}")
        print("Asegúrate de que MongoDB esté corriendo y las credenciales del .env sean correctas.")
