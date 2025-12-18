# tracker/views.py
from decimal import Decimal
import json

from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import Company, Tender, Expense, Payment
from .forms import CompanyForm, TenderForm, ExpenseForm


# ---------- Pages ----------

def dashboard(request):
    """
    Main dashboard page. JS fetches the live data from API endpoints,
    so we only send minimal context for server-side rendering (companies list).
    """
    companies = Company.objects.all().order_by('name')
    # Optionally provide a few tenders for initial render, but JS will fetch fresh data.
    tenders = Tender.objects.select_related('company').all()[:25]
    return render(request, 'tracker/dashboard.html', {
        'companies': companies,
        'tenders': tenders,
    })


# ----- Create views -----

def add_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company added successfully!')
            return redirect('tracker:dashboard')
    else:
        form = CompanyForm()
    return render(request, 'tracker/form.html', {'form': form, 'title': 'Add Company'})

# in tracker/views.py — edit these functions

from .forms import PaymentForm

def add_tender(request):
    if request.method == 'POST':
        form = TenderForm(request.POST)
        if form.is_valid():
            tender = form.save()
            messages.success(request, 'Tender added successfully!')
            return redirect('tracker:tender_edit', pk=tender.pk)
    else:
        form = TenderForm()

    # no payments yet for a new tender
    payment_form = PaymentForm()
    payments = []

    return render(request, 'tracker/form.html', {
        'form': form,
        'title': 'Add Tender',
        'payment_form': payment_form,
        'payments': payments,
        'tender': None
    })


def tender_edit(request, pk):
    tender = get_object_or_404(Tender, pk=pk)
    if request.method == 'POST':
        form = TenderForm(request.POST, instance=tender)
        if form.is_valid():
            t = form.save()
            t.update_payment_status()
            t.save()
            messages.success(request, 'Tender updated successfully!')
            return redirect('tracker:dashboard')
    else:
        form = TenderForm(instance=tender)

    payment_form = PaymentForm()
    payments = tender.payments.all().order_by('-date')

    return render(request, 'tracker/form.html', {
        'form': form,
        'title': 'Edit Tender',
        'payment_form': payment_form,
        'payments': payments,
        'tender': tender
    })


