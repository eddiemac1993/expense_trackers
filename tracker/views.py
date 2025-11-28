from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import Sum, Count
from django.contrib import messages
from .models import Company, Tender, Expense
from .forms import CompanyForm, TenderForm, ExpenseForm
from decimal import Decimal
import json
from django.db.models import Sum, Count



def dashboard(request):
    companies = Company.objects.all()
    tenders = Tender.objects.select_related('company').all()[:50]  # Limit for initial load
    return render(request, 'tracker/dashboard.html', {
        'companies': companies,
        'tenders': tenders,
    })


# Create Views
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


def add_tender(request):
    if request.method == 'POST':
        form = TenderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tender added successfully!')
            return redirect('tracker:dashboard')
    else:
        form = TenderForm()
    return render(request, 'tracker/form.html', {'form': form, 'title': 'Add Tender'})


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


# Edit Views
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


def tender_edit(request, pk):
    obj = get_object_or_404(Tender, pk=pk)
    if request.method == 'POST':
        form = TenderForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tender updated successfully!')
            return redirect('tracker:dashboard')
    else:
        form = TenderForm(instance=obj)
    return render(request, 'tracker/form.html', {'form': form, 'title': 'Edit Tender'})


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


# Delete Views
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


# API Endpoints
def api_tenders(request):
    """Return JSON list of tenders filtered by query params"""
    qs = Tender.objects.select_related('company').prefetch_related('expenses').all()

    # Apply filters
    company_id = request.GET.get('company')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if company_id:
        qs = qs.filter(company_id=company_id)
    if status:
        qs = qs.filter(payment_status=status)
    if date_from:
        qs = qs.filter(start_date__gte=date_from)
    if date_to:
        qs = qs.filter(end_date__lte=date_to)

    data = []
    for tender in qs:
        total_expenses = tender.total_expenses()
        profit = tender.profit()
        data.append({
            'id': tender.id,
            'tender_no': tender.tender_no,
            'company': tender.company.name,
            'company_id': tender.company.id,
            'client_name': tender.client_name,
            'total_value': float(tender.total_value),
            'total_expenses': float(total_expenses),
            'profit': float(profit),
            'payment_status': tender.payment_status,
            'start_date': tender.start_date.isoformat() if tender.start_date else None,
            'end_date': tender.end_date.isoformat() if tender.end_date else None,
            'expense_count': tender.expenses.count(),
        })

    return JsonResponse({'tenders': data})


def api_tenders_by_company(request):
    """Return aggregated totals per company for Chart.js"""
    qs = Tender.objects.select_related('company').values(
        'company__name', 'company_id'
    ).annotate(
        total_value=Sum('total_value'),
        total_expenses=Sum('expenses__amount'),
        tender_count=Count('id')
    )

    labels = []
    values = []
    profits = []
    expenses = []

    for row in qs:
        labels.append(row['company__name'])
        tv = row['total_value'] or Decimal('0.00')
        te = row['total_expenses'] or Decimal('0.00')
        values.append(float(tv))
        expenses.append(float(te))
        profits.append(float(tv - te))

    return JsonResponse({
        'labels': labels,
        'values': values,
        'expenses': expenses,
        'profits': profits
    })


def api_summary(request):
    """Return summary statistics for the dashboard"""
    total_tenders = Tender.objects.count()
    total_companies = Company.objects.count()
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_tender_value = Tender.objects.aggregate(total=Sum('total_value'))['total'] or Decimal('0.00')
    total_profit = total_tender_value - total_expenses

    # Status counts
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
        'total_profit': float(total_profit),
        'status_counts': status_counts
    })

# tracker/views.py (add near your other api_... functions)
from django.http import JsonResponse
from .models import Expense

def api_expenses(request):
    """
    Return JSON list of expenses for dashboard. Lightweight, limited to recent rows.
    """
    qs = Expense.objects.select_related('tender__company').order_by('-date')[:1000]
    expenses = []
    for e in qs:
        tender_display = f"{e.tender.tender_no} - {e.tender.company.name}" if e.tender else ""
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

from decimal import Decimal
from django.core.paginator import Paginator
from django.db.models import Sum

def expense_list(request):
    """
    Expense list with filtering by company and tender, and simple pagination.
    """
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
