from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Create
    path('company/add/', views.add_company, name='company_add'),
    path('tender/add/', views.add_tender, name='tender_add'),
    path('expense/add/', views.add_expense, name='expense_add'),
    path('expenses/', views.expense_list, name='expense_list'),

    # Edit
    path('company/<int:pk>/edit/', views.company_edit, name='company_edit'),
    path('tender/<int:pk>/edit/', views.tender_edit, name='tender_edit'),
    path('expense/<int:pk>/edit/', views.expense_edit, name='expense_edit'),

    # Delete
    path('company/<int:pk>/delete/', views.company_delete, name='company_delete'),
    path('tender/<int:pk>/delete/', views.tender_delete, name='tender_delete'),
    path('expense/<int:pk>/delete/', views.expense_delete, name='expense_delete'),

    # AJAX / API endpoints - CORRECTED NAMES:
    path('api/tenders/', views.api_tenders, name='api_tenders'),
    path('api/tenders-by-company/', views.api_tenders_by_company, name='api_tenders_by_company'),  # Fixed name
    path('api/summary/', views.api_summary, name='api_summary'),
    path('api/expenses/', views.api_expenses, name='api_expenses'),
]