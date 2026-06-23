from datetime import date, datetime
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    WEASYPRINT_AVAILABLE = False
    HTML = None

from .models import ProjectRecord, Payment


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
            completion_status=request.POST.get("completion_status", "PENDING_EVALUATION"),
        )

        messages.success(request, "Project record added successfully.")
        return redirect("projections:dashboardpro")

    # =========================
    # HANDLE DISPLAY (GET)
    # =========================
    all_records = ProjectRecord.objects.filter(is_active=True)

    overall_total_amount = (
        all_records.aggregate(total=Sum("amount")).get("total") or Decimal("0.00")
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

    # ✅ NEW: total pending
    total_pending = (
        records.filter(status="PENDING")
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
        "total_pending": total_pending,  # ✅ pass to template
        "overall_total_amount": overall_total_amount,
        "weasyprint_available": WEASYPRINT_AVAILABLE,
    })


def project_detail(request, pk):
    """
    Project detail page
    """
    project = get_object_or_404(ProjectRecord, pk=pk, is_active=True)
    return render(request, "projections/project_detail.html", {"project": project})


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


def payments_dashboard(request):
    """
    Payments & Outstanding Dashboard
    - Shows ONLY WON projects
    - Correct decimal precision (2dp)
    - Print-friendly
    """
    projects = (
        ProjectRecord.objects
        .filter(is_active=True, status="WON")
        .annotate(
            paid_amount=Coalesce(
                Sum("payments__amount_paid"),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
            outstanding_amount=F("amount") - Coalesce(
                Sum("payments__amount_paid"),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )
        .order_by("-project_date")
    )

    totals = projects.aggregate(
        total_projects_value=Sum("amount"),
        total_paid=Sum("paid_amount"),
        total_balance=Sum("outstanding_amount"),
    )

    return render(
        request,
        "projections/payments_dashboard.html",
        {"projects": projects, "totals": totals},
    )


def project_payments(request, pk):
    project = get_object_or_404(
        ProjectRecord,
        pk=pk,
        status="WON",
        is_active=True
    )

    payments = project.payments.order_by("-payment_date")

    total_paid = project.total_paid
    balance_due = project.balance_due

    if request.method == "POST":
        amount = Decimal(request.POST.get("amount_paid", "0"))
        payment_date = request.POST.get("payment_date")
        reference = request.POST.get("reference", "")
        notes = request.POST.get("notes", "")

        if amount <= 0:
            messages.error(request, "Amount must be greater than zero.")
            return redirect("projections:project_payments", pk=pk)

        if amount > balance_due:
            messages.error(request, "Payment exceeds remaining balance.")
            return redirect("projections:project_payments", pk=pk)

        Payment.objects.create(
            project=project,
            amount_paid=amount,
            payment_date=payment_date,
            reference=reference,
            notes=notes,
        )

        messages.success(request, "Payment recorded successfully.")
        return redirect("projections:project_payments", pk=pk)

    return render(
        request,
        "projections/project_payments.html",
        {
            "project": project,
            "payments": payments,
            "total_paid": total_paid,
            "balance_due": balance_due,
        }
    )


def edit_payment(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    project = payment.project

    other_payments_total = (
        Payment.objects
        .filter(project=project)
        .exclude(pk=payment.pk)
        .aggregate(total=Sum("amount_paid"))
        .get("total") or Decimal("0.00")
    )

    max_allowed = project.amount - other_payments_total

    if request.method == "POST":
        amount = Decimal(request.POST.get("amount_paid", "0"))
        payment_date = request.POST.get("payment_date")
        reference = request.POST.get("reference", "")
        notes = request.POST.get("notes", "")

        if amount <= 0:
            messages.error(request, "Amount must be greater than zero.")
            return redirect("projections:edit_payment", payment_id=payment_id)

        if amount > max_allowed:
            messages.error(
                request,
                f"Amount exceeds allowed maximum (ZMW {max_allowed:,.2f})."
            )
            return redirect("projections:edit_payment", payment_id=payment_id)

        payment.amount_paid = amount
        payment.payment_date = payment_date
        payment.reference = reference
        payment.notes = notes
        payment.save()

        messages.success(request, "Payment updated successfully.")
        return redirect("projections:project_payments", pk=project.pk)

    return render(
        request,
        "projections/edit_payment.html",
        {
            "payment": payment,
            "project": project,
            "max_allowed": max_allowed,
        }
    )


def payments_dashboard_pdf(request):
    """
    Export Payments & Outstanding Dashboard to PDF
    (WON projects only)
    """
    if not WEASYPRINT_AVAILABLE:
        messages.error(request, "PDF export is not available. Please install WeasyPrint.")
        return redirect("projections:payments_dashboard")

    projects = (
        ProjectRecord.objects
        .filter(is_active=True, status="WON")
        .annotate(
            paid_amount=Coalesce(
                Sum("payments__amount_paid"),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
            outstanding_amount=F("amount") - Coalesce(
                Sum("payments__amount_paid"),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )
        .order_by("-project_date")
    )

    totals = projects.aggregate(
        total_projects_value=Sum("amount"),
        total_paid=Sum("paid_amount"),
        total_balance=Sum("outstanding_amount"),
    )

    context = {
        "projects": projects,
        "totals": totals,
        "generated_on": datetime.now().strftime("%d %B %Y %H:%M"),
    }

    html_string = render_to_string("projections/payments_dashboard_pdf.html", context)
    html = HTML(string=html_string)

    response = HttpResponse(content_type="application/pdf")
    filename = f"payments_dashboard_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    response["Content-Disposition"] = f"inline; filename={filename}"

    html.write_pdf(response)
    return response


def add_payment(request, pk):
    project = get_object_or_404(
        ProjectRecord,
        pk=pk,
        is_active=True,
        status="WON"
    )

    total_paid = project.total_paid
    balance_due = project.balance_due

    if request.method == "POST":
        amount = Decimal(request.POST.get("amount_paid", "0"))
        payment_date = request.POST.get("payment_date")
        reference = request.POST.get("reference", "")

        if amount <= 0:
            messages.error(request, "Payment amount must be greater than zero.")
            return redirect("projections:add_payment", pk=pk)

        if amount > balance_due:
            messages.error(request, "Payment exceeds outstanding balance.")
            return redirect("projections:add_payment", pk=pk)

        Payment.objects.create(
            project=project,
            amount_paid=amount,
            payment_date=payment_date,
            reference=reference,
        )

        messages.success(request, "Payment recorded successfully.")
        return redirect("projections:payments_dashboard")

    return render(
        request,
        "projections/add_payment.html",
        {
            "project": project,
            "total_paid": total_paid,
            "balance_due": balance_due,
        }
    )


def export_projects_pdf(request):
    """
    Export filtered projects to PDF using WeasyPrint
    """
    if not WEASYPRINT_AVAILABLE:
        messages.error(request, "PDF export is not available. Please install WeasyPrint.")
        return redirect("projections:dashboardpro")

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

    # Calculate totals (filtered set)
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

    # ✅ NEW: total pending (filtered set)
    total_pending = (
        records.filter(status="PENDING")
        .aggregate(total=Sum("amount"))
        .get("total") or Decimal("0.00")
    )

    # Overall total (all active projects, not filter-based)
    overall_total_amount = (
        all_records.aggregate(total=Sum("amount"))
        .get("total") or Decimal("0.00")
    )

    company_totals = (
        records.filter(status="WON")
        .values("company")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    def format_amount(amount):
        if amount is None:
            return "0.00"
        return f"{amount:,.2f}"

    context = {
        "records": records,

        "total_won": total_won,
        "total_won_formatted": format_amount(total_won),

        "total_pending": total_pending,
        "total_pending_formatted": format_amount(total_pending),

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
        "format_amount": format_amount,
    }

    html_string = render_to_string("projections/pdf_export.html", context)
    html = HTML(string=html_string)

    response = HttpResponse(content_type="application/pdf")
    filename = f"project_projects_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    response["Content-Disposition"] = f"inline; filename={filename}"

    html.write_pdf(response)
    return response
