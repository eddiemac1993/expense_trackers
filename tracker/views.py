from django.shortcuts import render, redirect
from .models import Company, Tender, Expense
from .forms import CompanyForm, TenderForm, ExpenseForm

def dashboard(request):
    companies = Company.objects.all()
    tenders = Tender.objects.all()
    return render(request, 'tracker/dashboard.html', {
        'companies': companies,
        'tenders': tenders,
    })

def add_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = CompanyForm()
    return render(request, 'tracker/add_company.html', {'form': form})

def add_tender(request):
    if request.method == 'POST':
        form = TenderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = TenderForm()
    return render(request, 'tracker/add_tender.html', {'form': form})

def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'tracker/add_expense.html', {'form': form})
