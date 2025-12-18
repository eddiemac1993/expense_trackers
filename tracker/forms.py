from django import forms
from .models import Company, Tender, Expense

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'

class TenderForm(forms.ModelForm):
    class Meta:
        model = Tender
        fields = '__all__'

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = '__all__'

# tracker/forms.py (append)
from django import forms
from .models import Payment

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'note']  # tender is included as hidden in the template
