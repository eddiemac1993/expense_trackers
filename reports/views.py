from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from xhtml2pdf import pisa

from .models import (
    ExpenseTag,
    PendingProjectRecord,
    ProjectExpense,
    ProjectRecord,
)


def get_filtered_records(request):
    records = ProjectRecord.objects.prefetch_related("expenses").all()

    company = request.GET.get("company", "")
    client = request.GET.get("client", "")
    status = request.GET.get("status", "")
    tax_type = request.GET.get("tax_type", "")
    payment_status = request.GET.get("payment_status", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    selected_projects = request.GET.getlist("selected_projects")

    if company:
        records = records.filter(company=company)

    if client:
        records = records.filter(client=client)

    if status:
        records = records.filter(status=status)

    if tax_type:
        records = records.filter(tax_type=tax_type)

    if payment_status == "pending":
        records = records.filter(
            paid_value__lt=F("contract_value")
        )

    elif payment_status == "unpaid":
        records = records.filter(
            paid_value=0
        )

    elif payment_status == "partly_paid":
        records = records.filter(
            paid_value__gt=0,
            paid_value__lt=F("contract_value")
        )

    elif payment_status == "fully_paid":
        records = records.filter(
            paid_value__gte=F("contract_value")
        )

    if start_date:
        records = records.filter(
            start_date__gte=start_date
        )

    if end_date:
        records = records.filter(
            start_date__lte=end_date
        )

    if selected_projects:
        records = records.filter(
            id__in=selected_projects
        )

    return records.order_by(
        F("start_date").asc(nulls_last=True),
        "created_at"
    )


def get_report_context(request):
    records = get_filtered_records(request)

    pending_projects = (
        PendingProjectRecord.objects
        .exclude(status="Awarded")
        .order_by("submission_date", "created_at")
    )

    total_contract = sum(
        record.contract_value for record in records
    )

    total_expense = sum(
        record.expense_value for record in records
    )

    total_tax = sum(
        record.tax_amount for record in records
    )

    total_net_contract = sum(
        record.contract_excluding_tax for record in records
    )

    total_profit = total_net_contract - total_expense

    total_paid = sum(
        record.paid_value for record in records
    )

    total_pending = total_contract - total_paid

    companies = (
        ProjectRecord.objects
        .values_list("company", flat=True)
        .distinct()
        .order_by("company")
    )

    clients = (
        ProjectRecord.objects
        .values_list("client", flat=True)
        .distinct()
        .order_by("client")
    )

    return {
        "records": records,
        "pending_projects": pending_projects,

        "companies": companies,
        "clients": clients,

        "statuses": ProjectRecord.STATUS_CHOICES,
        "tax_types": ProjectRecord.TAX_CHOICES,
        "pending_statuses": PendingProjectRecord.STATUS_CHOICES,

        "selected_company": request.GET.get("company", ""),
        "selected_client": request.GET.get("client", ""),
        "selected_status": request.GET.get("status", ""),
        "selected_tax_type": request.GET.get("tax_type", ""),
        "selected_payment_status": request.GET.get("payment_status", ""),
        "selected_start_date": request.GET.get("start_date", ""),
        "selected_end_date": request.GET.get("end_date", ""),

        "selected_projects": request.GET.getlist("selected_projects"),

        "total_contract": total_contract,
        "total_net_contract": total_net_contract,
        "total_tax": total_tax,
        "total_expense": total_expense,
        "total_profit": total_profit,
        "total_paid": total_paid,
        "total_pending": total_pending,
    }


def project_report(request, project_id=None):
    editing_project = None

    if project_id:
        editing_project = get_object_or_404(
            ProjectRecord,
            id=project_id
        )

    if request.method == "POST":
        company = request.POST.get("company")
        project_supply = request.POST.get("project_supply")
        client = request.POST.get("client")

        contract_value = request.POST.get("contract_value") or 0
        paid_value = request.POST.get("paid_value") or 0

        tax_type = request.POST.get("tax_type") or "NONE"
        status = request.POST.get("status") or "Not started"

        start_date = request.POST.get("start_date") or None
        end_date = request.POST.get("end_date") or None

        if editing_project:
            project = editing_project

        else:
            project, created = ProjectRecord.objects.get_or_create(
                company=company,
                project_supply=project_supply,
                client=client,
                defaults={
                    "contract_value": contract_value,
                    "paid_value": paid_value,
                    "tax_type": tax_type,
                    "status": status,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )

            if created:
                return redirect("project_report")

        project.company = company
        project.project_supply = project_supply
        project.client = client

        project.contract_value = contract_value
        project.paid_value = paid_value

        project.tax_type = tax_type
        project.status = status

        project.start_date = start_date
        project.end_date = end_date

        project.save()

        return redirect("project_report")

    context = get_report_context(request)
    context["editing_project"] = editing_project

    return render(
        request,
        "reports/project_report.html",
        context
    )


def add_pending_project(request):
    if request.method == "POST":

        company = request.POST.get("company")
        project_supply = request.POST.get("project_supply")
        client = request.POST.get("client")

        submission_date = request.POST.get("submission_date") or None

        expected_award_date = (
            request.POST.get("expected_award_date") or None
        )

        contract_value = (
            request.POST.get("contract_value") or 0
        )

        tax_type = request.POST.get("tax_type") or "NONE"

        status = (
            request.POST.get("status")
            or "Submitted"
        )

        notes = request.POST.get("notes", "")

        PendingProjectRecord.objects.create(
            company=company,
            project_supply=project_supply,
            client=client,
            submission_date=submission_date,
            expected_award_date=expected_award_date,
            contract_value=contract_value,
            tax_type=tax_type,
            status=status,
            notes=notes,
        )

    return redirect("project_report")


def award_pending_project(request, pending_id):
    pending_project = get_object_or_404(
        PendingProjectRecord,
        id=pending_id
    )

    ProjectRecord.objects.create(
        company=pending_project.company,
        project_supply=pending_project.project_supply,
        client=pending_project.client,

        start_date=None,
        end_date=None,

        contract_value=pending_project.contract_value,
        paid_value=0,

        tax_type=pending_project.tax_type,
        status="Not started",
    )

    pending_project.status = "Awarded"
    pending_project.save()

    return redirect("project_report")


def delete_project_report(request, project_id):
    project = get_object_or_404(
        ProjectRecord,
        id=project_id
    )

    project.delete()

    return redirect("project_report")


def project_expenses(request, project_id):
    project = get_object_or_404(
        ProjectRecord,
        id=project_id
    )

    if request.method == "POST":

        reason = request.POST.get("reason")

        tag_name = request.POST.get("tag")

        amount = request.POST.get("amount") or 0

        notes = request.POST.get("notes", "")

        date = request.POST.get("date") or None

        tag = None

        if tag_name:
            tag, created = ExpenseTag.objects.get_or_create(
                name=tag_name
            )

        project.expenses.create(
            reason=reason,
            tag=tag,
            amount=amount,
            notes=notes,
            date=date,
        )

        return redirect(
            "project_expenses",
            project_id=project.id
        )

    expenses = project.expenses.all().order_by(
        "-date",
        "-created_at"
    )

    return render(
        request,
        "reports/project_expenses.html",
        {
            "project": project,
            "expenses": expenses,
        }
    )


def generate_project_report_pdf(request):
    context = get_report_context(request)

    template = get_template(
        "reports/project_report_pdf.html"
    )

    html = template.render(
        context,
        request=request
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = 'attachment; filename="project_report.pdf"'

    pisa_status = pisa.CreatePDF(
        html,
        dest=response,
        encoding="UTF-8"
    )

    if pisa_status.err:
        return HttpResponse(
            "Error generating PDF report"
        )

    return response