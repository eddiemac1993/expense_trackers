from django.urls import path
from .views import projection_dashboard, archive_project, project_detail

app_name = 'projections'

urlpatterns = [
    path('', projection_dashboard, name='dashboardpro'),
    path('archive/<int:pk>/', archive_project, name='archive_project'),
    path('project/<int:pk>/', project_detail, name='project_detail'),
]
