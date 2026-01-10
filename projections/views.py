from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages

from .models import ProjectRecord


from datetime import date
from decimal import Decimal

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

        try:
            project_date = date.fromisoformat(request.POST.get("project_date"))
        except Exception:
            messages.error(request, "Invalid project date.")
            return redirect("projections:dashboardpro")

        ProjectRecord.objects.create(
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            company=company_name,
            customer=request.POST.get("customer"),
            amount=request.POST.get("amount"),
            project_date=project_date,
            status=request.POST.get("status"),
            completion_status=request.POST.get(
                "completion_status",
                "PENDING_EVALUATION"
            ),
        )

        messages.success(request, "Project record added successfully.")
        return redirect("projections:dashboardpro")

    # =========================
    # HANDLE DISPLAY (GET)
    # =========================

    # ALL active records (base)
    all_records = ProjectRecord.objects.filter(is_active=True)

    # Combined overall total (WON + LOST + PENDING)
    overall_total_amount = (
        all_records.aggregate(total=Sum("amount"))
        .get("total") or Decimal("0.00")
    )

    # Records that will be filtered
    records = all_records.order_by("-project_date")

    # Dropdown data
    companies = (
        all_records.values_list("company", flat=True)
        .distinct()
        .order_by("company")
    )

    years = (
        all_records.values_list("year", flat=True)
        .distinct()
        .order_by("-year")
    )

    # =========================
    # FILTERS
    # =========================
    company = request.GET.get("company")
    status = request.GET.get("status")
    completion_status = request.GET.get("completion_status")
    year = request.GET.get("year")

    if company:
        records = records.filter(company=company)

    if status:
        records = records.filter(status=status)

    if completion_status:
        records = records.filter(completion_status=completion_status)

    if year:
        records = records.filter(year=year)

    # =========================
    # FILTERED TOTALS
    # =========================
    total_won = (
        records.filter(status="WON")
        .aggregate(total=Sum("amount"))
        .get("total") or Decimal("0.00")
    )

    total_lost = (
        records.filter(status="LOST")
        .aggregate(total=Sum("amount"))
        .get("total") or Decimal("0.00")
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

        # FILTERED TOTALS
        "total_won": total_won,
        "total_lost": total_lost,

        # OVERALL COMBINED TOTAL
        "overall_total_amount": overall_total_amount,
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
