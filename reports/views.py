from decimal import Decimal, InvalidOperation

from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.db.models import F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.views.decorators.http import require_POST
from xhtml2pdf import pisa

from .models import (
    CURRENCY_CHOICES,
    ExpenseTag,
    PendingProjectRecord,
    ProjectExpense,
    ProjectPayment,
    ProjectRecord,
    money_round,
)


INTERNAL_PROJECT_CODE = "solid2026"


COMPANY_ALIASES = {
    "solid connection z limited": "Solid Connections Zambia Ltd",
    "solid connections z limited": "Solid Connections Zambia Ltd",
    "solid connections z ltd": "Solid Connections Zambia Ltd",
    "solid connections zambia limited": "Solid Connections Zambia Ltd",
    "solid connections zambia ltd": "Solid Connections Zambia Ltd",
}

COMPANY_GROUPS = {
    "Solid Connections Zambia Ltd": [
        "Solid Connection (Z) Limited",
        "Solid Connections (Z) Limited",
        "Solid Connections Zambia Ltd",
    ],
}


def normalize_company_key(name):
    cleaned = "".join(
        char.lower() if char.isalnum() else " "
        for char in (name or "")
    )
    return " ".join(cleaned.split())


def clean_company_name(name):
    name = (name or "").strip()
    key = normalize_company_key(name)

    if key in COMPANY_ALIASES:
        return COMPANY_ALIASES[key]

    existing_names = list(
        ProjectRecord.objects.values_list("company", flat=True).distinct()
    )
    existing_names += list(
        PendingProjectRecord.objects.values_list("company", flat=True).distinct()
    )

    for existing_name in existing_names:
        if normalize_company_key(existing_name) == key:
            return existing_name

    return " ".join(name.split())


def company_filter_values(name):
    clean_name = clean_company_name(name)
    return COMPANY_GROUPS.get(clean_name, [clean_name])


def company_display_name(name):
    return clean_company_name(name)


def money_for_chart(value):
    return float(value or 0)


def clean_currency(value):
    valid_currencies = {currency for currency, label in CURRENCY_CHOICES}
    if value in valid_currencies:
        return value

    return "ZMW"


def clean_exchange_rate(value, currency):
    if currency == "ZMW":
        return Decimal("1.00")

    try:
        rate = Decimal(value or "1")
    except (InvalidOperation, TypeError):
        return Decimal("1.00")

    if rate <= 0:
        return Decimal("1.00")

    return rate


def clean_money(value):
    try:
        return money_round(Decimal(value or "0"))
    except (InvalidOperation, TypeError):
        return Decimal("0.00")


def payment_amount_zmw(amount, currency, exchange_rate):
    return money_round(amount * clean_exchange_rate(exchange_rate, currency))


def build_payment_rows(project, payments):
    rows = []
    cumulative_gross = money_round(project.paid_value_zmw - project.payment_value)
    cumulative_tax = Decimal("0.00")
    cumulative_net = cumulative_gross

    for number, payment in enumerate(payments, start=1):
        cumulative_gross += payment.amount_zmw
        cumulative_tax += payment.tax_amount_zmw
        cumulative_net += payment.net_amount_zmw

        rows.append({
            "number": number,
            "payment": payment,
            "cumulative_gross": cumulative_gross,
            "cumulative_tax": cumulative_tax,
            "cumulative_net": cumulative_net,
            "remaining_balance": project.contract_value_zmw - cumulative_gross,
        })

    return rows


def render_project_payments(
    request,
    project,
    error_message=None,
    submitted_payment=None,
):
    payments = list(project.payments.all().order_by("date", "created_at"))

    return render(
        request,
        "reports/project_payments.html",
        {
            "project": project,
            "payments": payments,
            "payment_rows": build_payment_rows(project, payments),
            "currencies": CURRENCY_CHOICES,
            "error_message": error_message,
            "submitted_payment": submitted_payment or {},
            "internal_page": project.is_internal,
        }
    )


