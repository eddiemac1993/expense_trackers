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

    # Extract numeric sequence
    raw_sequence = entry.paper_number.split("/")[-1]

    # Convert and apply offset
    display_sequence = int(raw_sequence) + 99

    # Override for display only
    entry.paper_number = f"{display_sequence:04d}"

    template = f"papers/{entry.company.slug}/{paper_type}.html"
    return render(request, template, {"entry": entry})



def paper_pdf(request, entry_id, paper_type):
    entry = get_object_or_404(PaperEntry, id=entry_id)

    # 1. Extract internal sequence (0003)
    raw_sequence = entry.paper_number.split("/")[-1]

    # 2. Apply offset so display starts at 100
    display_sequence = int(raw_sequence) + 99

    # 3. Override ONLY for display inside PDF
    entry.paper_number = f"{display_sequence:04d}"

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
        base_url=request.build_absolute_uri('/'),  # ✅ FIXED
    )

    pdf = html.write_pdf(
        font_config=font_config,
        presentational_hints=True
    )

    # 4. CLEAN DOWNLOAD NAME (this is the key)
    filename = f"{paper_type}_{entry.company.slug.upper()}_{display_sequence:04d}.pdf"

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
