from decimal import Decimal

from django.db import models


CURRENCY_CHOICES = [
    ("ZMW", "ZMW"),
    ("USD", "USD"),
]


def exchange_rate_for_zmw(currency, exchange_rate):
    if currency == "USD" and exchange_rate and exchange_rate > 0:
        return exchange_rate

    return Decimal("1.00")


class ProjectRecord(models.Model):
    STATUS_CHOICES = [
        ("Not started", "Not started"),
        ("Started", "Started"),
        ("Partial Done", "Partial Done"),
        ("Done", "Done"),
    ]

    TAX_CHOICES = [
        ("NONE", "No Tax"),
        ("TOT", "5% TOT"),
        ("VAT", "16% VAT"),
    ]

    company = models.CharField(max_length=255)
    project_supply = models.CharField("Project / Supply", max_length=255)
    client = models.CharField(max_length=255)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    contract_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    paid_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="ZMW")
    exchange_rate = models.DecimalField(
        "Exchange rate to ZMW",
        max_digits=12,
        decimal_places=4,
        default=1,
        help_text="Use the ZMW value for 1 USD. Leave as 1 for ZMW projects.",
    )

    is_internal = models.BooleanField(default=False, db_index=True)

    tax_type = models.CharField(
        max_length=10,
        choices=TAX_CHOICES,
        default="NONE"
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="Not started"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_date", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "project_supply", "client"],
                name="unique_company_project_client"
            )
        ]

    @property
    def effective_exchange_rate(self):
        return exchange_rate_for_zmw(self.currency, self.exchange_rate)

    @property
    def uses_foreign_currency(self):
        return self.currency != "ZMW"

    @property
    def contract_value_zmw(self):
        return self.contract_value * self.effective_exchange_rate

    @property
    def paid_value_zmw(self):
        return self.paid_value * self.effective_exchange_rate

    @property
    def tax_rate(self):
        if self.tax_type == "TOT":
            return Decimal("0.05")

        if self.tax_type == "VAT":
            return Decimal("0.16")

        return Decimal("0.00")

    @property
    def contract_excluding_tax(self):
        if self.tax_rate > 0:
            return self.contract_value_zmw / (Decimal("1.00") + self.tax_rate)

        return self.contract_value_zmw

    @property
    def tax_amount(self):
        return self.contract_value_zmw - self.contract_excluding_tax

    @property
    def expense_value(self):
        return sum(
            (expense.amount_zmw for expense in self.expenses.all()),
            Decimal("0.00")
        )

    @property
    def profit_value(self):
        return self.contract_excluding_tax - self.expense_value

    @property
    def pending_payment_value(self):
        return self.contract_value_zmw - self.paid_value_zmw

    @property
    def balance_value(self):
        return self.pending_payment_value

    def __str__(self):
        return f"{self.company} - {self.project_supply}"


class PendingProjectRecord(models.Model):
    STATUS_CHOICES = [
        ("Submitted", "Submitted"),
        ("Awaiting Award", "Awaiting Award"),
        ("Not Awarded", "Not Awarded"),
        ("Awarded", "Awarded"),
    ]

    company = models.CharField(max_length=255)
    project_supply = models.CharField("Project / Supply", max_length=255)
    client = models.CharField(max_length=255)

    submission_date = models.DateField(null=True, blank=True)
    expected_award_date = models.DateField(null=True, blank=True)

    contract_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="ZMW")
    exchange_rate = models.DecimalField(
        "Exchange rate to ZMW",
        max_digits=12,
        decimal_places=4,
        default=1,
        help_text="Use the ZMW value for 1 USD. Leave as 1 for ZMW projects.",
    )

    tax_type = models.CharField(
        max_length=10,
        choices=ProjectRecord.TAX_CHOICES,
        default="NONE"
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="Submitted"
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["submission_date", "created_at"]

    @property
    def effective_exchange_rate(self):
        return exchange_rate_for_zmw(self.currency, self.exchange_rate)

    @property
    def uses_foreign_currency(self):
        return self.currency != "ZMW"

    @property
    def contract_value_zmw(self):
        return self.contract_value * self.effective_exchange_rate

    def __str__(self):
        return f"{self.company} - {self.project_supply}"


class ExpenseTag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProjectExpense(models.Model):
    project = models.ForeignKey(
        ProjectRecord,
        on_delete=models.CASCADE,
        related_name="expenses"
    )

    date = models.DateField()
    reason = models.CharField(max_length=255)

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="ZMW")
    exchange_rate = models.DecimalField(
        "Exchange rate to ZMW",
        max_digits=12,
        decimal_places=4,
        default=1,
        help_text="Use the ZMW value for 1 USD. Leave as 1 for ZMW expenses.",
    )

    tag = models.ForeignKey(
        ExpenseTag,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    @property
    def effective_exchange_rate(self):
        return exchange_rate_for_zmw(self.currency, self.exchange_rate)

    @property
    def uses_foreign_currency(self):
        return self.currency != "ZMW"

    @property
    def amount_zmw(self):
        return self.amount * self.effective_exchange_rate

    def __str__(self):
        return f"{self.project.project_supply} - {self.currency} {self.amount}"