def validate_payment_data(
    request,
    project,
    existing_payment=None,
):
    reference = request.POST.get("reference", "")
    amount = clean_money(request.POST.get("amount"))
    currency = clean_currency(request.POST.get("currency") or project.currency)
    exchange_rate = clean_exchange_rate(
        request.POST.get("exchange_rate") or project.exchange_rate,
        currency
    )
    notes = request.POST.get("notes", "")
    date = request.POST.get("date") or None
    allow_overpayment = request.POST.get("allow_overpayment") == "1"
    gross_zmw = payment_amount_zmw(amount, currency, exchange_rate)

    submitted_payment = {
        "reference": reference,
        "amount": request.POST.get("amount", ""),
        "currency": currency,
        "exchange_rate": exchange_rate,
        "notes": notes,
        "date": date,
        "allow_overpayment": allow_overpayment,
    }

    if not date:
        return None, "Payment cannot be saved without a date.", submitted_payment

    if amount <= 0:
        return None, "Payment amount must be greater than zero.", submitted_payment

    existing_total = project.paid_value_zmw

    if existing_payment:
        existing_total -= existing_payment.amount_zmw

    new_total = existing_total + gross_zmw

    if new_total > project.contract_value_zmw and not allow_overpayment:
        return (
            None,
            "This payment will make total paid exceed the contract value. Tick allow overpayment to save it.",
            submitted_payment
        )

    return {
        "reference": reference,
        "amount": amount,
        "currency": currency,
        "exchange_rate": exchange_rate,
        "tax_rate": project.tax_rate,
        "notes": notes,
        "date": date,
    }, None, submitted_payment


def password_is_valid(request):
    password = request.POST.get("password", "").strip()
    return password == INTERNAL_PROJECT_CODE


