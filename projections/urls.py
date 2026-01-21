from django.urls import path
from . import views

app_name = 'projections'

urlpatterns = [
    path('', views.projection_dashboard, name='dashboardpro'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
    path('archive/<int:pk>/', views.archive_project, name='archive_project'),
    path('export-pdf/', views.export_projects_pdf, name='export_pdf'),
    path('payments/', views.payments_dashboard, name='payments_dashboard'),
    path(
    'payments/add/<int:pk>/',
    views.add_payment,
    name='add_payment'
),
    path(
    'payments/project/<int:pk>/',
    views.project_payments,
    name='project_payments'
),
    path(
    'payments/edit/<int:payment_id>/',
    views.edit_payment,
    name='edit_payment'
),

    path('payments/pdf/', views.payments_dashboard_pdf, name='payments_dashboard_pdf'),
]