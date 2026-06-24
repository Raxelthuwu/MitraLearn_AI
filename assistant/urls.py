from django.urls import path
from assistant import views

app_name = "assistant"

urlpatterns = [
    # Vista principal del chatbot (RF-1)
    path("", views.chatHome, name="home"),
    # API: enviar prompt → respuesta RAG (RF-3, RF-5, RF-7, RF-8)
    path("send/", views.chatSend, name="send"),
    # API: historial de conversación por chatId (RF-8)
    path("history/<str:chatId>/", views.chatHistory, name="history"),
    # API: calificar respuesta (RF-10)
    path("rate/", views.chatRate, name="rate"),
    # API: iniciar chat nuevo (RF-8)
    path("new/", views.chatNew, name="new"),
    # API: subir documento PDF y vectorizarlo (RF-1, RF-2)
    path("upload/", views.documentUpload, name="upload"),
]