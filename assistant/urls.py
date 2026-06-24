from django.urls import path
from assistant import views

app_name = "assistant"

urlpatterns = [
    # HTML stubs (provisional)
    path("", views.chatConfigView, name="config"),
    path("chat/<str:chatId>/", views.chatInterfaceView, name="chat"),

    # JSON API — conectar el front aquí
    path("api/config/", views.apiConfig, name="api_config"),
    path("api/sessions/", views.apiCreateSession, name="api_create_session"),
    path("api/sessions/<str:chatId>/", views.apiSessionDetail, name="api_session_detail"),
    path("api/sessions/<str:chatId>/messages/", views.apiSendMessage, name="api_send_message"),
    path("api/sessions/<str:chatId>/external-search/", views.apiExternalSearch, name="api_external_search"),
    path("api/sessions/<str:chatId>/rate/", views.apiRateMessage, name="api_rate_message"),
    path("api/ingest/", views.apiIngestPdf, name="api_ingest_pdf"),
]
