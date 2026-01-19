from django.urls import path
from . import views

app_name = 'projections'

urlpatterns = [
    path('', views.projection_dashboard, name='dashboardpro'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
    path('archive/<int:pk>/', views.archive_project, name='archive_project'),
    path('export-pdf/', views.export_projects_pdf, name='export_pdf'),
]