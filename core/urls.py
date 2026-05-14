from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('forum/', include('forum.urls', namespace='forum')),
    path('login/', include('login.urls', namespace='login')),
]