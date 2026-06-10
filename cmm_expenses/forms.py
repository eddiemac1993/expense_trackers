from django import forms
from .models import (
    ProjectRecord,
    ProjectExpense,
    PendingProjectRecord,
)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = ProjectRecord
        fields = "__all__"


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = ProjectExpense
        fields = "__all__"


class PendingProjectForm(forms.ModelForm):
    class Meta:
        model = PendingProjectRecord
        fields = "__all__"