from django.urls import path
from . import views

urlpatterns = [
    path('', views.paper_list, name='paper_list'),
    path('new/', views.create_paper_entry, name='paper_create'),

    # HTML preview
    path(
        'preview/<int:entry_id>/<str:paper_type>/',
        views.paper_preview,
        name='paper_preview'
    ),

    # PDF output
    path(
        'pdf/<int:entry_id>/<str:paper_type>/',
        views.paper_pdf,
        name='paper_pdf'
    ),
]
