from django.urls import path

from . import views

urlpatterns = [

    path("", views.project_report, name="project_report"),

    path(
        "project/<int:project_id>/edit/",
        views.project_report,
        name="edit_project_report"
    ),

    path(
        "internal/project/<int:project_id>/edit/",
        views.internal_project_report,
        name="internal_edit_project_report"
    ),

    path(
        "internal/login/",
        views.internal_project_login,
        name="internal_project_login"
    ),

    path(
        "internal/",
        views.internal_project_report,
        name="internal_project_report"
    ),

    path(
        "internal/logout/",
        views.internal_project_logout,
        name="internal_project_logout"
    ),

    path(
        "project/<int:project_id>/move-to-internal/",
        views.move_project_to_internal,
        name="move_project_to_internal"
    ),

    path(
        "project/<int:project_id>/move-to-user-view/",
        views.move_project_to_user_view,
        name="move_project_to_user_view"
    ),

    path(
        "project-report/<int:project_id>/expenses/<int:expense_id>/edit/",
        views.edit_expense,
        name="edit_expense"
    ),

    path(
        "project-report/<int:project_id>/expenses/<int:expense_id>/delete/",
        views.delete_expense,
        name="delete_expense"
    ),

    path(
        "project-report/<int:project_id>/payments/<int:payment_id>/edit/",
        views.edit_payment,
        name="edit_payment"
    ),

    path(
        "project-report/<int:project_id>/payments/<int:payment_id>/delete/",
        views.delete_payment,
        name="delete_payment"
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

    path(
        "project/<int:project_id>/payments/",
        views.project_payments,
        name="project_payments"
    ),

    path(
        "report/pdf/",
        views.generate_project_report_pdf,
        name="project_report_pdf"
    ),

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
