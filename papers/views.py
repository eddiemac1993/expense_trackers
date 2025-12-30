from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings

from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from .models import PaperEntry
from .forms import PaperEntryForm, PaperItemFormSet, ClientForm


def create_paper_entry(request):
    if request.method == 'POST':
        entry_form = PaperEntryForm(request.POST)
        client_form = ClientForm(request.POST)
        formset = PaperItemFormSet(request.POST)

        if entry_form.is_valid() and client_form.is_valid() and formset.is_valid():
            client = client_form.save()

            entry = entry_form.save(commit=False)
            entry.client = client
            entry.save()

            items = formset.save(commit=False)
            for item in items:
                item.entry = entry
                item.save()

            entry.calculate_totals()
            entry.save()

            return redirect('paper_list')
    else:
        entry_form = PaperEntryForm()
        client_form = ClientForm()
        formset = PaperItemFormSet()

    return render(request, 'papers/entry_form.html', {
        'form': entry_form,
        'client_form': client_form,
        'formset': formset
    })


def paper_list(request):
    entries = PaperEntry.objects.all().order_by('-created_at')
    return render(request, 'papers/paper_list.html', {'entries': entries})


def paper_preview(request, entry_id, paper_type):
    entry = get_object_or_404(PaperEntry, id=entry_id)
    template = f"papers/{entry.company.slug}/{paper_type}.html"
    return render(request, template, {"entry": entry})


def paper_pdf(request, entry_id, paper_type):
    """
    Render a paper (quotation, invoice, etc.) as a PDF using WeasyPrint
    """
    entry = get_object_or_404(PaperEntry, id=entry_id)

    template_path = f"papers/{entry.company.slug}/{paper_type}.html"
    template = get_template(template_path)

    html_string = template.render({
        "entry": entry,
        "request": request,
        "is_pdf": True,
    })


    font_config = FontConfiguration()

    html = HTML(
        string=html_string,
        base_url='/',                 # important
    )

    pdf = html.write_pdf(
        font_config=font_config,
        presentational_hints=True
    )

    filename = f"{paper_type}_{entry.paper_number or entry.id}.pdf"

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    return response
