from django.db import models
from django.utils.timezone import now


class Company(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)  # avoid migration pain
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

    @property
    def default_bank_account(self):
        return (
            self.bank_accounts.filter(is_default=True).first()
            or self.bank_accounts.first()
        )

    @property
    def bank_details(self):
        bank_account = self.default_bank_account
        if not bank_account:
            return ""

        return bank_account.formatted_details


class CompanyBankAccount(models.Model):
    company = models.ForeignKey(
        Company,
        related_name="bank_accounts",
        on_delete=models.CASCADE,
    )
    label = models.CharField(max_length=120, blank=True)
    bank_name = models.CharField(max_length=120)
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=80, blank=True)
    account_number_usd = models.CharField("USD account number", max_length=80, blank=True)
    branch = models.CharField(max_length=120, blank=True)
    branch_code = models.CharField(max_length=80, blank=True)
    sort_code = models.CharField(max_length=80, blank=True)
    swift_code = models.CharField(max_length=80, blank=True)
    notes = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["company__name", "-is_default", "bank_name", "label"]

    def __str__(self):
        return f"{self.company.name} - {self.display_label}"

    @property
    def display_label(self):
        if self.label:
            return self.label

        if self.branch:
            return f"{self.bank_name} ({self.branch})"

        return self.bank_name

    @property
    def formatted_details(self):
        lines = [
            f"Bank Name: {self.bank_name}",
            f"Account Name: {self.account_name}",
        ]

        if self.account_number:
            lines.append(f"Account Number: {self.account_number}")

        if self.account_number_usd:
            lines.append(f"USD Account Number: {self.account_number_usd}")

        if self.branch:
            lines.append(f"Branch: {self.branch}")

        if self.branch_code:
            lines.append(f"Branch Code: {self.branch_code}")

        if self.sort_code:
            lines.append(f"Sort Code: {self.sort_code}")

        if self.swift_code:
            lines.append(f"SWIFT Code: {self.swift_code}")

        if self.notes:
            lines.append(self.notes)

        return "\n".join(lines)


class Client(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)  # optional
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


def get_default_client():
    client, _ = Client.objects.get_or_create(
        name="Walk-In Client",
        defaults={
            "phone": "0000000000",
            "contact_person": "",
            "email": "",
            "address": "",
        },
    )
    return client


class PaperEntry(models.Model):
    class Kind(models.TextChoices):
        REAL = "REAL", "Real"
        SUPPORTING = "SUPPORT", "Supporting"
        PURCHASE_ORDER = "PO", "Purchase Order"
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    bank_account = models.ForeignKey(
        CompanyBankAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paper_entries",
    )

    # allow empty client on the form; database will still have one after save()
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.REAL)

    # only used when kind == SUPPORT
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="supporting_papers",
        limit_choices_to={"kind": Kind.REAL},
    )
    paper_number = models.CharField(max_length=50, unique=True, blank=True)  # KEEP AS BEFORE
    date = models.DateField(default=now)

    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    prepared_by = models.CharField(max_length=255, blank=True)
    delivered_by = models.CharField(max_length=255, blank=True)
    received_by = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_paper_number

    @property
    def display_paper_number(self):
        raw_number = (self.paper_number or "").strip()
        if not raw_number:
            return f"Entry {self.id or ''}".strip()

        if raw_number.isdigit():
            if self.kind == self.Kind.PURCHASE_ORDER:
                prefix = "PO"
            elif self.kind == self.Kind.SUPPORTING:
                prefix = "SUP"
            else:
                prefix = "PAP"
            return f"{prefix}-{int(raw_number) + 99:04d}"

        return raw_number

    @property
    def selected_bank_account(self):
        return self.bank_account or self.company.default_bank_account

    @property
    def selected_bank_details(self):
        bank_account = self.selected_bank_account
        if not bank_account:
            return ""

        return bank_account.formatted_details

    def calculate_totals(self):
        self.subtotal = sum(item.amount for item in self.items.all())
        self.tax_amount = (self.tax_percentage / 100) * self.subtotal if self.tax_percentage > 0 else 0
        self.total = self.subtotal + self.tax_amount

    def save(self, *args, **kwargs):
        if not self.client:
            self.client = get_default_client()
        super().save(*args, **kwargs)


class PaperItem(models.Model):
    entry = models.ForeignKey(PaperEntry, related_name="items", on_delete=models.CASCADE)
    description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True)

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
