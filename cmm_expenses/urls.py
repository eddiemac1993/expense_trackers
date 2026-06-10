from django.urls import path
from . import views


urlpatterns = [
    path("", views.dashboard, name="cmm_dashboard"),

    path("projects/", views.project_list, name="cmm_project_list"),
    path("projects/add/", views.add_project, name="cmm_add_project"),
    path("projects/<int:pk>/edit/", views.edit_project, name="cmm_edit_project"),
    path("projects/<int:pk>/delete/", views.delete_project, name="cmm_delete_project"),

    path("projects/<int:pk>/expenses/", views.project_expenses, name="cmm_project_expenses"),
    path("projects/<int:pk>/expenses/add/", views.add_expense, name="cmm_add_expense"),

    path("expenses/<int:pk>/edit/", views.edit_expense, name="cmm_edit_expense"),
    path("expenses/<int:pk>/delete/", views.delete_expense, name="cmm_delete_expense"),

    path("pending/", views.pending_project_list, name="cmm_pending_project_list"),
    path("pending/add/", views.add_pending_project, name="cmm_add_pending_project"),
    path("pending/<int:pk>/edit/", views.edit_pending_project, name="cmm_edit_pending_project"),
    path("pending/<int:pk>/delete/", views.delete_pending_project, name="cmm_delete_pending_project"),
]