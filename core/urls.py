from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Redirect root to forum
    path('', RedirectView.as_view(url='/forum/', permanent=False), name='home'),
    path('forum/', include('forum.urls', namespace='forum')),
    path('login/', include('login.urls', namespace='login')),
    path('assistant/', include('assistant.urls', namespace='assistant')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
