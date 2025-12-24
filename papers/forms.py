from django import forms
from django.forms import inlineformset_factory
from .models import PaperEntry, PaperItem, Client


class PaperEntryForm(forms.ModelForm):
    class Meta:
        model = PaperEntry
        fields = [
            'company',
            'client',
            'tax_percentage',
            'prepared_by',
        ]
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'tax_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prepared_by': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'contact_person', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PaperItemForm(forms.ModelForm):
    class Meta:
        model = PaperItem
        fields = ['description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }


PaperItemFormSet = inlineformset_factory(
    PaperEntry,
    PaperItem,
    form=PaperItemForm,
    extra=1,
    can_delete=True
)
