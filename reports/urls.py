from django.urls import path

from . import views

urlpatterns = [

    # ==========================================
    # PROJECT REPORT DASHBOARD
    # ==========================================

    path(
        "",
        views.project_report,
        name="project_report"
    ),

    # ==========================================
    # AWARDED PROJECTS
    # ==========================================

    path(
        "project/<int:project_id>/edit/",
        views.project_report,
        name="edit_project_report"
    ),

    path(
        "project/<int:project_id>/delete/",
        views.delete_project_report,
        name="delete_project_report"
    ),

    path(
        "project/<int:project_id>/expenses/",
        views.project_expenses,
        name="project_expenses"
    ),

    # ==========================================
    # PDF REPORT
    # ==========================================

    path(
        "report/pdf/",
        views.generate_project_report_pdf,
        name="project_report_pdf"
    ),

    # ==========================================
    # PENDING PROJECTS
    # ==========================================

    path(
        "pending/add/",
        views.add_pending_project,
        name="add_pending_project"
    ),

    path(
        "pending/<int:pending_id>/award/",
        views.award_pending_project,
        name="award_pending_project"
    ),

]