from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-company/', views.add_company, name='add_company'),
    path('add-tender/', views.add_tender, name='add_tender'),
    path('add-expense/', views.add_expense, name='add_expense'),
]
