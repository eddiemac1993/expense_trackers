from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings

from .models import PaperEntry
from .forms import PaperEntryForm, PaperItemFormSet, ClientForm

from django.shortcuts import render, redirect
from django.db import transaction
from django.db.models import Max

from .models import PaperEntry, get_default_client
from .forms import PaperEntryForm, ClientForm, PaperItemFormSet


def make_paper_number(kind):
    prefix = "SUP" if kind == PaperEntry.Kind.SUPPORTING else "PAP"
    next_sequence = (PaperEntry.objects.aggregate(m=Max("id"))["m"] or 0) + 100

    while True:
        paper_number = f"{prefix}-{next_sequence:04d}"
        if not PaperEntry.objects.filter(paper_number=paper_number).exists():
            return paper_number
        next_sequence += 1


@transaction.atomic
def create_paper_entry(request):
    if request.method == 'POST':
        entry_form = PaperEntryForm(request.POST)
        client_form = ClientForm(request.POST)
        formset = PaperItemFormSet(request.POST)

        # Client form is OPTIONAL now, so don't require client_form.is_valid() to proceed
        if entry_form.is_valid() and formset.is_valid():
            # -------- CLIENT (optional) --------
            client = None
            name = (client_form.data.get('name') or '').strip()

            if name:
                # Only validate/save client when user actually provided a name
                if client_form.is_valid():
                    client = client_form.save()
                else:
                    # client has name but has errors -> show them
                    return render(request, 'papers/entry_form.html', {
                        'form': entry_form,
                        'client_form': client_form,
                        'formset': formset
                    })
            else:
                # Use default "Walk-In Client"
                client = get_default_client()

            # -------- ENTRY --------
            entry = entry_form.save(commit=False)
            entry.client = client

            # If paper_number is empty OR duplicates, generate a readable reference.
            pn = (entry.paper_number or '').strip()
            if not pn or PaperEntry.objects.filter(paper_number=pn).exists():
                entry.paper_number = make_paper_number(entry.kind)

            entry.save()

            # -------- ITEMS --------
            items = formset.save(commit=False)
            for item in items:
                item.entry = entry
                item.save()

            # If any were removed via formset delete checkboxes
            for obj in formset.deleted_objects:
                obj.delete()

            # -------- TOTALS --------
            entry.calculate_totals()
            entry.save(update_fields=['subtotal', 'tax_amount', 'total'])

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


def edit_paper_entry(request, entry_id):
    entry = get_object_or_404(PaperEntry, id=entry_id)
    client = entry.client

    if request.method == "POST":
        entry_form = PaperEntryForm(request.POST, instance=entry)
        client_form = ClientForm(request.POST, instance=client)
        formset = PaperItemFormSet(request.POST, instance=entry)

        if entry_form.is_valid() and client_form.is_valid() and formset.is_valid():
            # save client updates
            client = client_form.save()

            # IMPORTANT: prevent client being overwritten to None
            entry = entry_form.save(commit=False)
            entry.client = client  # keep the actual client
            entry.save()

            items = formset.save(commit=False)

            for obj in formset.deleted_objects:
                obj.delete()

            for item in items:
                item.entry = entry
                item.save()

            entry.calculate_totals()
            entry.save(update_fields=["subtotal", "tax_amount", "total"])

            return redirect("paper_list")

    else:
        entry_form = PaperEntryForm(instance=entry)
        client_form = ClientForm(instance=client)
        formset = PaperItemFormSet(instance=entry)

    return render(request, "papers/entry_form.html", {
        "form": entry_form,
        "client_form": client_form,
        "formset": formset,
        "is_edit": True,
        "entry": entry,
    })

# views.py
def paper_list(request):
    kind = request.GET.get("kind", PaperEntry.Kind.REAL).strip()  # REAL / SUPPORT
    qs = PaperEntry.objects.all().order_by("-created_at")

    if kind in (PaperEntry.Kind.REAL, PaperEntry.Kind.SUPPORTING):
        qs = qs.filter(kind=kind)
    else:
        kind = ""

    return render(request, "papers/paper_list.html", {
        "entries": qs,
        "kind": kind,
        "real_count": PaperEntry.objects.filter(kind=PaperEntry.Kind.REAL).count(),
        "support_count": PaperEntry.objects.filter(kind=PaperEntry.Kind.SUPPORTING).count(),
    })


def paper_display_number(entry):
    return entry.display_paper_number

def paper_preview(request, entry_id, paper_type):
    entry = get_object_or_404(PaperEntry, id=entry_id)

    # Override for display only.
    entry.paper_number = paper_display_number(entry)

    template = f"papers/{entry.company.slug}/{paper_type}.html"
    return render(request, template, {"entry": entry})



def paper_pdf(request, entry_id, paper_type):
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration

    entry = get_object_or_404(PaperEntry, id=entry_id)

    # Override ONLY for display inside PDF.
    display_number = paper_display_number(entry)
    entry.paper_number = display_number

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

    filename = f"{paper_type}_{entry.company.slug.upper()}_{display_number}.pdf"

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
