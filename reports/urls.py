from django.urls import path

from . import views


urlpatterns = [

    # =========================
    # MAIN PROJECT REPORT
    # =========================

    path(
        "project-report/",
        views.project_report,
        name="project_report"
    ),

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

    path(
        "project-report/pdf/",
        views.generate_project_report_pdf,
        name="project_report_pdf"
    ),

    # =========================
    # PROJECT EXPENSES
    # =========================

    path(
        "project-report/<int:project_id>/expenses/",
        views.project_expenses,
        name="project_expenses"
    ),

    # =========================
    # PENDING PROJECTS
    # =========================

    path(
        "pending-project/add/",
        views.add_pending_project,
        name="add_pending_project"
    ),

    path(
        "pending-project/<int:pending_id>/award/",
        views.award_pending_project,
        name="award_pending_project"
    ),

]