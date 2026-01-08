from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import FileResponse, Http404
import os

from .forms import DocumentUploadForm
from .models import Document, Category
from django.db.models import Q


def upload_document(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)

            # user may be anonymous now
            if request.user.is_authenticated:
                document.uploaded_by = request.user
            else:
                document.uploaded_by = None

            document.save()

            messages.success(request, 'Document uploaded successfully.')
            return redirect('documents:document_list')
    else:
        form = DocumentUploadForm()

    return render(request, 'documents/upload.html', {
        'form': form
    })


def document_list(request):
    documents = Document.objects.filter(is_active=True)
    categories = Category.objects.all()

    q = request.GET.get('q')
    category_id = request.GET.get('category')

    if q:
        documents = documents.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q)
        )

    if category_id:
        documents = documents.filter(category_id=category_id)

    return render(request, 'documents/list.html', {
        'documents': documents,
        'categories': categories,
    })



def download_document(request, pk):
    try:
        document = Document.objects.get(pk=pk, is_active=True)
    except Document.DoesNotExist:
        raise Http404("Document not found")

    return FileResponse(
        document.file.open('rb'),
        as_attachment=True,
        filename=os.path.basename(document.file.name)
    )