def get_filtered_records(request, internal=False):
    records = ProjectRecord.objects.prefetch_related("expenses", "payments").filter(
        is_internal=internal
    )

    search = request.GET.get("q", "").strip()
    company = request.GET.get("company", "")
    client = request.GET.get("client", "")
    status = request.GET.get("status", "")
    tax_type = request.GET.get("tax_type", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    selected_projects = request.GET.getlist("selected_projects")

    if search:
        records = records.filter(
            Q(company__icontains=search)
            | Q(project_supply__icontains=search)
            | Q(client__icontains=search)
        )

    if company:
        records = records.filter(company__in=company_filter_values(company))

    if client:
        records = records.filter(client=client)

    if status:
        records = records.filter(status=status)

    if tax_type:
        records = records.filter(tax_type=tax_type)

    if start_date:
        records = records.filter(start_date__gte=start_date)

    if end_date:
        records = records.filter(start_date__lte=end_date)

    if selected_projects:
        records = records.filter(id__in=selected_projects)

    sort = request.GET.get("sort", "start_date")
    sort_options = {
        "company": "company",
        "-company": "-company",
        "client": "client",
        "-client": "-client",
        "start_date": F("start_date").asc(nulls_last=True),
        "-start_date": F("start_date").desc(nulls_last=True),
        "end_date": F("end_date").asc(nulls_last=True),
        "-end_date": F("end_date").desc(nulls_last=True),
        "contract": "contract_value",
        "-contract": "-contract_value",
        "paid": "paid_value",
        "-paid": "-paid_value",
        "status": "status",
        "-status": "-status",
        "created": "created_at",
        "-created": "-created_at",
    }

    ordering = sort_options.get(sort, sort_options["start_date"])

    if isinstance(ordering, str):
        return records.order_by(ordering, "created_at")

    return records.order_by(ordering, "created_at")


def get_report_context(request, paginate=True, internal=False):
    records = get_filtered_records(request, internal=internal)
    all_record_list = list(records)
    payment_status = request.GET.get("payment_status", "")
    selected_sort = request.GET.get("sort", "start_date")

    if payment_status == "pending":
        all_record_list = [
            record for record in all_record_list
            if record.paid_value_zmw < record.contract_value_zmw
        ]

    elif payment_status == "unpaid":
        all_record_list = [
            record for record in all_record_list
            if record.paid_value_zmw == 0
        ]

    elif payment_status == "partly_paid":
        all_record_list = [
            record for record in all_record_list
            if 0 < record.paid_value_zmw < record.contract_value_zmw
        ]

    elif payment_status == "fully_paid":
        all_record_list = [
            record for record in all_record_list
            if record.paid_value_zmw >= record.contract_value_zmw
        ]

    if selected_sort == "paid":
        all_record_list = sorted(
            all_record_list,
            key=lambda record: record.paid_value_zmw
        )
    elif selected_sort == "-paid":
        all_record_list = sorted(
            all_record_list,
            key=lambda record: record.paid_value_zmw,
            reverse=True
        )

    records = all_record_list

    if internal:
        pending_projects = PendingProjectRecord.objects.none()
    else:
        pending_projects = (
            PendingProjectRecord.objects
            .exclude(status="Awarded")
            .order_by("submission_date", "created_at")
        )

    total_contract = sum(record.contract_value_zmw for record in all_record_list)
    total_expense = sum(record.expense_value for record in all_record_list)
    total_tax = sum(record.tax_amount for record in all_record_list)
    total_net_contract = sum(record.contract_excluding_tax for record in all_record_list)
    total_profit = total_net_contract - total_expense
    total_paid = sum(record.paid_value_zmw for record in all_record_list)
    total_pending = total_contract - total_paid
    total_final_expected_profit = sum(
        record.final_expected_profit_value for record in all_record_list
    )

    company_chart = {}

    for record in all_record_list:
        company_name = company_display_name(record.company)

        company_data = company_chart.setdefault(company_name, {
            "contract": 0,
            "paid": 0,
            "balance": 0,
            "expenses": 0,
            "profit": 0,
        })

        company_data["contract"] += money_for_chart(record.contract_value_zmw)
        company_data["paid"] += money_for_chart(record.paid_value_zmw)
        company_data["balance"] += money_for_chart(record.pending_payment_value)
        company_data["expenses"] += money_for_chart(record.expense_value)
        company_data["profit"] += money_for_chart(record.profit_value)

    chart_items = sorted(
        company_chart.items(),
        key=lambda item: item[1]["contract"],
        reverse=True
    )

    report_chart_data = {
        "labels": [company for company, data in chart_items],
        "contracts": [data["contract"] for company, data in chart_items],
        "paids": [data["paid"] for company, data in chart_items],
        "balances": [data["balance"] for company, data in chart_items],
        "expenses": [data["expenses"] for company, data in chart_items],
        "profits": [data["profit"] for company, data in chart_items],
    }

    companies = sorted({
        company_display_name(company)
        for company in list(
            ProjectRecord.objects
            .filter(is_internal=internal)
            .values_list("company", flat=True)
        )
    })

    if not internal:
        pending_companies = [
            company_display_name(company)
            for company in PendingProjectRecord.objects.values_list(
                "company",
                flat=True
            )
        ]

        companies = sorted(set(companies + pending_companies))

    clients = (
        ProjectRecord.objects
        .filter(is_internal=internal)
        .values_list("client", flat=True)
        .distinct()
        .order_by("client")
    )

    query_params = request.GET.copy()
    query_params.pop("page", None)

    return {
        "records": records,
        "page_obj": None,
        "result_count": len(all_record_list),
        "filter_querystring": query_params.urlencode(),
        "report_chart_data": report_chart_data,
        "pending_projects": pending_projects,

        "companies": companies,
        "clients": clients,

        "statuses": ProjectRecord.STATUS_CHOICES,
        "tax_types": ProjectRecord.TAX_CHOICES,
        "currencies": CURRENCY_CHOICES,
        "pending_statuses": PendingProjectRecord.STATUS_CHOICES,

        "selected_search": request.GET.get("q", "").strip(),
        "selected_company": company_display_name(request.GET.get("company", "")),
        "selected_client": request.GET.get("client", ""),
        "selected_status": request.GET.get("status", ""),
        "selected_tax_type": request.GET.get("tax_type", ""),
        "selected_payment_status": request.GET.get("payment_status", ""),
        "selected_start_date": request.GET.get("start_date", ""),
        "selected_end_date": request.GET.get("end_date", ""),
        "selected_sort": selected_sort,

        "selected_projects": request.GET.getlist("selected_projects"),

        "total_contract": total_contract,
        "total_net_contract": total_net_contract,
        "total_tax": total_tax,
        "total_expense": total_expense,
        "total_profit": total_profit,
        "total_paid": total_paid,
        "total_pending": total_pending,
        "total_final_expected_profit": total_final_expected_profit,

        "internal_page": internal,
    }


def project_report(request, project_id=None):
    editing_project = None

    if request.method == "POST" and not request.user.is_staff:
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    if project_id:
        editing_project = get_object_or_404(
            ProjectRecord,
            id=project_id,
            is_internal=False
        )

    if request.method == "POST":
        company = clean_company_name(request.POST.get("company"))
        project_supply = request.POST.get("project_supply")
        client = request.POST.get("client")

        contract_value = request.POST.get("contract_value") or 0
        paid_value = request.POST.get("paid_value") or 0
        currency = clean_currency(request.POST.get("currency"))
        exchange_rate = clean_exchange_rate(
            request.POST.get("exchange_rate"),
            currency
        )

        tax_type = request.POST.get("tax_type") or "NONE"
        status = request.POST.get("status") or "Not started"

        start_date = request.POST.get("start_date") or None
        end_date = request.POST.get("end_date") or None

        if editing_project:
            project = editing_project
            tax_type_changed = project.tax_type != tax_type

            if (
                tax_type_changed
                and project.payments.exists()
                and request.POST.get("confirm_tax_recalculate") != "1"
            ):
                context = get_report_context(request, internal=False)
                context["editing_project"] = editing_project
                context["tax_recalculate_warning"] = True
                return render(
                    request,
                    "reports/project_report.html",
                    context
                )
        else:
            project, created = ProjectRecord.objects.get_or_create(
                company=company,
                project_supply=project_supply,
                client=client,
                is_internal=False,
                defaults={
                    "contract_value": contract_value,
                    "paid_value": paid_value,
                    "currency": currency,
                    "exchange_rate": exchange_rate,
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
        project.currency = currency
        project.exchange_rate = exchange_rate
        project.tax_type = tax_type
        project.status = status
        project.start_date = start_date
        project.end_date = end_date
        project.is_internal = False
        project.save()

        if (
            editing_project
            and tax_type_changed
            and request.POST.get("confirm_tax_recalculate") == "1"
        ):
            project.payments.update(tax_rate=project.tax_rate)

        return redirect("project_report")

    context = get_report_context(request, internal=False)
    context["editing_project"] = editing_project

    return render(
        request,
        "reports/project_report.html",
        context
    )


def internal_project_login(request):
    if request.method == "POST":
        code = request.POST.get("code", "").strip()

        if code == INTERNAL_PROJECT_CODE:
            request.session["internal_project_access"] = True
            return redirect("internal_project_report")

        return render(
            request,
            "reports/internal_login.html",
            {
                "error": "Invalid access code"
            }
        )

    return render(
        request,
        "reports/internal_login.html"
    )


def internal_project_logout(request):
    request.session.pop("internal_project_access", None)
    return redirect("project_report")


def internal_project_report(request, project_id=None):
    if not request.session.get("internal_project_access"):
        return redirect("internal_project_login")

    editing_project = None

    if project_id:
        editing_project = get_object_or_404(
            ProjectRecord,
            id=project_id,
            is_internal=True
        )

    if request.method == "POST":
        company = clean_company_name(request.POST.get("company"))
        project_supply = request.POST.get("project_supply")
        client = request.POST.get("client")

        contract_value = request.POST.get("contract_value") or 0
        paid_value = request.POST.get("paid_value") or 0
        currency = clean_currency(request.POST.get("currency"))
        exchange_rate = clean_exchange_rate(
            request.POST.get("exchange_rate"),
            currency
        )

        tax_type = request.POST.get("tax_type") or "NONE"
        status = request.POST.get("status") or "Not started"

        start_date = request.POST.get("start_date") or None
        end_date = request.POST.get("end_date") or None

        if editing_project:
            project = editing_project
            tax_type_changed = project.tax_type != tax_type

            if (
                tax_type_changed
                and project.payments.exists()
                and request.POST.get("confirm_tax_recalculate") != "1"
            ):
                context = get_report_context(request, internal=True)
                context["editing_project"] = editing_project
                context["internal_page"] = True
                context["tax_recalculate_warning"] = True
                return render(
                    request,
                    "reports/project_report.html",
                    context
                )
        else:
            project = ProjectRecord()
            tax_type_changed = False

        project.company = company
        project.project_supply = project_supply
        project.client = client
        project.contract_value = contract_value
        project.paid_value = paid_value
        project.currency = currency
        project.exchange_rate = exchange_rate
        project.tax_type = tax_type
        project.status = status
        project.start_date = start_date
        project.end_date = end_date
        project.is_internal = True
        project.save()

        if (
            editing_project
            and tax_type_changed
            and request.POST.get("confirm_tax_recalculate") == "1"
        ):
            project.payments.update(tax_rate=project.tax_rate)

        return redirect("internal_project_report")

    context = get_report_context(request, internal=True)
    context["editing_project"] = editing_project
    context["internal_page"] = True

    return render(
        request,
        "reports/project_report.html",
        context
    )


@staff_member_required
@require_POST
def move_project_to_internal(request, project_id):
    if not password_is_valid(request):
        return HttpResponse(
            "Incorrect password. Project was not moved.",
            status=403
        )

    project = get_object_or_404(
        ProjectRecord,
        id=project_id,
        is_internal=False
    )

    project.is_internal = True
    project.save(update_fields=["is_internal"])

    return redirect("project_report")


@require_POST
def move_project_to_user_view(request, project_id):
    if not request.session.get("internal_project_access"):
        return redirect("internal_project_login")

    if not password_is_valid(request):
        return HttpResponse(
            "Incorrect password. Project was not moved.",
            status=403
        )

    project = get_object_or_404(
        ProjectRecord,
        id=project_id,
        is_internal=True
    )

    project.is_internal = False
    project.save(update_fields=["is_internal"])

    return redirect("internal_project_report")


@staff_member_required
@require_POST
def add_pending_project(request):
    company = clean_company_name(request.POST.get("company"))
    project_supply = request.POST.get("project_supply")
    client = request.POST.get("client")

    submission_date = request.POST.get("submission_date") or None
    expected_award_date = request.POST.get("expected_award_date") or None
    contract_value = request.POST.get("contract_value") or 0
    currency = clean_currency(request.POST.get("currency"))
    exchange_rate = clean_exchange_rate(
        request.POST.get("exchange_rate"),
        currency
    )
    tax_type = request.POST.get("tax_type") or "NONE"
    status = request.POST.get("status") or "Submitted"
    notes = request.POST.get("notes", "")

    PendingProjectRecord.objects.create(
        company=company,
        project_supply=project_supply,
        client=client,
        submission_date=submission_date,
        expected_award_date=expected_award_date,
        contract_value=contract_value,
        currency=currency,
        exchange_rate=exchange_rate,
        tax_type=tax_type,
        status=status,
        notes=notes,
    )

    return redirect("project_report")


@staff_member_required
@require_POST
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
        currency=pending_project.currency,
        exchange_rate=pending_project.exchange_rate,
        paid_value=0,
        tax_type=pending_project.tax_type,
        status="Not started",
        is_internal=False,
    )

    pending_project.status = "Awarded"
    pending_project.save()

    return redirect("project_report")


@staff_member_required
@require_POST
def delete_project_report(request, project_id):
    project = get_object_or_404(
        ProjectRecord,
        id=project_id
    )

    is_internal = project.is_internal
    project.delete()

    if is_internal:
        return redirect("internal_project_report")

    return redirect("project_report")


def project_expenses(request, project_id):
    project = get_object_or_404(
        ProjectRecord,
        id=project_id
    )

    if project.is_internal and not request.session.get("internal_project_access"):
        return redirect("internal_project_login")

    if request.method == "POST":
        if not request.user.is_staff and not request.session.get("internal_project_access"):
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")

        reason = request.POST.get("reason")
        tag_name = request.POST.get("tag")
        amount = request.POST.get("amount") or 0
        currency = clean_currency(request.POST.get("currency") or project.currency)
        exchange_rate = clean_exchange_rate(
            request.POST.get("exchange_rate") or project.exchange_rate,
            currency
        )
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
            currency=currency,
            exchange_rate=exchange_rate,
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
            "currencies": CURRENCY_CHOICES,
            "internal_page": project.is_internal,
        }
    )


