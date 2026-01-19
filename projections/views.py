from datetime import date, datetime
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    HTML = None

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
    all_records = ProjectRecord.objects.filter(is_active=True)
    overall_total_amount = (
        all_records.aggregate(total=Sum("amount"))
        .get("total") or Decimal("0.00")
    )
    records = all_records.order_by("-project_date")
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
        "total_won": total_won,
        "total_lost": total_lost,
        "overall_total_amount": overall_total_amount,
        "weasyprint_available": WEASYPRINT_AVAILABLE,  # Pass to template
    })


def project_detail(request, pk):
    """
    Project detail page
    """
    project = get_object_or_404(ProjectRecord, pk=pk, is_active=True)
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


def export_projects_pdf(request):
    """
    Export filtered projects to PDF using WeasyPrint
    """
    if not WEASYPRINT_AVAILABLE:
        messages.error(request, "PDF export is not available. Please install WeasyPrint.")
        return redirect("projections:dashboardpro")
    
    # Apply same filters as dashboard
    all_records = ProjectRecord.objects.filter(is_active=True)
    records = all_records.order_by("-project_date")
    
    # Get filter parameters
    company = request.GET.get("company")
    status = request.GET.get("status")
    completion_status = request.GET.get("completion_status")
    year = request.GET.get("year")
    
    # Apply filters
    if company:
        records = records.filter(company=company)
    if status:
        records = records.filter(status=status)
    if completion_status:
        records = records.filter(completion_status=completion_status)
    if year:
        records = records.filter(year=year)
    
    # Calculate totals
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
    
    overall_total_amount = (
        all_records.aggregate(total=Sum("amount"))
        .get("total") or Decimal("0.00")
    )
    
    # Get company totals for the filtered set
    company_totals = (
        records.filter(status="WON")
        .values("company")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    
    # Format amounts with thousand separators
    def format_amount(amount):
        if amount is None:
            return "0.00"
        # Format with thousand separators
        return f"{amount:,.2f}"
    
    # Create PDF context
    context = {
        "records": records,
        "total_won": total_won,
        "total_won_formatted": format_amount(total_won),
        "total_lost": total_lost,
        "total_lost_formatted": format_amount(total_lost),
        "overall_total_amount": overall_total_amount,
        "overall_total_formatted": format_amount(overall_total_amount),
        "company_totals": company_totals,
        "filter_summary": {
            "company": company,
            "status": status,
            "completion_status": completion_status,
            "year": year,
        },
        "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "filter_applied": any([company, status, completion_status, year]),
        "total_records": records.count(),
        "format_amount": format_amount,  # Pass function to template
    }
    
    # Render HTML template
    html_string = render_to_string("projections/pdf_export.html", context)
    
    # Create PDF
    html = HTML(string=html_string)
    
    # Create response
    response = HttpResponse(content_type="application/pdf")
    filename = f"project_projects_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    response["Content-Disposition"] = f"inline; filename={filename}"
    
    # Generate PDF
    html.write_pdf(response)
    
    return response