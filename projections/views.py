from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages

from .models import ProjectRecord


@require_http_methods(["GET", "POST"])
def projection_dashboard(request):
    """
    Project Projections Dashboard
    - GET: list records, filters, totals, charts
    - POST: create new project record
    """

    # =========================
    # HANDLE CREATE (POST)
    # =========================
    if request.method == "POST":
        company_select = request.POST.get("company_select")
        company_new = request.POST.get("company_new", "").strip()

        # Resolve company name
        if company_select == "__new__":
            if not company_new:
                messages.error(request, "Please enter a new company name.")
                return redirect("projections:dashboardpro")
            company_name = company_new
        else:
            if not company_select:
                messages.error(request, "Please select a company.")
                return redirect("projections:dashboardpro")
            company_name = company_select

        # Parse project date safely
        try:
            project_date = date.fromisoformat(request.POST.get("project_date"))
        except Exception:
            messages.error(request, "Invalid project date.")
            return redirect("projections:dashboardpro")

        # Create project record
        ProjectRecord.objects.create(
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            company=company_name,
            customer=request.POST.get("customer"),
            amount=request.POST.get("amount"),
            project_date=project_date,
            status=request.POST.get("status"),
        )

        messages.success(request, "Project record added successfully.")
        return redirect("projections:dashboardpro")

    # =========================
    # HANDLE DISPLAY (GET)
    # =========================

    records = (
        ProjectRecord.objects
        .filter(is_active=True)
        .order_by("-project_date")
    )

    # Distinct companies for dropdown
    companies = (
        ProjectRecord.objects
        .filter(is_active=True)
        .values_list("company", flat=True)
        .distinct()
        .order_by("company")
    )

    # Available years
    years = (
        ProjectRecord.objects
        .filter(is_active=True)
        .values_list("year", flat=True)
        .distinct()
        .order_by("-year")
    )

    # Filters
    company = request.GET.get("company")
    status = request.GET.get("status")
    year = request.GET.get("year")

    if company:
        records = records.filter(company=company)

    if status:
        records = records.filter(status=status)

    if year:
        records = records.filter(year=year)

    # =========================
    # AGGREGATES
    # =========================
    total_won = (
        records.filter(status="WON")
        .aggregate(total=Sum("amount"))
        .get("total") or 0
    )

    total_lost = (
        records.filter(status="LOST")
        .aggregate(total=Sum("amount"))
        .get("total") or 0
    )

    company_totals = (
        records.filter(status="WON")
        .values("company")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    return render(request, "projections/dashboard.html", {
        "records": records,
        "companies": companies,
        "years": years,
        "company_totals": company_totals,
        "total_won": total_won,
        "total_lost": total_lost,
    })


def project_detail(request, pk):
    """
    Project detail page
    """
    project = get_object_or_404(
        ProjectRecord,
        pk=pk,
        is_active=True
    )

    return render(request, "projections/project_detail.html", {
        "project": project
    })


@require_POST
def archive_project(request, pk):
    """
    Soft delete (archive) a project record
    """
    project = get_object_or_404(ProjectRecord, pk=pk)
    project.is_active = False
    project.save(update_fields=["is_active"])

    messages.success(request, "Project record archived successfully.")
    return redirect("projections:dashboardpro")
