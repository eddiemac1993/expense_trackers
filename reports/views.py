from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa

from .models import ProjectRecord, ExpenseTag


def get_filtered_records(request):
    records = ProjectRecord.objects.all().order_by("-created_at")

    company = request.GET.get("company", "")
    client = request.GET.get("client", "")
    status = request.GET.get("status", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    if company:
        records = records.filter(company=company)

    if client:
        records = records.filter(client=client)

    if status:
        records = records.filter(status=status)

    if start_date:
        records = records.filter(start_date__gte=start_date)

    if end_date:
        records = records.filter(start_date__lte=end_date)

    return records


def get_report_context(request):
    records = get_filtered_records(request)

    total_contract = sum(record.contract_value for record in records)
    total_expense = sum(record.expense_value for record in records)
    total_profit = total_contract - total_expense
    total_paid = sum(record.paid_value for record in records)

    companies = ProjectRecord.objects.values_list(
        "company", flat=True
    ).distinct().order_by("company")

    clients = ProjectRecord.objects.values_list(
        "client", flat=True
    ).distinct().order_by("client")

    context = {
        "records": records,
        "companies": companies,
        "clients": clients,
        "statuses": ProjectRecord.STATUS_CHOICES,

        "selected_company": request.GET.get("company", ""),
        "selected_client": request.GET.get("client", ""),
        "selected_status": request.GET.get("status", ""),
        "selected_start_date": request.GET.get("start_date", ""),
        "selected_end_date": request.GET.get("end_date", ""),

        "total_contract": total_contract,
        "total_expense": total_expense,
        "total_profit": total_profit,
        "total_paid": total_paid,
    }

    return context


def project_report(request, project_id=None):
    editing_project = None

    if project_id:
        editing_project = get_object_or_404(ProjectRecord, id=project_id)

    if request.method == "POST":
        company = request.POST.get("company")
        project_supply = request.POST.get("project_supply")
        client = request.POST.get("client")
        contract_value = request.POST.get("contract_value") or 0
        paid_value = request.POST.get("paid_value") or 0
        status = request.POST.get("status")
        start_date = request.POST.get("start_date") or None
        end_date = request.POST.get("end_date") or None

        if editing_project:
            editing_project.company = company
            editing_project.project_supply = project_supply
            editing_project.client = client
            editing_project.contract_value = contract_value
            editing_project.paid_value = paid_value
            editing_project.status = status
            editing_project.start_date = start_date
            editing_project.end_date = end_date
            editing_project.save()

        else:
            ProjectRecord.objects.create(
                company=company,
                project_supply=project_supply,
                client=client,
                contract_value=contract_value,
                paid_value=paid_value,
                status=status,
                start_date=start_date,
                end_date=end_date,
            )

        return redirect("project_report")

    context = get_report_context(request)
    context["editing_project"] = editing_project

    return render(request, "reports/project_report.html", context)


def delete_project_report(request, project_id):
    project = get_object_or_404(ProjectRecord, id=project_id)
    project.delete()
    return redirect("project_report")


def project_expenses(request, project_id):
    project = get_object_or_404(ProjectRecord, id=project_id)

    if request.method == "POST":
        reason = request.POST.get("reason")
        tag_name = request.POST.get("tag")
        amount = request.POST.get("amount") or 0
        notes = request.POST.get("notes")
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

        return redirect("project_expenses", project_id=project.id)

    expenses = project.expenses.all().order_by("-date")

    context = {
        "project": project,
        "expenses": expenses,
    }

    return render(request, "reports/project_expenses.html", context)


def generate_project_report_pdf(request):
    context = get_report_context(request)

    template = get_template("reports/project_report_pdf.html")
    html = template.render(context, request=request)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="project_report.pdf"'

    pisa_status = pisa.CreatePDF(
        html,
        dest=response,
        encoding="UTF-8"
    )

    if pisa_status.err:
        return HttpResponse("Error generating PDF report")

    return response