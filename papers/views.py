from django.db import transaction
from django.db.models import Max
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import select_template
from xhtml2pdf import pisa

from .forms import ClientForm, PaperEntryForm, PaperItemFormSet
from .models import PaperEntry, get_default_client


PAPER_TYPES = {
    "quotation": "Quotation",
    "invoice": "Invoice",
    "delivery": "Delivery Note",
    "receipt": "Receipt",
    "purchase_order": "Purchase Order",
}


def make_paper_number(kind):
    if kind == PaperEntry.Kind.PURCHASE_ORDER:
        prefix = "PO"
    elif kind == PaperEntry.Kind.SUPPORTING:
        prefix = "SUP"
    else:
        prefix = "PAP"

    next_sequence = (PaperEntry.objects.aggregate(m=Max("id"))["m"] or 0) + 100

    while True:
        paper_number = f"{prefix}-{next_sequence:04d}"
        if not PaperEntry.objects.filter(paper_number=paper_number).exists():
            return paper_number
        next_sequence += 1


@transaction.atomic
def create_paper_entry(request):
    if request.method == "POST":
        entry_form = PaperEntryForm(request.POST)
        client_form = ClientForm(request.POST)
        formset = PaperItemFormSet(request.POST)

        if entry_form.is_valid() and formset.is_valid():
            client = None
            name = (client_form.data.get("name") or "").strip()

            if name:
                if client_form.is_valid():
                    client = client_form.save()
                else:
                    return render(request, "papers/entry_form.html", {
                        "form": entry_form,
                        "client_form": client_form,
                        "formset": formset,
                    })
            else:
                client = get_default_client()

            entry = entry_form.save(commit=False)
            entry.client = client

            paper_number = (entry.paper_number or "").strip()
            if not paper_number or PaperEntry.objects.filter(paper_number=paper_number).exists():
                entry.paper_number = make_paper_number(entry.kind)

            entry.save()

            items = formset.save(commit=False)
            for item in items:
                item.entry = entry
                item.save()

            for obj in formset.deleted_objects:
                obj.delete()

            entry.calculate_totals()
            entry.save(update_fields=["subtotal", "tax_amount", "total"])

            return redirect("paper_list")
    else:
        initial_kind = request.GET.get("kind", "")
        if initial_kind not in PaperEntry.Kind.values:
            initial_kind = PaperEntry.Kind.REAL

        entry_form = PaperEntryForm(initial={"kind": initial_kind})
        client_form = ClientForm()
        formset = PaperItemFormSet()

    return render(request, "papers/entry_form.html", {
        "form": entry_form,
        "client_form": client_form,
        "formset": formset,
    })


def edit_paper_entry(request, entry_id):
    entry = get_object_or_404(PaperEntry, id=entry_id)
    client = entry.client

    if request.method == "POST":
        entry_form = PaperEntryForm(request.POST, instance=entry)
        client_form = ClientForm(request.POST, instance=client)
        formset = PaperItemFormSet(request.POST, instance=entry)

        if entry_form.is_valid() and client_form.is_valid() and formset.is_valid():
            client = client_form.save()

            entry = entry_form.save(commit=False)
            entry.client = client
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


def paper_list(request):
    kind = request.GET.get("kind", PaperEntry.Kind.REAL).strip()
    qs = (
        PaperEntry.objects
        .select_related("company", "client", "bank_account")
        .all()
        .order_by("-created_at")
    )

    if kind in (PaperEntry.Kind.REAL, PaperEntry.Kind.SUPPORTING, PaperEntry.Kind.PURCHASE_ORDER):
        qs = qs.filter(kind=kind)
    else:
        kind = ""

    return render(request, "papers/paper_list.html", {
        "entries": qs,
        "kind": kind,
        "real_count": PaperEntry.objects.filter(kind=PaperEntry.Kind.REAL).count(),
        "support_count": PaperEntry.objects.filter(kind=PaperEntry.Kind.SUPPORTING).count(),
        "purchase_order_count": PaperEntry.objects.filter(kind=PaperEntry.Kind.PURCHASE_ORDER).count(),
    })


def paper_display_number(entry):
    return entry.display_paper_number


def effective_paper_type(entry, paper_type):
    if entry.kind == PaperEntry.Kind.PURCHASE_ORDER:
        return "purchase_order"

    return paper_type


def paper_template(entry, paper_type):
    paper_type = effective_paper_type(entry, paper_type)

    if paper_type not in PAPER_TYPES:
        raise Http404("Unsupported paper type")

    return select_template([
        f"papers/{entry.company.slug}/{paper_type}.html",
        f"papers/{paper_type}.html",
    ])


def paper_preview(request, entry_id, paper_type):
    entry = get_object_or_404(
        PaperEntry.objects.select_related("company", "client", "bank_account"),
        id=entry_id
    )
    paper_type = effective_paper_type(entry, paper_type)

    entry.paper_number = paper_display_number(entry)

    template = paper_template(entry, paper_type)
    return HttpResponse(template.render({
        "entry": entry,
        "paper_type": PAPER_TYPES[paper_type],
    }, request))


def paper_pdf(request, entry_id, paper_type):
    entry = get_object_or_404(
        PaperEntry.objects.select_related("company", "client", "bank_account"),
        id=entry_id
    )
    paper_type = effective_paper_type(entry, paper_type)

    display_number = paper_display_number(entry)
    entry.paper_number = display_number

    template = paper_template(entry, paper_type)
    html_string = template.render({
        "entry": entry,
        "request": request,
        "is_pdf": True,
        "paper_type": PAPER_TYPES[paper_type],
    })

    filename = f"{paper_type}_{entry.company.slug.upper()}_{display_number}.pdf"
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    try:
        from weasyprint import HTML
        from weasyprint.text.fonts import FontConfiguration

        font_config = FontConfiguration()
        html = HTML(
            string=html_string,
            base_url=request.build_absolute_uri("/"),
        )
        response.write(html.write_pdf(
            font_config=font_config,
            presentational_hints=True,
        ))
        return response
    except Exception:
        pisa_status = pisa.CreatePDF(
            html_string,
            dest=response,
            encoding="UTF-8",
            link_callback=lambda uri, rel: uri,
        )

        if pisa_status.err:
            return HttpResponse("Error generating PDF document", status=500)

    return response