def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('tracker:dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'tracker/form.html', {'form': form, 'title': 'Add Expense'})


# ----- Edit views -----

def company_edit(request, pk):
    obj = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company updated successfully!')
            return redirect('tracker:dashboard')
    else:
        form = CompanyForm(instance=obj)
    return render(request, 'tracker/form.html', {'form': form, 'title': 'Edit Company'})


def expense_edit(request, pk):
    obj = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('tracker:dashboard')
    else:
        form = ExpenseForm(instance=obj)
    return render(request, 'tracker/form.html', {'form': form, 'title': 'Edit Expense'})


# ----- Delete endpoints (AJAX friendly) -----

@require_POST
def company_delete(request, pk):
    obj = get_object_or_404(Company, pk=pk)
    obj.delete()
    return JsonResponse({'success': True, 'message': 'Company deleted successfully'})


@require_POST
def tender_delete(request, pk):
    obj = get_object_or_404(Tender, pk=pk)
    obj.delete()
    return JsonResponse({'success': True, 'message': 'Tender deleted successfully'})


@require_POST
def expense_delete(request, pk):
    obj = get_object_or_404(Expense, pk=pk)
    obj.delete()
    return JsonResponse({'success': True, 'message': 'Expense deleted successfully'})


# ----- Payments helper -----

@require_POST
def add_payment(request):
    """
    Simple endpoint to add a Payment record.
    Expects POST fields: 'tender' (id) and 'amount'.
    Returns JSON success or HttpResponseBadRequest.
    """
    tender_id = request.POST.get('tender')
    amount = request.POST.get('amount')
    if not tender_id or not amount:
        return HttpResponseBadRequest('Missing tender or amount')

    try:
        tender = Tender.objects.get(pk=tender_id)
    except Tender.DoesNotExist:
        return HttpResponseBadRequest('Tender not found')

    try:
        amt = Decimal(amount)
    except Exception:
        return HttpResponseBadRequest('Invalid amount')

    Payment.objects.create(tender=tender, amount=amt)
    # Optionally update tender payment_status
    tender.update_payment_status()
    tender.save()
    return JsonResponse({'success': True, 'message': 'Payment recorded'})


# ---------- APIs consumed by frontend ----------

def api_tenders(request):
    """
    Return tenders with computed fields:
      - total_paid
      - balance
      - total_expenses
      - profit
      - expense_overrun
    Supports filters: company, status, date_from, date_to, q
    """
    qs = Tender.objects.select_related('company').all()

    company_id = request.GET.get('company')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    q = request.GET.get('q')

    if company_id:
        qs = qs.filter(company_id=company_id)
    if status:
        qs = qs.filter(payment_status=status)
    if date_from:
        qs = qs.filter(start_date__gte=date_from)
    if date_to:
        qs = qs.filter(end_date__lte=date_to)
    if q:
        qs = qs.filter(Q(tender_no__icontains=q) | Q(client_name__icontains=q) | Q(company__name__icontains=q))

    data = []
    for tender in qs:
        total_expenses = tender.total_expenses()
        total_paid = tender.total_paid()
        balance = (tender.total_value or Decimal('0.00')) - total_paid
        profit = (tender.total_value or Decimal('0.00')) - total_expenses
        expense_overrun = tender.expense_overrun()

        # Update dynamic payment_status (do not save unless you want persistence here)
        tender.update_payment_status()

        data.append({
            'id': tender.id,
            'tender_no': tender.tender_no,
            'company': tender.company.name if tender.company else '',
            'company_id': tender.company.id if tender.company else None,
            'client_name': tender.client_name,
            'total_value': float(tender.total_value or 0),
            'total_expenses': float(total_expenses),
            'total_paid': float(total_paid),
            'balance': float(balance),
            'profit': float(profit),
            'expense_overrun': float(expense_overrun),
            'payment_status': tender.payment_status,
            'start_date': tender.start_date.isoformat() if tender.start_date else None,
            'end_date': tender.end_date.isoformat() if tender.end_date else None,
            'expense_count': tender.expenses.count(),
            'payment_count': tender.payments.count(),
        })

    return JsonResponse({'tenders': data})


def api_tenders_by_company(request):
    """
    Aggregated per-company totals used for charting.
    Returns arrays: labels, values (tender sum), paids (payments sum), expenses, profits, overruns
    """
    companies = Company.objects.all().order_by('name')

    labels = []
    values = []
    paids = []
    expenses = []
    profits = []
    overruns = []

    for c in companies:
        # totals per company
        tv = Tender.objects.filter(company=c).aggregate(total=Sum('total_value'))['total'] or Decimal('0.00')
        te = Expense.objects.filter(tender__company=c).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        tp = Payment.objects.filter(tender__company=c).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # profit as value - expenses
        profit = (tv or Decimal('0.00')) - (te or Decimal('0.00'))

        # company-level overrun: sum of tender.expense_overrun()
        overrun = Decimal('0.00')
        for t in Tender.objects.filter(company=c):
            overrun += t.expense_overrun()

        labels.append(c.name)
        values.append(float(tv))
        paids.append(float(tp))
        expenses.append(float(te))
        profits.append(float(profit))
        overruns.append(float(overrun))

    return JsonResponse({
        'labels': labels,
        'values': values,
        'paids': paids,
        'expenses': expenses,
        'profits': profits,
        'overruns': overruns,
    })


def api_summary(request):
    total_tenders = Tender.objects.count()
    total_companies = Company.objects.count()
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_tender_value = Tender.objects.aggregate(total=Sum('total_value'))['total'] or Decimal('0.00')
    total_paid = Payment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_profit = (total_tender_value or Decimal('0.00')) - (total_expenses or Decimal('0.00'))

    status_counts = {
        'Pending': Tender.objects.filter(payment_status='Pending').count(),
        'Partially_Paid': Tender.objects.filter(payment_status='Partially Paid').count(),
        'Paid': Tender.objects.filter(payment_status='Paid').count(),
    }

    return JsonResponse({
        'total_tenders': total_tenders,
        'total_companies': total_companies,
        'total_expenses': float(total_expenses),
        'total_tender_value': float(total_tender_value),
        'total_paid': float(total_paid),
        'total_profit': float(total_profit),
        'status_counts': status_counts
    })


def api_expenses(request):
    qs = Expense.objects.select_related('tender__company').order_by('-date')[:1000]
    expenses = []

    for e in qs:
        if e.tender and e.tender.company:
            tender_display = f"{e.tender.tender_no} - {e.tender.company.name}"
        elif e.tender:
            tender_display = e.tender.tender_no
        else:
            tender_display = ""

        expenses.append({
            'id': e.id,
            'tender_id': e.tender.id if e.tender else None,
            'tender': tender_display,
            'category': e.category,
            'description': e.description or '',
            'amount': float(e.amount),
            'date': e.date.isoformat(),
        })

    return JsonResponse({'expenses': expenses})



# ----- Expense list page with basic filtering & pagination -----

def expense_list(request):
    companies = Company.objects.all().order_by('name')
    tenders_qs = Tender.objects.select_related('company').order_by('-start_date')

    qs = Expense.objects.select_related('tender__company').order_by('-date')

    company_id = request.GET.get('company')
    tender_id = request.GET.get('tender')

    selected_company_name = None
    selected_tender_name = None

    if company_id:
        qs = qs.filter(tender__company_id=company_id)
        tenders_qs = tenders_qs.filter(company_id=company_id)
        try:
            selected_company_name = Company.objects.get(pk=company_id).name
        except Company.DoesNotExist:
            selected_company_name = None

    if tender_id:
        qs = qs.filter(tender_id=tender_id)
        try:
            selected_tender_name = Tender.objects.get(pk=tender_id).tender_no
        except Tender.DoesNotExist:
            selected_tender_name = None

    paginator = Paginator(qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_amount = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    context = {
        'title': 'All Expenses',
        'companies': companies,
        'tenders': tenders_qs,
        'expenses': page_obj,
        'total_amount': total_amount,
        'selected_company': int(company_id) if company_id else None,
        'selected_tender': int(tender_id) if tender_id else None,
        'selected_company_name': selected_company_name,
        'selected_tender_name': selected_tender_name,
    }
    return render(request, 'tracker/expense_list.html', context)
