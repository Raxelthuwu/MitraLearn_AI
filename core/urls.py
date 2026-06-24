from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('assistant/', include('assistant.urls', namespace='assistant')),
    path('forum/', include('forum.urls', namespace='forum')),
    path('login/', include('login.urls', namespace='login')),
]