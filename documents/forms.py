from django import forms
from .models import Document


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            'title',
            'file',
            'category',
            'description',
            'expiry_date',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control'
            })

        self.fields['expiry_date'].widget.attrs.update({
            'type': 'date'
        })

    def clean_file(self):
        file = self.cleaned_data.get('file')
    
        if not file:
            raise forms.ValidationError("Please select a file to upload.")
    
        allowed_extensions = [
            '.pdf', '.doc', '.docx',
            '.xls', '.xlsx',
            '.jpg', '.jpeg', '.png',
        ]
    
        import os
        ext = os.path.splitext(file.name)[1].lower()
    
        if ext not in allowed_extensions:
            raise forms.ValidationError(
                "Unsupported file type. Allowed: PDF, Word, Excel, images."
            )
    
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            raise forms.ValidationError(
                "File size must not exceed 10MB."
            )
    
        return file

