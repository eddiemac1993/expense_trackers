from django.urls import path
from . import views

urlpatterns = [
    path("project-report/", views.project_report, name="project_report"),

    path(
        "project-report/<int:project_id>/edit/",
        views.project_report,
        name="edit_project_report"
    ),

    path(
        "project-report/<int:project_id>/delete/",
        views.delete_project_report,
        name="delete_project_report"
    ),

    path("project-report/pdf/", views.generate_project_report_pdf, name="project_report_pdf"),

    path(
        "project-report/<int:project_id>/expenses/",
        views.project_expenses,
        name="project_expenses"
    ),
]