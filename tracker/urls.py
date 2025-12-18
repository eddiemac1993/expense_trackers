# tracker/urls.py
from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    # Dashboard / pages
    path('', views.dashboard, name='dashboard'),

    # Company CRUD
    path('company/add/', views.add_company, name='company_add'),
    path('company/<int:pk>/edit/', views.company_edit, name='company_edit'),
    path('company/<int:pk>/delete/', views.company_delete, name='company_delete'),

    # Tender CRUD
    path('tender/add/', views.add_tender, name='tender_add'),
    path('tender/<int:pk>/edit/', views.tender_edit, name='tender_edit'),
    path('tender/<int:pk>/delete/', views.tender_delete, name='tender_delete'),

    # Expense CRUD & list
    path('expense/add/', views.add_expense, name='expense_add'),
    path('expense/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expense/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('expenses/', views.expense_list, name='expense_list'),

    # Payments (simple add endpoint used by add_payment view)
    path('payment/add/', views.add_payment, name='add_payment'),

    # API endpoints consumed by the dashboard JS
    path('api/tenders/', views.api_tenders, name='api_tenders'),
    path('api/tenders_by_company/', views.api_tenders_by_company, name='api_tenders_by_company'),
    path('api/summary/', views.api_summary, name='api_summary'),
    path('api/expenses/', views.api_expenses, name='api_expenses'),
]
