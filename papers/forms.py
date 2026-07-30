from django import forms
from django.forms import inlineformset_factory
from .models import CompanyBankAccount, PaperEntry, PaperItem, Client


class PaperEntryForm(forms.ModelForm):
    class Meta:
        model = PaperEntry
        fields = [
            "company",
            "bank_account",
            "tax_percentage",
            "prepared_by",
            "delivered_by",
            "received_by",
            "date",
            "kind",
            "parent",
        ]
        widgets = {
            "company": forms.Select(attrs={"class": "form-select"}),
            "bank_account": forms.Select(attrs={"class": "form-select", "id": "id_bank_account"}),
            "tax_percentage": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "prepared_by": forms.TextInput(attrs={"class": "form-control"}),
            "delivered_by": forms.TextInput(attrs={"class": "form-control"}),
            "received_by": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),

            "kind": forms.Select(attrs={"class": "form-select", "id": "id_kind"}),
            "parent": forms.Select(attrs={"class": "form-select", "id": "id_parent"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = PaperEntry.objects.filter(kind=PaperEntry.Kind.REAL)
        self.fields["parent"].required = False
        self.fields["bank_account"].queryset = (
            CompanyBankAccount.objects
            .select_related("company")
            .order_by("company__name", "-is_default", "bank_name", "label")
        )
        self.fields["bank_account"].label = "Bank details for this document"
        self.fields["bank_account"].required = False
        self.fields["bank_account"].empty_label = "Use company default bank"

    def clean(self):
        cleaned = super().clean()
        kind = cleaned.get("kind")
        parent = cleaned.get("parent")
        company = cleaned.get("company")
        bank_account = cleaned.get("bank_account")

        if kind == PaperEntry.Kind.SUPPORTING and not parent:
            raise forms.ValidationError("Supporting paper must be linked to a Real paper.")
        if kind != PaperEntry.Kind.SUPPORTING:
            cleaned["parent"] = None

        if bank_account and company and bank_account.company_id != company.id:
            self.add_error(
                "bank_account",
                "Choose a bank account that belongs to the selected company."
            )

        return cleaned

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
