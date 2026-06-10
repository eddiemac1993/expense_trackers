from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('tracker/', include('tracker.urls')),
    path('projections/', include('projections.urls')),
    path('papers/', include('papers.urls')),
    path('documents/', include('documents.urls')),
    path("", include("reports.urls")),
    path("cmm-expenses/", include("cmm_expenses.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
