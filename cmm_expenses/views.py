from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.contrib import messages

from .models import ProjectRecord, ProjectExpense, PendingProjectRecord
from .forms import ProjectForm, ExpenseForm, PendingProjectForm


def dashboard(request):
    projects = ProjectRecord.objects.all()
    pending_projects = PendingProjectRecord.objects.all()
    expenses = ProjectExpense.objects.select_related("project", "tag")[:10]

    total_contract = sum((p.contract_value for p in projects), Decimal("0.00"))
    total_paid = sum((p.paid_value for p in projects), Decimal("0.00"))
    total_expenses = sum((p.expense_value for p in projects), Decimal("0.00"))
    total_profit = sum((p.profit_value for p in projects), Decimal("0.00"))
    total_pending_payment = sum((p.pending_payment_value for p in projects), Decimal("0.00"))

    context = {
        "projects": projects,
        "pending_projects": pending_projects,
        "recent_expenses": expenses,
        "total_contract": total_contract,
        "total_paid": total_paid,
        "total_expenses": total_expenses,
        "total_profit": total_profit,
        "total_pending_payment": total_pending_payment,
    }

    return render(request, "dashboard.html", context)


def project_list(request):
    projects = ProjectRecord.objects.all()
    return render(request, "project_list.html", {"projects": projects})


def add_project(request):
    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project added successfully.")
        return redirect("cmm_project_list")

    return render(request, "project_form.html", {"form": form, "title": "Add Project"})


def edit_project(request, pk):
    project = get_object_or_404(ProjectRecord, pk=pk)
    form = ProjectForm(request.POST or None, instance=project)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project updated successfully.")
        return redirect("cmm_project_list")

    return render(request, "project_form.html", {"form": form, "title": "Edit Project"})


def delete_project(request, pk):
    project = get_object_or_404(ProjectRecord, pk=pk)

    if request.method == "POST":
        project.delete()
        messages.success(request, "Project deleted successfully.")
        return redirect("cmm_project_list")

    return render(request, "confirm_delete.html", {"object": project})


def project_expenses(request, pk):
    project = get_object_or_404(ProjectRecord, pk=pk)
    expenses = project.expenses.select_related("tag").all()

    return render(request, "project_expenses.html", {
        "project": project,
        "expenses": expenses,
    })


def add_expense(request, pk):
    project = get_object_or_404(ProjectRecord, pk=pk)

    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.project = project
            expense.save()
            messages.success(request, "Expense added successfully.")
            return redirect("cmm_project_expenses", pk=project.pk)
    else:
        form = ExpenseForm(initial={"project": project})

    return render(request, "expense_form.html", {
        "form": form,
        "project": project,
        "title": "Add Expense",
    })


def edit_expense(request, pk):
    expense = get_object_or_404(ProjectExpense, pk=pk)
    project = expense.project
    form = ExpenseForm(request.POST or None, instance=expense)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Expense updated successfully.")
        return redirect("cmm_project_expenses", pk=project.pk)

    return render(request, "expense_form.html", {
        "form": form,
        "project": project,
        "title": "Edit Expense",
    })


def delete_expense(request, pk):
    expense = get_object_or_404(ProjectExpense, pk=pk)
    project = expense.project

    if request.method == "POST":
        expense.delete()
        messages.success(request, "Expense deleted successfully.")
        return redirect("cmm_project_expenses", pk=project.pk)

    return render(request, "confirm_delete.html", {"object": expense})


def pending_project_list(request):
    pending_projects = PendingProjectRecord.objects.all()
    return render(request, "pending_project_list.html", {
        "pending_projects": pending_projects
    })


def add_pending_project(request):
    form = PendingProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pending project added successfully.")
        return redirect("cmm_pending_project_list")

    return render(request, "pending_project_form.html", {
        "form": form,
        "title": "Add Pending Project",
    })


def edit_pending_project(request, pk):
    pending_project = get_object_or_404(PendingProjectRecord, pk=pk)
    form = PendingProjectForm(request.POST or None, instance=pending_project)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pending project updated successfully.")
        return redirect("cmm_pending_project_list")

    return render(request, "pending_project_form.html", {
        "form": form,
        "title": "Edit Pending Project",
    })


def delete_pending_project(request, pk):
    pending_project = get_object_or_404(PendingProjectRecord, pk=pk)

    if request.method == "POST":
        pending_project.delete()
        messages.success(request, "Pending project deleted successfully.")
        return redirect("cmm_pending_project_list")

    return render(request, "confirm_delete.html", {"object": pending_project})