def project_payments(request, project_id):
    project = get_object_or_404(
        ProjectRecord,
        id=project_id
    )

    if project.is_internal and not request.session.get("internal_project_access"):
        return redirect("internal_project_login")

    if request.method == "POST":
        if not request.user.is_staff and not request.session.get("internal_project_access"):
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")

        payment_data, error_message, submitted_payment = validate_payment_data(
            request,
            project
        )

        if error_message:
            return render_project_payments(
                request,
                project,
                error_message=error_message,
                submitted_payment=submitted_payment
            )

        project.payments.create(
            **payment_data
        )

        return redirect(
            "project_payments",
            project_id=project.id
        )

    return render_project_payments(request, project)


def generate_project_report_pdf(request):
    internal = request.GET.get("internal") == "1"

    if internal and not request.session.get("internal_project_access"):
        return redirect("internal_project_login")

    context = get_report_context(
        request,
        paginate=False,
        internal=internal
    )

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

    filename = "internal_project_report.pdf" if internal else "project_report.pdf"

    response[
        "Content-Disposition"
    ] = f'attachment; filename="{filename}"'

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


@staff_member_required
def edit_expense(request, project_id, expense_id):
    project = get_object_or_404(ProjectRecord, id=project_id)

    expense = get_object_or_404(
        ProjectExpense,
        id=expense_id,
        project=project
    )

    if request.method == "POST":
        expense.reason = request.POST.get("reason")
        expense.amount = request.POST.get("amount") or 0
        expense.currency = clean_currency(request.POST.get("currency"))
        expense.exchange_rate = clean_exchange_rate(
            request.POST.get("exchange_rate"),
            expense.currency
        )
        expense.notes = request.POST.get("notes", "")
        expense.date = request.POST.get("date") or None

        tag_name = request.POST.get("tag", "").strip()

        if tag_name:
            tag, created = ExpenseTag.objects.get_or_create(
                name=tag_name
            )
            expense.tag = tag
        else:
            expense.tag = None

        expense.save()

    return redirect(
        "project_expenses",
        project_id=project.id
    )


@staff_member_required
@require_POST
def delete_expense(request, project_id, expense_id):
    project = get_object_or_404(ProjectRecord, id=project_id)

    expense = get_object_or_404(
        ProjectExpense,
        id=expense_id,
        project=project
    )

    expense.delete()

    return redirect(
        "project_expenses",
        project_id=project.id
    )


@staff_member_required
def edit_payment(request, project_id, payment_id):
    project = get_object_or_404(ProjectRecord, id=project_id)

    payment = get_object_or_404(
        ProjectPayment,
        id=payment_id,
        project=project
    )

    if request.method == "POST":
        payment_data, error_message, submitted_payment = validate_payment_data(
            request,
            project,
            existing_payment=payment
        )

        if error_message:
            return render_project_payments(
                request,
                project,
                error_message=error_message,
                submitted_payment=submitted_payment
            )

        payment.reference = payment_data["reference"]
        payment.amount = payment_data["amount"]
        payment.currency = payment_data["currency"]
        payment.exchange_rate = payment_data["exchange_rate"]
        payment.tax_rate = payment_data["tax_rate"]
        payment.notes = payment_data["notes"]
        payment.date = payment_data["date"]
        payment.save()

    return redirect(
        "project_payments",
        project_id=project.id
    )


@staff_member_required
@require_POST
def delete_payment(request, project_id, payment_id):
    project = get_object_or_404(ProjectRecord, id=project_id)

    payment = get_object_or_404(
        ProjectPayment,
        id=payment_id,
        project=project
    )

    payment.delete()

    return redirect(
        "project_payments",
        project_id=project.id
    )
